"""SimilarityIndex build: a normalised FAISS inner-product index, the id list and the manifest.

The index step reads the trained vectors from Parquet in batches (BR5.4), scales each batch to
unit length so the inner product is the cosine (BR5.1), drops zero-length vectors, and adds the
batch to an exact index. It then checks the ids against the catalogue and the row counts against
each other (BR5.2) and writes the manifest last (BR6.6), so an interrupted build leaves the app
unable to start. Every file is written under a temporary name and renamed when complete (BR6.1).
The artist file (`artists.sqlite`) is written by the catalogue step, not here.
"""

import sqlite3
import sys
import time
from collections.abc import Iterable, Iterator, Sequence
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path

import faiss
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from listenbrainz_recs import fsutil, steps
from listenbrainz_recs.errors import DataError, RecsError
from listenbrainz_recs.manifest import new_manifest, write_manifest
from listenbrainz_recs.paths import (
    ARTIST_IDS_FILE,
    ARTISTS_DB_FILE,
    FAISS_INDEX_FILE,
    MANIFEST_FILE,
    output_paths,
)
from listenbrainz_recs.settings import load_settings

BATCH_ROWS = 50_000  # vectors read from Parquet and added to the index at a time (BR5.4)
CHECK_BATCH = 500  # ids checked against the catalogue per query (below SQLite's variable limit)
MIN_NORM = 1e-12  # a vector shorter than this counts as zero length

# One batch of vectors: artist ids and a matrix with one row per id.
VectorBatch = tuple[Sequence[str], np.ndarray]


@dataclass
class IndexSummary:
    """Counters for the one-line run summary (NFR2.13)."""

    artists: int
    dropped: int
    dimension: int
    seconds: float

    def line(self) -> str:
        return (
            f"index: {self.artists} artists indexed ({self.dropped} dropped), "
            f"dimension {self.dimension}, wrote {FAISS_INDEX_FILE}, "
            f"{ARTIST_IDS_FILE}, {MANIFEST_FILE} in {self.seconds:.1f}s"
        )


def _check_ids_in_catalogue(catalogue: Path, ids: Sequence[str]) -> None:
    """Stop naming the first id that the catalogue does not hold (BR5.2)."""
    rerun = "Run the catalogue step: uv run listenbrainz-recs-catalogue"
    if not catalogue.is_file():
        raise DataError(f"Missing the artist catalogue {catalogue}. {rerun}")
    try:
        with closing(sqlite3.connect(catalogue.resolve().as_uri() + "?mode=ro", uri=True)) as db:
            for start in range(0, len(ids), CHECK_BATCH):
                chunk = list(ids[start : start + CHECK_BATCH])
                marks = ",".join("?" * len(chunk))
                known = {
                    mbid
                    for (mbid,) in db.execute(
                        f"SELECT mbid FROM artist WHERE mbid IN ({marks})",  # "?" marks only
                        chunk,
                    )
                }
                for mbid in chunk:
                    if mbid not in known:
                        raise DataError(
                            f"Indexed artist {mbid} is not in the catalogue {catalogue}. "
                            f"The catalogue and the vectors come from different data. {rerun}"
                        )
    except sqlite3.Error as exc:
        raise DataError(f"Cannot read the catalogue {catalogue}: {exc}. {rerun}") from exc


def build_index_from_batches(
    models_dir: Path, batches: Iterable[VectorBatch], source_dump: str
) -> IndexSummary:
    """Build the index files from batches of vectors and write the manifest last.

    The old manifest is removed first, so an interrupted build leaves none (BR6.6). Ids must be
    unique across batches; the catalogue in `models_dir` must hold every indexed id (BR5.2).
    """
    started = time.perf_counter()
    models_dir.mkdir(parents=True, exist_ok=True)
    fsutil.clear(models_dir / MANIFEST_FILE)

    index: faiss.IndexFlatIP | None = None
    ids: list[str] = []
    seen: set[str] = set()
    dropped = 0
    for batch_ids, vectors in batches:
        matrix = np.ascontiguousarray(vectors, dtype=np.float32)
        if matrix.ndim != 2 or matrix.shape[0] != len(batch_ids):
            raise DataError("Artist ids and vectors do not line up.")
        if index is not None and matrix.shape[1] != index.d:
            raise DataError(f"Vector length changed from {index.d} to {matrix.shape[1]}.")
        norms = np.linalg.norm(matrix, axis=1)
        usable = np.isfinite(matrix).all(axis=1) & (norms > MIN_NORM)
        dropped += int((~usable).sum())
        kept = [mbid for mbid, ok in zip(batch_ids, usable, strict=True) if ok]
        duplicates = [mbid for mbid in kept if mbid in seen]
        if duplicates or len(set(kept)) != len(kept):
            raise DataError("Duplicate artist ids among the vectors.")
        if not kept:
            continue
        matrix = np.ascontiguousarray(matrix[usable])
        faiss.normalize_L2(matrix)  # unit length, so inner product equals cosine (BR5.1)
        if index is None:
            index = faiss.IndexFlatIP(int(matrix.shape[1]))
        index.add(matrix)  # type: ignore[call-arg]
        ids.extend(kept)
        seen.update(kept)
    if index is None or not ids:
        raise DataError("No usable artist vectors to index.")
    if index.ntotal != len(ids):
        raise DataError(f"The index holds {index.ntotal} rows for {len(ids)} ids.")

    _check_ids_in_catalogue(models_dir / ARTISTS_DB_FILE, ids)

    faiss_path = models_dir / FAISS_INDEX_FILE
    faiss_tmp = fsutil.tmp_path(faiss_path)
    try:
        faiss.write_index(index, str(faiss_tmp))
        fsutil.publish(faiss_tmp, faiss_path)
    except (RuntimeError, OSError) as exc:
        fsutil.clear(faiss_tmp)
        raise DataError(f"Cannot write {faiss_path}: {exc}") from exc
    fsutil.write_text_atomic(models_dir / ARTIST_IDS_FILE, "\n".join(ids) + "\n")

    write_manifest(models_dir, new_manifest(source_dump, len(ids)))  # last (BR6.6)
    return IndexSummary(
        artists=len(ids),
        dropped=dropped,
        dimension=int(index.d),
        seconds=time.perf_counter() - started,
    )


def build_index_files(
    models_dir: Path, artist_ids: Sequence[str], vectors: np.ndarray, source_dump: str
) -> IndexSummary:
    """Build the index files from vectors already in memory (one batch)."""
    return build_index_from_batches(models_dir, [(artist_ids, vectors)], source_dump)


def _vector_matrix(column: pa.ChunkedArray, source: Path) -> np.ndarray:
    """Turn an Arrow list-of-float column into a 2-D array, checking every list has one length."""
    values = column.combine_chunks()
    if values.null_count:
        raise DataError(f"Some vectors in {source} are missing.")
    offsets = np.asarray(values.offsets.to_numpy(zero_copy_only=False))
    lengths = np.unique(np.diff(offsets))
    if len(lengths) != 1:
        raise DataError(f"Vectors in {source} do not all have the same length.")
    flat = values.flatten().to_numpy(zero_copy_only=False)
    return flat.reshape(len(values), int(lengths[0]))


def read_vector_batches(vectors_dir: Path, batch_rows: int = BATCH_ROWS) -> Iterator[VectorBatch]:
    """Read the trained vector Parquet files batch by batch (BR5.4)."""
    files = sorted(vectors_dir.glob("*.parquet"))
    if not files:
        raise DataError(f"No vector files in {vectors_dir}. Run the train step again.")
    for file in files:
        try:
            for batch in pq.ParquetFile(file).iter_batches(
                batch_size=batch_rows, columns=["artist_mbid", "features"]
            ):
                table = pa.Table.from_batches([batch])
                yield (
                    table.column("artist_mbid").to_pylist(),
                    _vector_matrix(table.column("features"), file),
                )
        except (OSError, KeyError, pa.ArrowException) as exc:
            raise DataError(f"Cannot read the trained vectors {file}: {exc}") from exc


def build(work_dir: Path, models_dir: Path, *, batch_rows: int = BATCH_ROWS) -> IndexSummary:
    """Run the index step. Raises `RecsError` subclasses on failure.

    The train and catalogue markers must both come from the current prepare run (BR6.3, BR6.4);
    nothing is changed when an input is missing or stale.
    """
    started = time.perf_counter()
    prepared = steps.require_prepared(work_dir)
    trained = steps.require_marker(work_dir, steps.TRAIN)
    catalogued = steps.require_marker(work_dir, steps.CATALOGUE)
    steps.require_current(work_dir, trained)
    steps.require_current(work_dir, catalogued)
    paths = output_paths(work_dir, models_dir)

    steps.clear_marker(work_dir, steps.INDEX)  # an interrupted run must not look finished
    source_dump = str(prepared.details.get("source_dump", "unknown"))
    summary = build_index_from_batches(
        models_dir, read_vector_batches(paths.vectors, batch_rows), source_dump
    )
    summary.seconds = time.perf_counter() - started
    steps.write_marker(work_dir, steps.INDEX, input_run_id=trained.run_id, details=asdict(summary))
    return summary


def main() -> int:
    """Command entry point: `uv run listenbrainz-recs-index`."""
    try:
        settings = load_settings()
        summary = build(settings.work_dir, settings.models_dir)
    except RecsError as exc:
        print(f"index failed: {exc}", file=sys.stderr)
        return 1
    print(summary.line())
    return 0


if __name__ == "__main__":
    sys.exit(main())

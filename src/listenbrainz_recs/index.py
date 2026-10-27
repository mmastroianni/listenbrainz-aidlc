"""SimilarityIndex build: normalised FAISS inner-product index, id list, artist file, manifest.

Files follow contract C2. Each is written under a temporary name and renamed when complete, and
the manifest is written last (BR4.1), so an interrupted build leaves no manifest.
"""

import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from listenbrainz_recs import fsutil
from listenbrainz_recs.catalog import ArtistRow, write_artist_db
from listenbrainz_recs.errors import DataError, RecsError
from listenbrainz_recs.manifest import new_manifest, write_manifest
from listenbrainz_recs.paths import (
    ARTIST_IDS_FILE,
    ARTIST_NAMES_DIR,
    ARTISTS_DB_FILE,
    FAISS_INDEX_FILE,
    INTERACTIONS_DIR,
    MANIFEST_FILE,
    PREPARED_MARKER,
    TRAINED_MARKER,
    VECTORS_DIR,
)
from listenbrainz_recs.settings import load_settings


@dataclass
class IndexSummary:
    """Counters for the one-line run summary (NFR2.5)."""

    artists: int
    dropped: int
    dimension: int
    seconds: float

    def line(self) -> str:
        return (
            f"index: {self.artists} artists indexed ({self.dropped} dropped), "
            f"dimension {self.dimension}, wrote {ARTISTS_DB_FILE}, {FAISS_INDEX_FILE}, "
            f"{ARTIST_IDS_FILE}, {MANIFEST_FILE} in {self.seconds:.1f}s"
        )


def build_index_files(
    models_dir: Path,
    artist_ids: Sequence[str],
    vectors: np.ndarray,
    names: Mapping[str, str],
    listener_counts: Mapping[str, int],
    source_dump: str,
) -> IndexSummary:
    """Write all C2 files for the given artists. Artists with unusable vectors are dropped."""
    started = time.perf_counter()
    matrix = np.ascontiguousarray(vectors, dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[0] != len(artist_ids):
        raise DataError("Artist ids and vectors do not line up.")
    if len(set(artist_ids)) != len(artist_ids):
        raise DataError("Duplicate artist ids among the vectors.")

    norms = np.linalg.norm(matrix, axis=1)
    usable = np.isfinite(matrix).all(axis=1) & (norms > 1e-12)
    if not usable.any():
        raise DataError("No usable artist vectors to index.")
    kept_ids = [mbid for mbid, ok in zip(artist_ids, usable, strict=True) if ok]
    matrix = np.ascontiguousarray(matrix[usable])
    faiss.normalize_L2(matrix)  # unit length, so inner product equals cosine (BR3.1)

    models_dir.mkdir(parents=True, exist_ok=True)
    fsutil.clear(models_dir / MANIFEST_FILE)  # an interrupted build must leave no manifest

    rows = (
        ArtistRow(mbid, names.get(mbid, ""), max(1, int(listener_counts.get(mbid, 1))))
        for mbid in kept_ids
    )
    write_artist_db(models_dir / ARTISTS_DB_FILE, rows)

    index = faiss.IndexFlatIP(matrix.shape[1])
    index.add(matrix)  # type: ignore[call-arg]
    faiss_path = models_dir / FAISS_INDEX_FILE
    faiss_tmp = fsutil.tmp_path(faiss_path)
    faiss.write_index(index, str(faiss_tmp))
    fsutil.publish(faiss_tmp, faiss_path)

    fsutil.write_text_atomic(models_dir / ARTIST_IDS_FILE, "\n".join(kept_ids) + "\n")

    write_manifest(models_dir, new_manifest(source_dump, len(kept_ids)))  # last (BR4.1)
    return IndexSummary(
        artists=len(kept_ids),
        dropped=len(artist_ids) - len(kept_ids),
        dimension=int(matrix.shape[1]),
        seconds=time.perf_counter() - started,
    )


def build(work_dir: Path, models_dir: Path) -> IndexSummary:
    """Run the index step from the trained vectors. Raises `RecsError` subclasses on failure."""
    started = time.perf_counter()
    fsutil.require_marker(work_dir, PREPARED_MARKER, "prepare")
    fsutil.require_marker(work_dir, TRAINED_MARKER, "train")
    try:
        prepared = fsutil.read_json(work_dir / PREPARED_MARKER)
        vector_table = pq.read_table(work_dir / VECTORS_DIR)
        artist_ids = vector_table.column("artist_mbid").to_pylist()
        vectors = np.array(vector_table.column("features").to_pylist(), dtype=np.float32)
        names = {
            row["artist_mbid"]: row["artist_name"]
            for row in pq.read_table(work_dir / ARTIST_NAMES_DIR).to_pylist()
        }
        counts_table = pq.read_table(work_dir / INTERACTIONS_DIR, columns=["artist_mbid"])
        listener_counts: dict[str, int] = {}
        for mbid in counts_table.column("artist_mbid").to_pylist():
            listener_counts[mbid] = listener_counts.get(mbid, 0) + 1  # (listener, artist) unique
    except (OSError, ValueError, KeyError, pa.ArrowException) as exc:
        raise DataError(f"Cannot read the trained data in {work_dir}: {exc}") from exc

    summary = build_index_files(
        models_dir,
        artist_ids,
        vectors,
        names,
        listener_counts,
        str(prepared.get("source_dump", "unknown")),
    )
    summary.seconds = time.perf_counter() - started
    return summary


def main() -> int:
    """Command entry point: `uv run listenbrainz-recs-index`."""
    settings = load_settings()
    try:
        summary = build(settings.work_dir, settings.models_dir)
    except RecsError as exc:
        print(f"index failed: {exc}", file=sys.stderr)
        return 1
    print(summary.line())
    return 0


if __name__ == "__main__":
    sys.exit(main())

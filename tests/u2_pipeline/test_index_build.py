"""Index step: batch reading, id and row agreement, manifest last, missing and stale input."""

import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

import faiss
import numpy as np
import pytest
from fixtures.sample_data import KEPT_ARTISTS

from listenbrainz_recs import index as index_module
from listenbrainz_recs.catalogue import CatalogueArtist, write_catalogue_db
from listenbrainz_recs.errors import DataError, StartupError, StepOrderError
from listenbrainz_recs.index import (
    IndexSummary,
    build,
    build_index_files,
    build_index_from_batches,
    read_vector_batches,
)
from listenbrainz_recs.manifest import read_manifest
from listenbrainz_recs.paths import (
    ARTIST_IDS_FILE,
    ARTISTS_DB_FILE,
    CATALOGUE_MARKER,
    FAISS_INDEX_FILE,
    INDEX_MARKER,
    MANIFEST_FILE,
    VECTORS_DIR,
)
from listenbrainz_recs.steps import PREPARE, TRAIN, read_marker, write_marker
from listenbrainz_recs.store import load_store


@pytest.fixture
def work_and_models(pipeline_outputs: tuple[Path, Path], tmp_path: Path) -> tuple[Path, Path]:
    """Private copies of the fixture pipeline's work and models folders."""
    work, models = pipeline_outputs
    shutil.copytree(work, tmp_path / "work")
    shutil.copytree(models, tmp_path / "models")
    return tmp_path / "work", tmp_path / "models"


def _all_rows(index: faiss.Index) -> np.ndarray:
    return np.vstack([index.reconstruct(i) for i in range(index.ntotal)])


def test_index_agrees_with_the_id_file_the_manifest_and_the_catalogue(
    pipeline_outputs: tuple[Path, Path],
) -> None:
    _, models = pipeline_outputs
    index = faiss.read_index(str(models / FAISS_INDEX_FILE))
    ids = (models / ARTIST_IDS_FILE).read_text(encoding="utf-8").split()
    assert len(ids) == index.ntotal == read_manifest(models).artist_count == KEPT_ARTISTS
    assert np.allclose(np.linalg.norm(_all_rows(index), axis=1), 1.0, atol=1e-5)
    with closing(sqlite3.connect(models / ARTISTS_DB_FILE)) as db:
        in_catalogue = {r[0] for r in db.execute("SELECT mbid FROM artist")}
    assert set(ids) <= in_catalogue
    assert load_store(models).manifest.artist_count == KEPT_ARTISTS  # the app accepts the files


def test_step_writes_its_marker_and_a_counts_only_summary(
    work_and_models: tuple[Path, Path],
) -> None:
    work, models = work_and_models
    summary = build(work, models)
    assert isinstance(summary, IndexSummary)
    assert (summary.artists, summary.dropped) == (KEPT_ARTISTS, 0)
    marker = read_marker(work, "index")
    trained = read_marker(work, TRAIN)
    assert marker is not None and trained is not None
    assert marker.input_run_id == trained.run_id
    assert (work / INDEX_MARKER).is_file()
    line = summary.line()
    assert line.startswith("index: ") and "artists indexed" in line and "dimension 8" in line


def test_batch_boundaries_give_the_same_index_as_one_batch(
    work_and_models: tuple[Path, Path], tmp_path: Path
) -> None:
    work, models = work_and_models
    outputs = []
    counts: list[int] = []
    for name, rows in (("small", 5), ("whole", 100_000)):
        target = tmp_path / name
        target.mkdir()
        shutil.copy(models / ARTISTS_DB_FILE, target / ARTISTS_DB_FILE)
        batches = list(read_vector_batches(work / VECTORS_DIR, rows))
        counts.append(len(batches))
        build_index_from_batches(target, batches, "dump")
        outputs.append(
            (
                (target / ARTIST_IDS_FILE).read_text(encoding="utf-8"),
                _all_rows(faiss.read_index(str(target / FAISS_INDEX_FILE))),
            )
        )
    assert counts[0] > counts[1]  # the small batch size really splits the files
    assert outputs[0][0] == outputs[1][0]
    assert np.allclose(outputs[0][1], outputs[1][1])


def test_an_id_missing_from_the_catalogue_stops_the_step_without_a_manifest(
    work_and_models: tuple[Path, Path],
) -> None:
    work, models = work_and_models
    with closing(sqlite3.connect(models / ARTISTS_DB_FILE)) as db:
        victim = db.execute("SELECT mbid FROM artist ORDER BY mbid LIMIT 1").fetchone()[0]
        db.execute("DELETE FROM artist WHERE mbid = ?", (victim,))
        db.commit()
    with pytest.raises(DataError, match=victim):
        build(work, models)
    assert not (models / MANIFEST_FILE).exists()
    assert read_marker(work, "index") is None


def test_interrupted_build_leaves_no_manifest_and_the_app_refuses_to_start(
    work_and_models: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    work, models = work_and_models
    assert (models / MANIFEST_FILE).is_file()  # an earlier complete build

    def fail(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(index_module, "write_manifest", fail)
    with pytest.raises(OSError, match="disk full"):
        build(work, models)
    assert not (models / MANIFEST_FILE).exists()
    assert not list(models.glob("*.tmp"))
    assert read_marker(work, "index") is None
    with pytest.raises(StartupError, match="index"):
        load_store(models)


def test_missing_catalogue_or_train_input_names_the_step_to_run(
    work_and_models: tuple[Path, Path],
) -> None:
    work, models = work_and_models
    (work / CATALOGUE_MARKER).unlink()
    with pytest.raises(StepOrderError, match="catalogue"):
        build(work, models)
    (work / "trained.json").unlink()
    with pytest.raises(StepOrderError, match="train"):
        build(work, models)
    assert (models / MANIFEST_FILE).is_file()  # a refused run changes nothing


def test_stale_inputs_are_refused_naming_the_step_to_run_again(
    work_and_models: tuple[Path, Path],
) -> None:
    work, models = work_and_models
    trained = read_marker(work, TRAIN)
    assert trained is not None
    write_marker(work, TRAIN, input_run_id="an-older-prepare-run")  # train made from older data
    with pytest.raises(StepOrderError, match=r"older prepare run.*train"):
        build(work, models)
    write_marker(work, PREPARE)  # prepare run again: its report no longer matches
    with pytest.raises(StepOrderError, match="prepare"):
        build(work, models)


def test_zero_length_vectors_are_dropped_and_bad_input_is_refused(tmp_path: Path) -> None:
    models = tmp_path
    artists = [CatalogueArtist(m, m.upper(), None, 9 - i, []) for i, m in enumerate("abcd")]
    write_catalogue_db(models / ARTISTS_DB_FILE, artists)
    vectors = np.array([[1, 0], [0, 0], [np.nan, 1], [0, 2]], dtype=np.float32)
    summary = build_index_files(models, list("abcd"), vectors, "dump")
    assert (summary.artists, summary.dropped) == (2, 2)
    assert (models / ARTIST_IDS_FILE).read_text(encoding="utf-8").split() == ["a", "d"]
    with pytest.raises(DataError, match="No usable"):
        build_index_files(models, ["a"], np.zeros((1, 2), dtype=np.float32), "dump")
    with pytest.raises(DataError, match="line up"):
        build_index_files(models, ["a"], vectors, "dump")
    with pytest.raises(DataError, match="Duplicate"):
        build_index_files(models, ["a", "a"], np.ones((2, 2), dtype=np.float32), "dump")
    with pytest.raises(DataError, match="length changed"):
        build_index_from_batches(
            models,
            [
                (["a"], np.ones((1, 2), dtype=np.float32)),
                (["b"], np.ones((1, 3), dtype=np.float32)),
            ],
            "dump",
        )
    assert not (models / MANIFEST_FILE).exists()


def test_missing_catalogue_file_and_empty_vector_folder_are_clear_errors(tmp_path: Path) -> None:
    with pytest.raises(DataError, match="catalogue step"):
        build_index_files(tmp_path, ["a"], np.ones((1, 2), dtype=np.float32), "dump")
    with pytest.raises(DataError, match="No vector files"):
        list(read_vector_batches(tmp_path))
    broken = tmp_path / "vectors"
    broken.mkdir()
    (broken / "part-0.parquet").write_bytes(b"not parquet")
    with pytest.raises(DataError, match=r"Cannot read the trained vectors"):
        list(read_vector_batches(broken))

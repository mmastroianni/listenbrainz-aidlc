"""Built files for the walking skeleton: C2 files, unit-length index rows, manifest last.

Changed by u2-pipeline: the artist file now comes from the catalogue step, so these tests build the
catalogue first (hand-made) and then the index, and the index-only checks moved to
`tests/u2_pipeline/test_index_build.py`.
"""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

import faiss
import numpy as np
import pytest
from conftest import build_models
from fixtures.sample_data import artist_mbid

from listenbrainz_recs import index as index_module
from listenbrainz_recs.manifest import FORMAT_VERSION
from listenbrainz_recs.paths import (
    ARTIST_IDS_FILE,
    ARTISTS_DB_FILE,
    C2_FILES,
    FAISS_INDEX_FILE,
    MANIFEST_FILE,
)
from listenbrainz_recs.text import normalize_name

IDS = ["a", "b", "c"]
VECTORS = np.array([[3.0, 0.0], [0.0, 2.0], [1.0, 1.0]], dtype=np.float32)
NAMES = {"a": "Alpha", "b": "Béta", "c": ""}
COUNTS = {"a": 5, "b": 2}


def _build(models: Path, ids=IDS, vectors=VECTORS) -> None:
    build_models(models, ids, vectors, NAMES, COUNTS, "dump-1")


def test_all_c2_files_are_written_with_a_manifest(tmp_path: Path) -> None:
    _build(tmp_path)
    assert {p.name for p in tmp_path.iterdir()} == set(C2_FILES)
    manifest = json.loads((tmp_path / MANIFEST_FILE).read_text(encoding="utf-8"))
    assert manifest["format_version"] == FORMAT_VERSION
    assert manifest["artist_count"] == 3
    assert manifest["source_dump"] == "dump-1"
    assert manifest["built_at"].endswith("Z")


def test_index_rows_are_unit_length_and_line_up_with_the_id_list(tmp_path: Path) -> None:
    _build(tmp_path)
    index = faiss.read_index(str(tmp_path / FAISS_INDEX_FILE))
    ids = (tmp_path / ARTIST_IDS_FILE).read_text(encoding="utf-8").split()
    assert ids == IDS
    rows = np.vstack([index.reconstruct(i) for i in range(index.ntotal)])
    assert np.allclose(np.linalg.norm(rows, axis=1), 1.0, atol=1e-5)
    # Scores are cosine similarity: a and c are 45 degrees apart.
    scores, labels = index.search(rows[:1], 3)
    assert labels[0][0] == 0
    assert scores[0][1] == pytest.approx(np.sqrt(0.5), abs=1e-5)


def test_artist_file_holds_names_counts_and_empty_extras(tmp_path: Path) -> None:
    _build(tmp_path)
    with closing(sqlite3.connect(tmp_path / ARTISTS_DB_FILE)) as db:
        rows = db.execute("SELECT mbid, name, description, listener_count FROM artist").fetchall()
        assert sorted(rows) == [
            ("a", "Alpha", None, 5),
            ("b", "Béta", None, 2),
            ("c", "c", None, 1),  # no name falls back to the id
        ]
        assert db.execute("SELECT COUNT(*) FROM artist_genre").fetchone() == (0,)
        assert db.execute("SELECT norm_name FROM artist_search WHERE mbid='b'").fetchone() == (
            "beta",
        )


def test_unusable_vectors_are_dropped_not_indexed(tmp_path: Path) -> None:
    vectors = np.array([[1.0, 0.0], [0.0, 0.0], [np.nan, 1.0]], dtype=np.float32)
    _build(tmp_path, vectors=vectors)
    assert (tmp_path / ARTIST_IDS_FILE).read_text(encoding="utf-8").split() == ["a"]


def test_interrupted_build_leaves_no_manifest_and_no_temp_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _build(tmp_path)  # an older, complete build
    assert (tmp_path / MANIFEST_FILE).exists()

    def fail(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(index_module, "write_manifest", fail)
    with pytest.raises(OSError, match="disk full"):
        _build(tmp_path)
    assert not (tmp_path / MANIFEST_FILE).exists()  # BR4.1: the app would refuse to start
    assert not list(tmp_path.glob("*.tmp"))


def test_index_step_on_pipeline_output_covers_every_artist(
    pipeline_outputs: tuple[Path, Path],
) -> None:
    _, models = pipeline_outputs
    ids = (models / ARTIST_IDS_FILE).read_text(encoding="utf-8").split()
    assert len(ids) == 3 * 8 + 1
    with closing(sqlite3.connect(models / ARTISTS_DB_FILE)) as db:
        in_db = {r[0] for r in db.execute("SELECT mbid FROM artist")}
        name, count = db.execute(
            "SELECT name, listener_count FROM artist WHERE mbid=?", (artist_mbid(97),)
        ).fetchone()
    assert set(ids) == in_db
    assert (name, count) == ("Five Spelled", 5)  # the five-listener artist, most used spelling


def test_normalize_name_ignores_case_accents_and_spacing() -> None:
    assert normalize_name("  Émile   ZOLA ") == "emile zola"

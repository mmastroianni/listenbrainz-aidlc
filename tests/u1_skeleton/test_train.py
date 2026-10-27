"""SimilarityTraining on the walking-skeleton path: one vector per kept artist (BR2.1; AC4.2.1).

Changed by u2-pipeline: training reads the kept artists from the prepare step's output, the fixture
uses a small rank (the full-size settings are checked in `tests/u2_pipeline/test_train_full.py`),
and an unreadable input is now reported by the shared Spark failure message.
"""

import json
import shutil
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import pytest
from conftest import FIXTURE_TRAIN_SETTINGS
from fixtures.sample_data import ARTISTS_PER_GROUP, KEPT_ARTISTS, group_of
from pyspark.sql import SparkSession

from listenbrainz_recs.errors import DataError, StepOrderError
from listenbrainz_recs.paths import INTERACTIONS_DIR, TRAINED_MARKER, VECTORS_DIR
from listenbrainz_recs.train import train


@pytest.fixture(scope="module")
def trained(prepared_work: Path, spark: SparkSession, tmp_path_factory: pytest.TempPathFactory):
    work = tmp_path_factory.mktemp("work_train")
    shutil.copytree(prepared_work, work, dirs_exist_ok=True)
    summary = train(work, spark, settings=FIXTURE_TRAIN_SETTINGS)
    return work, summary


def test_every_prepared_artist_has_exactly_one_vector(trained) -> None:
    work, summary = trained
    prepared = set(pq.read_table(work / INTERACTIONS_DIR).column("artist_mbid").to_pylist())
    ids = [row["artist_mbid"] for row in pq.read_table(work / VECTORS_DIR).to_pylist()]
    assert len(ids) == len(set(ids)) == summary.artists == KEPT_ARTISTS
    assert set(ids) == prepared


def test_vectors_have_the_same_finite_length(trained) -> None:
    work, summary = trained
    rows = pq.read_table(work / VECTORS_DIR).to_pylist()
    matrix = np.array([row["features"] for row in rows], dtype=np.float32)
    assert matrix.shape == (summary.artists, FIXTURE_TRAIN_SETTINGS.rank)
    assert np.isfinite(matrix).all()


def test_artists_listened_to_together_end_up_closer(trained) -> None:
    work, _ = trained
    rows = pq.read_table(work / VECTORS_DIR).to_pylist()
    # Fixture artists are "00000000-0000-4000-8000-<index>"; ignore the extra artist (>= 24).
    rows = [r for r in rows if int(r["artist_mbid"].rsplit("-", 1)[1]) < 3 * ARTISTS_PER_GROUP]
    groups = np.array([group_of(int(r["artist_mbid"].rsplit("-", 1)[1])) for r in rows])
    matrix = np.array([r["features"] for r in rows], dtype=np.float64)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    sims = matrix @ matrix.T
    same = groups[:, None] == groups[None, :]
    off_diagonal = ~np.eye(len(rows), dtype=bool)
    assert sims[same & off_diagonal].mean() > sims[~same].mean()


def test_training_writes_a_marker(trained) -> None:
    work, summary = trained
    marker = json.loads((work / TRAINED_MARKER).read_text(encoding="utf-8"))
    assert marker["step"] == "train"
    assert marker["details"]["artists"] == summary.artists
    assert "train:" in summary.line()


def test_training_before_prepare_names_the_missing_step(tmp_path: Path) -> None:
    with pytest.raises(StepOrderError, match="prepare"):
        train(tmp_path)


def test_unreadable_prepared_data_is_a_clear_error(
    prepared_work: Path, tmp_path: Path, spark: SparkSession
) -> None:
    work = tmp_path / "work"
    shutil.copytree(prepared_work, work)
    shutil.rmtree(work / INTERACTIONS_DIR)
    (work / INTERACTIONS_DIR).mkdir()
    (work / INTERACTIONS_DIR / "part-0.parquet").write_text("not parquet", encoding="utf-8")
    with pytest.raises(DataError, match="train step failed"):
        train(work, spark, settings=FIXTURE_TRAIN_SETTINGS)
    assert not (work / TRAINED_MARKER).exists()

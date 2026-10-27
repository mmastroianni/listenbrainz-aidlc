"""SimilarityTraining: one vector per artist from prepared listen counts (BR2.1; AC4.2.1)."""

import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import pytest
from fixtures.sample_data import ARTISTS_PER_GROUP, group_of
from pyspark.sql import SparkSession

from listenbrainz_recs.errors import DataError, StepOrderError
from listenbrainz_recs.paths import INTERACTIONS_DIR, PREPARED_MARKER, TRAINED_MARKER, VECTORS_DIR
from listenbrainz_recs.prep import prepare
from listenbrainz_recs.train import RANK, train


@pytest.fixture(scope="module")
def trained(sample_dump_root: Path, spark: SparkSession, tmp_path_factory: pytest.TempPathFactory):
    work = tmp_path_factory.mktemp("work_train")
    prepare(sample_dump_root, work)
    summary = train(work, spark)
    return work, summary


def test_every_prepared_artist_has_exactly_one_vector(trained) -> None:
    work, summary = trained
    prepared = set(pq.read_table(work / INTERACTIONS_DIR).column("artist_mbid").to_pylist())
    vectors = pq.read_table(work / VECTORS_DIR).to_pylist()
    ids = [row["artist_mbid"] for row in vectors]
    assert len(ids) == len(set(ids)) == summary.artists
    assert set(ids) == prepared


def test_vectors_have_the_same_finite_length(trained) -> None:
    work, summary = trained
    rows = pq.read_table(work / VECTORS_DIR).to_pylist()
    matrix = np.array([row["features"] for row in rows], dtype=np.float32)
    assert matrix.shape == (summary.artists, RANK)
    assert np.isfinite(matrix).all()


def test_artists_listened_to_together_end_up_closer(trained) -> None:
    work, _ = trained
    rows = pq.read_table(work / VECTORS_DIR).to_pylist()
    # Fixture artists are "00000000-0000-4000-8000-<index>"; ignore the lone extra artist (>= 24).
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
    assert marker["artists"] == summary.artists
    assert "train:" in summary.line()


def test_training_before_prepare_names_the_missing_step(tmp_path: Path) -> None:
    with pytest.raises(StepOrderError, match="prepare"):
        train(tmp_path)


def test_unreadable_prepared_data_is_a_clear_error(tmp_path: Path, spark: SparkSession) -> None:
    (tmp_path / PREPARED_MARKER).write_text("{}", encoding="utf-8")
    broken = tmp_path / INTERACTIONS_DIR
    broken.mkdir()
    (broken / "part-0.parquet").write_text("not parquet", encoding="utf-8")
    with pytest.raises(DataError, match="Spark training failed"):
        train(tmp_path, spark)
    assert not (tmp_path / TRAINED_MARKER).exists()

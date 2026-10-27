"""Shared fixtures: a tiny synthetic dump, one shared local SparkSession, fixture paths."""

from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest
from fixtures.sample_data import artist_mbid, write_sample
from pyspark.sql import SparkSession

from listenbrainz_recs.paths import LISTENING_DUMP_RELATIVE

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def sample_dump_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A data root holding a synthetic listening dump in the dump's own folder layout."""
    root = tmp_path_factory.mktemp("dump_root")
    write_sample(root.joinpath(*LISTENING_DUMP_RELATIVE))
    return root


@pytest.fixture(scope="session")
def pipeline_outputs(
    sample_dump_root: Path, spark: SparkSession, tmp_path_factory: pytest.TempPathFactory
) -> tuple[Path, Path]:
    """Runs prepare, train and index on the fixtures; returns (work dir, models dir)."""
    from listenbrainz_recs.index import build
    from listenbrainz_recs.prep import prepare
    from listenbrainz_recs.train import train

    work = tmp_path_factory.mktemp("pipeline_work")
    models = tmp_path_factory.mktemp("pipeline_models")
    prepare(sample_dump_root, work)
    train(work, spark)
    build(work, models)
    return work, models


TINY_VECTORS = np.array(
    [[1.0, 0.0], [0.9, 0.1], [0.5, 0.5], [0.0, 1.0], [-1.0, 0.0]], dtype=np.float32
)
TINY_NAMES = ["Alpha", "Béta", "Gamma", "Delta", "Epsilon"]
TINY_COUNTS = [50, 40, 30, 20, 10]


@pytest.fixture(scope="session")
def tiny_models(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Hand-made built files for five artists (ids `artist_mbid(1..5)`), no Spark needed.

    Seen from artist 1 the ranking is 2 (cos ~0.994), 3 (~0.707), 4 (0), 5 (-1).
    """
    from listenbrainz_recs.index import build_index_files

    ids = [artist_mbid(n) for n in range(1, 6)]
    models = tmp_path_factory.mktemp("tiny_models")
    build_index_files(
        models,
        ids,
        TINY_VECTORS,
        dict(zip(ids, TINY_NAMES, strict=True)),
        dict(zip(ids, TINY_COUNTS, strict=True)),
        "tiny-dump",
    )
    return models


@pytest.fixture
def single_artist_models(tmp_path: Path) -> Path:
    """Built files holding one artist, which therefore has no neighbours."""
    from listenbrainz_recs.index import build_index_files

    only = artist_mbid(1)
    build_index_files(
        tmp_path,
        [only],
        np.array([[1.0, 0.0]], dtype=np.float32),
        {only: "Only One"},
        {only: 3},
        "tiny-dump",
    )
    return tmp_path


@pytest.fixture(scope="session")
def spark() -> Iterator[SparkSession]:
    """One local SparkSession shared by the whole test session (keeps runs fast)."""
    from listenbrainz_recs.spark import get_spark

    session = get_spark("listenbrainz-recs-tests", master="local[2]", shuffle_partitions=4)
    yield session
    session.stop()

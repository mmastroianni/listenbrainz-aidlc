"""Shared fixtures: a tiny synthetic dump, one shared local SparkSession, hand-built models."""

import shutil
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path

import numpy as np
import pytest
from fixtures.sample_data import artist_mbid, write_dump_folder
from pyspark.sql import SparkSession

from listenbrainz_recs.train import TrainSettings

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Small model settings so fixture runs stay fast; the real defaults are tested separately.
FIXTURE_TRAIN_SETTINGS = TrainSettings(rank=8, max_iter=4)


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def sample_dump_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A data root holding a synthetic listening dump and MusicBrainz tables (real layout)."""
    return write_dump_folder(tmp_path_factory.mktemp("dump_root"))


@pytest.fixture(scope="session")
def spark() -> Iterator[SparkSession]:
    """One local SparkSession shared by the whole test session (keeps runs fast)."""
    from listenbrainz_recs.spark import get_spark

    session = get_spark(
        "listenbrainz-recs-tests", master="local[2]", shuffle_partitions=4, memory="2g"
    )
    yield session
    session.stop()


@pytest.fixture(scope="session")
def prepared_work(
    sample_dump_root: Path, spark: SparkSession, tmp_path_factory: pytest.TempPathFactory
) -> Path:
    """A work folder after the prepare step on the fixture dump. Copy it before changing it."""
    from listenbrainz_recs.prep import prepare

    work = tmp_path_factory.mktemp("prepared_work")
    prepare(sample_dump_root, work, spark)
    return work


@pytest.fixture(scope="session")
def pipeline_outputs(
    sample_dump_root: Path,
    prepared_work: Path,
    spark: SparkSession,
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, Path]:
    """Runs train, catalogue and index on the fixtures; returns (work dir, models dir)."""
    from listenbrainz_recs.catalogue import build_catalogue
    from listenbrainz_recs.index import build
    from listenbrainz_recs.train import train

    work = tmp_path_factory.mktemp("pipeline_work")
    shutil.copytree(prepared_work, work, dirs_exist_ok=True)
    models = tmp_path_factory.mktemp("pipeline_models")
    train(work, spark, settings=FIXTURE_TRAIN_SETTINGS)
    build_catalogue(sample_dump_root, work, models, spark)
    build(work, models)
    return work, models


def build_models(
    models: Path,
    ids: Sequence[str],
    vectors: np.ndarray,
    names: Mapping[str, str],
    counts: Mapping[str, int],
    source_dump: str = "tiny-dump",
) -> None:
    """Write hand-made C2 files: the catalogue first, then the index over the same ids."""
    from listenbrainz_recs.catalogue import CatalogueArtist, popularity_order, write_catalogue_db
    from listenbrainz_recs.index import build_index_files
    from listenbrainz_recs.paths import ARTISTS_DB_FILE

    rows = popularity_order(
        CatalogueArtist(mbid, names.get(mbid, ""), None, int(counts.get(mbid, 1)), [])
        for mbid in ids
    )
    models.mkdir(parents=True, exist_ok=True)
    write_catalogue_db(models / ARTISTS_DB_FILE, rows)
    build_index_files(models, ids, vectors, source_dump)


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
    ids = [artist_mbid(n) for n in range(1, 6)]
    models = tmp_path_factory.mktemp("tiny_models")
    build_models(
        models,
        ids,
        TINY_VECTORS,
        dict(zip(ids, TINY_NAMES, strict=True)),
        dict(zip(ids, TINY_COUNTS, strict=True)),
    )
    return models


@pytest.fixture(scope="session")
def search_models(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Named artists for the suggestion tests (ids 1 to 6), all indexed."""
    from fixtures.web_models import build_web_models, search_artists

    models = tmp_path_factory.mktemp("search_models")
    build_web_models(models, search_artists())
    return models


@pytest.fixture(scope="session")
def paging_models(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """46 chained artists: artist 1 has 45 neighbours, ranked in id order."""
    from fixtures.web_models import build_web_models, chain_artists

    models = tmp_path_factory.mktemp("paging_models")
    build_web_models(models, chain_artists(46))
    return models


@pytest.fixture(scope="session")
def exact_page_models(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """21 chained artists: artist 1 has exactly 20 neighbours."""
    from fixtures.web_models import build_web_models, chain_artists

    models = tmp_path_factory.mktemp("exact_page_models")
    build_web_models(models, chain_artists(21))
    return models


@pytest.fixture(scope="session")
def gap_models(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Three indexed artists plus one that is in the catalogue only."""
    from fixtures.web_models import build_web_models, gap_artists

    models = tmp_path_factory.mktemp("gap_models")
    build_web_models(models, gap_artists(), indexed=3)
    return models


@pytest.fixture
def single_artist_models(tmp_path: Path) -> Path:
    """Built files holding one artist, which therefore has no neighbours."""
    only = artist_mbid(1)
    build_models(
        tmp_path,
        [only],
        np.array([[1.0, 0.0]], dtype=np.float32),
        {only: "Only One"},
        {only: 3},
    )
    return tmp_path

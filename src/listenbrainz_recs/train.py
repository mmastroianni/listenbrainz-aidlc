"""SimilarityTraining: learn one vector per kept artist with Spark ALS on implicit listen counts.

Reads only the prepared listen counts (never the raw dump, BR2.4) and writes `vectors/` (artist id
plus vector) to the work folder. An artist whose vector has zero length is left out and counted
(BR2.1). The settings are the current app's and live in one block (BR2.2). Spark gets an explicit
memory setting and data stays in Spark and Parquet (BR2.3).
"""

import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from pyspark import StorageLevel
from pyspark.ml.feature import StringIndexer
from pyspark.ml.recommendation import ALS
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from listenbrainz_recs import fsutil, steps
from listenbrainz_recs.errors import DataError, RecsError
from listenbrainz_recs.paths import SPARK_TEMP_DIR, OutputPaths, output_paths
from listenbrainz_recs.settings import load_settings
from listenbrainz_recs.spark import get_spark, spark_failure


@dataclass(frozen=True)
class TrainSettings:
    """The current app's training settings (`pipeline/train_als.py`), held in one place (BR2.2)."""

    rank: int = 64
    max_iter: int = 10
    reg_param: float = 0.1
    alpha: float = 20.0
    seed: int = 42


DEFAULT_SETTINGS = TrainSettings()

# Stands in for the model fit: interactions -> (artist_mbid, features). Tests swap it.
FitFunction = Callable[[DataFrame, TrainSettings], DataFrame]


@dataclass
class TrainSummary:
    """Counters for the one-line run summary (NFR2.13)."""

    artists: int
    dropped: int
    rank: int
    seconds: float

    def line(self) -> str:
        return (
            f"train: {self.artists} artist vectors of rank {self.rank} "
            f"({self.dropped} zero-length dropped), wrote vectors/ in {self.seconds:.1f}s"
        )


def learn_vectors(interactions: DataFrame, settings: TrainSettings) -> DataFrame:
    """Fit implicit-feedback ALS on log(1 + listen count) and return (artist_mbid, features)."""
    indexer = StringIndexer(
        inputCol="artist_mbid",
        outputCol="item",
        handleInvalid="error",
        stringOrderType="alphabetAsc",
    )
    indexed = indexer.fit(interactions).transform(interactions)
    indexed = indexed.withColumn("item", F.col("item").cast("int"))
    training = indexed.select(
        F.col("user_id").alias("user"),
        F.col("item"),
        F.log1p(F.col("listen_count")).cast("float").alias("rating"),
    )
    als = ALS(
        rank=settings.rank,
        maxIter=settings.max_iter,
        regParam=settings.reg_param,
        alpha=settings.alpha,
        implicitPrefs=True,
        userCol="user",
        itemCol="item",
        ratingCol="rating",
        coldStartStrategy="drop",
        seed=settings.seed,
    )
    model = als.fit(training)
    mapping = indexed.select("artist_mbid", "item").distinct()
    return (
        model.itemFactors.withColumnRenamed("id", "item")
        .join(mapping, "item")
        .select("artist_mbid", F.col("features"))
    )


def _has_length(features: DataFrame) -> DataFrame:
    """Keep only vectors that are finite and not of zero length (BR2.1)."""
    squared = F.aggregate(
        F.col("features").cast("array<double>"), F.lit(0.0), lambda acc, x: acc + x * x
    )
    return features.where((squared > 1e-24) & (squared < float("inf")))


def train(
    work_dir: Path,
    spark: SparkSession | None = None,
    *,
    settings: TrainSettings = DEFAULT_SETTINGS,
    fit: FitFunction = learn_vectors,
) -> TrainSummary:
    """Run the train step and return its summary. Raises `RecsError` subclasses on failure."""
    started = time.perf_counter()
    paths = output_paths(work_dir, work_dir)  # train writes only under the work folder
    prepared = steps.require_prepared(work_dir)
    steps.clear_marker(work_dir, steps.TRAIN)  # an interrupted run must not look finished

    session = spark if spark is not None else get_spark("listenbrainz-recs-train")
    tmp = fsutil.tmp_path(paths.vectors)
    try:
        written, dropped = _fit_and_write(session, paths, tmp, settings, fit)
    except RecsError:
        fsutil.clear(tmp)
        raise
    except Exception as exc:  # integration boundary: Spark/JVM failures surface as many types
        fsutil.clear(tmp)
        raise spark_failure("train", exc) from exc

    fsutil.publish(tmp, paths.vectors)
    summary = TrainSummary(
        artists=written,
        dropped=dropped,
        rank=settings.rank,
        seconds=time.perf_counter() - started,
    )
    steps.write_marker(work_dir, steps.TRAIN, input_run_id=prepared.run_id, details=asdict(summary))
    return summary


def _fit_and_write(
    spark: SparkSession, paths: OutputPaths, tmp: Path, settings: TrainSettings, fit: FitFunction
) -> tuple[int, int]:
    """Fit, drop zero-length vectors, write Parquet; return (vectors written, vectors dropped)."""
    expected = spark.read.parquet(str(paths.artist_listeners)).count()
    interactions = spark.read.parquet(str(paths.interactions))
    vectors = fit(interactions, settings)
    vectors.persist(StorageLevel.DISK_ONLY)
    try:
        learned = vectors.count()
        if learned != expected:
            raise DataError(f"Training produced {learned} vectors for {expected} kept artists.")
        fsutil.clear(tmp)
        _has_length(vectors).coalesce(4).write.mode("overwrite").parquet(str(tmp))
    finally:
        vectors.unpersist()
    written = spark.read.parquet(str(tmp)).count()
    return written, learned - written


def main() -> int:
    """Command entry point: `uv run listenbrainz-recs-train`."""
    spark: SparkSession | None = None
    try:
        settings = load_settings()
        steps.require_prepared(settings.work_dir)  # fail before Spark starts
        spark = get_spark(
            "listenbrainz-recs-train",
            memory=settings.spark_memory,
            local_dir=settings.work_dir / SPARK_TEMP_DIR,
        )
        summary = train(settings.work_dir, spark)
    except RecsError as exc:
        print(f"train failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if spark is not None:
            spark.stop()
    print(summary.line())
    return 0


if __name__ == "__main__":
    sys.exit(main())

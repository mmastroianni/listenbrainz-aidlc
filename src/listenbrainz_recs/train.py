"""SimilarityTraining: learn one vector per artist with Spark ALS on implicit listen counts.

Reads the prepared listen counts (never the raw dump) and writes `vectors/` (artist id plus
vector) to the work folder (BR2.1).
"""

import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from pyspark.ml.recommendation import ALS
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from listenbrainz_recs import fsutil
from listenbrainz_recs.errors import DataError, RecsError
from listenbrainz_recs.fsutil import require_marker
from listenbrainz_recs.paths import (
    INTERACTIONS_DIR,
    PREPARED_MARKER,
    TRAINED_MARKER,
    VECTORS_DIR,
)
from listenbrainz_recs.settings import load_settings

RANK = 16  # small for the skeleton (NFR1.3); u2-pipeline sets the full-size values
MAX_ITER = 5
REG_PARAM = 0.1
ALPHA = 20.0
SEED = 42


@dataclass
class TrainSummary:
    """Counters for the one-line run summary (NFR2.5)."""

    artists: int
    rank: int
    seconds: float

    def line(self) -> str:
        return (
            f"train: {self.artists} artist vectors of rank {self.rank}, "
            f"wrote {VECTORS_DIR}/ in {self.seconds:.1f}s"
        )


def train(
    work_dir: Path,
    spark: SparkSession | None = None,
    *,
    rank: int = RANK,
    max_iter: int = MAX_ITER,
) -> TrainSummary:
    """Run the train step and return its summary. Raises `RecsError` subclasses on failure."""
    started = time.perf_counter()
    require_marker(work_dir, PREPARED_MARKER, "prepare")
    marker = work_dir / TRAINED_MARKER
    fsutil.clear(marker)

    owns_spark = spark is None
    try:
        if spark is None:
            from listenbrainz_recs.spark import get_spark

            spark = get_spark("listenbrainz-recs-train")
        artists = _fit_and_write(spark, work_dir, rank, max_iter)
    except RecsError:
        raise
    except Exception as exc:  # integration boundary: Spark/JVM failures surface as many types
        raise DataError(f"Spark training failed: {exc}") from exc
    finally:
        if owns_spark and spark is not None:
            spark.stop()

    summary = TrainSummary(artists=artists, rank=rank, seconds=time.perf_counter() - started)
    fsutil.write_json_atomic(marker, {"step": "train", **asdict(summary)})
    return summary


def _fit_and_write(spark: SparkSession, work_dir: Path, rank: int, max_iter: int) -> int:
    from pyspark.ml.feature import StringIndexer

    interactions = spark.read.parquet(str(work_dir / INTERACTIONS_DIR))
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
        rank=rank,
        maxIter=max_iter,
        regParam=REG_PARAM,
        alpha=ALPHA,
        implicitPrefs=True,
        userCol="user",
        itemCol="item",
        ratingCol="rating",
        coldStartStrategy="drop",
        seed=SEED,
    )
    model = als.fit(training)

    mapping = indexed.select("artist_mbid", "item").distinct()
    vectors = (
        model.itemFactors.withColumnRenamed("id", "item")
        .join(mapping, "item")
        .select("artist_mbid", F.col("features"))
    )
    tmp = fsutil.tmp_path(work_dir / VECTORS_DIR)
    fsutil.clear(tmp)
    vectors.coalesce(1).write.mode("overwrite").parquet(str(tmp))
    count = spark.read.parquet(str(tmp)).count()
    expected = mapping.count()
    if count != expected:
        raise DataError(f"Training produced {count} vectors for {expected} artists.")
    fsutil.publish(tmp, work_dir / VECTORS_DIR)
    return count


def main() -> int:
    """Command entry point: `uv run listenbrainz-recs-train`."""
    settings = load_settings()
    try:
        summary = train(settings.work_dir)
    except RecsError as exc:
        print(f"train failed: {exc}", file=sys.stderr)
        return 1
    print(summary.line())
    return 0


if __name__ == "__main__":
    sys.exit(main())

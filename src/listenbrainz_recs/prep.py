"""ListeningDataPrep: turn the listening dump into anonymous listen counts (BR1.3 to BR1.8, BR3.2).

Runs in Spark with an explicit column layout, so growth in the dump is a longer run and not a
larger Python memory footprint (NFR1.10). Per run it:

- counts and skips malformed lines and unusable entries (BR1.3, BR1.4),
- adds up repeated entries for one listener and artist (BR1.6),
- keeps artists with at least 5 distinct listeners (BR1.7),
- picks each kept artist's most used name (BR3.2),
- writes only (listener number, artist id, listen count) per row, the artist names, the kept
  artists' listener counts, a report, and a marker last (BR1.5, BR1.8, BR6.1).

The dump is only read (BR1.2). Output shows counts only, never a listener number (NFR3.6).
"""

import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from pyspark import StorageLevel
from pyspark.sql import Column, DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, LongType, StringType, StructField, StructType

from listenbrainz_recs import fsutil, steps
from listenbrainz_recs.dump_source import check_dump_files, dump_label, read_lines
from listenbrainz_recs.errors import DataError, RecsError
from listenbrainz_recs.paths import (
    ARTIST_LISTENERS_DIR,
    ARTIST_NAMES_DIR,
    INTERACTIONS_DIR,
    SPARK_TEMP_DIR,
    OutputPaths,
    output_paths,
)
from listenbrainz_recs.settings import load_settings
from listenbrainz_recs.spark import get_spark, spark_failure

MIN_LISTENERS = 5  # BR1.7: an artist needs this many distinct listeners
MAX_INT = 2**31 - 1  # listener numbers and counts must fit Spark ALS's integer columns

# The listening dump's own layout: one JSON object per line (BR1.3).
LINE_SCHEMA = StructType(
    [
        StructField("user_id", LongType()),
        StructField(
            "data",
            ArrayType(
                StructType(
                    [
                        StructField("artist_mbid", StringType()),
                        StructField("artist_name", StringType()),
                        StructField("listen_count", LongType()),
                    ]
                )
            ),
        ),
    ]
)


@dataclass
class PrepSummary:
    """Counters for the one-line run summary and the report (NFR2.13, NFR2.14)."""

    run_id: str
    source_dump: str
    lines_read: int = 0
    valid_records: int = 0
    skipped_records: int = 0
    skipped_entries: int = 0
    rows: int = 0
    artists: int = 0
    seconds: float = 0.0

    def line(self) -> str:
        return (
            f"prepare: read {self.lines_read} lines ({self.skipped_records} skipped), "
            f"{self.skipped_entries} entries skipped, {self.rows} listen counts, "
            f"{self.artists} artists kept, wrote {INTERACTIONS_DIR}/, {ARTIST_NAMES_DIR}/ and "
            f"{ARTIST_LISTENERS_DIR}/ in {self.seconds:.1f}s"
        )


def _is_usable(entry: Column) -> Column:
    """An entry with an artist id and a listen count of at least 1 (BR1.4)."""
    return (
        entry["artist_mbid"].isNotNull()
        & (F.trim(entry["artist_mbid"]) != "")
        & entry["listen_count"].isNotNull()
        & (entry["listen_count"] >= 1)
    )


def _read_text_lines(spark: SparkSession, dump_file: Path, max_lines: int | None) -> DataFrame:
    """The dump's lines as a one-column (`value`) DataFrame; a sample reads the first N lines."""
    if max_lines is None:
        return spark.read.text(str(dump_file))
    sample = [(line.rstrip("\r\n"),) for line in read_lines(dump_file, max_lines)]
    return spark.createDataFrame(sample, "value string")


def _parse(lines: DataFrame) -> DataFrame:
    """One row per line: listener number, entries, and whether the line is usable (BR1.3)."""
    record = F.from_json(F.col("value"), LINE_SCHEMA)
    parsed = lines.select(record["user_id"].alias("user_id"), record["data"].alias("data"))
    valid = (
        F.col("user_id").isNotNull()
        & F.col("data").isNotNull()
        & F.col("user_id").between(0, MAX_INT)
    )
    return parsed.withColumn("valid", valid)


def _write(frame: DataFrame, target: Path) -> None:
    fsutil.clear(target)
    frame.write.mode("overwrite").parquet(str(target))


def _build_outputs(
    spark: SparkSession, parsed: DataFrame, paths: OutputPaths, summary: PrepSummary
) -> dict[str, Path]:
    """Compute the three outputs into temporary folders and fill in the summary counts."""
    stats = parsed.agg(
        F.count(F.lit(1)).alias("total"),
        F.sum(F.col("valid").cast("int")).alias("valid"),
        F.sum(
            F.when(
                F.col("valid"),
                F.size(F.col("data")) - F.size(F.filter(F.col("data"), _is_usable)),
            ).otherwise(0)
        ).alias("bad_entries"),
    ).first()
    total = int(stats["total"] or 0) if stats else 0
    summary.lines_read = total
    summary.valid_records = int(stats["valid"] or 0) if stats else 0
    summary.skipped_records = total - summary.valid_records
    summary.skipped_entries = int(stats["bad_entries"] or 0) if stats else 0
    if summary.valid_records == 0:
        raise DataError(
            f"No usable listener line in the listening dump: all {total} lines were malformed."
        )

    entries = (
        parsed.where(F.col("valid"))
        .select("user_id", F.explode(F.filter(F.col("data"), _is_usable)).alias("e"))
        .select(
            F.col("user_id").cast("int").alias("user_id"),  # range checked with the line
            F.trim(F.col("e.artist_mbid")).alias("artist_mbid"),
            F.nullif(F.trim(F.col("e.artist_name")), F.lit("")).alias("artist_name"),
            F.col("e.listen_count").alias("listen_count"),
        )
    )
    counts = entries.groupBy("user_id", "artist_mbid").agg(  # BR1.6: repeats are added together
        F.least(F.sum("listen_count"), F.lit(MAX_INT)).cast("int").alias("listen_count")
    )
    counts.persist(StorageLevel.DISK_ONLY)

    tmp = {
        "listeners": fsutil.tmp_path(paths.artist_listeners),
        "interactions": fsutil.tmp_path(paths.interactions),
        "names": fsutil.tmp_path(paths.artist_names),
    }
    try:
        listeners = (
            counts.groupBy("artist_mbid")
            .agg(F.count(F.lit(1)).cast("int").alias("listener_count"))
            .where(F.col("listener_count") >= MIN_LISTENERS)  # BR1.7: 4 is out, 5 is in
        )
        _write(listeners, tmp["listeners"])
        kept = spark.read.parquet(str(tmp["listeners"]))
        summary.artists = kept.count()
        if summary.artists == 0:
            raise DataError(
                f"No artist has at least {MIN_LISTENERS} listeners in the {total} lines read."
            )

        _write(
            counts.join(kept.select("artist_mbid"), "artist_mbid", "left_semi").select(
                "user_id", "artist_mbid", "listen_count"
            ),
            tmp["interactions"],
        )
        summary.rows = spark.read.parquet(str(tmp["interactions"])).count()

        # BR3.2: the spelling used by the most listeners; ties go to the alphabetically first.
        spellings = (
            entries.where(F.col("artist_name").isNotNull())
            .select("user_id", "artist_mbid", "artist_name")
            .distinct()
            .join(kept.select("artist_mbid"), "artist_mbid", "left_semi")
            .groupBy("artist_mbid", "artist_name")
            .agg(F.count(F.lit(1)).alias("listeners"))
            .groupBy("artist_mbid")
            .agg(
                F.min(F.struct((-F.col("listeners")).alias("neg"), F.col("artist_name"))).alias("b")
            )
            .select("artist_mbid", F.col("b.artist_name").alias("artist_name"))
        )
        names = (
            kept.select("artist_mbid")
            .join(spellings, "artist_mbid", "left")
            .select("artist_mbid", F.coalesce(F.col("artist_name"), F.lit("")).alias("artist_name"))
        )
        _write(names, tmp["names"])
    except BaseException:
        for folder in tmp.values():
            fsutil.clear(folder)
        raise
    finally:
        counts.unpersist()
    return tmp


def prepare(
    data_root: Path | None,
    work_dir: Path,
    spark: SparkSession | None = None,
    *,
    max_lines: int | None = None,
) -> PrepSummary:
    """Run the prepare step and return its summary. Raises `RecsError` subclasses on failure.

    `max_lines` limits the run to the first N listener lines (a sample run); None reads the whole
    dump. The settings and dump checks run first, so a failure there writes nothing (BR1.1).
    """
    started = time.perf_counter()
    files = check_dump_files(data_root)  # BR1.1: stops before anything is written
    paths = output_paths(work_dir, work_dir)  # prepare writes only under the work folder
    summary = PrepSummary(run_id=steps.new_run_id(), source_dump=dump_label(files.listening))

    work_dir.mkdir(parents=True, exist_ok=True)
    steps.clear_marker(work_dir, steps.PREPARE)  # an interrupted run must not look finished
    session = spark if spark is not None else get_spark("listenbrainz-recs-prepare")
    try:
        parsed = _parse(_read_text_lines(session, files.listening, max_lines))
        parsed.persist(StorageLevel.DISK_ONLY)
        try:
            tmp = _build_outputs(session, parsed, paths, summary)
        finally:
            parsed.unpersist()
    except RecsError:
        raise
    except Exception as exc:  # integration boundary: Spark/JVM failures surface as many types
        raise spark_failure("prepare", exc) from exc

    fsutil.publish(tmp["listeners"], paths.artist_listeners)
    fsutil.publish(tmp["interactions"], paths.interactions)
    fsutil.publish(tmp["names"], paths.artist_names)
    summary.seconds = time.perf_counter() - started
    report = {
        "run_id": summary.run_id,
        "run_timestamp": steps.now_utc(),
        "source_dump": summary.source_dump,
        "valid_records": summary.valid_records,
        "skipped_records": summary.skipped_records,
        "skipped_entries": summary.skipped_entries,
        "kept_artists": summary.artists,
    }
    fsutil.write_json_atomic(paths.prepare_report, report)  # BR1.8
    steps.write_marker(work_dir, steps.PREPARE, run_id=summary.run_id, details=asdict(summary))
    return summary


def main() -> int:
    """Command entry point: `uv run listenbrainz-recs-prepare`."""
    spark: SparkSession | None = None
    try:
        settings = load_settings()
        # Fail on a bad location before a Spark session is started (BR1.1).
        check_dump_files(settings.data_root)
        spark = get_spark(
            "listenbrainz-recs-prepare",
            memory=settings.spark_memory,
            local_dir=settings.work_dir / SPARK_TEMP_DIR,
        )
        summary = prepare(
            settings.data_root, settings.work_dir, spark, max_lines=settings.prep_max_lines
        )
    except RecsError as exc:
        print(f"prepare failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if spark is not None:
            spark.stop()
    print(summary.line())
    return 0


if __name__ == "__main__":
    sys.exit(main())

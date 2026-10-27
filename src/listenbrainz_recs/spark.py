"""Local Spark session setup shared by the pipeline steps (NFR1.7, NFR4.2, NFR8.4).

The session always uses a local master, binds the driver to 127.0.0.1 and has the web page off,
so a pipeline step opens no network port.
"""

from pathlib import Path

from pyspark.sql import SparkSession

from listenbrainz_recs.errors import DataError
from listenbrainz_recs.settings import DEFAULT_SPARK_MEMORY, SPARK_MEMORY_VAR, load_settings


def get_spark(
    app_name: str,
    *,
    master: str = "local[*]",
    shuffle_partitions: int = 64,
    log_level: str = "ERROR",
    memory: str | None = None,
    local_dir: Path | None = None,
) -> SparkSession:
    """Return the (single) local Spark session, creating it on first use.

    `memory` is the driver memory (default: the LISTENBRAINZ_SPARK_MEMORY setting). It only takes
    effect when the session is created, so it is set before the session starts. `local_dir` moves
    Spark's scratch files into the git-ignored work folder.
    """
    size = memory if memory is not None else load_settings().spark_memory
    builder = (
        SparkSession.builder.appName(app_name)  # type: ignore[attr-defined]
        .master(master)
        .config("spark.driver.memory", size or DEFAULT_SPARK_MEMORY)
        .config("spark.sql.shuffle.partitions", str(shuffle_partitions))
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.ui.enabled", "false")
        .config("spark.ui.showConsoleProgress", "false")
    )
    if local_dir is not None:
        local_dir.mkdir(parents=True, exist_ok=True)
        builder = builder.config("spark.local.dir", str(local_dir.resolve()))
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel(log_level)
    return spark


def is_out_of_memory(exc: BaseException) -> bool:
    """True when `exc` is the JVM or Python running out of memory (NFR2.12)."""
    text = str(exc)
    return isinstance(exc, MemoryError) or "OutOfMemoryError" in text or "Java heap space" in text


def spark_failure(step: str, exc: BaseException) -> DataError:
    """A short message for a Spark failure; an out-of-memory stop names the setting (BR2.3).

    Only the first line of the error is kept, so no data from a failing record is echoed.
    """
    if is_out_of_memory(exc):
        return DataError(
            f"The {step} step ran out of memory. Raise {SPARK_MEMORY_VAR} (now "
            f"{load_settings().spark_memory}; it must fit in the machine's memory) and run the "
            f"{step} step again."
        )
    first = (str(exc).strip().splitlines() or [type(exc).__name__])[0][:300]
    return DataError(f"The {step} step failed in Spark: {first}")

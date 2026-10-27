"""Local Spark session setup shared by the pipeline steps."""

from pyspark.sql import SparkSession


def get_spark(
    app_name: str,
    *,
    master: str = "local[2]",
    shuffle_partitions: int = 8,
    log_level: str = "ERROR",
) -> SparkSession:
    """Return the (single) local Spark session, creating it on first use."""
    spark = (
        SparkSession.builder.appName(app_name)  # type: ignore[attr-defined]
        .master(master)
        .config("spark.sql.shuffle.partitions", str(shuffle_partitions))
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.ui.enabled", "false")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel(log_level)
    return spark

"""MusicBrainz source: artist descriptions and recognised genres, read with Spark (BR3.3, BR3.4).

The dump's tables are tab-separated text with ``\\N`` for null and backslash escapes, so they are
read as plain text lines and split on tabs, which avoids any quoting rules. Only the columns that
are needed are kept (artist: 0 id, 1 gid, 13 short description; artist_tag: 0 artist id, 1 tag id,
2 votes; tag: 0 id, 1 name; genre: 2 name). The files are only ever read.
"""

from pathlib import Path

from pyspark.sql import Column, DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from listenbrainz_recs.dump_source import MusicBrainzTables

ARTIST_ID_COL, ARTIST_GID_COL, ARTIST_COMMENT_COL = 0, 1, 13
ARTIST_TAG_ARTIST_COL, ARTIST_TAG_TAG_COL, ARTIST_TAG_VOTES_COL = 0, 1, 2
TAG_ID_COL, TAG_NAME_COL = 0, 1
GENRE_NAME_COL = 2

_NULL_MARK = "\\N"
_BACKSLASH_HOLDER = "\u0001"


def _table(spark: SparkSession, path: Path, columns: dict[int, str]) -> DataFrame:
    """Read chosen columns (column number -> alias); ``\\N`` and short rows give null."""
    lines = spark.read.text(str(path))
    cells = F.split(F.col("value"), "\t", -1)  # -1 keeps trailing empty cells
    selected = []
    for number, alias in columns.items():
        cell = F.try_element_at(cells, F.lit(number + 1))
        selected.append(F.when(cell == _NULL_MARK, F.lit(None)).otherwise(cell).alias(alias))
    return lines.select(*selected)


def unescape(column: Column) -> Column:
    """Undo the dump's escapes: a doubled backslash is one, escaped tab/newline become a space."""
    held = F.regexp_replace(column, r"\\\\", _BACKSLASH_HOLDER)
    spaced = F.regexp_replace(held, r"\\[tnr]", " ")
    return F.regexp_replace(spaced, _BACKSLASH_HOLDER, r"\\")


def _key(column: Column) -> Column:
    return F.lower(F.trim(column))


def _mb_artists(spark: SparkSession, tables: MusicBrainzTables) -> DataFrame:
    return _table(
        spark,
        tables.artist,
        {ARTIST_ID_COL: "mb_id", ARTIST_GID_COL: "gid", ARTIST_COMMENT_COL: "comment"},
    ).select(
        F.col("mb_id").try_cast("long").alias("mb_id"),
        _key(F.col("gid")).alias("key"),
        F.col("comment"),
    )


def read_descriptions(spark: SparkSession, tables: MusicBrainzTables, kept: DataFrame) -> DataFrame:
    """One row per kept artist with its short description, or null (BR3.3, BR3.5).

    `kept` has an ``artist_mbid`` column. A blank or missing comment, or an artist MusicBrainz
    does not know, gives a null description.
    """
    described = _mb_artists(spark, tables).select(
        "key", F.nullif(F.trim(unescape(F.col("comment"))), F.lit("")).alias("description")
    )
    return (
        kept.select("artist_mbid")
        .withColumn("key", _key(F.col("artist_mbid")))
        .join(described, "key", "left")
        .select("artist_mbid", "description")
    )


def read_genres(spark: SparkSession, tables: MusicBrainzTables, kept: DataFrame) -> DataFrame:
    """Ranked genres of the kept artists: ``artist_mbid, genre, votes, rank`` (BR3.4).

    A genre is a tag whose lower-cased, trimmed name is on the genre table's list; tags with 0 or
    fewer votes are ignored; votes of tag spellings that fold to one genre are added together;
    rank 1 is the most voted, ties broken alphabetically.
    """
    genre_names = (
        _table(spark, tables.genre, {GENRE_NAME_COL: "name"})
        .select(_key(F.col("name")).alias("genre"))
        .where(F.col("genre").isNotNull() & (F.col("genre") != ""))
        .distinct()
    )
    genre_tags = (
        _table(spark, tables.tag, {TAG_ID_COL: "tag_id", TAG_NAME_COL: "name"})
        .select(
            F.col("tag_id").try_cast("long").alias("tag_id"), _key(F.col("name")).alias("genre")
        )
        .join(F.broadcast(genre_names), "genre")
        .where(F.col("tag_id").isNotNull())
    )
    votes = (
        _table(
            spark,
            tables.artist_tag,
            {
                ARTIST_TAG_ARTIST_COL: "mb_id",
                ARTIST_TAG_TAG_COL: "tag_id",
                ARTIST_TAG_VOTES_COL: "votes",
            },
        )
        .select(
            F.col("mb_id").try_cast("long").alias("mb_id"),
            F.col("tag_id").try_cast("long").alias("tag_id"),
            F.col("votes").try_cast("int").alias("votes"),
        )
        .where(F.col("votes") > 0)
        .join(F.broadcast(genre_tags), "tag_id")
    )
    kept_ids = (
        kept.select("artist_mbid")
        .withColumn("key", _key(F.col("artist_mbid")))
        .join(_mb_artists(spark, tables).select("mb_id", "key"), "key")
        .select("artist_mbid", "mb_id")
    )
    totals = (
        kept_ids.join(votes, "mb_id")
        .groupBy("artist_mbid", "genre")
        .agg(F.sum("votes").cast("int").alias("votes"))
    )
    order = Window.partitionBy("artist_mbid").orderBy(F.col("votes").desc(), F.col("genre").asc())
    return totals.select("artist_mbid", "genre", "votes", F.row_number().over(order).alias("rank"))

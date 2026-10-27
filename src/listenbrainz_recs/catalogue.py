"""ArtistCatalog build: the catalogue step writes `artists.sqlite` (contract C2; BR3.1 to BR3.5,
BR4.1, BR4.8, BR6.1).

For every kept artist the file holds the name (most used spelling), the MusicBrainz short
description (none when blank), the listener count and the ranked genres. An artist MusicBrainz has
no record of is kept with no description and no genres (Q2). Artists are numbered by popularity
(listeners descending, then name, then id); that number is the row number of the full-text table,
so a search can read matches in the final order and stop early (NFR1.6).

Only artist-level data is read: the artist names, the kept artists' listener counts and the
MusicBrainz tables. No listener number reaches this file (NFR3.5).
"""

import sqlite3
import sys
import time
from collections.abc import Callable, Iterable, Iterator
from contextlib import closing
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from listenbrainz_recs import fsutil, steps
from listenbrainz_recs.dump_source import locate_musicbrainz_tables
from listenbrainz_recs.errors import DataError, RecsError
from listenbrainz_recs.paths import ARTISTS_DB_FILE, SPARK_TEMP_DIR, output_paths
from listenbrainz_recs.settings import load_settings
from listenbrainz_recs.text import normalize_name

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

INSERT_BATCH = 5_000

SCHEMA = """
CREATE TABLE artist (
    mbid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    listener_count INTEGER NOT NULL,
    popularity INTEGER NOT NULL
);
CREATE TABLE artist_genre (
    mbid TEXT NOT NULL,
    genre TEXT NOT NULL,
    votes INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    PRIMARY KEY (mbid, rank),
    UNIQUE (mbid, genre)
);
CREATE TABLE artist_name_index (
    norm_name TEXT NOT NULL,
    popularity INTEGER NOT NULL,
    mbid TEXT NOT NULL,
    PRIMARY KEY (norm_name, popularity)
) WITHOUT ROWID;
CREATE VIRTUAL TABLE artist_search USING fts5(
    norm_name,
    mbid UNINDEXED,
    tokenize = 'unicode61 remove_diacritics 0',
    prefix = '1 2 3'
);
"""


@dataclass(frozen=True)
class CatalogueArtist:
    """Everything the app shows about one kept artist; `genres` is (genre, votes), best first."""

    mbid: str
    name: str
    description: str | None
    listener_count: int
    genres: list[tuple[str, int]] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        """The stored name; an artist with no name at all is shown by its id."""
        return self.name.strip() or self.mbid


def _popularity_key(artist: CatalogueArtist) -> tuple[int, str, str]:
    return (-artist.listener_count, artist.display_name, artist.mbid)


def popularity_order(artists: Iterable[CatalogueArtist]) -> list[CatalogueArtist]:
    """Sort artists most popular first: listeners descending, then name, then id (BR4.4)."""
    return sorted(artists, key=_popularity_key)


@dataclass
class WrittenCounts:
    """What `write_catalogue_db` stored."""

    artists: int = 0
    described: int = 0
    with_genres: int = 0


@dataclass
class CatalogueSummary:
    """Counters for the one-line run summary (NFR2.13)."""

    artists: int
    described: int
    with_genres: int
    seconds: float

    def line(self) -> str:
        return (
            f"catalogue: {self.artists} artists ({self.described} with a description, "
            f"{self.with_genres} with genres), wrote {ARTISTS_DB_FILE} in {self.seconds:.1f}s"
        )


def _flush(
    db: sqlite3.Connection,
    artist_rows: list[tuple[str, str, str | None, int, int]],
    genre_rows: list[tuple[str, str, int, int]],
    name_rows: list[tuple[str, int, str]],
    search_rows: list[tuple[int, str, str]],
) -> None:
    db.executemany("INSERT INTO artist VALUES (?, ?, ?, ?, ?)", artist_rows)
    db.executemany("INSERT INTO artist_genre VALUES (?, ?, ?, ?)", genre_rows)
    db.executemany("INSERT INTO artist_name_index VALUES (?, ?, ?)", name_rows)
    db.executemany(
        "INSERT INTO artist_search (rowid, norm_name, mbid) VALUES (?, ?, ?)", search_rows
    )
    for rows in (artist_rows, genre_rows, name_rows, search_rows):
        rows.clear()


def write_catalogue_db(
    path: Path,
    artists: Iterable[CatalogueArtist],
    *,
    before_publish: Callable[[], None] | None = None,
) -> WrittenCounts:
    """Write the catalogue file atomically (temp name, then rename) and return what it holds.

    `artists` must already be in popularity order (see `popularity_order`); the n-th artist gets
    popularity n. The earlier file is replaced only when the new one is complete (BR6.1);
    `before_publish` runs just before the rename, when the new file is known to be good.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = fsutil.tmp_path(path)
    fsutil.clear(tmp)
    counts = WrittenCounts()
    artist_rows: list[tuple[str, str, str | None, int, int]] = []
    genre_rows: list[tuple[str, str, int, int]] = []
    name_rows: list[tuple[str, int, str]] = []
    search_rows: list[tuple[int, str, str]] = []
    previous: tuple[int, str, str] | None = None
    try:
        with closing(sqlite3.connect(tmp)) as db:
            db.execute("PRAGMA journal_mode = OFF")
            db.execute("PRAGMA synchronous = OFF")
            db.executescript(SCHEMA)
            for artist in artists:
                key = _popularity_key(artist)
                if previous is not None and key <= previous:
                    raise DataError(
                        f"Catalogue rows are not in popularity order at artist {artist.mbid}."
                    )
                previous = key
                counts.artists += 1
                number = counts.artists
                name = artist.display_name
                description = (artist.description or "").strip() or None
                counts.described += description is not None
                counts.with_genres += bool(artist.genres)
                artist_rows.append((artist.mbid, name, description, artist.listener_count, number))
                for rank, (genre, votes) in enumerate(artist.genres, start=1):
                    genre_rows.append((artist.mbid, genre, votes, rank))
                normalised = normalize_name(name)
                name_rows.append((normalised, number, artist.mbid))
                search_rows.append((number, normalised, artist.mbid))
                if len(artist_rows) >= INSERT_BATCH:
                    _flush(db, artist_rows, genre_rows, name_rows, search_rows)
            _flush(db, artist_rows, genre_rows, name_rows, search_rows)
            db.execute("INSERT INTO artist_search (artist_search) VALUES ('optimize')")
            db.commit()
    except sqlite3.Error as exc:
        fsutil.clear(tmp)
        raise DataError(f"Cannot write the catalogue {path}: {exc}") from exc
    except BaseException:
        fsutil.clear(tmp)
        raise
    if counts.artists == 0:
        fsutil.clear(tmp)
        raise DataError("No artists to write to the catalogue.")
    if before_publish is not None:
        before_publish()
    fsutil.publish(tmp, path)
    return counts


def _stream_artists(
    spark: "SparkSession", paths_work: Path, data_root: Path | None
) -> Iterator[CatalogueArtist]:
    """Kept artists with MusicBrainz details, in popularity order, streamed out of Spark."""
    from pyspark.sql import functions as F

    from listenbrainz_recs.musicbrainz import read_descriptions, read_genres
    from listenbrainz_recs.paths import ARTIST_LISTENERS_DIR, ARTIST_NAMES_DIR

    tables = locate_musicbrainz_tables(data_root)
    listeners = spark.read.parquet(str(paths_work / ARTIST_LISTENERS_DIR))
    names = spark.read.parquet(str(paths_work / ARTIST_NAMES_DIR))
    kept = listeners.join(names, "artist_mbid")
    descriptions = read_descriptions(spark, tables, kept)
    genres = (
        read_genres(spark, tables, kept)
        .groupBy("artist_mbid")
        .agg(F.sort_array(F.collect_list(F.struct("rank", "genre", "votes"))).alias("ranked"))
    )
    artists = (
        kept.join(descriptions, "artist_mbid", "left")
        .join(genres, "artist_mbid", "left")
        .select(
            F.col("artist_mbid"),
            F.coalesce(
                F.nullif(F.trim(F.col("artist_name")), F.lit("")), F.col("artist_mbid")
            ).alias("name"),
            F.col("description"),
            F.col("listener_count"),
            F.coalesce(F.col("ranked"), F.array()).alias("ranked"),
        )
        .orderBy(F.col("listener_count").desc(), F.col("name").asc(), F.col("artist_mbid").asc())
    )
    for row in artists.toLocalIterator():
        yield CatalogueArtist(
            mbid=row["artist_mbid"],
            name=row["name"],
            description=row["description"],
            listener_count=int(row["listener_count"]),
            genres=[(g["genre"], int(g["votes"])) for g in row["ranked"]],
        )


def build_catalogue(
    data_root: Path | None,
    work_dir: Path,
    models_dir: Path,
    spark: "SparkSession | None" = None,
) -> CatalogueSummary:
    """Run the catalogue step. Raises `RecsError` subclasses on failure.

    The MusicBrainz tables and the prepare marker are checked first, so a failure there writes
    nothing (BR1.1, BR6.3). The earlier catalogue stays in place until the new one is complete
    (NFR2.10); when the new one replaces it, the manifest is removed because the index built from
    the earlier catalogue must be rebuilt (BR6.6).
    """
    from listenbrainz_recs.spark import get_spark, spark_failure

    started = time.perf_counter()
    locate_musicbrainz_tables(data_root)  # BR1.1: stops before anything is written
    prepared = steps.require_prepared(work_dir)
    paths = output_paths(work_dir, models_dir)

    steps.clear_marker(work_dir, steps.CATALOGUE)  # an interrupted run must not look finished
    session = spark if spark is not None else get_spark("listenbrainz-recs-catalogue")
    models_dir.mkdir(parents=True, exist_ok=True)
    try:
        artists = _stream_artists(session, work_dir, data_root)
        counts = write_catalogue_db(
            paths.artists_db, artists, before_publish=lambda: fsutil.clear(paths.manifest)
        )
    except RecsError:
        raise
    except Exception as exc:  # integration boundary: Spark/JVM failures surface as many types
        raise spark_failure("catalogue", exc) from exc

    summary = CatalogueSummary(
        artists=counts.artists,
        described=counts.described,
        with_genres=counts.with_genres,
        seconds=time.perf_counter() - started,
    )
    steps.write_marker(
        work_dir, steps.CATALOGUE, input_run_id=prepared.run_id, details=asdict(summary)
    )
    return summary


def main() -> int:
    """Command entry point: `uv run listenbrainz-recs-catalogue`."""
    from listenbrainz_recs.spark import get_spark

    spark = None
    try:
        settings = load_settings()
        locate_musicbrainz_tables(settings.data_root)  # fail before Spark starts
        steps.require_prepared(settings.work_dir)
        spark = get_spark(
            "listenbrainz-recs-catalogue",
            memory=settings.spark_memory,
            local_dir=settings.work_dir / SPARK_TEMP_DIR,
        )
        summary = build_catalogue(settings.data_root, settings.work_dir, settings.models_dir, spark)
    except RecsError as exc:
        print(f"catalogue failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if spark is not None:
            spark.stop()
    print(summary.line())
    return 0


if __name__ == "__main__":
    sys.exit(main())

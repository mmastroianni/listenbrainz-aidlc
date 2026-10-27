"""ArtistCatalog build: writes `artists.sqlite` (contract C2) from artist-level fields only."""

import sqlite3
from collections.abc import Iterable
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from listenbrainz_recs import fsutil
from listenbrainz_recs.text import normalize_name

SCHEMA = """
CREATE TABLE artist (
    mbid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    listener_count INTEGER NOT NULL
);
CREATE TABLE artist_genre (
    mbid TEXT NOT NULL,
    genre TEXT NOT NULL,
    rank INTEGER NOT NULL,
    PRIMARY KEY (mbid, genre)
);
CREATE TABLE artist_search (
    mbid TEXT PRIMARY KEY,
    norm_name TEXT NOT NULL
);
CREATE INDEX artist_search_norm_name ON artist_search (norm_name);
"""


@dataclass(frozen=True)
class ArtistRow:
    """What the skeleton knows about one artist; description and genres come from u2-pipeline."""

    mbid: str
    name: str
    listener_count: int


def write_artist_db(path: Path, rows: Iterable[ArtistRow]) -> int:
    """Write the artist file atomically (temp name, then rename) and return the row count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = fsutil.tmp_path(path)
    fsutil.clear(tmp)
    count = 0
    with closing(sqlite3.connect(tmp)) as db:
        db.executescript(SCHEMA)
        for row in rows:
            name = row.name.strip() or row.mbid
            db.execute(
                "INSERT INTO artist (mbid, name, description, listener_count) "
                "VALUES (?, ?, NULL, ?)",
                (row.mbid, name, row.listener_count),
            )
            db.execute(
                "INSERT INTO artist_search (mbid, norm_name) VALUES (?, ?)",
                (row.mbid, normalize_name(name)),
            )
            count += 1
        db.commit()
    fsutil.publish(tmp, path)
    return count

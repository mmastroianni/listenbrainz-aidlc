"""Hand-made built files for the web unit: named artists, a long neighbour chain, a gap."""

from collections.abc import Sequence
from pathlib import Path

import numpy as np
from fixtures.sample_data import artist_mbid

from listenbrainz_recs.catalogue import CatalogueArtist, popularity_order, write_catalogue_db
from listenbrainz_recs.index import build_index_files
from listenbrainz_recs.paths import ARTISTS_DB_FILE

ANGLE_STEP = 0.01  # radians between neighbours, so the ranking from artist 1 is 2, 3, 4, ...


def build_web_models(
    models: Path, artists: Sequence[CatalogueArtist], indexed: int | None = None
) -> None:
    """Write C2 files for `artists`; only the first `indexed` of them get a vector.

    Vectors lie on a quarter circle in the order given, so seen from the first artist the
    ranking is the order of the list. The rest are in the catalogue only.
    """
    count = len(artists) if indexed is None else indexed
    models.mkdir(parents=True, exist_ok=True)
    write_catalogue_db(models / ARTISTS_DB_FILE, popularity_order(artists))
    angles = np.arange(count, dtype=np.float32) * ANGLE_STEP
    vectors = np.stack([np.cos(angles), np.sin(angles)], axis=1).astype(np.float32)
    build_index_files(models, [a.mbid for a in artists[:count]], vectors, "web-dump")


def chain_artists(count: int) -> list[CatalogueArtist]:
    """`count` artists named "Artist 01", "Artist 02", ... with falling popularity."""
    return [
        CatalogueArtist(
            artist_mbid(n), f"Artist {n:02d}", f"Description {n}", 1000 - n, [("jazz", 3)]
        )
        for n in range(1, count + 1)
    ]


def search_artists() -> list[CatalogueArtist]:
    """Names for the suggestion tests; ids 1 to 6."""
    rows = [
        (1, "Henry Threadgill", "US jazz saxophonist and composer", 90, [("jazz", 5)]),
        (2, "Henry Threadgill Sextett", None, 40, [("jazz", 2), ("free jazz", 1)]),
        (3, "Björk", "Icelandic singer", 80, [("art pop", 4), ("electronic", 2)]),
        (4, "Bjork Tribute Band", None, 20, []),
        (5, "Anthony Braxton", "US composer", 60, [("free jazz", 3)]),
        (6, "<script>alert(1)</script>", "<b>bold</b>", 10, []),
    ]
    return [CatalogueArtist(artist_mbid(n), name, desc, c, g) for n, name, desc, c, g in rows]


GAP_ID = artist_mbid(99)


def gap_artists() -> list[CatalogueArtist]:
    """Three indexed artists plus artist 99, which is in the catalogue but has no vector."""
    rows = [(1, "Alpha", 50), (2, "Beta", 40), (3, "Gamma", 30), (99, "Lonely", 5)]
    return [CatalogueArtist(artist_mbid(n), name, None, c, []) for n, name, c in rows]

"""ArtistCatalog: artist details and name suggestions from `artists.sqlite` (contract C1)."""

from collections.abc import Iterable
from dataclasses import dataclass, field

from listenbrainz_recs.store import ModelStore
from listenbrainz_recs.text import normalize_name

MAX_SUGGESTIONS = 10
SQLITE_BATCH = 500  # stays well below SQLite's bound-variable limit


@dataclass(frozen=True)
class ArtistSummary:
    mbid: str
    name: str
    description: str | None
    listener_count: int
    genres: list[str] = field(default_factory=list)


def _like_pattern(text: str, *, prefix_only: bool) -> str:
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"{escaped}%" if prefix_only else f"%{escaped}%"


class ArtistCatalog:
    """Read-only artist lookups. All queries are batched, parameterised SQLite reads."""

    def __init__(self, store: ModelStore) -> None:
        self._store = store

    def get(self, mbid: str) -> ArtistSummary | None:
        return self.get_many([mbid]).get(mbid)

    def get_many(self, mbids: Iterable[str]) -> dict[str, ArtistSummary]:
        """Map each known id to its summary; unknown ids are absent from the result."""
        wanted = list(dict.fromkeys(mbids))
        found: dict[str, ArtistSummary] = {}
        for start in range(0, len(wanted), SQLITE_BATCH):
            chunk = wanted[start : start + SQLITE_BATCH]
            marks = ",".join("?" * len(chunk))
            with self._store.db_lock:
                artists = self._store.db.execute(
                    "SELECT mbid, name, description, listener_count FROM artist "
                    f"WHERE mbid IN ({marks})",  # only "?" placeholders are joined in
                    chunk,
                ).fetchall()
                genres = self._store.db.execute(
                    f"SELECT mbid, genre FROM artist_genre WHERE mbid IN ({marks}) "
                    "ORDER BY mbid, rank",
                    chunk,
                ).fetchall()
            by_artist: dict[str, list[str]] = {}
            for mbid, genre in genres:
                by_artist.setdefault(mbid, []).append(genre)
            for mbid, name, description, count in artists:
                found[mbid] = ArtistSummary(mbid, name, description, count, by_artist.get(mbid, []))
        return found

    def suggest(self, text: str, limit: int = MAX_SUGGESTIONS) -> list[ArtistSummary]:
        """Up to 10 artists whose name contains `text`, ignoring case and accents.

        Closest match first (exact, then prefix, then contains), then most listeners first.
        Whitespace-only text returns [].
        """
        query = normalize_name(text)
        if not query:
            return []
        limit = max(1, min(limit, MAX_SUGGESTIONS))
        with self._store.db_lock:
            rows = self._store.db.execute(
                "SELECT a.mbid FROM artist_search s JOIN artist a ON a.mbid = s.mbid "
                "WHERE s.norm_name LIKE ? ESCAPE '\\' "
                "ORDER BY (s.norm_name = ?) DESC, (s.norm_name LIKE ? ESCAPE '\\') DESC, "
                "a.listener_count DESC, a.name LIMIT ?",
                (
                    _like_pattern(query, prefix_only=False),
                    query,
                    _like_pattern(query, prefix_only=True),
                    limit,
                ),
            ).fetchall()
        order = [mbid for (mbid,) in rows]
        summaries = self.get_many(order)
        return [summaries[m] for m in order if m in summaries]

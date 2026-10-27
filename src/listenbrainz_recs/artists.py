"""ArtistCatalog: artist details and name suggestions from `artists.sqlite` (contract C1).

Suggestions come in four tiers (BR4.4): the name equals the typed text; the name starts with it;
every typed word starts some word of the name; each tier ordered by popularity (more listeners,
then name, then id). The catalogue step numbers artists by that order, so every query below reads
its rows already in the final order and stops after the first few; nothing is sorted over all
matches except the starts-with range, which is limited by the sorted index (NFR1.6).

Typed text is normalised first (BR4.1), leaving only letters, digits and single spaces, and is then
only ever a bound parameter or a quoted word in the full-text query, never query syntax (NFR8.5).
"""

from collections.abc import Iterable
from dataclasses import dataclass, field

from listenbrainz_recs.store import ModelStore
from listenbrainz_recs.text import normalize_name

MAX_SUGGESTIONS = 10
SQLITE_BATCH = 500  # stays well below SQLite's bound-variable limit
_AFTER_ANY_TEXT = "\U0010ffff"  # sorts after every character a normalised name can hold


@dataclass(frozen=True)
class ArtistSummary:
    mbid: str
    name: str
    description: str | None
    listener_count: int
    genres: list[str] = field(default_factory=list)


def _word_query(words: list[str]) -> str:
    """A full-text query where every word is a quoted word start; words hold no query syntax."""
    return " ".join(f'"{word}"*' for word in words)


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
        """Up to 10 artists matching the typed `text`, closest first (BR4.3 to BR4.7).

        Ignores case and accents and treats punctuation as a space. Text with no letters or digits
        returns []. A larger `limit` is capped at 10, not refused.
        """
        query = normalize_name(text)
        if not query:
            return []
        limit = max(1, min(limit, MAX_SUGGESTIONS))
        order: list[str] = []
        with self._store.db_lock:
            for fetch in (self._exact, self._starts_with, self._word_starts):
                for mbid in fetch(query, limit + len(order)):
                    if mbid not in order:
                        order.append(mbid)
                if len(order) >= limit:
                    break
        order = order[:limit]
        summaries = self.get_many(order)
        return [summaries[m] for m in order if m in summaries]

    def _exact(self, query: str, limit: int) -> list[str]:
        """Tier 0: the name equals the text, most popular first."""
        rows = self._store.db.execute(
            "SELECT mbid FROM artist_name_index WHERE norm_name = ? ORDER BY popularity LIMIT ?",
            (query, limit),
        ).fetchall()
        return [mbid for (mbid,) in rows]

    def _starts_with(self, query: str, limit: int) -> list[str]:
        """Tier 1: the name starts with the text, most popular first."""
        rows = self._store.db.execute(
            "SELECT mbid FROM artist_name_index WHERE norm_name >= ? AND norm_name < ? "
            "ORDER BY popularity LIMIT ?",
            (query, query + _AFTER_ANY_TEXT, limit),
        ).fetchall()
        return [mbid for (mbid,) in rows]

    def _word_starts(self, query: str, limit: int) -> list[str]:
        """Tier 2: every typed word starts a word of the name; rows come in popularity order."""
        rows = self._store.db.execute(
            "SELECT mbid FROM artist_search WHERE artist_search MATCH ? ORDER BY rowid LIMIT ?",
            (_word_query(query.split()), limit),
        ).fetchall()
        return [mbid for (mbid,) in rows]

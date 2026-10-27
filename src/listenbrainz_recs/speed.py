"""Speed check: 95% of 100 lookups answer in under 200 ms (BR5.3; NFR1.5, NFR1.6, NFR2.15).

Run by hand after a full-size build with `uv run listenbrainz-recs-speed`; it is not part of the
default test run. It loads the built files exactly as the app does, picks 100 different artists,
times one similar-artist lookup and one suggestion lookup for each, and prints the number of lookups
and the 95th percentile of both kinds against the 200 ms limit. It exits non-zero on a fail.
Only artist ids and names are used; nothing about listeners is read.
"""

import math
import random
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from listenbrainz_recs.artists import ArtistCatalog
from listenbrainz_recs.errors import RecsError
from listenbrainz_recs.settings import load_settings
from listenbrainz_recs.similarity import SimilarityIndex
from listenbrainz_recs.store import ModelStore, load_store

LOOKUPS = 100  # different artists to time
LIMIT_MS = 200.0
PERCENTILE = 95
SEED = 42  # the same artists are picked on every run, so runs compare
TYPED_CHARACTERS = 8  # how much of an artist's name is "typed" for the suggestion lookup


@dataclass(frozen=True)
class KindResult:
    """The timing of one kind of lookup."""

    name: str
    p95_ms: float
    limit_ms: float

    @property
    def passed(self) -> bool:
        return self.p95_ms < self.limit_ms

    def line(self, count: int) -> str:
        verdict = "PASS" if self.passed else "FAIL"
        return (
            f"{self.name}: {count} lookups, 95th percentile {self.p95_ms:.1f} ms "
            f"(limit {self.limit_ms:.0f} ms) {verdict}"
        )


@dataclass(frozen=True)
class SpeedReport:
    """Both kinds of lookup, timed on the same artists."""

    count: int
    similar: KindResult
    suggestions: KindResult

    @property
    def passed(self) -> bool:
        return self.similar.passed and self.suggestions.passed

    def lines(self) -> list[str]:
        return [self.similar.line(self.count), self.suggestions.line(self.count)]


def percentile(values: Sequence[float], percent: float) -> float:
    """The nearest-rank percentile: the smallest value that `percent`% of the values do not pass."""
    if not values:
        raise ValueError("no values to take a percentile of")
    ordered = sorted(values)
    rank = max(1, math.ceil(percent / 100 * len(ordered)))
    return ordered[rank - 1]


def _time_ms(call: Callable[[], object]) -> float:
    started = time.perf_counter()
    call()
    return (time.perf_counter() - started) * 1000


def typed_text(name: str) -> str:
    """The first characters of a name, as if the person had typed that much."""
    return name[:TYPED_CHARACTERS]


def run_speed_check(
    store: ModelStore,
    *,
    count: int = LOOKUPS,
    limit_ms: float = LIMIT_MS,
    neighbours: Callable[[str], object] | None = None,
    suggest: Callable[[str], object] | None = None,
) -> SpeedReport:
    """Time one lookup of each kind for `count` different artists (fewer when fewer exist).

    `neighbours` and `suggest` stand in for the real lookups (tests pass slow ones to prove a
    failure is reported); by default they are the app's own `SimilarityIndex` and `ArtistCatalog`.
    """
    similarity = SimilarityIndex(store)
    catalog = ArtistCatalog(store)
    find_similar = neighbours or (lambda mbid: similarity.neighbours(mbid, 0, 20))
    find_by_name = suggest or catalog.suggest

    picked = random.Random(SEED).sample(store.ids, min(count, len(store.ids)))
    names = catalog.get_many(picked)
    similar_ms: list[float] = []
    suggest_ms: list[float] = []
    for mbid in picked:
        similar_ms.append(_time_ms(lambda mbid=mbid: find_similar(mbid)))
        text = typed_text(names[mbid].name if mbid in names else mbid)
        suggest_ms.append(_time_ms(lambda text=text: find_by_name(text)))
    return SpeedReport(
        count=len(picked),
        similar=KindResult("similar artists", percentile(similar_ms, PERCENTILE), limit_ms),
        suggestions=KindResult("suggestions", percentile(suggest_ms, PERCENTILE), limit_ms),
    )


def main() -> int:
    """Command entry point: `uv run listenbrainz-recs-speed`. Exit 0 on pass, 1 on fail or error."""
    try:
        settings = load_settings()
        store = load_store(settings.models_dir)
    except RecsError as exc:
        print(f"speed check failed: {exc}", file=sys.stderr)
        return 1
    try:
        report = run_speed_check(store)
    finally:
        store.close()
    for line in report.lines():
        print(line)
    print("speed check: " + ("PASS" if report.passed else "FAIL"))
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())

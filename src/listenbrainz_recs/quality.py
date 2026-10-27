"""Quality check against the current app: a sheet to fill in by eye, then a verdict (FR8.1).

`uv run listenbrainz-recs-quality-sheet NAME_OR_ID ...` writes a markdown sheet (BR5.1) listing the
new app's top 20 artists, with genres, for up to 5 artists, each with a verdict line left
`unset`. The owner compares by eye with the current app and replaces each `unset` with
`better-or-equal` or `worse`. `uv run listenbrainz-recs-quality-verdict` then reads the sheet and
prints pass (at least 4 of 5 better-or-equal), fail or incomplete (BR5.2).

The sheet holds names, ids and genres only, and both commands print counts only (BR5.3, NFR2.23).
Nothing about listeners is read or written.
"""

import argparse
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from listenbrainz_recs.artists import ArtistCatalog, ArtistSummary
from listenbrainz_recs.errors import RecsError, UnknownArtist
from listenbrainz_recs.settings import load_settings
from listenbrainz_recs.similarity import SimilarityIndex
from listenbrainz_recs.store import ModelStore, load_store
from listenbrainz_recs.text import normalize_name

DEFAULT_SHEET = Path("docs/quality-check.md")
MAX_ARTISTS = 5
TOP_N = 20
PASS_MINIMUM = 4  # at least 4 of the 5 artists marked better-or-equal
BETTER = "better-or-equal"
WORSE = "worse"
UNSET = "unset"
VERDICT_VALUES = (BETTER, WORSE, UNSET)
VERDICT_LINE = re.compile(r"^\s*verdict\s*:\s*(.*?)\s*$", re.IGNORECASE)
MBID_TEXT = re.compile(r"^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")


class QualityCheckError(RecsError):
    """The sheet cannot be written or read; the message names what to fix."""


def _genres(artist: ArtistSummary) -> str:
    return ", ".join(artist.genres) if artist.genres else "no genres listed"


def find_artist(catalog: ArtistCatalog, wanted: str) -> ArtistSummary:
    """The artist for an id or an exact name (ignoring case and accents), or an error."""
    wanted = wanted.strip()
    if MBID_TEXT.match(wanted):
        found = catalog.get(wanted.lower())
        if found is not None:
            return found
    else:
        key = normalize_name(wanted)
        for candidate in catalog.suggest(wanted, 10):
            if normalize_name(candidate.name) == key:
                return candidate
    raise QualityCheckError(f"No artist matches '{wanted}'. Check the spelling or use its id.")


def _section(
    number: int, artist: ArtistSummary, similarity: SimilarityIndex, catalog: ArtistCatalog
) -> str:
    try:
        page = similarity.neighbours(artist.mbid, offset=0, limit=TOP_N)
    except UnknownArtist as exc:
        raise QualityCheckError(
            f"'{artist.name}' has too little listening data to have similar artists."
        ) from exc
    names = catalog.get_many(n.mbid for n in page.items)
    lines = [f"## {number}. {artist.name} (`{artist.mbid}`)", "", "New app's top 20:", ""]
    for rank, neighbour in enumerate(page.items, start=1):
        other = names.get(neighbour.mbid)
        label = other.name if other else neighbour.mbid
        lines.append(f"{rank}. {label}: {_genres(other) if other else 'no genres listed'}")
    lines += ["", f"Verdict: {UNSET}", ""]
    return "\n".join(lines)


def build_sheet(store: ModelStore, wanted: Sequence[str]) -> str:
    """The sheet text for up to 5 artists given by name or id (BR5.1, BR5.3)."""
    if not wanted:
        raise QualityCheckError("Name at least one artist (up to 5), by name or id.")
    if len(wanted) > MAX_ARTISTS:
        raise QualityCheckError(f"Give at most {MAX_ARTISTS} artists; {len(wanted)} were named.")
    catalog = ArtistCatalog(store)
    similarity = SimilarityIndex(store)
    artists = [find_artist(catalog, text) for text in wanted]  # every name checked before writing
    head = [
        "# Quality check against the current app",
        "",
        "For each artist, open the same artist in the current app and compare its list with the",
        f"new app's list below. Replace `{UNSET}` on each verdict line with `{BETTER}` or",
        f"`{WORSE}`, then run `uv run listenbrainz-recs-quality-verdict`. The check passes when at",
        f"least {PASS_MINIMUM} of 5 artists are marked `{BETTER}`.",
        "",
    ]
    sections = [
        _section(number, artist, similarity, catalog) for number, artist in enumerate(artists, 1)
    ]
    return "\n".join(head) + "\n" + "\n".join(sections)


def sheet_main(argv: Sequence[str] | None = None) -> int:
    """Command entry point: `uv run listenbrainz-recs-quality-sheet`."""
    parser = argparse.ArgumentParser(
        description="Write the quality-check sheet: the new app's top 20 for up to 5 artists."
    )
    parser.add_argument("artists", nargs="*", help="up to 5 artist names or MusicBrainz ids")
    parser.add_argument("--output", type=Path, default=DEFAULT_SHEET, help="default: %(default)s")
    parser.add_argument("--models-dir", type=Path, default=None, help="built files folder")
    args = parser.parse_args(argv)
    try:
        models_dir = args.models_dir if args.models_dir is not None else load_settings().models_dir
        store = load_store(models_dir)
        try:
            text = build_sheet(store, args.artists)
        finally:
            store.close()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    except RecsError as exc:
        print(f"quality-sheet: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"quality-sheet: cannot write {args.output}: {exc.strerror}", file=sys.stderr)
        return 1
    count = len(args.artists)
    print(f"quality-sheet: wrote {count} artist{'s' if count != 1 else ''} to {args.output}")
    return 0


@dataclass(frozen=True)
class Verdicts:
    """What the owner marked: the counts and the derived result (BR5.2)."""

    total: int
    marked: int
    better: int

    @property
    def result(self) -> str:
        if self.marked < self.total:
            return "incomplete"
        return "pass" if self.better >= PASS_MINIMUM else "fail"


def parse_sheet(text: str, source: str = "the sheet") -> Verdicts:
    """Count the verdict lines; raise `QualityCheckError` naming a line that cannot be read."""
    values: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        match = VERDICT_LINE.match(line)
        if match is None:
            continue
        value = match.group(1).strip("`* ").lower()
        if value not in VERDICT_VALUES:
            raise QualityCheckError(
                f"{source}, line {number}: cannot read verdict '{match.group(1)}'; "
                f"use {BETTER}, {WORSE} or {UNSET}."
            )
        values.append(value)
    if not values:
        raise QualityCheckError(f"{source} has no verdict lines; run the sheet command first.")
    marked = [v for v in values if v != UNSET]
    return Verdicts(total=len(values), marked=len(marked), better=values.count(BETTER))


def verdict_main(argv: Sequence[str] | None = None) -> int:
    """Command entry point: `uv run listenbrainz-recs-quality-verdict`."""
    parser = argparse.ArgumentParser(description="Read the filled quality-check sheet.")
    parser.add_argument("sheet", nargs="?", type=Path, default=DEFAULT_SHEET)
    args = parser.parse_args(argv)
    try:
        text = args.sheet.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"quality-verdict: cannot read {args.sheet}: {exc.strerror}", file=sys.stderr)
        return 1
    try:
        verdicts = parse_sheet(text, str(args.sheet))
    except QualityCheckError as exc:
        print(f"quality-verdict: {exc}", file=sys.stderr)
        return 1
    print(
        f"quality-verdict: {verdicts.marked} of {verdicts.total} verdicts marked, "
        f"{verdicts.better} better-or-equal: {verdicts.result}"
    )
    return 0 if verdicts.result == "pass" else 1

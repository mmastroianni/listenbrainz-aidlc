"""ListeningDataPrep: turn the first 5,000 dump lines into anonymous listen counts.

Keeps only (listener number, artist id, listen count) per entry, plus an artist-id to
artist-name table. No other listener detail is stored (BR1.4, NFR3.1).
"""

import json
import sys
import time
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from listenbrainz_recs import fsutil
from listenbrainz_recs.dump_source import dump_label, locate_listening_dump, read_lines
from listenbrainz_recs.errors import DataError, RecsError
from listenbrainz_recs.paths import (
    ARTIST_NAMES_DIR,
    INTERACTIONS_DIR,
    PREPARED_MARKER,
    TRAINED_MARKER,
)
from listenbrainz_recs.settings import load_settings

SAMPLE_LINES = 5_000  # BR1.3: the skeleton reads only the first 5,000 listener lines
BATCH_ROWS = 50_000
MAX_LISTENER_NUMBER = 2**31 - 1  # Spark ALS needs integer listener numbers

INTERACTION_SCHEMA = pa.schema(
    [
        ("user_id", pa.int32()),
        ("artist_mbid", pa.string()),
        ("listen_count", pa.int32()),
    ]
)
NAME_SCHEMA = pa.schema([("artist_mbid", pa.string()), ("artist_name", pa.string())])


@dataclass
class PrepSummary:
    """Counters for the one-line run summary (NFR2.5)."""

    source_dump: str
    lines_read: int = 0
    lines_skipped: int = 0
    entries_skipped: int = 0
    listeners: int = 0
    rows: int = 0
    artists: int = 0
    seconds: float = 0.0

    def line(self) -> str:
        return (
            f"prepare: read {self.lines_read} lines ({self.lines_skipped} skipped), "
            f"{self.entries_skipped} entries skipped, {self.listeners} listeners, "
            f"{self.rows} listen counts, {self.artists} artists kept, "
            f"wrote {INTERACTIONS_DIR}/ and {ARTIST_NAMES_DIR}/ in {self.seconds:.1f}s"
        )


def parse_line(line: str) -> tuple[int, list[object]] | None:
    """Return (listener number, raw entries) for one dump line, or None if the line is unusable."""
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(record, dict):
        return None
    user_id = record.get("user_id")
    entries = record.get("data")
    if (
        isinstance(user_id, bool)
        or not isinstance(user_id, int)
        or not 0 <= user_id <= MAX_LISTENER_NUMBER
        or not isinstance(entries, list)
    ):
        return None
    return user_id, entries


def usable_entry(entry: object) -> tuple[str, str, int] | None:
    """Return (artist id, artist name, listen count), or None if the entry is skipped (BR1.5)."""
    if not isinstance(entry, dict):
        return None
    mbid = entry.get("artist_mbid")
    count = entry.get("listen_count")
    if not isinstance(mbid, str) or not mbid.strip():
        return None
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        return None
    if count > MAX_LISTENER_NUMBER:
        return None
    name = entry.get("artist_name")
    return mbid.strip(), name.strip() if isinstance(name, str) else "", count


class _InteractionWriter:
    """Writes listen counts to Parquet in batches so memory stays flat."""

    def __init__(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self._writer = pq.ParquetWriter(folder / "part-0.parquet", INTERACTION_SCHEMA)
        self._users: list[int] = []
        self._mbids: list[str] = []
        self._counts: list[int] = []

    def add(self, user_id: int, mbid: str, count: int) -> None:
        self._users.append(user_id)
        self._mbids.append(mbid)
        self._counts.append(count)
        if len(self._users) >= BATCH_ROWS:
            self.flush()

    def flush(self) -> None:
        if not self._users:
            return
        table = pa.table(
            {"user_id": self._users, "artist_mbid": self._mbids, "listen_count": self._counts},
            schema=INTERACTION_SCHEMA,
        )
        self._writer.write_table(table)
        self._users, self._mbids, self._counts = [], [], []

    def close(self) -> None:
        self.flush()
        self._writer.close()


def _collect(
    lines: Iterable[str], writer: _InteractionWriter, summary: PrepSummary
) -> dict[str, Counter[str]]:
    """Parse lines, write usable counts, and return the names seen per artist id."""
    names: dict[str, Counter[str]] = {}
    seen_artists: set[str] = set()
    for line in lines:
        summary.lines_read += 1
        parsed = parse_line(line)
        if parsed is None:
            summary.lines_skipped += 1
            continue
        user_id, entries = parsed
        per_artist: dict[str, int] = {}
        for entry in entries:
            usable = usable_entry(entry)
            if usable is None:
                summary.entries_skipped += 1
                continue
            mbid, name, count = usable
            per_artist[mbid] = per_artist.get(mbid, 0) + count  # (listener, artist) is unique
            if name:
                names.setdefault(mbid, Counter())[name] += 1
        if not per_artist:
            continue
        summary.listeners += 1
        for mbid, count in per_artist.items():
            writer.add(user_id, mbid, min(count, MAX_LISTENER_NUMBER))
            summary.rows += 1
            seen_artists.add(mbid)
    summary.artists = len(seen_artists)
    for mbid in seen_artists:
        names.setdefault(mbid, Counter())
    return names


def prepare(data_root: Path | None, work_dir: Path, max_lines: int = SAMPLE_LINES) -> PrepSummary:
    """Run the prepare step and return its summary. Raises `RecsError` subclasses on failure."""
    started = time.perf_counter()
    dump_file = locate_listening_dump(data_root)  # BR1.1: stops before anything is written
    summary = PrepSummary(source_dump=dump_label(dump_file))

    work_dir.mkdir(parents=True, exist_ok=True)
    marker = work_dir / PREPARED_MARKER
    fsutil.clear(marker)  # an interrupted run must not look finished
    fsutil.clear(work_dir / TRAINED_MARKER)

    interactions_final = work_dir / INTERACTIONS_DIR
    names_final = work_dir / ARTIST_NAMES_DIR
    interactions_tmp = fsutil.tmp_path(interactions_final)
    names_tmp = fsutil.tmp_path(names_final)
    fsutil.clear(interactions_tmp)
    fsutil.clear(names_tmp)

    writer = _InteractionWriter(interactions_tmp)
    try:
        names = _collect(read_lines(dump_file, max_lines), writer, summary)
    except OSError as exc:
        raise DataError(f"Failed while reading or writing prepared data: {exc}") from exc
    finally:
        writer.close()

    if summary.rows == 0:
        raise DataError(f"No usable listen counts in the first {max_lines} lines of {dump_file}.")

    names_tmp.mkdir(parents=True, exist_ok=True)
    mbids = sorted(names)
    pq.write_table(
        pa.table(
            {
                "artist_mbid": mbids,
                "artist_name": [names[m].most_common(1)[0][0] if names[m] else "" for m in mbids],
            },
            schema=NAME_SCHEMA,
        ),
        names_tmp / "part-0.parquet",
    )

    fsutil.publish(interactions_tmp, interactions_final)
    fsutil.publish(names_tmp, names_final)
    summary.seconds = time.perf_counter() - started
    fsutil.write_json_atomic(marker, {"step": "prepare", **asdict(summary)})
    return summary


def main() -> int:
    """Command entry point: `uv run listenbrainz-recs-prepare`."""
    settings = load_settings()
    try:
        summary = prepare(settings.data_root, settings.work_dir)
    except RecsError as exc:
        print(f"prepare failed: {exc}", file=sys.stderr)
        return 1
    print(summary.line())
    return 0


if __name__ == "__main__":
    sys.exit(main())

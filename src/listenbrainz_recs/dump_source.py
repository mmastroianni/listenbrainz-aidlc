"""DumpSource: finds, checks and reads the listening dump. The only code that opens dump files.

Dump files are only ever opened for reading (BR1.2).
"""

import itertools
from collections.abc import Iterator
from pathlib import Path

from listenbrainz_recs.errors import ConfigError
from listenbrainz_recs.paths import LISTENING_DUMP_RELATIVE
from listenbrainz_recs.settings import DATA_ROOT_VAR

DUMP_FOLDER_PREFIX = "listenbrainz-statistics-dump-"


def locate_listening_dump(data_root: Path | None) -> Path:
    """Return the listening dump file under `data_root`, or raise `ConfigError` (BR1.1).

    `data_root` may be the dump folder itself (holding ``lbdump/``) or a folder holding one or
    more ``listenbrainz-statistics-dump-*`` folders, in which case the newest is used.
    """
    if data_root is None:
        raise ConfigError(
            f"The {DATA_ROOT_VAR} setting is not set. Point it at the folder holding the "
            "ListenBrainz dump (for example: export "
            f"{DATA_ROOT_VAR}=/path/to/listenbrainz)."
        )
    if not data_root.is_dir():
        raise ConfigError(f"{DATA_ROOT_VAR} points at {data_root}, which is not a folder.")

    candidates = [data_root]
    candidates += sorted(
        (p for p in data_root.glob(f"{DUMP_FOLDER_PREFIX}*") if p.is_dir()), reverse=True
    )
    for folder in candidates:
        dump = folder.joinpath(*LISTENING_DUMP_RELATIVE)
        if dump.is_file():
            return dump
    expected = "/".join(LISTENING_DUMP_RELATIVE)
    raise ConfigError(
        f"No listening dump found: expected {expected} under {data_root} "
        f"(or under a {DUMP_FOLDER_PREFIX}* folder inside it)."
    )


def dump_label(dump_file: Path) -> str:
    """The name of the dump folder a dump file sits in, recorded in the manifest."""
    folder = dump_file.parents[len(LISTENING_DUMP_RELATIVE) - 1]
    return folder.name


def read_lines(dump_file: Path, max_lines: int | None = None) -> Iterator[str]:
    """Yield up to `max_lines` raw lines of the dump, reading it line by line, read-only."""
    try:
        handle = dump_file.open("r", encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ConfigError(f"Cannot read the listening dump {dump_file}: {exc}") from exc
    with handle:
        yield from itertools.islice(handle, max_lines)

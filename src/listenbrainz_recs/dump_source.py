"""DumpSource: finds and checks the dumps, and reads the listening dump line by line.

This is the only code that locates dump files. Dump files are only ever opened for reading
(BR1.2), and every location check runs before any output is written (BR1.1, NFR3.8).
"""

import itertools
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from listenbrainz_recs.errors import ConfigError
from listenbrainz_recs.paths import (
    LISTENING_DUMP_RELATIVE,
    MUSICBRAINZ_ARTIST_TABLE,
    MUSICBRAINZ_ARTIST_TAG_TABLE,
    MUSICBRAINZ_GENRE_TABLE,
    MUSICBRAINZ_RELATIVE_CANDIDATES,
    MUSICBRAINZ_TABLES,
    MUSICBRAINZ_TAG_TABLE,
)
from listenbrainz_recs.settings import DATA_ROOT_VAR

DUMP_FOLDER_PREFIX = "listenbrainz-statistics-dump-"


@dataclass(frozen=True)
class MusicBrainzTables:
    """The four MusicBrainz tables (tab-separated files) the catalogue step reads."""

    folder: Path
    artist: Path
    artist_tag: Path
    tag: Path
    genre: Path


@dataclass(frozen=True)
class DumpFiles:
    """Every dump file a run needs, all found before anything is written."""

    listening: Path
    musicbrainz: MusicBrainzTables


def _require_root(data_root: Path | None) -> Path:
    if data_root is None:
        raise ConfigError(
            f"The {DATA_ROOT_VAR} setting is not set. Point it at the folder holding the "
            "ListenBrainz dump (for example: export "
            f"{DATA_ROOT_VAR}=/path/to/listenbrainz)."
        )
    if not data_root.is_dir():
        raise ConfigError(f"{DATA_ROOT_VAR} points at {data_root}, which is not a folder.")
    return data_root


def locate_listening_dump(data_root: Path | None) -> Path:
    """Return the listening dump file under `data_root`, or raise `ConfigError` (BR1.1).

    `data_root` may be the dump folder itself (holding ``lbdump/``) or a folder holding one or
    more ``listenbrainz-statistics-dump-*`` folders, in which case the newest is used.
    """
    root = _require_root(data_root)
    candidates = [root]
    candidates += sorted(
        (p for p in root.glob(f"{DUMP_FOLDER_PREFIX}*") if p.is_dir()), reverse=True
    )
    for folder in candidates:
        dump = folder.joinpath(*LISTENING_DUMP_RELATIVE)
        if dump.is_file():
            return dump
    expected = "/".join(LISTENING_DUMP_RELATIVE)
    raise ConfigError(
        f"No listening dump found: expected {expected} under {root} "
        f"(or under a {DUMP_FOLDER_PREFIX}* folder inside it)."
    )


def locate_musicbrainz_tables(data_root: Path | None) -> MusicBrainzTables:
    """Return the MusicBrainz tables under `data_root`, or raise `ConfigError` (BR1.1).

    Looks for the ``mbdump`` folder at ``data/musicbrainz/mbdump``, ``musicbrainz/mbdump`` or
    ``mbdump`` under the data location. Every table must be present; the message names the setting
    and each missing file.
    """
    root = _require_root(data_root)
    folders = [root.joinpath(*parts) for parts in MUSICBRAINZ_RELATIVE_CANDIDATES]
    existing = [folder for folder in folders if folder.is_dir()]
    if not existing:
        expected = "/".join(MUSICBRAINZ_RELATIVE_CANDIDATES[0])
        raise ConfigError(
            f"No MusicBrainz tables found: expected {expected} under {root} "
            f"({DATA_ROOT_VAR}), holding {', '.join(MUSICBRAINZ_TABLES)}."
        )
    for folder in existing:
        if all((folder / name).is_file() for name in MUSICBRAINZ_TABLES):
            return MusicBrainzTables(
                folder=folder,
                artist=folder / MUSICBRAINZ_ARTIST_TABLE,
                artist_tag=folder / MUSICBRAINZ_ARTIST_TAG_TABLE,
                tag=folder / MUSICBRAINZ_TAG_TABLE,
                genre=folder / MUSICBRAINZ_GENRE_TABLE,
            )
    folder = existing[0]
    missing = [name for name in MUSICBRAINZ_TABLES if not (folder / name).is_file()]
    raise ConfigError(
        f"MusicBrainz table file(s) missing in {folder}: {', '.join(missing)}. "
        f"Check the dump under {DATA_ROOT_VAR} ({root})."
    )


def check_dump_files(data_root: Path | None) -> DumpFiles:
    """Check the setting, the listening dump and the MusicBrainz tables, in that order.

    Called at the start of the prepare and catalogue steps, before any output folder is created.
    """
    return DumpFiles(
        listening=locate_listening_dump(data_root),
        musicbrainz=locate_musicbrainz_tables(data_root),
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

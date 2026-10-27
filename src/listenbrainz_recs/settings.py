"""Settings read from environment variables (BR1.1, BR2.3).

- LISTENBRAINZ_DATA_ROOT: folder holding the ListenBrainz and MusicBrainz dumps (read-only).
  Required by the prepare and catalogue steps; there is deliberately no built-in default path.
- LISTENBRAINZ_WORK_DIR: intermediate data (default ``data/``, git-ignored).
- LISTENBRAINZ_MODELS_DIR: built files for the web app (default ``models/``, git-ignored).
- LISTENBRAINZ_SPARK_MEMORY: Spark driver memory, for example ``24g`` (default ``24g``, which
  fits the owner's 32 GB machine; raise it only if a step reports it ran out of memory).
- LISTENBRAINZ_PREP_MAX_LINES: optional; read only this many listener lines of the listening
  dump (a sample run). Unset means the whole dump.
"""

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from listenbrainz_recs.errors import ConfigError

DATA_ROOT_VAR = "LISTENBRAINZ_DATA_ROOT"
WORK_DIR_VAR = "LISTENBRAINZ_WORK_DIR"
MODELS_DIR_VAR = "LISTENBRAINZ_MODELS_DIR"
SPARK_MEMORY_VAR = "LISTENBRAINZ_SPARK_MEMORY"
PREP_MAX_LINES_VAR = "LISTENBRAINZ_PREP_MAX_LINES"

DEFAULT_WORK_DIR = "data"
DEFAULT_MODELS_DIR = "models"
DEFAULT_SPARK_MEMORY = "24g"

_MEMORY_PATTERN = re.compile(r"^[1-9][0-9]*[kmgt]$", re.IGNORECASE)


@dataclass(frozen=True)
class Settings:
    """Resolved locations and limits. `data_root` is None when the setting is missing."""

    data_root: Path | None
    work_dir: Path
    models_dir: Path
    spark_memory: str = DEFAULT_SPARK_MEMORY
    prep_max_lines: int | None = None


def _read_memory(raw: str) -> str:
    if not raw:
        return DEFAULT_SPARK_MEMORY
    if not _MEMORY_PATTERN.match(raw):
        raise ConfigError(
            f"{SPARK_MEMORY_VAR} is '{raw}', which is not a memory size. "
            "Use a number and a unit, for example 24g or 8192m."
        )
    return raw.lower()


def _read_max_lines(raw: str) -> int | None:
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if value < 1:
        raise ConfigError(
            f"{PREP_MAX_LINES_VAR} is '{raw}', which is not a whole number of 1 or more. "
            "Unset it to read the whole dump."
        )
    return value


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Read the settings from `env` (defaults to the process environment)."""
    source = os.environ if env is None else env
    raw_root = source.get(DATA_ROOT_VAR, "").strip()
    return Settings(
        data_root=Path(raw_root).expanduser() if raw_root else None,
        work_dir=Path(source.get(WORK_DIR_VAR, "").strip() or DEFAULT_WORK_DIR),
        models_dir=Path(source.get(MODELS_DIR_VAR, "").strip() or DEFAULT_MODELS_DIR),
        spark_memory=_read_memory(source.get(SPARK_MEMORY_VAR, "").strip()),
        prep_max_lines=_read_max_lines(source.get(PREP_MAX_LINES_VAR, "").strip()),
    )

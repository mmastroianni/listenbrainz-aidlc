"""Settings read from environment variables (BR1.1).

- LISTENBRAINZ_DATA_ROOT: folder holding the ListenBrainz dump (read-only). Required by
  the prepare step; there is deliberately no built-in default path.
- LISTENBRAINZ_WORK_DIR: intermediate data (default ``data/``, git-ignored).
- LISTENBRAINZ_MODELS_DIR: built files for the web app (default ``models/``, git-ignored).
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DATA_ROOT_VAR = "LISTENBRAINZ_DATA_ROOT"
WORK_DIR_VAR = "LISTENBRAINZ_WORK_DIR"
MODELS_DIR_VAR = "LISTENBRAINZ_MODELS_DIR"

DEFAULT_WORK_DIR = "data"
DEFAULT_MODELS_DIR = "models"


@dataclass(frozen=True)
class Settings:
    """Resolved locations. `data_root` is None when the setting is missing."""

    data_root: Path | None
    work_dir: Path
    models_dir: Path


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Read the settings from `env` (defaults to the process environment)."""
    source = os.environ if env is None else env
    raw_root = source.get(DATA_ROOT_VAR, "").strip()
    return Settings(
        data_root=Path(raw_root).expanduser() if raw_root else None,
        work_dir=Path(source.get(WORK_DIR_VAR, "").strip() or DEFAULT_WORK_DIR),
        models_dir=Path(source.get(MODELS_DIR_VAR, "").strip() or DEFAULT_MODELS_DIR),
    )

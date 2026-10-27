"""Atomic write helpers: write under a temporary name, then rename (BR4.1, NFR2.2)."""

import json
import os
import shutil
from pathlib import Path
from typing import Any

from listenbrainz_recs.errors import StepOrderError


def tmp_path(path: Path) -> Path:
    """The temporary sibling of `path` used while it is being written."""
    return path.with_name(path.name + ".tmp")


def clear(path: Path) -> None:
    """Remove a file or folder if it exists."""
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def publish(tmp: Path, final: Path) -> None:
    """Move a finished temporary file or folder into place, replacing any older one."""
    if final.is_dir() and not final.is_symlink():
        shutil.rmtree(final)
    os.replace(tmp, final)


def write_text_atomic(path: Path, text: str) -> None:
    """Write a text file atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = tmp_path(path)
    tmp.write_text(text, encoding="utf-8")
    publish(tmp, path)


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    """Write a JSON file atomically."""
    write_text_atomic(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def require_marker(work_dir: Path, marker: str, step: str) -> None:
    """Stop with the missing step's name when its output marker is absent (NFR2.3)."""
    if not (work_dir / marker).is_file():
        raise StepOrderError(
            f"The {step} step has not been run in {work_dir}. "
            f"Run it first: uv run listenbrainz-recs-{step}"
        )


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object from `path`."""
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} does not hold a JSON object")
    return data

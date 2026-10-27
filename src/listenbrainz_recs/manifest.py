"""BuildManifest: the C2 manifest, written last so its presence means the build finished."""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from listenbrainz_recs import fsutil
from listenbrainz_recs.errors import StartupError
from listenbrainz_recs.paths import BUILDING_STEP, MANIFEST_FILE

FORMAT_VERSION = 1  # bumped by the owner of C2 (u2-pipeline) whenever the file layout changes


@dataclass(frozen=True)
class Manifest:
    format_version: int
    built_at: str  # ISO-8601 UTC
    source_dump: str
    artist_count: int


def new_manifest(source_dump: str, artist_count: int) -> Manifest:
    built_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return Manifest(FORMAT_VERSION, built_at, source_dump, artist_count)


def write_manifest(models_dir: Path, manifest: Manifest) -> None:
    fsutil.write_json_atomic(models_dir / MANIFEST_FILE, asdict(manifest))


def read_manifest(models_dir: Path) -> Manifest:
    """Read and check the manifest; raise `StartupError` naming what to re-run (BR4.2)."""
    path = models_dir / MANIFEST_FILE
    step = BUILDING_STEP[MANIFEST_FILE]
    rerun = f"Re-run the {step} step: uv run listenbrainz-recs-{step}"
    if not path.is_file():
        raise StartupError(f"Missing {MANIFEST_FILE} in {models_dir}. {rerun}")
    try:
        raw = fsutil.read_json(path)
        manifest = Manifest(
            format_version=int(raw["format_version"]),
            built_at=str(raw["built_at"]),
            source_dump=str(raw["source_dump"]),
            artist_count=int(raw["artist_count"]),
        )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise StartupError(f"{path} is unreadable or incomplete ({exc}). {rerun}") from exc
    if manifest.format_version != FORMAT_VERSION:
        raise StartupError(
            f"{path} has format version {manifest.format_version}, but this code expects "
            f"{FORMAT_VERSION}. {rerun}"
        )
    return manifest

"""ModelStore: loads the C2 built files once and checks them (BR4.2, NFR1.1, NFR2.1)."""

import sqlite3
import threading
from dataclasses import dataclass, field
from pathlib import Path

import faiss

from listenbrainz_recs.errors import StartupError
from listenbrainz_recs.manifest import Manifest, read_manifest
from listenbrainz_recs.paths import (
    ARTIST_IDS_FILE,
    ARTISTS_DB_FILE,
    BUILDING_STEP,
    C2_FILES,
    FAISS_INDEX_FILE,
)

# The tables the catalogue step writes and the lookups read.
CATALOGUE_TABLES = frozenset({"artist", "artist_genre", "artist_name_index", "artist_search"})


@dataclass
class ModelStore:
    """Everything the lookup classes read, held in memory or as an open read-only handle."""

    manifest: Manifest
    ids: list[str]
    row_of: dict[str, int]
    index: faiss.Index
    db: sqlite3.Connection
    db_lock: threading.Lock = field(default_factory=threading.Lock)

    def close(self) -> None:
        self.db.close()


def check_files_present(models_dir: Path) -> None:
    """Raise `StartupError` naming every missing C2 file and the step that builds it."""
    missing = [name for name in C2_FILES if not (models_dir / name).is_file()]
    if not missing:
        return
    steps = sorted({BUILDING_STEP[name] for name in missing})
    commands = ", ".join(f"uv run listenbrainz-recs-{s}" for s in steps)
    raise StartupError(
        f"Missing built file(s) in {models_dir}: {', '.join(missing)}. "
        f"Re-run the {' and '.join(steps)} step ({commands})."
    )


def load_store(models_dir: Path) -> ModelStore:
    """Load and cross-check the built files, or raise `StartupError` (the app never half-starts)."""
    check_files_present(models_dir)
    manifest = read_manifest(models_dir)
    rerun = "Re-run the index step: uv run listenbrainz-recs-index"

    try:
        index = faiss.read_index(str(models_dir / FAISS_INDEX_FILE))
    except (RuntimeError, OSError) as exc:
        raise StartupError(f"{FAISS_INDEX_FILE} cannot be read ({exc}). {rerun}") from exc

    ids = (models_dir / ARTIST_IDS_FILE).read_text(encoding="utf-8").split()
    if not (len(ids) == index.ntotal == manifest.artist_count):
        raise StartupError(
            f"Built files disagree: {len(ids)} ids, {index.ntotal} index rows, "
            f"{manifest.artist_count} artists in the manifest. {rerun}"
        )

    db_uri = (models_dir / ARTISTS_DB_FILE).resolve().as_uri() + "?mode=ro"
    try:
        db = sqlite3.connect(db_uri, uri=True, check_same_thread=False)
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not tables >= CATALOGUE_TABLES:
            db.close()
            missing = ", ".join(sorted(CATALOGUE_TABLES - tables))
            raise StartupError(
                f"{ARTISTS_DB_FILE} lacks table(s) {missing}. "
                "Re-run the catalogue step: uv run listenbrainz-recs-catalogue"
            )
        (rows,) = db.execute("SELECT COUNT(*) FROM artist").fetchone()
    except sqlite3.Error as exc:
        raise StartupError(
            f"{ARTISTS_DB_FILE} cannot be read ({exc}). "
            "Re-run the catalogue step: uv run listenbrainz-recs-catalogue"
        ) from exc
    # The catalogue holds every kept artist; the index holds those with a usable vector, so the
    # catalogue may have more artists than the index but never fewer.
    if rows < len(ids):
        db.close()
        raise StartupError(
            f"{ARTISTS_DB_FILE} holds {rows} artists but the index has {len(ids)}. {rerun}"
        )

    return ModelStore(
        manifest=manifest,
        ids=ids,
        row_of={mbid: row for row, mbid in enumerate(ids)},
        index=index,
        db=db,
    )

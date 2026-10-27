"""File and folder names shared by the pipeline steps and the web app.

Nothing here is an absolute path: locations come from `settings.py`. `output_paths` builds every
output path from the work and models folders, so no step writes anywhere else (BR1.9, NFR5.2).
"""

from dataclasses import dataclass
from pathlib import Path

# Relative location of the listening dump inside a dump folder (BR1.1).
LISTENING_DUMP_RELATIVE = ("lbdump", "statistics", "artists_all_time.jsonl")

# Where the MusicBrainz tables may sit under the data location (first folder that has them).
MUSICBRAINZ_RELATIVE_CANDIDATES = (
    ("data", "musicbrainz", "mbdump"),
    ("musicbrainz", "mbdump"),
    ("mbdump",),
)
# The four MusicBrainz tables the catalogue step reads (BR1.1).
MUSICBRAINZ_ARTIST_TABLE = "artist"
MUSICBRAINZ_ARTIST_TAG_TABLE = "artist_tag"
MUSICBRAINZ_TAG_TABLE = "tag"
MUSICBRAINZ_GENRE_TABLE = "genre"
MUSICBRAINZ_TABLES = (
    MUSICBRAINZ_ARTIST_TABLE,
    MUSICBRAINZ_ARTIST_TAG_TABLE,
    MUSICBRAINZ_TAG_TABLE,
    MUSICBRAINZ_GENRE_TABLE,
)

# Intermediate data (work folder, git-ignored).
INTERACTIONS_DIR = "interactions"  # Parquet: user_id, artist_mbid, listen_count
ARTIST_NAMES_DIR = "artist_names"  # Parquet: artist_mbid, artist_name
ARTIST_LISTENERS_DIR = "artist_listeners"  # Parquet: artist_mbid, listener_count (kept artists)
VECTORS_DIR = "vectors"  # Parquet: artist_mbid, features
SPARK_TEMP_DIR = "spark-tmp"  # Spark's own scratch space, kept inside the ignored work folder
PREPARE_REPORT_FILE = "prepare_report.json"

# Step markers (BR6.3, BR6.4): written last by each step.
PREPARED_MARKER = "prepared.json"
TRAINED_MARKER = "trained.json"
CATALOGUE_MARKER = "catalogued.json"
INDEX_MARKER = "indexed.json"

# Built files (models folder, git-ignored). Contract C2.
MANIFEST_FILE = "manifest.json"
ARTISTS_DB_FILE = "artists.sqlite"
FAISS_INDEX_FILE = "artists.faiss"
ARTIST_IDS_FILE = "artist_ids.txt"

C2_FILES = (MANIFEST_FILE, ARTISTS_DB_FILE, FAISS_INDEX_FILE, ARTIST_IDS_FILE)

# The pipeline step that builds each C2 file, named in startup errors (BR4.2).
BUILDING_STEP = {
    MANIFEST_FILE: "index",
    ARTISTS_DB_FILE: "catalogue",
    FAISS_INDEX_FILE: "index",
    ARTIST_IDS_FILE: "index",
}


@dataclass(frozen=True)
class OutputPaths:
    """Every file or folder a pipeline step may create."""

    work_dir: Path
    models_dir: Path
    interactions: Path
    artist_names: Path
    artist_listeners: Path
    vectors: Path
    spark_temp: Path
    prepare_report: Path
    prepared_marker: Path
    trained_marker: Path
    catalogue_marker: Path
    index_marker: Path
    manifest: Path
    artists_db: Path
    faiss_index: Path
    artist_ids: Path

    def all_paths(self) -> tuple[Path, ...]:
        """Every output path, for tests that check nothing is written elsewhere."""
        return (
            self.interactions,
            self.artist_names,
            self.artist_listeners,
            self.vectors,
            self.spark_temp,
            self.prepare_report,
            self.prepared_marker,
            self.trained_marker,
            self.catalogue_marker,
            self.index_marker,
            self.manifest,
            self.artists_db,
            self.faiss_index,
            self.artist_ids,
        )


def output_paths(work_dir: Path, models_dir: Path) -> OutputPaths:
    """Build every output path from the work and models folders (BR1.9, NFR5.2)."""
    return OutputPaths(
        work_dir=work_dir,
        models_dir=models_dir,
        interactions=work_dir / INTERACTIONS_DIR,
        artist_names=work_dir / ARTIST_NAMES_DIR,
        artist_listeners=work_dir / ARTIST_LISTENERS_DIR,
        vectors=work_dir / VECTORS_DIR,
        spark_temp=work_dir / SPARK_TEMP_DIR,
        prepare_report=work_dir / PREPARE_REPORT_FILE,
        prepared_marker=work_dir / PREPARED_MARKER,
        trained_marker=work_dir / TRAINED_MARKER,
        catalogue_marker=work_dir / CATALOGUE_MARKER,
        index_marker=work_dir / INDEX_MARKER,
        manifest=models_dir / MANIFEST_FILE,
        artists_db=models_dir / ARTISTS_DB_FILE,
        faiss_index=models_dir / FAISS_INDEX_FILE,
        artist_ids=models_dir / ARTIST_IDS_FILE,
    )

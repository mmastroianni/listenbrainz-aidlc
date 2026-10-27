"""File and folder names shared by the pipeline steps and the web app.

Nothing here is an absolute path: locations come from `settings.py`.
"""

# Relative location of the listening dump inside a dump folder (BR1.1).
LISTENING_DUMP_RELATIVE = ("lbdump", "statistics", "artists_all_time.jsonl")

# Intermediate data (work folder, git-ignored).
INTERACTIONS_DIR = "interactions"  # Parquet: user_id, artist_mbid, listen_count
ARTIST_NAMES_DIR = "artist_names"  # Parquet: artist_mbid, artist_name
VECTORS_DIR = "vectors"  # Parquet: artist_mbid, features
PREPARED_MARKER = "prepared.json"
TRAINED_MARKER = "trained.json"

# Built files (models folder, git-ignored). Contract C2.
MANIFEST_FILE = "manifest.json"
ARTISTS_DB_FILE = "artists.sqlite"
FAISS_INDEX_FILE = "artists.faiss"
ARTIST_IDS_FILE = "artist_ids.txt"

C2_FILES = (MANIFEST_FILE, ARTISTS_DB_FILE, FAISS_INDEX_FILE, ARTIST_IDS_FILE)

# The pipeline step that builds each C2 file, named in startup errors (BR4.2).
BUILDING_STEP = {
    MANIFEST_FILE: "index",
    ARTISTS_DB_FILE: "index",
    FAISS_INDEX_FILE: "index",
    ARTIST_IDS_FILE: "index",
}

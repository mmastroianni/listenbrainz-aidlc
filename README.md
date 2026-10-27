# listenbrainz-recs

Similar-artist recommendations from ListenBrainz listening data: Spark ALS collaborative
filtering, a FAISS cosine index and a small FastAPI app. Everything runs locally; there are no
remote services.

This is the walking skeleton (unit `u1-skeleton`): it reads the first 5,000 listener lines of the
dump, trains a small model, builds the index and answers one endpoint,
`GET /api/artists/{mbid}/similar`.

## Prerequisites

- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- A Java runtime (Spark needs it): `java -version`
- The ListenBrainz statistics dump, read in place and never modified

## Settings (environment variables)

| Variable | Meaning | Default |
|----------|---------|---------|
| `LISTENBRAINZ_DATA_ROOT` | Folder holding the dump (a `listenbrainz-statistics-dump-*` folder, or a folder containing one) | none: required by the prepare step |
| `LISTENBRAINZ_WORK_DIR` | Intermediate data | `data/` (git-ignored) |
| `LISTENBRAINZ_MODELS_DIR` | Built files read by the app | `models/` (git-ignored) |

## Build the sample and start the app

```bash
uv sync
export LISTENBRAINZ_DATA_ROOT=/path/to/listenbrainz   # the folder that holds the dump
uv run listenbrainz-recs-prepare   # first 5,000 lines -> anonymous listen counts
uv run listenbrainz-recs-train     # Spark ALS -> one vector per artist
uv run listenbrainz-recs-index     # FAISS index, artist file, manifest (written last)
uv run listenbrainz-recs-serve     # http://127.0.0.1:8000
```

Then, for example:

```bash
curl http://127.0.0.1:8000/api/health
curl "http://127.0.0.1:8000/api/artists/<musicbrainz-id>/similar?limit=10"
```

The app refuses to start, naming the step to re-run, when a built file is missing or the manifest
format version differs. Pass `--host` to bind something other than 127.0.0.1 (a deliberate choice).

## Checks

```bash
bash scripts/check.sh                  # ruff check, ruff format --check, ty, pytest + 80% coverage
uv run pytest tests/u1_skeleton -q     # this unit's tests only
```

GitHub Actions runs the same check (`.github/workflows/ci.yml`), switched off until the code is
pushed to GitHub.

## Rules this project follows

Dumps are read-only; no listener-level data leaves the pipeline; no paid or remote services; dumps,
data and model files are never committed.

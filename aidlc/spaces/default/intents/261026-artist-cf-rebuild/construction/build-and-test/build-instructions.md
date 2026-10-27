# Build Instructions

How to set up, build and check the whole project (units u1-skeleton, u2-pipeline and u3-web). Sources: `construction/u1-skeleton/code-generation/code-summary.md`, `construction/u2-pipeline/code-generation/code-summary.md`, `construction/u3-web/code-generation/code-summary.md` and the project `README.md`.

## Prerequisites

- Python 3.12 and `uv`.
- A Java runtime (Spark needs it): `java -version`.
- The ListenBrainz statistics dump and the MusicBrainz tables, read in place from `../listenbrainz` and never modified.

## Install

```bash
uv sync
```

There is nothing to compile: the project is Python and plain web files, so the build is the dependency install plus the pre-merge check below.

## Environment

| Variable | Use | Default |
|----------|-----|---------|
| `LISTENBRAINZ_DATA_ROOT` | Folder holding the dumps (required by the prepare and catalogue steps) | none |
| `LISTENBRAINZ_WORK_DIR` | Intermediate data | `data/` (git-ignored) |
| `LISTENBRAINZ_MODELS_DIR` | Built files read by the app | `models/` (git-ignored) |
| `LISTENBRAINZ_SPARK_MEMORY` | Spark driver memory | `24g` |
| `LISTENBRAINZ_PREP_MAX_LINES` | Sample run: read only this many listener lines | unset (whole dump) |

## Build verification

```bash
bash scripts/check.sh
```

It runs, in order: a check that no data or model file is tracked by git, `ruff check`, `ruff format --check`, `ty check`, and `pytest tests` with the 80% coverage floor. All must pass.

## Building the data (the runtime build)

Run the four pipeline steps in order (full commands and checks are in the README, "Rebuild from a new dump"): prepare, train, catalogue, index. For a full-size rebuild without touching the sample or skeleton folders:

```bash
export LISTENBRAINZ_DATA_ROOT=/home/michael/listenbrainz
export LISTENBRAINZ_WORK_DIR=data/full LISTENBRAINZ_MODELS_DIR=models/full
uv run listenbrainz-recs-prepare && uv run listenbrainz-recs-train \
  && uv run listenbrainz-recs-catalogue && uv run listenbrainz-recs-index
```

## Troubleshooting

- **A step says an earlier step has not been run, or is out of date:** run the step it names, then the steps after it, in order.
- **Spark runs out of memory:** raise `LISTENBRAINZ_SPARK_MEMORY` to a value that fits the machine, and run that step again.
- **`ty` reports a PySpark or FAISS typing problem:** use a narrow ignore on that line; never turn a check off.
- **The app refuses to start:** read the message; it names the missing file or version and the step to run.

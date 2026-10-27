# Unit Test Instructions — u1-skeleton

Follows the Testing Contract in `code-generation-plan.md` (custom: test-first for lookup and web, test-after for pipeline), the Standard strategy (5 to 8 tests per component) and the 80% line-coverage floor from `inception/practices-discovery/team-practices.md`.

## Framework and Setup

- pytest and pytest-cov in the uv dev group; configuration in `pyproject.toml`.
- Prerequisites: `uv sync`, and a Java runtime for Spark.
- Shared fixtures in `tests/conftest.py`: one local `SparkSession` for the test session; paths to `tests/fixtures/`; a built-files builder that runs prepare, train and index on the fixtures into a temp folder.

## Run THIS unit's tests

```
uv run pytest tests/u1_skeleton -q
```

With coverage (the floor is 80% and is never lowered):

```
uv run pytest tests/u1_skeleton -q --cov=listenbrainz_recs --cov-report=term-missing --cov-fail-under=80
```

## Test Files and Scope

| File | Layer | Order | Approx. tests |
|------|-------|-------|---------------|
| `test_dump_source.py` | DumpSource | after | 5 |
| `test_prep.py` | ListeningDataPrep | after | 6 |
| `test_train.py` | SimilarityTraining | after | 4 |
| `test_build.py` | index, catalogue, manifest | after | 6 |
| `test_lookup.py` | SimilarityIndex, ArtistCatalog | first (Red, Green, Refactor) | 7 |
| `test_api.py` | WebApp | first (Red, Green, Refactor) | 8 |
| `test_end_to_end.py` | full slice on fixtures | after | 1 |

Each file covers the happy path and at least two error or edge cases.

## Mocking and Test Data

- No mocks for Spark or FAISS: they run on tiny fixtures.
- Fixtures: `tests/fixtures/listens_sample.jsonl` (a few hundred synthetic lines in the dump's shape, including one malformed line and one entry with a missing artist id) and a handful of expected artists.
- Tests never read the full dumps and never write under the data location.

## Not Run Here

The 200 ms speed check at full size runs in u2-pipeline; `/api/artists/{mbid}/similar` timing on fixtures is checked in `test_api.py`.

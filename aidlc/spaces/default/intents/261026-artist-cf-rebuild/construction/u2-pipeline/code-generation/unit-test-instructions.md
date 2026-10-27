# Unit Test Instructions — u2-pipeline

Follows the Testing Contract in `code-generation-plan.md` (custom ordering: search and lookup tests first, pipeline and training tests after), Test Strategy Standard, and the 80% line-coverage floor from the team practices.

## Framework and configuration

- `pytest` 9.1.1 and `pytest-cov` 7.1.0 in the `uv` dev group; configuration is in `pyproject.toml` (`[tool.pytest.ini_options]`, `[tool.coverage.*]`, floor 80). Nothing new is installed for this unit.
- One shared local `SparkSession` for the whole test run, from `tests/conftest.py` (`spark` fixture, `local[2]`, 4 shuffle partitions). Fixtures pass a small memory size and a small model rank so runs stay fast.
- Tests never read the real dumps. They use the synthetic dump written by `tests/fixtures/sample_data.py`, a small synthetic MusicBrainz folder written by new helpers in the same file, and hand-built catalogue and index files.

## Run this unit's tests

```bash
uv run pytest tests/u2_pipeline -q
```

With coverage for this unit's code:

```bash
uv run pytest tests/u2_pipeline -q --cov=listenbrainz_recs --cov-report=term-missing
```

The whole-project pre-merge check, run before merging the Bolt, is `bash scripts/check.sh`. The skeleton's tests stay in `tests/u1_skeleton` and are run by that check, not by the commands above.

## Test files

| File | Component | Kind | Planned tests |
|------|-----------|------|---------------|
| `test_steps.py` | Step markers | unit | 6 |
| `test_dump_source_full.py` | DumpSource, MusicBrainz tables | unit and integration | 6 |
| `test_prep_full.py` | ListeningDataPrep | integration on fixture | 9 |
| `test_train_full.py` | SimilarityTraining | integration on fixture | 7 |
| `test_catalogue.py` | ArtistCatalog build | integration on fixture | 8 |
| `test_index_build.py` | SimilarityIndex build | integration on fixture | 7 |
| `test_search.py` | ArtistCatalog search (test-first) | unit | 14 |
| `test_speed.py` | Speed command | unit and timing guard | 5 |
| `test_privacy_and_hygiene.py` | Privacy and repository rules | integration | 6 |
| `test_runbook.py` | README runbook | unit | 1 |

About 69 tests. Each test file covers the happy path and at least two error or edge cases (missing input, stale input, malformed data, empty text), as the construction rules require.

## Order of work

- Search (`test_search.py`): write all tests first and run them to see them fail (record the failing output), then write the code and run until green, then refactor while green.
- Everything else: write the code for a step, then its tests, run them, and move on only when green.

## Expected coverage

- Line coverage at or above 80% for the whole project, measured by `pytest-cov`. The floor is not lowered. New modules (`steps.py`, `musicbrainz.py`, `catalogue.py`, `speed.py`) are expected above 85% each.
- The Spark out-of-memory path and the speed command's real full-size path are covered by unit tests of their messages and arithmetic only.

## Mocking and stubbing

- No mocks for Spark, SQLite or FAISS: they run for real on the fixtures.
- The out-of-memory test raises the error from a small stand-in function passed in place of the model fit, because the real condition is not reproducible in a test.
- The speed command's slow-lookup test passes a lookup function that sleeps, to prove a failure is reported.
- Filesystem tests use pytest's `tmp_path`; dump files are read-only copies there.

## Test data

- `tests/fixtures/sample_data.py` keeps the deterministic synthetic listening dump (300 listeners in three artist groups plus edge lines) and gains: an artist with exactly 4 listeners and one with exactly 5, one malformed line, repeated entries for one listener and artist, one artist spelled two ways, and a synthetic MusicBrainz folder (`artist`, `artist_tag`, `tag`, `genre` tab-separated tables) with one artist that has no description, one with no genres, and one missing from the tables.
- Hand-built catalogue fixtures for search: artists with equal and different listener counts, accents, punctuation, same-name pairs and long names.

## Not run by the default test run

- The full-size speed check (BR5.3): needs the full-size built files. Run it by hand with `uv run listenbrainz-recs-speed` after a full rebuild.
- A full-size training run (AC4.2.2): too long for tests; done by the owner following the runbook.

# Unit Test Instructions — u3-web

Follows the Testing Contract in `code-generation-plan.md` (custom ordering: search, lookup and web tests first), Test Strategy Standard, and the 80% line-coverage floor from the team practices. Every layer in this unit is test-first.

## Framework and configuration

- `pytest` 9.1.1 and `pytest-cov` 7.1.0 in the `uv` dev group, with FastAPI's `TestClient` (through `httpx` 0.28.1, already in the dev group); configuration is in `pyproject.toml`. Nothing new is installed for this unit.
- Endpoint tests build the app on hand-made built files from `tests/conftest.py` (`tiny_models` and `single_artist_models`, no Spark needed) plus a catalogue-only artist for the missing-from-index case.
- Page tests read the three page files through the test client and from disk; they check text and structure. They do not run a browser; the keyboard and phone pass is by hand (`docs/manual-checks.md`).

## Run this unit's tests

```bash
uv run pytest tests/u3_web -q
```

With coverage for this unit's code:

```bash
uv run pytest tests/u3_web -q --cov=listenbrainz_recs --cov-report=term-missing
```

The whole-project pre-merge check, run before merging the Bolt, is `bash scripts/check.sh`. The skeleton's and u2-pipeline's tests stay in `tests/u1_skeleton` and `tests/u2_pipeline` and are run by that check, not by the commands above.

## Test files

| File | Component | Kind | Planned tests |
|------|-----------|------|---------------|
| `test_suggest_endpoint.py` | Suggestion endpoint | API | 9 |
| `test_similar_endpoint.py` | Similar-artists endpoint | API | 11 |
| `test_headers_logs_concurrency.py` | Page headers, logging, parallel requests, failure paths, timing guard | API | 11 |
| `test_page_files.py` | The page, stylesheet and script | file and structure checks | 16 |
| `test_quality_check.py` | Quality-check sheet and verdict | unit and command | 10 |
| `test_runner_ready.py` | Runner readiness | unit | 1 |

About 58 tests. Each file covers the happy path and at least two error or edge cases (blank text, over-long text, malformed id, unknown id, missing artist name), as the construction rules require.

## Order of work

Every step is test-first: write the tests, run them and keep the failing output for the report, write the code, run until green, then refactor while green.

## Expected coverage

- Line coverage at or above 80% for the whole project, measured by `pytest-cov`. The floor is not lowered. `app/main.py` and `quality.py` are expected above 90% each.
- The page script itself is not executed by any test; it is covered by text and structure checks, the `node --check` syntax pass when Node is installed, and the manual pass. This is stated in the code summary.

## Mocking and stubbing

- No mocks for FAISS or SQLite: they run for real on the hand-made files.
- Failure-path tests close the catalogue connection or replace the index search with a function that raises, to prove the short 500 answer and the ERROR log.
- The timing guard uses the real built fixture files and the test client.

## Test data

- `tiny_models` (five artists) and `single_artist_models` (one artist, no neighbours) from `tests/conftest.py`; a helper builds a 45-neighbour set for paging, and a catalogue with one artist that has no vector for the missing-from-index case.
- Quality-check tests use the same files and a hand-written sheet for the verdict command, including unset, worse, and unreadable lines.

## Not run by the default test run

- The keyboard and phone pass (AC2.4.1 to AC2.4.5 in a real browser): by hand before `v0.1.0`, from `docs/manual-checks.md`.
- The full-size speed check (AC1.1.6, AC2.1.6): `uv run listenbrainz-recs-speed` after a full rebuild.

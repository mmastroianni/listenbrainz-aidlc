# Code Generation Plan — u2-pipeline

## Summary

- Builds: the full-size pipeline (prepare with all the rules, full-size training, a new catalogue step with MusicBrainz details and genres, a batch-reading index step), four-tier name search, a speed check command, and the rebuild runbook.
- Touches: `src/listenbrainz_recs/` (prep, train, index, artists, store, settings, paths, spark, plus new `steps.py`, `musicbrainz.py`, `catalogue.py`, `speed.py`), `tests/u2_pipeline/`, `tests/u1_skeleton/` where the new rules change old expectations, `pyproject.toml`, `README.md`.
- Tests: about 70 new tests (unit, integration on fixture data, and a fixture-size timing guard), search tests written before the code and pipeline tests after it, all under the 80% coverage floor.

Inputs: `construction/u2-pipeline/functional-design/` (BR1.1 to BR6.6, W1 to W6), `construction/u2-pipeline/nfr-requirements/` and `nfr-design/` (NFR1.5 to NFR8.6), contracts C1 and C2 in `inception/contract-design/contract-summary.md`, and the skeleton code from `construction/u1-skeleton/code-generation/code-summary.md`. Stories covered: AC1.1.1 to AC1.1.6, AC1.2.1, AC1.2.2, AC4.1.1 to AC4.1.6, AC4.2.1, AC4.2.2, AC4.3.1, AC4.3.2.

## Testing Contract

```json
{
  "version": 1,
  "methodology": "custom",
  "source": "project",
  "ordering": "- Write tests first for code with clear expected outputs (search, lookup, web layer); write tests after the implementation for exploratory data-pipeline and model-training code, pinning behaviour on small fixture data. (learned 2026-10-26)",
  "scope": "mvp",
  "test_strategy": "standard",
  "project_type": "greenfield",
  "applicable_notes": [
    {
      "layer": "org",
      "text": "We treat tests as a first-class deliverable in every Bolt. The specific\nmethodology (TDD, BDD, ATDD, or classic test-after) is affirmed at\npractices-discovery and recorded in `team.md` under this heading with explicit\n`Methodology` and `Ordering` fields; Code Generation resolves those fields\nindependently from coverage, tooling, and scope notes.\n\nWhen no posture has been affirmed, our default per scope is:\n- **Methodology**: test-after\n- **Ordering**: implement each applicable testable layer, then write and run\n  that layer's tests.\n- `mvp`, `enterprise`, `feature`, `infra`, `classic` add an 80% line-coverage\n  floor and CI execution before merge.\n- `bugfix`, `security-patch` add a targeted regression for the specific\n  bug/vulnerability and require the existing suite to remain green.\n- `express` uses the Minimal strategy: requirement-driven unit tests (one per\n  requirement, with a happy-path floor per component); existing tests remain\n  green.\n- `poc`, `refactor`, `workshop` add no extra new-test floor and require the\n  existing suite to remain green.\n\nThe active `Test Strategy` still applies in every scope and determines test\nvolume/types. Scope floors are additive; they never reduce or replace the\nselected strategy.\n\nBuild and Test verifies defined coverage floors and affirmed quality targets;\nthey may not be weakened to make a step pass.\n\nAffirm a stricter posture in `team.md` if the team commits to one."
    },
    {
      "layer": "team",
      "text": "- **Methodology**: custom\n- **Methodology evidence**: The owner chose a mix of cadences in the interview\n  (Q3: \"test-first (TDD) for search, lookup and the web layer; test-after for the\n  data pipeline and model training\"). The search, lookup and web layers are pure\n  Python with clear inputs and outputs, so tests can lead; the Spark data\n  pipeline and the model training are exploratory and data-shaped, so tests\n  follow the implementation. The existing app has no tests, so there was no\n  prior habit to keep.\n- **Ordering**: For search, lookup and the web layer we write the tests before the implementation; for the data pipeline and model training we implement first, then write and run that layer's tests before moving on.\n- **Coverage floor**: 80% line coverage, measured with `pytest-cov`. The floor\n  is never lowered to make a step pass.\n- **Tooling**: `pytest` and `pytest-cov` in the `uv` dev dependency group, run\n  with `uv run pytest`.\n- **Test data**: tests never read the full dumps. Spark and FAISS steps are\n  tested on small fixture files under `tests/fixtures/` (a few hundred synthetic\n  listen rows), with one local `SparkSession` shared across the test session to\n  keep runs fast.\n- **Test types** (Test Strategy: Standard): unit tests for pure logic,\n  integration tests for each pipeline step on fixture data, and API tests for the\n  FastAPI endpoints with `TestClient`. The lookup-speed check against the 200 ms\n  target (constraint TC-4) runs separately from the default suite because it\n  needs the full-size index.\n- **Pre-merge check**: one local check command runs before every Bolt merge and\n  must pass: `ruff check`, `ruff format --check`, `ty` on our own code, and\n  `pytest` with the coverage floor.\n- **GitHub Actions**: a workflow running the same check is set up in the\n  repository but stays switched off until the code is pushed to GitHub; once it\n  is, it runs on every push alongside the local command."
    },
    {
      "layer": "project",
      "text": "- Write tests first for code with clear expected outputs (search, lookup, web layer); write tests after the implementation for exploratory data-pipeline and model-training code, pinning behaviour on small fixture data. (learned 2026-10-26)"
    }
  ],
  "obligations": {
    "strategy": "standard",
    "strategy_volume": [
      "Five to eight tests per component.",
      "Unit tests plus integration tests for key boundaries.",
      "Add E2E, performance, or security tests when requirements demand them."
    ],
    "scope_floor": [
      "Meet an 80% line-coverage floor.",
      "Run the selected tests in CI before merge."
    ],
    "combination_rule": "Apply every selected-strategy obligation and every scope-floor obligation; neither replaces the other, and a targeted scope regression may add the narrowest necessary test type beyond the strategy default."
  },
  "plan_profile": {
    "methodology": "custom",
    "runner_step": "Bootstrap the minimal test runner/configuration and record the exact unit-scoped command.",
    "runner_ready_before_first_test": true,
    "testable_layers": [
      "Data model / database behavior",
      "Repository / data access",
      "Business logic",
      "API / endpoint",
      "Frontend behavior"
    ],
    "steps": [
      "Project structure and production configuration skeleton.",
      "Bootstrap the minimal test runner/configuration and record the exact unit-scoped command.",
      "Custom ordering - - Write tests first for code with clear expected outputs (search, lookup, web layer); write tests after the implementation for exploratory data-pipeline and model-training code, pinning behaviour on small fixture data. (learned 2026-10-26)",
      "Implementation and tests - preserve that exact ordering; do not convert it to layer-local TDD.",
      "Environment/build configuration.",
      "Documentation and traceability."
    ]
  },
  "input_sha256": "sha256:3c4012b801ed9587da34a23e9f642ad8f1a605882bec1e87a57ecd251c0a37fd",
  "contract_sha256": "sha256:bffd3c553674c9573102ccd3ef9a9e0bc667154c9dd87c6e9258dc92d6460ffd"
}
```

## How the plan is ordered

The runner already exists from u1-skeleton, so the first steps are structure and configuration, then the exact unit-scoped test command. Search and lookup code is test-first: Red (tests that fail), Green (the code), then refactor while green. Pipeline and training code is implement-first: each step is written, then its tests are written and run before the next step starts. The skeleton's code is changed in place; nothing is duplicated.

## Steps

### Structure and configuration

- [x] **Step 1: Project structure and settings** (BR1.9, BR2.3, NFR1.7, NFR5.2). Add `tests/u2_pipeline/`. In `settings.py` add the Spark memory setting (`LISTENBRAINZ_SPARK_MEMORY`, default `24g`) and an optional prepare sample size (`LISTENBRAINZ_PREP_MAX_LINES`, default none = whole dump). In `paths.py` add the new names: the catalogue marker, the index marker, the kept-artist listener counts folder, the prepare report file, and the MusicBrainz table names. Add one function that builds every output path from the work and models folders. Give `get_spark` a memory argument that defaults to the setting.
- [x] **Step 2: Test runner command** (runner readiness). The runner, configuration and 80% floor already exist in `pyproject.toml`. Confirm the unit-scoped command `uv run pytest tests/u2_pipeline -q` collects and runs (the folder gets a trivial import test first) and record it in `unit-test-instructions.md`. Add the `listenbrainz-recs-catalogue` and `listenbrainz-recs-speed` command entries to `pyproject.toml`.

### Step markers and sources (test-after)

- [x] **Step 3: Step markers** (BR6.3, BR6.4, BR6.1; NFR2.8). New `steps.py`: write a marker with step name, run id, input run id and time; require a marker with a message naming the missing input and the step to run; refuse a stale input whose run id does not match. Replace the skeleton's `require_marker` calls. Then tests in `tests/u2_pipeline/test_steps.py`: write and read, missing input message, stale input message, a rebuilt earlier step makes later steps refuse, markers are written atomically.
- [x] **Step 4: MusicBrainz source** (BR1.1, BR1.2; NFR3.7, NFR3.8). New `musicbrainz.py` and a `DumpSource` extension: locate the MusicBrainz tables (`artist`, `artist_tag`, `tag`, `genre`) under the data location, check all are present before anything is written, name the setting and the missing file otherwise; open read-only. Then tests in `test_dump_source_full.py`: found in the real folder layout, a missing table named in the message, a missing setting, nothing written on failure, dump files unchanged (checksum and modification time) after a run.

### Prepare (test-after)

- [x] **Step 5: Prepare with all the rules** (BR1.3 to BR1.8, BR3.2; NFR1.10, NFR3.4, NFR3.6, NFR2.13, NFR2.14). Rewrite `prep.py` in Spark with an explicit column layout: read the listening dump as text, count malformed lines (not JSON, no listener number, data not a list) as skipped records, count unusable entries separately, add repeats for one listener and artist, keep artists with at least 5 distinct listeners, choose each artist's most used name (ties alphabetical), write the three-column listen counts, the artist name file, the kept-artist listener counts and the prepare report, then the marker. Keep an optional line limit for sample runs. Print one counts-only summary line. Then tests in `test_prep_full.py` on the fixture: one malformed line gives 1 skipped record and all valid lines processed (AC4.1.3), 4 listeners dropped and 5 kept (AC4.1.4), repeats summed, name choice and tie, output columns only listener number, artist id and count (AC4.1.5), the report file read back, no listener number in the printed output, sample limit.

### Training (test-after)

- [x] **Step 6: Full-size training** (BR2.1 to BR2.4; NFR1.7, NFR1.8, NFR2.12). Update `train.py`: rank 64, 10 iterations, regularisation 0.1, alpha 20 and seed in one settings block (fixtures pass a small rank for speed), read only the prepared data, count and drop zero-length vectors, write vectors and the train marker with run ids, catch an out-of-memory error and name the memory setting. Then tests in `test_train_full.py`: default settings are the current app's, one vector per kept artist (AC4.2.1), trains without the dump present (BR2.4), missing and stale prepare input messages, zero-length vectors dropped and counted, the out-of-memory message, summary line.

### Catalogue (test-after)

- [x] **Step 7: Catalogue step** (BR3.1 to BR3.5, BR4.1, BR4.8, BR6.1; NFR2.10, NFR3.5, NFR8.5). New `catalogue.py` and command `listenbrainz-recs-catalogue`, replacing the skeleton's `catalog.py`: read the kept artists, their names and listener counts, join the MusicBrainz artist short description (blank means none), join recognised genre tags with positive votes ranked by votes then name, keep artists that MusicBrainz lacks with no description and no genres, number artists by popularity (listeners desc, name, id), and write `artists.sqlite` under a temporary name with the `artist`, `artist_genre`, the sorted name index and the full-text `artist_search` tables, then the catalogue marker. Then tests in `test_catalogue.py` on a small MusicBrainz fixture: all five fields present, description from MusicBrainz and none when blank, genre filtering and ranking, artist missing from MusicBrainz kept (Q2), popularity numbering, listener counts, file written atomically and the earlier file kept when the step fails, no listener data in the file.

### Index (test-after)

- [x] **Step 8: Index step** (BR5.1, BR5.2, BR5.4, BR6.1, BR6.6; NFR1.7, NFR2.9, NFR2.11). Rewrite the build part of `index.py`: check the train and catalogue markers come from the same prepare run, remove the old manifest first, read the vector Parquet files in batches, scale each batch to unit length, drop zero-length vectors, add to the exact index, write the id file, check every id exists in the catalogue and the row counts agree, and write the manifest last. The artist file is no longer written here. Update `paths.py` `BUILDING_STEP` and the startup messages in `store.py` so `artists.sqlite` names the catalogue step. Then tests in `test_index_build.py`: the index agrees with the id file, ids missing from the catalogue stop the step without a manifest, interrupted build leaves no manifest and the app's startup check refuses it, missing and stale input messages, batch boundaries give the same index as one batch, summary line.

### Search (test-first)

- [x] **Step 9: Red — search tests** (AC1.1.1 to AC1.1.5, AC1.2.1, AC1.2.2; BR4.1 to BR4.7; NFR8.5). Write `tests/u2_pipeline/test_search.py` against a hand-built catalogue fixture (no Spark) before any search code. Cover: "henry thr" finds "Henry Threadgill"; "bjork" finds "Björk"; punctuation as a space; whitespace-only and empty text give []; no match gives []; exact name beats starts-with beats word match; more listeners first inside a tier; equal listeners fall back to name then id so order is stable; at most 10 results and a larger limit is capped; two same-name artists both appear with their own descriptions; no description stays `None`; genres come back in rank order; quotes, percent signs, stars and `OR 1=1` typed text never raise; a single-letter text still returns 10. Run them and record the failing output.
- [x] **Step 10: Green — search implementation** (BR4.1 to BR4.7). Rewrite `ArtistCatalog.suggest` in `artists.py` for the new tables: the sorted-name-index queries for the exact and starts-with tiers, then the full-text query read in popularity order, merged without repeats up to the limit. Keep `get` and `get_many`. Run the Red tests until they pass, then refactor while green. Update the startup check in `store.py` for the new tables.

### Speed check and hygiene (test-after)

- [x] **Step 11: Speed command** (BR5.3; NFR1.5, NFR1.6, NFR1.9, NFR2.15). New `speed.py`: pick 100 different artists from the loaded files, time one `neighbours` and one `suggest` lookup each (typed text taken from the artist name), compute the 95th percentile, print the count, the number and pass or fail against 200 ms for both kinds, exit non-zero on fail. It is not part of the default test run. Then tests in `test_speed.py`: percentile arithmetic, output format, fail exit code on a forced slow lookup, fewer than 100 artists uses what exists, and a fixture-size guard that both lookups answer under 200 ms (NFR1.9).
- [x] **Step 12: Privacy and hygiene tests** (AC4.1.1, AC4.1.5, AC4.1.6; NFR3.4 to NFR3.8, NFR4.2, NFR5.2, NFR8.4). Write `test_privacy_and_hygiene.py`: after a full fixture build no built file or step output holds a fixture listener number; dump files are unchanged after every step; each step creates files only under the work and models folders; the Spark session is local, with no web page and bound to 127.0.0.1; `.gitignore` lists `data/` and `models/`; no HTTP client library is imported anywhere in `src`.

### Existing code, documentation and check

- [x] **Step 13: Update the skeleton's tests and callers** (all). Change the skeleton's tests and the shared fixtures in `tests/conftest.py` where the new rules change expectations: the 5-listener cutoff, the new prepare signature, the catalogue step before the index step, and four-tier search replacing the contains search. Keep every skeleton behaviour that still holds; do not weaken an assertion to make it pass, change it to the new rule and say so in the code summary.
- [x] **Step 14: Rebuild runbook** (AC4.3.1, AC4.3.2; BR6.2, BR6.5). In `README.md` add the section "Rebuild from a new dump": the four steps in order with command, input, output and a check, then the start command and the speed command, the memory setting and the sample setting, and what each missing or stale input message looks like. Add a short test that the section names all four commands in order.
- [x] **Step 15: Pre-merge check and real-data sample run** (NFR6, NFR7). Run `bash scripts/check.sh` (ruff check, ruff format --check, ty, pytest with 80% coverage) and fix every finding without relaxing a check. Then run the four steps on the first 5,000 listener lines of the real dump with the real MusicBrainz tables (read-only) to show the pieces connect, and record the timings and one lookup. The full-size run and the full-size speed check are long and are left to the owner after this build (the runbook says how); they are recorded as not run here.
- [ ] **Step 16: Documentation and traceability.** Fill in the module docstrings that cite the BR rules, write `code-summary.md`, `source-manifest.json` and `traceability.json` as the stage describes.

## Story and rule traceability

| Plan steps | Acceptance criteria | Rules |
|------------|--------------------|-------|
| 9, 10 | AC1.1.1 to AC1.1.5, AC1.2.1, AC1.2.2 | BR4.1 to BR4.7 |
| 11 | AC1.1.6 | BR5.3 |
| 4, 5, 12 | AC4.1.1 to AC4.1.6 | BR1.1 to BR1.9, BR3.2 |
| 6 | AC4.2.1, AC4.2.2 | BR2.1 to BR2.4 |
| 3, 8, 14 | AC4.3.1, AC4.3.2 | BR6.1 to BR6.6, BR5.2 |
| 7 | AC1.2.1, AC1.2.2 (details and genres) | BR3.1 to BR3.5, BR4.8 |

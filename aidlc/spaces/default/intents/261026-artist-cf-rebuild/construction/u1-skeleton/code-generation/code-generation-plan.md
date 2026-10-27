# Code Generation Plan — u1-skeleton

## Summary

- Builds: the walking skeleton: project scaffold, pre-merge check, and a thin slice (prepare, train, index, one similar-artists endpoint) on 5,000 lines of the real dump.
- Touches: `pyproject.toml`, `scripts/check.sh`, `.gitignore`, `.github/workflows/ci.yml` (switched off), `src/listenbrainz_recs/`, `tests/u1_skeleton/`, `README.md`.
- Tests: about 35 pytest tests (unit, integration on fixture data, API tests with TestClient) at 80% line coverage; web and lookup tests are written first, pipeline tests after.

Package: `src/listenbrainz_recs/` (same name as the current app). Sources: `construction/u1-skeleton/functional-design/` (entities, rules BR1.1 to BR6.1), `nfr-requirements/`, `nfr-design/`, `inception/contract-design/contract-summary.md` (C1, C2, C3), `inception/units-generation/unit-of-work.md` (U1), and `inception/requirements-analysis/requirements.md`. Stories covered (ACs): AC2.1.1, AC2.1.5, AC4.1.1, AC4.1.2, AC4.1.5, AC4.1.6, AC4.2.1, AC4.4.1, AC4.4.2; NFRs NFR1.1, NFR1.3, NFR2.1 to NFR2.7, NFR3.1 to NFR3.3, NFR5.1, NFR8.1 to NFR8.3.

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

## Steps

Ordering follows the contract: scaffold and runner first; the lookup and web layers test-first (Red, Green, Refactor); the data pipeline and training implemented first, then tested.

- [x] **Step 1 — Project scaffold and production config** (all stories): rename `master` to `main` if no commits yet; `pyproject.toml` (uv_build, Python 3.12, runtime deps pyspark/faiss-cpu/numpy/pandas/pyarrow/fastapi/uvicorn; dev deps pytest, pytest-cov, ruff, ty pinned; ruff line length 100, rules E F W I B UP SIM; pytest and coverage config with `fail_under = 80`); `src/listenbrainz_recs/{__init__,paths,settings}.py` with the data-location and models-folder settings (BR1.1); `.gitignore` for data, models, `.venv` (BR6.1, NFR5.1).
- [x] **Step 2 — Test runner readiness and check script** (NFR6): `tests/conftest.py` (shared local SparkSession fixture, fixture paths), `tests/fixtures/` tiny dump sample (a few hundred synthetic lines in the dump's JSON-lines shape), `scripts/check.sh` (ruff check, ruff format --check, ty, pytest with coverage), and a smoke test; record the exact unit-scoped command `uv run pytest tests/u1_skeleton -q` in the instructions file.
- [x] **Step 3 — DumpSource** (BR1.1, BR1.2; AC4.1.1, AC4.1.2), test-after: `dump_source.py` locates and validates the dump, opens read-only; tests for missing setting, missing file, unchanged dump files.
- [x] **Step 4 — ListeningDataPrep** (BR1.3 to BR1.5; AC4.1.5): `prep.py` reads the first 5,000 lines, skips bad entries, writes anonymous listen counts and artist names to Parquet in batches, one summary line; tests on fixtures including a malformed entry and a no-extra-listener-fields check.
- [x] **Step 5 — SimilarityTraining** (BR2.1; AC4.2.1): `train.py` runs Spark ALS (implicit feedback, small rank) and writes one vector per artist; test on fixture data that every artist has a vector.
- [x] **Step 6 — SimilarityIndex and ArtistCatalog build** (BR3.1, BR4.1; NFR1.1): `index.py` builds the normalised FAISS inner-product index and id list; `catalog.py` builds `artists.sqlite` (names, listener counts; empty description and genres); `manifest.py` writes `manifest.json` last; temp-name-then-rename; step markers; tests on fixtures.
- [x] **Step 7 — Lookup tests first** (BR3.1, BR3.2; AC2.1.1), Red: tests for `SimilarityIndex.neighbours` (ranked, excludes self, paging, unknown id raises, no-neighbour artist returns empty) and `ArtistCatalog.get_many`; run and record the failing output.
- [x] **Step 8 — Lookup implementation** (BR3.1, BR3.2), Green then Refactor: `store.py` (loads files once), `similarity.py`, `artists.py` classes per contract C1.
- [x] **Step 9 — Web layer tests first** (BR4.2, BR5.1, BR5.2, NFR8.2; AC2.1.1, AC2.1.5, AC4.4.2), Red: TestClient tests for `GET /api/artists/{mbid}/similar` (ranked results with names and cosine, 404 unknown, 422 bad paging or id, no listener fields), `GET /api/health`, startup failure with each C2 file removed and with a wrong format version.
- [x] **Step 10 — Web layer implementation** (BR4.2, BR4.3, BR5.1, BR5.2; AC4.4.1), Green then Refactor: `app/main.py` (FastAPI app factory, startup checks, request logging, allow-listed responses, 127.0.0.1 default), command entry point `uv run listenbrainz-recs-serve`, pipeline entry points `prepare`, `train`, `index`.
- [x] **Step 11 — End-to-end skeleton test** (all of the above; the verification command's target): one integration test builds all files from the fixture sample into a temp folder and queries the endpoint; `scripts/check.sh` runs it.
- [x] **Step 12 — CI workflow file and docs** (NFR6): `.github/workflows/ci.yml` running `scripts/check.sh`, kept off (`if: false` on the job) until the code is pushed; README with the sample-build commands and start command.
- [x] **Step 13 — Traceability and summary**: `code-summary.md`, `source-manifest.json`, `traceability.json`.

## Story-to-Step Traceability

| Item | Steps |
|------|-------|
| AC2.1.1 ranked neighbours | 7, 8, 9, 10 |
| AC2.1.5 no listener data | 9, 10 |
| AC4.1.1, AC4.1.2 read-only dumps, missing setting | 3 |
| AC4.1.5, AC4.1.6 anonymous data, git-ignored | 1, 4 |
| AC4.2.1 one vector per artist | 5 |
| AC4.4.1, AC4.4.2 start command, fail-fast | 9, 10 |
| NFR1.1, NFR1.3 speed, build time | 6, 8, 11 |
| NFR2.x reliability and observability | 6, 9, 10 |

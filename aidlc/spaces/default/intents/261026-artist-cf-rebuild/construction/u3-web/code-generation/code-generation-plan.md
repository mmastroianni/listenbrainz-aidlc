# Code Generation Plan — u3-web

## Summary

- Builds: the suggestion endpoint, the missing-from-index handling, page headers, the one-page site (HTML, CSS and JavaScript) at `/` and `/artist/<id>`, and the two quality-check commands with their README section.
- Touches: `src/listenbrainz_recs/app/main.py`, new `src/listenbrainz_recs/app/static/` (page, stylesheet, script) and `src/listenbrainz_recs/quality.py`, `tests/u3_web/`, `tests/u1_skeleton/` where the new rules change old expectations, `pyproject.toml`, `README.md`, `docs/manual-checks.md`.
- Tests: about 55 new tests (endpoint, header, page-file and quality-check tests through the test client), all written before the code they check, under the 80% coverage floor; the keyboard and phone pass is done by hand and listed in `docs/manual-checks.md`.

Inputs: `construction/u3-web/functional-design/` (BR1.1 to BR5.3, W1 to W4), `construction/u3-web/nfr-requirements/` and `nfr-design/` (NFR1.11 to NFR8.10), the page designs in `inception/refined-mockups/`, contracts C1 and C3 in `inception/contract-design/contract-summary.md`, and the code from u1-skeleton and u2-pipeline (`construction/u2-pipeline/code-generation/code-summary.md`). Stories covered: AC1.1.1 to AC1.1.6, AC1.2.1, AC1.2.2, AC2.1.1 to AC2.1.6, AC2.2.1, AC2.2.2, AC2.3.1 to AC2.3.3, AC2.4.1 to AC2.4.5, AC3.1.1, AC3.1.2, AC3.2.1, AC3.2.2, AC5.1.1, AC5.1.2.

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

The runner already exists, so the first steps are structure and the exact unit-scoped test command. Everything in this unit is search, lookup or web code, so every layer is test-first: Red (write tests that fail and record the failing output), Green (the code), then refactor while green. The skeleton's endpoint and the u2-pipeline catalogue are changed in place; nothing is duplicated.

## Steps

### Structure and configuration

- [x] **Step 1: Project structure** (NFR1.14, NFR4.3). Add `tests/u3_web/` and the folder `src/listenbrainz_recs/app/static/` for the page files. Add the two quality-check command entries (`listenbrainz-recs-quality-sheet`, `listenbrainz-recs-quality-verdict`) to `pyproject.toml`. Make sure the page files ship with the package.
- [x] **Step 2: Test runner command** (runner readiness). Confirm `uv run pytest tests/u3_web -q` collects and runs (a trivial import test first) and record it in `unit-test-instructions.md`. The runner, configuration and 80% floor already exist.

### Endpoints (test-first)

- [x] **Step 3: Red — endpoint tests** (AC1.1.1 to AC1.1.5, AC2.1.1, AC2.1.5, AC2.2.1, AC2.2.2, AC2.3.1, AC2.3.2, AC2.3.3; BR1.1 to BR1.4, BR2.1 to BR2.5; NFR1.13, NFR2.18, NFR2.20, NFR3.9, NFR3.11, NFR3.12, NFR3.13, NFR8.8, NFR8.9). Write `tests/u3_web/test_suggest_endpoint.py`, `test_similar_endpoint.py` and `test_headers_logs_concurrency.py` before any endpoint code. Cover: suggestions for "henry thr" and "bjork" in the catalogue's order, at most 10, an empty list for no match and for blank text, text of 201 characters refused with 422, response keys limited to the allow-list on both endpoints and the health endpoint; paging 20 at a time with `has_more` false when exactly 20 exist and after 45 are shown in three pages, the bar on page two scaled against the first page's top score; an artist in the catalogue but not in the index returns the artist with no items; an id in neither is 404; a malformed id, a negative offset and a limit of 0 or 101 are 422; page headers (policy, no-sniff, no-referrer) on `/`, `/artist/<id>` and an endpoint; the log holds the path and not the typed text; 5 parallel requests to each endpoint all succeed; a timing guard of 20 lookups each under 200 ms; two failure paths per endpoint (closed catalogue connection, index read error) give a short 500 and an ERROR log. Run them and record the failing output.
- [x] **Step 4: Green — endpoint code** (BR1.1 to BR1.4, BR2.1 to BR2.5, BR3.1; NFR3.9, NFR3.11 to NFR3.13, NFR8.8). In `app/main.py` add `GET /api/suggest` (text limit 200, up to 10, allow-listed fields), the catalogue check when the index reports an unknown id, the header middleware, and the routes `/`, `/artist/{mbid}` and the static files, keeping the skeleton's validation, logging and error handlers. Run the Red tests until they pass, then refactor while green.

### The page (test-first)

- [x] **Step 5: Red — page tests** (AC2.1.2 to AC2.1.4, AC2.3.1 to AC2.3.3, AC2.4.1 to AC2.4.5, AC3.1.1, AC3.1.2, AC3.2.1, AC3.2.2; BR3.1 to BR3.3, BR4.1 to BR4.13; NFR1.14, NFR1.15, NFR2.17, NFR2.19, NFR3.10, NFR4.3). Write `tests/u3_web/test_page_files.py` through the test client before the page files exist. Cover: `/` and `/artist/<id>` (including a malformed id) return the same HTML page; the page declares its language, has one `h1` and one `h2`, a visible label "Artist", the combobox and listbox roles, a polite live region and a clear button; the stylesheet has the design tokens, the focus ring, a 375 px layout with no fixed width wider than the screen, a wrapping rule for names and the phone rules; the script has no `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write` or `eval`, the 150 ms pause, the request counters and busy flag, the history calls, the exact messages from BR4.3 and BR4.9, the three link prefixes and `rel="noopener noreferrer"`, and the key names Down, Up, Enter and Escape; no `http://` or `https://` address in the three files except the three link patterns; the three files total under 100 KB. Run them and record the failing output.
- [x] **Step 6: Green — the page** (BR3.1 to BR3.3, BR4.1 to BR4.13). Write `app/static/index.html`, `style.css` and `app.js` following `inception/refined-mockups/mockups.md`, `interaction-spec.md`, `accessibility-checklist.md` and `design-system-mapping.md`: plain files, text-only rendering, the states in BR4.9, history entries for picks, focus rules, five placeholder rows, Retry, Show more, clear button, three icon links as inline SVG with labels. Run the Red tests until they pass, then refactor while green. Then start the app on the sample build and check the page in a browser-less pass: fetch each file and endpoint with `curl`, and run `node --check` on the script when Node is installed (report when it is not).

### Quality check (test-first)

- [x] **Step 7: Red — quality-check tests** (AC5.1.1, AC5.1.2; BR5.1 to BR5.3; NFR2.23, NFR5.3). Write `tests/u3_web/test_quality_check.py`: the sheet lists the new app's top 20 for each named artist with genres and an unset verdict line; more than 5 artists is refused; a name that matches nothing stops with a message naming it; the sheet holds no listener fields; the verdict command reports pass for 4 of 5 better-or-equal, fail for 3 of 5, incomplete when any is unset, and a clear message naming the line when the sheet cannot be read; printouts are counts only. Run them and record the failing output.
- [x] **Step 8: Green — quality-check commands** (BR5.1 to BR5.3). New `quality.py` with the two commands; the sheet is written to `docs/quality-check.md` by default (a path argument overrides it). Run the Red tests until they pass, then refactor while green.

### Existing code, documentation and check

- [x] **Step 9: Update the skeleton's tests** (all). Change a skeleton test only where the new rules change its expectation (for example the artist in the catalogue but not in the index, and the extra response headers); do not weaken an assertion, change it to the new rule and say so in the code summary.
- [x] **Step 10: Documentation** (AC4.4.1; BR5.1, BR5.2). Add to `README.md` the page and the two addresses, the suggestion endpoint, and a "Quality check against the current app" section with the two commands and what to do between them. Write `docs/manual-checks.md` from the accessibility checklist: the keyboard and phone pass the owner does by hand before `v0.1.0`, with each item as a checkbox.
- [x] **Step 11: Pre-merge check and sample run** (NFR6, NFR7). Run `bash scripts/check.sh` and fix every finding without relaxing a check. Then start the app on the sample build from u2-pipeline (`models/sample`, git-ignored), fetch `/`, `/artist/<an id from the sample>`, `/api/suggest?q=bjork` and a similar-artists page 1 and 2 with `curl`, and record the timings and header check. The browser keyboard and phone pass and the full-size speed check are the owner's and are recorded as not run here.
- [ ] **Step 12: Documentation and traceability.** Fill in the module docstrings that cite the BR rules, write `code-summary.md`, `source-manifest.json` and `traceability.json` as the stage describes.

## Story and rule traceability

| Plan steps | Acceptance criteria | Rules |
|------------|--------------------|-------|
| 3, 4 | AC1.1.1 to AC1.1.5, AC2.1.1, AC2.1.5, AC2.2.1, AC2.2.2, AC2.3.1, AC2.3.2 | BR1.1 to BR1.4, BR2.1 to BR2.5 |
| 5, 6 | AC1.2.1, AC1.2.2, AC2.1.2 to AC2.1.4, AC2.3.3, AC2.4.1 to AC2.4.5, AC3.1.1, AC3.1.2, AC3.2.1, AC3.2.2 | BR3.1 to BR3.3, BR4.1 to BR4.13 |
| 7, 8 | AC5.1.1, AC5.1.2 | BR5.1 to BR5.3 |
| 3, 11 | AC1.1.6, AC2.1.6 | BR1.4 (fixture timing guard here; full-size check is the owner's) |

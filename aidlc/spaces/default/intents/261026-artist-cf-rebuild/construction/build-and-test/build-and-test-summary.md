# Build and Test Summary

## Overall Status

- **Build:** ready. `uv sync` and `bash scripts/check.sh` pass (ruff, format, `ty`, 277 tests, 94.52% coverage against the 80% floor).
- **Full-size run:** done on the real dump in about 13 minutes, with the 200 ms speed check passing (similar artists 21.4 ms, suggestions 0.9 ms at the 95th percentile). Details are in `test-results.md`.
- **Result:** one applicable target is `Unverified`: the browser part of NFR2.19. Under the stage's failure rule that makes Build and Test not yet successful. Everything else that could be measured here is `Met`.

## Test Type Inventory

Test Strategy is Standard, so the stage generated build, integration, performance and security instruction files (`build-instructions.md`, `integration-test-instructions.md`, `performance-test-instructions.md`, `security-test-instructions.md`). Unit tests are per unit (`construction/*/code-generation/unit-test-instructions.md`).

## Coverage Expectations per Unit

| Unit | Tests | Expected |
|------|-------|----------|
| u1-skeleton | 76 | part of the 80% project floor |
| u2-pipeline | 115 | new modules above 85% (all are: `steps` 100%, `musicbrainz` 100%, `catalogue` 85%, `speed` 99%) |
| u3-web | 86 | `main.py` and `quality.py` above 90% (97% and 98%) |

The 80% floor applies to the whole project and was met at 94.52%.

## Target Verification Matrix

Evidence keys: **A** = `bash scripts/check.sh`, 277 passed, run in this stage (`test-results.md`); **B** = the full-size rebuild and speed check in this stage (`test-results.md`); **C** = a code read of `src/listenbrainz_recs/app/static/app.js` in this stage. Sources are each unit's `nfr-requirements/` folder (u1: `construction/u1-skeleton/nfr-requirements/`, u2: `construction/u2-pipeline/nfr-requirements/`, u3: `construction/u3-web/nfr-requirements/`) and the Testing Contract in each `code-generation-plan.md`.

| Target ID | Source | Expected | Actual | Evidence | Owning Stage | Verdict |
|-----------|--------|----------|--------|----------|--------------|---------|
| NFR1.1 | u1 performance | sample lookup p95 under 200 ms | passes in the timing test | A: `tests/u1_skeleton/test_api.py` | build-and-test | Met |
| NFR1.2 | u1 performance | full-size lookup p95 under 200 ms | 21.4 ms | B: speed command | build-and-test | Met |
| NFR1.3 | u1 performance | skeleton build under 5 min on 5,000 lines | prepare 51 s + train 59 s + catalogue 44 s + index 0.9 s | u2 code summary sample run | build-and-test | Met |
| NFR1.4 | u1 scalability | design streams, scales to the full dump | full dump prepared in 182 s | B | build-and-test | Met |
| NFR2.1 | u1 reliability | startup refuses missing file or version | tested for each missing file | A: `tests/u1_skeleton/test_api.py`, `tests/u3_web` | build-and-test | Met |
| NFR2.2 | u1 reliability | atomic writes, manifest last | tested, interrupted build leaves no manifest | A: `tests/u2_pipeline/test_index_build.py` | build-and-test | Met |
| NFR2.3 | u1 reliability | steps refuse missing input | tested | A: `tests/u2_pipeline/test_steps.py` | build-and-test | Met |
| NFR2.4 | u1 reliability | boundary errors surfaced | two failure paths per step tested | A | build-and-test | Met |
| NFR2.5 | u1 observability | one summary line per step | seen on the full run and tested | A, B | build-and-test | Met |
| NFR2.6 | u1 observability | request log lines | tested | A: `tests/u3_web/test_headers_logs_concurrency.py` | build-and-test | Met |
| NFR2.7 | u1 observability | health endpoint | tested | A: `tests/u1_skeleton/test_api.py` | build-and-test | Met |
| NFR3.1 | u1 security | no listener data in files or responses | tested | A | build-and-test | Met |
| NFR3.2 | u1 security | prepared data holds only the three columns | tested | A: `tests/u2_pipeline/test_prep_full.py` | build-and-test | Met |
| NFR3.3 | u1 security | dumps opened read-only | tested; real dump times unchanged | A, B | build-and-test | Met |
| NFR4.1 | u1 security | no paid or remote service | no HTTP client imported, tested | A: `tests/u2_pipeline/test_privacy_and_hygiene.py` | build-and-test | Met |
| NFR5.1 | u1 security | data and models git-ignored | check script finds no tracked files; `git status` shows none | A | build-and-test | Met |
| NFR8.1 | u1 security | listens on 127.0.0.1 by default | tested | A: `tests/u1_skeleton/test_api.py` | build-and-test | Met |
| NFR8.2 | u1 security | bad ids give 404 or 422 | tested | A | build-and-test | Met |
| NFR8.3 | u1 scalability | 5 concurrent requests | tested | A: `tests/u3_web/test_headers_logs_concurrency.py` | build-and-test | Met |
| NFR1.5 | u2 tech-stack | similar-artist p95 under 200 ms at full size | 21.4 ms | B | build-and-test | Met |
| NFR1.6 | u2 tech-stack | suggestion p95 under 200 ms at full size | 0.9 ms (short texts 0.3 to 2.9 ms) | B | build-and-test | Met |
| NFR1.7 | u2 tech-stack | training and index build peak under 32 GB | training 12.7 GB sampled; index step 1.4 s on a 68 MB index | B | build-and-test | Met |
| NFR1.8 | u2 tech-stack | step time reported, no limit | each step prints its duration | B | build-and-test | Met |
| NFR1.9 | u2 tech-stack | fixture lookups under 200 ms | passes | A: `tests/u2_pipeline/test_speed.py` | build-and-test | Met |
| NFR1.10 | u2 tech-stack | full dump workable by streaming | prepared in 182 s | B | build-and-test | Met |
| NFR2.8 | u2 tech-stack | missing and stale input messages | tested | A: `tests/u2_pipeline/test_steps.py` | build-and-test | Met |
| NFR2.9 | u2 tech-stack | manifest last, interrupted index leaves none | tested | A: `tests/u2_pipeline/test_index_build.py` | build-and-test | Met |
| NFR2.10 | u2 tech-stack | failed step leaves earlier files usable | tested | A: `tests/u2_pipeline/test_catalogue.py` | build-and-test | Met |
| NFR2.11 | u2 tech-stack | file boundary errors surfaced | tested | A | build-and-test | Met |
| NFR2.12 | u2 tech-stack | out-of-memory message names the setting | message unit-tested; real condition not reproduced (as the requirement allows) | A: `tests/u2_pipeline/test_train_full.py` | build-and-test | Met |
| NFR2.13 | u2 tech-stack | one counts-only summary line per step | tested and seen | A, B | build-and-test | Met |
| NFR2.14 | u2 tech-stack | prepare report stored | `data/full/prepare_report.json` written | A, B | build-and-test | Met |
| NFR2.15 | u2 tech-stack | speed command prints both percentiles | seen | B | build-and-test | Met |
| NFR3.4 | u2 security | prepared data has no listener detail | tested | A | build-and-test | Met |
| NFR3.5 | u2 security | no listener data in built files | tested | A: `tests/u2_pipeline/test_privacy_and_hygiene.py` | build-and-test | Met |
| NFR3.6 | u2 security | output shows counts only | tested | A | build-and-test | Met |
| NFR3.7 | u2 security | dumps unchanged | tested; real dump times unchanged | A, B | build-and-test | Met |
| NFR3.8 | u2 security | bad location writes nothing | tested | A: `tests/u2_pipeline/test_dump_source_full.py` | build-and-test | Met |
| NFR4.2 | u2 security | no remote service from the pipeline | local Spark, tested | A | build-and-test | Met |
| NFR5.2 | u2 security | output only in ignored folders | tested; `git status` shows no data files | A | build-and-test | Met |
| NFR8.4 | u2 security | no network port from the pipeline | Spark page off, driver on 127.0.0.1, tested | A | build-and-test | Met |
| NFR8.5 | u2 security | typed text only a value, never an error | tested | A: `tests/u2_pipeline/test_search.py` | build-and-test | Met |
| NFR8.6 | u2 tech-stack | 5 concurrent lookups | tested | A | build-and-test | Met |
| NFR1.11 | u3 performance | suggestion endpoint p95 under 200 ms at full size | 0.9 ms on the catalogue (the endpoint adds one call) | B | build-and-test | Met |
| NFR1.12 | u3 performance | similar-artists endpoint p95 under 200 ms at full size | 21.4 ms on the index and catalogue | B | build-and-test | Met |
| NFR1.13 | u3 performance | endpoints under 200 ms on the fixture | passes | A: `tests/u3_web/test_headers_logs_concurrency.py` | build-and-test | Met |
| NFR1.14 | u3 performance | page files under 100 KB | 23,535 bytes | A: `tests/u3_web/test_page_files.py` | build-and-test | Met |
| NFR1.15 | u3 performance | one request per pause, pick or Show more | request counts match the script | C | build-and-test | Met |
| NFR2.16 | u3 reliability | startup fails fast on bad files | tested | A | build-and-test | Met |
| NFR2.17 | u3 reliability | failure shows plain message and Retry | JSON and script text tested | A: `tests/u3_web/test_page_files.py` | build-and-test | Met |
| NFR2.18 | u3 reliability | catalogue-only artist shows "not enough data" | tested | A: `tests/u3_web/test_similar_endpoint.py` | build-and-test | Met |
| NFR2.19 | u3 reliability | late replies and double clicks handled, checked in the manual pass and by a review of the script | script review (C) shows request counters and the busy flag; not run in a browser | C; manual pass pending (`docs/manual-checks.md`) | build-and-test | Unverified |
| NFR2.20 | u3 reliability | boundary errors give a short 500 and an ERROR log | tested, two paths per endpoint | A: `tests/u3_web/test_headers_logs_concurrency.py` | build-and-test | Met |
| NFR2.21 | u3 observability | log path and status, never query text | tested | A | build-and-test | Met |
| NFR2.22 | u3 observability | health endpoint | tested | A | build-and-test | Met |
| NFR2.23 | u3 observability | quality commands print counts only | tested | A: `tests/u3_web/test_quality_check.py` | build-and-test | Met |
| NFR3.9 | u3 security | no listener data in responses | tested | A | build-and-test | Met |
| NFR3.10 | u3 security | page shows text only, no markup APIs | script text tested | A: `tests/u3_web/test_page_files.py` | build-and-test | Met |
| NFR3.11 | u3 security | errors are short JSON | tested | A | build-and-test | Met |
| NFR3.12 | u3 security | page headers set | tested | A | build-and-test | Met |
| NFR3.13 | u3 security | no query text in logs | tested | A | build-and-test | Met |
| NFR4.3 | u3 security | page loads nothing from other sites | tested | A | build-and-test | Met |
| NFR5.3 | u3 security | quality sheet has artist-level data only | tested | A | build-and-test | Met |
| NFR8.7 | u3 security | 127.0.0.1 by default | tested | A | build-and-test | Met |
| NFR8.8 | u3 security | inputs validated, 404 or 422 | tested | A | build-and-test | Met |
| NFR8.9 | u3 scalability | 5 concurrent requests | tested | A | build-and-test | Met |
| NFR8.10 | u3 scalability | no per-user state | no sessions, cookies or caches in `main.py` | A | build-and-test | Met |
| TC-COVERAGE | Testing Contract (all units) | 80% line coverage | 94.52% | A | build-and-test | Met |
| TC-PRE-MERGE | Testing Contract and project rule | pre-merge check passes | passes | A | build-and-test | Met |
| TC-STRATEGY | Testing Contract (Standard) | 5 to 8 tests per component, unit plus integration | 277 tests, 76 + 115 + 86 per unit | A | build-and-test | Met |
| TC-SPEED-SEPARATE | team practices | full-size speed check runs apart from the default suite | run as its own command | B | build-and-test | Met |
| TC-CI | Testing Contract (scope floor) | tests run in CI before merge | the plan has CI Pipeline still ahead; CI Pipeline, later in this plan, sets up CI to run these tests before merge | not applicable here | ci-pipeline | N/A |

## Readiness Assessment

- **Build-ready:** yes.
- **Test-ready:** yes for everything that can run without a person: 277 tests pass and the full-size rebuild and speed check pass.
- **Deployment-ready:** not applicable; v1 is local only and the Operation phase is skipped.

## Known Limitations and Outstanding Items

- **Not yet seen in a browser:** the page script and the keyboard, focus and phone behaviour (AC2.4.1 to AC2.4.5 and the browser part of NFR2.19). The owner's pass in `docs/manual-checks.md` is needed before `v0.1.0`.
- **Quality check (FR8.1, US5.1):** the owner still has to compare 5 artists against the current app with the two quality-check commands; this is a person's judgement, not a test.
- **Unit records still say Deferred** for AC1.1.6, AC2.1.6 and AC4.2.2 and for NFR1.2, NFR1.4, NFR1.5, NFR1.6, NFR1.7, NFR1.11, NFR1.12. They were measured in this stage (see the matrix); the approved unit records were not edited, which is why the cross-unit traceability check still lists them.
- **Skeleton demo data:** `data/` and `models/` still hold the skeleton's sample outputs beside the new `data/full`, `data/sample`, `models/full` and `models/sample` folders. All are git-ignored.

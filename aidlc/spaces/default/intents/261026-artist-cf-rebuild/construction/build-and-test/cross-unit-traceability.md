# Cross-Unit Traceability

Produced from `aidlc engine sensor-traceability --stage build-and-test`, run after all three units were approved. Sources: `inception/requirements-analysis/requirements.md`, `inception/user-stories/stories.md` and each unit's `functional-design/`, `nfr-requirements/`, `nfr-design/` and `code-generation/traceability.json`.

## Verdict: FAIL on the record, with every gap explained

The check lists 18 uncovered items. All of them are items that the unit records marked `Deferred` (to be measured at full size) because the full-size run had not happened when the unit was approved. This stage ran the full rebuild and the speed check, and every one of them is now measured and `Met` (see `build-and-test-summary.md`). The approved unit records were not edited, so the sensor still reads them as not built.

## Uncovered items

| ID | Why it is uncovered | Owning Unit | Status now |
|----|---------------------|-------------|------------|
| AC1.1.6 | Deferred in u2-pipeline and u3-web: full-size suggestion timing | u2-pipeline, u3-web | Met: 0.9 ms at the 95th percentile (limit 200 ms) |
| AC2.1.6 | Deferred in u3-web: full-size similar-artists timing | u3-web | Met: 21.4 ms |
| AC4.2.2 | Deferred in u2-pipeline: full-size training within memory | u2-pipeline | Met: training finished, peak Java memory 12.7 GB |
| NFR1 | Rolls up NFR1.2, NFR1.4, NFR1.5, NFR1.6, NFR1.7, NFR1.11, NFR1.12, all Deferred in the unit records | all units | Met (matrix rows) |
| NFR4 | u1-skeleton NFR4.1 was not traced as built | u1-skeleton | Met: no HTTP client is imported (tested) |
| NFR8 | The sensor attributes `NFR8.5` to u3-web because u3-web's security text mentions it; it is u2-pipeline's requirement and is built there | u2-pipeline | Met: `tests/u2_pipeline/test_search.py` |
| FR2.1, FR2.2 | Follow from AC4.2.2 | u2-pipeline | Met |
| FR3.1, FR3.2, FR5.1, FR5.2, FR5.3, FR5.9 | Follow from AC2.1.6 | u1-skeleton, u3-web | Met |
| FR4.1, FR4.2, FR4.3, FR4.5 | Follow from AC1.1.6 | u2-pipeline, u3-web | Met |

## Everything else

All other functional requirements (FR1.1 to FR1.4, FR4.4, FR5.4 to FR5.8, FR6.1 to FR6.6, FR7.1, FR7.2, FR8.1), every other acceptance criterion in the 13 stories (US1.1 to US5.1) and NFR2, NFR3 and NFR5 (with NFR6 and NFR7 `N/A` as process rules) are covered by a built file or test in at least one unit, as the sensor output shows. NFR2, NFR3 and NFR5 are covered; NFR6 and NFR7 are `N/A` with their reasons recorded in each unit's NFR requirements.

## Findings for the approval gate

- The unit records' `Deferred` entries should be read together with the matrix in `build-and-test-summary.md`, which carries the full-size evidence.
- Items covered by `app.js` rather than by a test (the page behaviour for AC1.1.4, AC1.1.5, AC1.2.x, AC2.1.2, AC2.1.4, AC2.3.3, AC2.4.x, AC3.1.x, AC3.2.1) have been code-read and syntax-checked but not run; they wait for the owner's browser pass.
- The owner's quality check (AC5.1.1, AC5.1.2) is built but not yet run on real artists.

# Tech Stack Decisions — u2-pipeline

The stack is fixed by the project rule (same tools as the current app) and the team practices, and carries over unchanged from the skeleton (`construction/u1-skeleton/nfr-requirements/tech-stack-decisions.md`). This file records how each tool is used at full size, and the performance, scale, reliability and observability requirements for this unit. u2-pipeline is a library unit, so those four categories are written here instead of in files of their own. Sources: `inception/requirements-analysis/requirements.md`, the functional design (`construction/u2-pipeline/functional-design/functional-spec.md`, `rules.md`), `inception/contract-design/contract-summary.md` and `nfr-requirements-questions.md`.

## Stack

| Concern | Choice | Why |
|---------|--------|-----|
| Language and packaging | Python 3.12, uv, `src/` layout | Unchanged; team practices |
| Data preparation and training | PySpark with its implicit-feedback ALS; settings rank 64, 10 iterations, regularisation 0.1, alpha 20 (BR2.2) | Same as the current app (`pipeline/train_als.py`); proven at full size |
| Spark running mode | Local master with an explicit driver memory setting and the web page off | One machine; NFR1.3, NFR8.4 |
| Nearest-neighbour index | FAISS exact inner-product index over unit-length vectors, built from batches | Same as the current app; contract C2; BR5.1, BR5.4 |
| Artist details and name search | SQLite, with its full-text search table over normalised names | Contract C2; the current app does the same; the tiers in BR4.4 are applied on top of the matches |
| Interim data format | Parquet | Spark's native output |
| MusicBrainz tables | The dump's tab-separated tables, read by Spark | Same as the current app (`pipeline/build_artist_tags.py`) |
| Quality tools | ruff, ty (pinned), pytest, pytest-cov, one shared local SparkSession in tests | Team practices |

No new runtime dependency is added. UMAP stays out; it is stretch scope.

## Performance and resources

| ID | Requirement | Target | Measured by |
|----|-------------|--------|-------------|
| NFR1.5 | Similar-artist lookup at full size | Under 200 ms at the 95th percentile over 100 lookups of different artists, on the owner's machine | The speed check command (BR5.3), run by hand after a full build; not in the default test run |
| NFR1.6 | Suggestion lookup at full size | Under 200 ms at the 95th percentile over 100 lookups of different typed texts | The same speed check command (BR5.3) |
| NFR1.7 | Peak memory of full-size training and of the index build | Under 32 GB, the low end of the owner's range | Spark's memory setting is 24 GB or less for the driver; the full-size run completes without running out of memory; vectors are read in batches (BR2.3, BR5.4) |
| NFR1.8 | Time of preparation, training and the index build | No limit; each step prints how long it took | Step summary line (NFR2.8) |
| NFR1.9 | The same lookups on the fixture-sized build | Under 200 ms in the default test run, as a guard against slow code | A timing test on the fixture |

## Scale

| ID | Requirement | Target |
|----|-------------|--------|
| NFR8.6 | Users and concurrency | One local user; the pipeline steps run one at a time; the catalogue and index handle 5 concurrent lookups without errors |
| NFR1.10 | Data size | The steps stream the listening dump and read vectors in batches, so the full dump (the listening file is about 3.5 GB) is workable without raising the memory target |

## Reliability

| ID | Requirement | Pass criterion |
|----|-------------|----------------|
| NFR2.8 | A step stops with a clear message when the step before it has not been run, or when its input is older than a newer run of the earlier step | A test runs each later step without its input and with a stale input; the message names the missing input and the step to run (BR6.3, BR6.4) |
| NFR2.9 | Files are written under a temporary name and renamed when complete; the manifest is written last | A test that interrupts the index step after the index file leaves no manifest, and the app's startup check refuses it (BR6.1, BR6.6) |
| NFR2.10 | A failed step leaves the previous good files usable | A test makes the catalogue step fail part way and finds the earlier catalogue file unchanged |
| NFR2.11 | Failures at file boundaries (reading a dump, reading a Parquet file, opening the catalogue) are shown as a message, not swallowed | Two failure paths per step are tested, as the construction rules ask |
| NFR2.12 | An out-of-memory stop names the memory setting to raise | A unit test of the message; the real condition is not reproduced in tests (BR2.3) |

Rebuilding is the recovery: re-run the steps in the documented order. The dumps are never modified, so there is nothing else to back up.

## Observability

| ID | Requirement | Pass criterion |
|----|-------------|----------------|
| NFR2.13 | Each step prints one summary line: rows read, lines skipped, entries skipped, artists kept, output files and duration | Asserted in an integration test on the fixture (BR1.8) |
| NFR2.14 | The prepare report is stored next to the prepared data | A test reads it back after a prepare run |
| NFR2.15 | The speed check prints the measured 95th percentile and the number of lookups for both lookup kinds | The command's output shows both numbers and a pass or fail |

No dashboards, alerts or tracing are needed in v1 (the Operation phase is skipped).

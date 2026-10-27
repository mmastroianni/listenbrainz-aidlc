# Performance Test Instructions

Covers the performance targets in each unit's `nfr-requirements/` (u1-skeleton NFR1.1 to NFR1.4, u2-pipeline NFR1.5 to NFR1.10, u3-web NFR1.11 to NFR1.15) and the requirement NFR1 in `inception/requirements-analysis/requirements.md`.

## Targets

| Target | Expected | Check |
|--------|----------|-------|
| Similar-artist lookup, full size | 95th percentile under 200 ms over 100 lookups of different artists | `uv run listenbrainz-recs-speed` against the full build |
| Suggestion lookup, full size | 95th percentile under 200 ms over 100 lookups of different typed texts | the same command |
| Training and index build memory, full size | peak under 32 GB | `/usr/bin/time -v` around each step (peak size of the largest process) |
| Preparation and training time | no limit; reported | each step's summary line |
| Both lookups on the fixture build | under 200 ms in the default test run | `tests/u2_pipeline/test_speed.py`, `tests/u3_web/test_headers_logs_concurrency.py` |
| Page files | under 100 KB in total | `tests/u3_web/test_page_files.py` |

## Run the full-size check

```bash
export LISTENBRAINZ_MODELS_DIR=models/full     # the folder the full rebuild wrote
uv run listenbrainz-recs-speed
```

It prints, for each lookup kind, the number of lookups, the 95th percentile in milliseconds and pass or fail, and exits non-zero on a fail. Run it after the full rebuild, on the owner's machine, with nothing else heavy running.

## Test data and environment

The full build in `models/full` (git-ignored). The command picks 100 different artists with a fixed seed so runs are comparable.

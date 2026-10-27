# Test Results

Run on the owner's machine (20 cores, 62 GB memory) on 2026-10-27. Build and Test ran every command in the instruction files except the browser pass, which needs a person and a browser.

## Build

| Step | Command | Result |
|------|---------|--------|
| Install | `uv sync` | 37 packages checked, nothing to change |
| Pre-merge check | `bash scripts/check.sh` | passed: no tracked data or model files, `ruff check`, `ruff format --check`, `ty check` (no checks disabled), pytest with the coverage floor |

## Unit and integration tests

| Unit | Tests | Passed | Failed | Skipped |
|------|-------|--------|--------|---------|
| u1-skeleton (`tests/u1_skeleton`) | 76 | 76 | 0 | 0 |
| u2-pipeline (`tests/u2_pipeline`) | 115 | 115 | 0 | 0 |
| u3-web (`tests/u3_web`) | 86 | 86 | 0 | 0 |
| Total | 277 | 277 | 0 | 0 |

The three unit commands were collected separately for the counts, then the whole suite ran once inside the pre-merge check (97.8 s), so no test was counted twice. The integration boundaries in `integration-test-instructions.md` are covered by these tests (`test_end_to_end.py`, `test_index_build.py`, the endpoint tests). One pytest warning appears in the run (a `StarletteDeprecationWarning` about the test client noted in the u1-skeleton summary); it is not a failure.

**Coverage:** 94.52% total (floor 80%). Lowest module: `store.py` 81%. `catalogue.py` 85%, `index.py` 88%, `train.py` 90%, `spark.py` 90%.

## Full-size rebuild on the real dump

Whole dump, read in place, work and models folders `data/full` and `models/full` (git-ignored). Dump file modification times were the same before and after (`artists_all_time.jsonl` 2026-09-17 10:20, the MusicBrainz tables 2026-10-11).

| Step | Wall time | Result |
|------|-----------|--------|
| prepare | 181.7 s | 84,850 lines read, 0 skipped lines, 7,708,318 skipped entries (no artist id), 28,901,172 listen counts, 267,604 artists kept |
| train | 504.1 s | 267,604 vectors of rank 64, 0 dropped; peak Java memory 12.7 GB (sampled every 3 s) |
| catalogue | 54.3 s | 267,604 artists, 105,451 with a description (39.4%), 83,221 with genres (31.1%); peak Java memory 6.3 GB |
| index | 1.4 s | 267,604 artists indexed, dimension 64, 0 dropped; `artists.faiss` 68.5 MB, `artists.sqlite` 119 MB |

The whole rebuild took about 13 minutes. The memory of the prepare step was not sampled; one reading during that step showed the Java process at 20.7 GB (the Spark limit is 24 GB). The 32 GB target covers training and the index build.

## Speed check on the full build

`LISTENBRAINZ_MODELS_DIR=models/full uv run listenbrainz-recs-speed`:

- similar artists: 100 lookups, 95th percentile 21.4 ms (limit 200 ms) PASS
- suggestions: 100 lookups, 95th percentile 0.9 ms (limit 200 ms) PASS

That command types whole artist names. Short texts, which match the most artists, were timed separately on the same build: "a" 2.5 ms, "s" 2.9 ms, "b" 1.9 ms, "the" 1.5 ms, "th" 1.2 ms, "m" 2.3 ms, "e" 1.2 ms, each returning 10 results; "henry thr" returned Henry Threadgill in 0.5 ms and "bjork" returned Björk first in 0.3 ms.

## Page script review

`app.js` was read against `BR4.1` to `BR4.13` and the NFR design: request numbering for suggestions and results, the busy flag for Show more, Retry, history entries and the text-only rendering are all present and consistent. It was also syntax-checked with `node --check` by the developer agent. It has not been run in a browser (no test executes it, and no browser is available to this session), so keyboard use, focus movement and the phone layout are unseen.

## Failures

No command failed. One target is `Unverified`: the browser part of NFR2.19 (late suggestion replies and double clicks, checked in the manual pass), which is the owner's pass in `docs/manual-checks.md`. See the Target Verification Matrix in `build-and-test-summary.md`.

**Accepted failure:** the owner chose "Accept failure" at the halt-and-ask, so the stage goes to its approval gate with NFR2.19 still `Unverified`. The browser pass in `docs/manual-checks.md` stays on the owner's list before `v0.1.0`.

## Loop-Back Log

None. No loop-back was needed: the one unverified target has no code fix, only a manual pass.

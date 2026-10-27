# Code Summary — u2-pipeline

Built from the approved plan (`code-generation-plan.md`) and the tests described in `unit-test-instructions.md`, following the functional design (`construction/u2-pipeline/functional-design/`), the NFR designs (`construction/u2-pipeline/nfr-design/`) and contracts C1 to C3 (`inception/contract-design/contract-summary.md`).

## Files Created

| Area | Files |
|------|-------|
| Pipeline | `steps.py` (step markers with run ids, missing and stale input checks), `musicbrainz.py` (MusicBrainz tables), `catalogue.py` (catalogue step, replaces `catalog.py`), `speed.py` (speed command) |
| Tests | `tests/u2_pipeline/test_{steps,dump_source_full,prep_full,train_full,catalogue,index_build,search,speed,privacy_and_hygiene,runbook,runner_ready}.py` |

## Files Modified

| Area | Files |
|------|-------|
| Pipeline | `prep.py` (rewritten in Spark with all the rules), `train.py` (full-size settings, markers, memory message), `index.py` (batch reading, consistency checks, manifest last; no longer writes the artist file), `dump_source.py`, `settings.py`, `paths.py`, `spark.py`, `fsutil.py`, `text.py` |
| Lookup | `artists.py` (four-tier search), `store.py` (startup check for the catalogue tables) |
| Project | `pyproject.toml` (the catalogue and speed commands), `README.md` ("Rebuild from a new dump" runbook, settings, stop messages) |
| Tests | `tests/conftest.py`, `tests/fixtures/sample_data.py`, and five skeleton test files (see below) |

`src/listenbrainz_recs/catalog.py` was deleted; `catalogue.py` replaces it. No commits were made.

## Key Implementation Decisions

- **Steps and markers:** each step ends by writing a marker with a run id and the run id of the marker it read, so a later step refuses a missing input and a stale one, naming the step to run (BR6.3, BR6.4).
- **Prepare in Spark:** one pass counts malformed lines and unusable entries, sums repeats, applies the 5-listener cutoff and picks each artist's most used name. `LISTENBRAINZ_PREP_MAX_LINES` gives a sample run; unset means the whole dump.
- **Training:** rank 64, 10 iterations, regularisation 0.1, alpha 20, seed 42 (the current app's settings). Spark driver memory defaults to 24 GB (`LISTENBRAINZ_SPARK_MEMORY`); an out-of-memory error names that setting.
- **Catalogue step:** descriptions and recognised genres from MusicBrainz; artists MusicBrainz lacks are kept with no description and no genres; artists numbered by popularity so search can read matches already in order.
- **Search:** exact and starts-with matches use a sorted name index; word-start matches use the full-text table read in popularity order; the typed text is normalised and only used as a bound parameter or a quoted word.
- **Index step:** reads vectors in batches, checks ids against the catalogue, removes the old manifest first and writes the new one last.
- **Speed command:** 100 seeded artists, nearest-rank 95th percentile for both lookup kinds, exit code 1 on fail.

## Test Coverage Summary

- `bash scripts/check.sh` passes: ruff check, ruff format --check, ty with no checks disabled, and 191 pytest tests at 94.09% coverage against the 80% floor. `uv run pytest tests/u2_pipeline -q` passes.
- New tests per file: steps 7, dump_source_full 10, prep_full 14, train_full 12, catalogue 11, index_build 9, search 24, speed 8, privacy_and_hygiene 7, runbook 2, runner_ready 11, which is 115 in u2 (the plan estimated about 70). The skeleton keeps 76.
- Search tests were written first. Against the skeleton's contains-based search, 2 of 24 failed (words in any order, and text inside a word), the rest already passed, so the Red set was weaker than ideal; all 24 pass after the rewrite.
- Real-data sample run (first 5,000 listener lines, real MusicBrainz tables, read-only): prepare 51 s, train 59 s, catalogue 44 s, index 0.9 s; 46,698 artists kept; 42% have a description and 60% have genres. A Björk lookup took 12.6 ms (Portishead 0.959, Massive Attack 0.956, Aphex Twin 0.935), and "bjork" suggested Björk first. The sample speed check gave a 95th percentile of 13.7 ms for similar artists and 0.7 ms for suggestions.

## Tests Written but Not Executed in This Stage

- The full-size speed check (AC1.1.6, NFR1.5, NFR1.6): it needs the full-size built files; the owner runs `uv run listenbrainz-recs-speed` after a full rebuild.
- Full-size training within memory (AC4.2.2, NFR1.7): too long for this build; the owner runs it by following the README runbook.
- "henry thr" returns nothing on the 5,000-line sample because Henry Threadgill is not among its artists; the behaviour is covered by the fixture test.
- The GitHub Actions workflow was not run; it stays switched off until the code is pushed.

## Deviations from the Plan

- The plan estimated about 70 new tests; 115 were written.
- The starts-with tier uses a range query on the sorted name index ordered by popularity, not rows already in order, so a one-letter prefix scans tens of thousands of index rows at full size. The full-size speed check will show whether that is fast enough.
- The catalogue may hold more artists than the index (zero-length vectors are dropped from the index), so such an artist is searchable but returns "unknown artist" from the index. The startup check now requires the catalogue to hold at least as many artists as the index.
- Prepare also fails when the MusicBrainz tables are missing, because all dump files are checked before anything is written (BR1.1).
- The developer agent edited `store.py` once through a shell heredoc, against the instruction to use file tools; the change is small and later edits used file tools.
- The first build attempt stopped on an API rate limit after steps 1 to 6; a second run found those steps done and finished the rest.

## Skeleton Tests Changed

No assertion was weakened; each moved to the new rule and the comments say so.

- `test_lookup.py`: search matches by word start, so `suggest("a")` returns only Alpha; added checks that `"lph"` returns nothing and `"al"` finds Alpha.
- `test_api.py`: a missing `artists.sqlite` now names the catalogue step.
- `test_build.py`: builds the catalogue first, because the artist file now comes from the catalogue step.
- `test_prep.py`: updated for the 5-listener cutoff, the new summary fields, a smaller line limit and the required MusicBrainz tables.
- `test_train.py`: uses the fixture rank and the prepared fixture; the unreadable-input message is "train step failed".

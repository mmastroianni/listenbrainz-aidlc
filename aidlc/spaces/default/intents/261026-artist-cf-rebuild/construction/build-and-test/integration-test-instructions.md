# Integration Test Instructions

Key boundaries and cross-unit interactions. Test Strategy is Standard, so this file covers the boundaries between units; unit tests are in each unit's `unit-test-instructions.md`. Sources: `inception/contract-design/contract-summary.md` (C1, C2, C3), the three units' code summaries and test instructions.

## Boundaries covered

| Boundary | Contract | Provider to consumer | Where it is tested |
|----------|----------|----------------------|--------------------|
| Pipeline to built files | C2 | u2-pipeline writes, u3-web reads at startup | `tests/u1_skeleton/test_end_to_end.py`, `tests/u2_pipeline/test_index_build.py`, `tests/u3_web/test_similar_endpoint.py` (app started on built fixture files) |
| Catalogue and index interfaces | C1 | u1-skeleton interfaces, u2-pipeline behaviour, u3-web calls | `tests/u2_pipeline/test_search.py`, `tests/u1_skeleton/test_lookup.py`, `tests/u3_web/test_suggest_endpoint.py` |
| Endpoints to the page | C3 | u3-web endpoints to its page | `tests/u3_web/test_suggest_endpoint.py`, `test_similar_endpoint.py`, `test_page_files.py` |
| Step order and stale input | C2 | each pipeline step to the next | `tests/u2_pipeline/test_steps.py`, `test_index_build.py` |

## Run

```bash
bash scripts/check.sh                       # everything, with the coverage floor
uv run pytest tests/u1_skeleton/test_end_to_end.py -q    # the pipeline on the fixture, end to end
```

## Cross-unit checks run by hand against a real build

After the four pipeline steps on the real dump (README, "Rebuild from a new dump"):

1. Start the app: `uv run listenbrainz-recs-serve`.
2. `curl 'http://127.0.0.1:8000/api/suggest?q=bjork'` returns Björk first.
3. `curl 'http://127.0.0.1:8000/api/artists/<Björk id>/similar'` returns 20 items with `has_more` true.
4. Ask for page 2 with `offset=20` and see the bar scale continue from page 1.
5. Open `http://127.0.0.1:8000/` in a browser and follow `docs/manual-checks.md`.

## Test data and environment

- Fixture tests build their own files under pytest's temporary folders and use one shared local SparkSession; they never read the real dumps.
- The real-build checks read the dumps read-only and write only to the git-ignored work and models folders.

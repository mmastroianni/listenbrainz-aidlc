# Quality Gates

Sources: the Testing Posture in `aidlc/spaces/default/memory/team.md` and `project.md`, the Testing Contract in each unit's `code-generation-plan.md`, and the Build and Test results (`construction/build-and-test/test-results.md`). Every gate below is enforced by `bash scripts/check.sh`, which is both the local pre-merge check and the one command the CI workflow runs (`construction/ci-pipeline/ci-config.md`).

## Gates that block a merge

| Gate | Threshold | Enforced by | Last result (Build and Test) |
|------|-----------|-------------|------------------------------|
| No data or model files tracked by git | none tracked under `data`, `models`, `*.parquet`, `*.faiss`, `*.sqlite` | the first step of `scripts/check.sh` (`git ls-files`) | passes |
| Lint | no `ruff check` findings (rule sets E, F, W, I, B, UP, SIM, line length 100) | `ruff check .` | passes |
| Formatting | no `ruff format --check` differences | `ruff format --check .` | passes |
| Type check | no `ty check` errors, no checks disabled | `ty check` | passes |
| Tests | all tests pass | `pytest tests` | 277 passed |
| Coverage | at least 80% line coverage, never lowered | `pytest --cov=listenbrainz_recs --cov-fail-under=80` | 94.52% |

The pre-merge check is mandatory before a Bolt is merged into `main` (project rule), and the coverage floor is never lowered to make a step pass (Testing Posture).

## Checks that run apart from CI

| Check | Threshold | How it runs | Last result |
|-------|-----------|-------------|-------------|
| Full-size speed check | 95th percentile under 200 ms for similar artists and for suggestions, over 100 lookups each | `uv run listenbrainz-recs-speed` after a full rebuild, on the owner's machine | 21.4 ms and 0.9 ms, pass |
| Full-size rebuild | finishes within 32 GB of memory, no time limit | the four pipeline steps, as in the README | finished in about 13 minutes, training peak 12.7 GB |
| Keyboard and phone pass | every box in `docs/manual-checks.md` ticked | by hand before tagging `v0.1.0` | not done yet |
| Quality check against the current app | at least 4 of 5 artists marked at least as good | `listenbrainz-recs-quality-sheet` then `-verdict` | not done yet |

## Do the gates enforce what Build and Test ran?

Yes. Build and Test's commands were `uv sync` and `bash scripts/check.sh` (plus the three per-unit test commands, which are subsets of the same suite). The workflow runs the same two commands, so every gate Build and Test relied on for the automated results is a CI gate once the workflow is switched on. The checks listed as running apart from CI are exactly the ones Build and Test ran by hand or left to the owner.

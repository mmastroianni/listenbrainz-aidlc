# CI Pipeline — Questions

Context: the four things this stage normally asks are already answered by the team practices (`inception/practices-discovery/team-practices.md`, the Testing Posture, Way of Working and Deployment sections of `aidlc/spaces/default/memory/team.md`) and by what u1-skeleton built (`.github/workflows/ci.yml`, `scripts/check.sh`), so no new questions were needed:

- CI tool: GitHub Actions, with a workflow file already in the repository, switched off until the code is pushed to GitHub (team practices).
- Branch strategy: trunk-based development on `main`; each Bolt is squash-merged into `main` (team practices).
- Quality gates before merge: the local check command `bash scripts/check.sh` (`ruff check`, `ruff format --check`, `ty`, and `pytest` with the 80% coverage floor), the same command the workflow runs.
- Artifact repositories: none. There is no deployment and no package or container to publish in v1; built data and model files are never committed.

Please confirm what this stage will do with them.

## Consolidated Summary Confirmation

- Keep the existing workflow as it is: it already runs the recorded check command on every push and pull request, with Java 21 for Spark and Python 3.12 through uv, and it stays switched off with `if: false` until the code is pushed to GitHub; turning it on is deleting that one line.
- Write `ci-config.md` (what the workflow does and how to turn it on) and `quality-gates.md` (the gates, their thresholds and the commands that enforce them, matched to the Build and Test results).
- Keep the full-size speed check and the browser pass out of CI: they need the full-size files and a person, and they stay manual, as the team practices say.
- Run the Construction phase check and write the verdict to `verification/phase-check-construction.md`, reporting honestly what it finds: the full-size items that unit records marked Deferred were measured in Build and Test, and the browser part of NFR2.19 is still unverified.
- No change to application code, the workflow file or the check script in this stage.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

# CI Configuration

Sources: `construction/ci-pipeline/ci-pipeline-questions.md` (the confirmed answers), the team practices (`inception/practices-discovery/team-practices.md`; Way of Working, Testing Posture and Deployment in `aidlc/spaces/default/memory/team.md`), the code summaries (`construction/u1-skeleton/code-generation/code-summary.md`, `construction/u2-pipeline/code-generation/code-summary.md`, `construction/u3-web/code-generation/code-summary.md`) and the Build and Test results (`construction/build-and-test/build-and-test-summary.md`, `test-results.md`).

## What exists

The CI pipeline was built in u1-skeleton and is kept unchanged: `.github/workflows/ci.yml`, one job named `check`.

| Setting | Value |
|---------|-------|
| CI tool | GitHub Actions |
| Triggers | every push and every pull request |
| Runner | `ubuntu-latest` |
| Steps | check out; install uv (`astral-sh/setup-uv@v5`); install Java 21 (`actions/setup-java@v4`, Temurin, needed by Spark); `uv python install 3.12`; `uv sync`; `bash scripts/check.sh` |
| Current state | **switched off**: the job carries `if: false` |
| Branch strategy | trunk-based on `main`; each Bolt is squash-merged into `main` (team practices) |
| Artifact repository | none; v1 builds no package or container and publishes nothing |

## Why it is adequate as it stands

- It runs the exact command the team recorded as the pre-merge check and that Build and Test ran (`bash scripts/check.sh`), so a result on GitHub means the same as a local result.
- The command needs no secrets, no network service and no dump: every test uses small fixtures and the one shared local SparkSession, so the workflow needs no environment variables.
- Java 21 and Python 3.12 are the versions the project was built and checked on.

## Turning it on

The team practices say the workflow stays off until the code is pushed to GitHub. Then:

1. Create the private GitHub repository and push `main`.
2. Delete the `if: false` line in `.github/workflows/ci.yml` and commit that as its own change.
3. Make sure the first run goes green. From then on it runs on every push alongside the local command.

## What CI does not run

- **The full-size speed check** (`uv run listenbrainz-recs-speed`): it needs the full-size built files, which are never committed and would need the real dumps. It stays a manual check on the owner's machine, as the Testing Posture says.
- **The full-size rebuild** (prepare, train, catalogue, index): same reason.
- **The browser keyboard and phone pass** (`docs/manual-checks.md`) and the quality check against the current app: they need a person.

## Optional improvements, not applied

These were not asked for and are left out of this stage: caching uv's downloads between runs, and a `permissions: contents: read` block for the job. Either can be added in the same change that turns the workflow on.

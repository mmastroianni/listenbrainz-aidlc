# Practices Discovery Evidence

> Greenfield, lead-only run (no support reviews, no contribution files). The
> lead drafted from the framework defaults and the owner's existing app, the
> owner answered the interview (Q1 to Q8) and confirmed the consolidated summary
> ("Looks correct"), and the lead integrated the answers.

## Sources

| Source | What it gave | How it is used |
|--------|--------------|----------------|
| `aidlc/spaces/default/memory/org.md` (Way of Working, Walking Skeleton, Testing Posture, Deployment, Code Style) | Framework defaults | Suggested defaults in the interview, not team facts |
| `aidlc/spaces/default/memory/team.md` | Empty template | No affirmed baseline; this is a first run |
| `aidlc/spaces/default/memory/project.md` | Toolset fixed to the existing app's tools; `../listenbrainz` is reference only | Constraints carried into the practices |
| `aidlc/spaces/default/intents/261026-artist-cf-rebuild/aidlc-state.md` | Greenfield, scope `mvp`, Test Strategy Standard, Operation phase skipped, Construction unit-major and serial | Shapes the testing and deployment practices |
| `.claude/scopes/aidlc-mvp.md` | `skeleton: on` | Walking-skeleton suggestion |
| `ideation/scope-definition/scope-document.md` | Core scope, stretch items, out-of-scope hosting and deployment prep | Deployment section; skeleton slice contents |
| `ideation/feasibility/constraint-register.md` | TC-1 to TC-5, OC-1 to OC-4, RC-1 to RC-3 | Solo work, local only, 200 ms lookup target, hard-rule candidates |
| `../listenbrainz/pyproject.toml` (existing app, evidence of habit) | `uv` with `uv_build`; dev group has only `ruff`; ruff line length 100, rules `E F W I B UP SIM`; Python `>=3.11` | Code Style; no test tooling to inherit |
| `../listenbrainz/.python-version` (existing app) | `3.12` | Python version |
| `../listenbrainz/README.md` (existing app) | `uv run ruff check` and `uv run ruff format`; pipeline steps run in order as `python -m` modules; data and models in gitignored folders | Code Style and Deployment |
| `../listenbrainz/.gitignore` (existing app) | Dumps, `data/`, `models/`, `scratch/` are ignored | Hard-rule candidate on committing data |
| `git` in `../listenbrainz` (existing app) | Branch `main`, a GitHub `origin` remote, 2 commits, short imperative messages | Trunk name and commit-message style |
| `git` in this repository | Branch `master`, no commits, no remote | Branch rename question (Q1) |
| `practices-discovery-questions.md` | Owner's answers to Q1 to Q8 and the confirmed summary | Authoritative source for every practice and rule |

## What Was Inferred (lead draft)

- **No test habit to inherit.** The existing app has no `tests/` folder and no
  test runner in its dependencies, so the testing posture was the owner's
  choice rather than a carried-over habit.
- **Spark and FAISS make testing heavier.** Tests that start Spark are slow, so
  the practices use small fixture files and one shared local `SparkSession`.
- **"CI before merge" needs a local meaning.** There is no hosting and no remote
  in this repository, so the pre-merge gate is a local command. The
  `ci-pipeline` stage (3.7) will formalise it.
- **Deployment defaults do not apply in v1.** Hosting and deployment preparation
  are out of scope and the Operation phase is skipped, so the org default
  (deploy on merge to staging) is kept only as a stance for a later intent.
- **Branch name mismatch.** The framework default trunk is `main`; this
  repository is on `master` with no commits yet, so renaming costs nothing now.

## Interview Decisions

| Q | Area | Decision | Where it lands |
|---|------|----------|----------------|
| Q1 | Way of Working | A: rename `master` to `main`, keep it local for now; trunk-based, one squash commit per Bolt | `team-practices.md` § Way of Working |
| Q2 | Walking Skeleton | A: yes, build the thin end-to-end slice first | `team-practices.md` § Walking Skeleton |
| Q3 | Testing Posture | C (custom): "test-first (TDD) for search, lookup and the web layer; test-after for the data pipeline and model training"; 80% line coverage | `team-practices.md` § Testing Posture (`Methodology: custom`) |
| Q4 | Testing Posture | C: both a local check command and GitHub Actions | Refined by Q8 |
| Q8 | Testing Posture / Way of Working | B: local only for now; add the GitHub Actions setup but switch it on once the code is pushed later. Resolves the conflict between Q1 (local) and Q4 (GitHub Actions) | `team-practices.md` § Testing Posture and § Way of Working |
| Q5 | Deployment | A: released means merged to `main` and the app starts locally; tag `v0.1.0` when the core scope is done | `team-practices.md` § Deployment |
| Q6 | Code Style | B: "with ty as the type checker (uv + ruff + ty), checking our own code; PySpark, FAISS and UMAP parts excused; pinned version; part of the pre-merge check"; ruff settings and Python 3.12 kept | `team-practices.md` § Code Style |
| Q7 | Hard rules | A, B, C, D all confirmed; D split into a `NEVER` rule (no dumps, intermediate data or model files in git) and an `ALWAYS` rule (pre-merge check passes before merge) | `discovered-rules.md` |

Origins of the hard rules: A (dumps read-only) is constraint TC-2, B (no
listener data) is RC-1 and C (no paid services) is OC-3, all owner-stated in
Feasibility and re-confirmed in Q7; D was inferred from the existing app's
`.gitignore` and the `mvp` coverage and CI floor, and became a hard rule only on
the owner's Q7 answer. Not repeated as rules: the fixed toolset (already in
`project.md` § Tech Stack) and `../listenbrainz` as reference only (already in
`project.md` § Corrections).

## Remaining Uncertainty

- **`ty` maturity.** `ty` is a young type checker; its rules and output may
  change between releases, which is why the owner pinned the version. Excusing
  PySpark, FAISS and UMAP parts needs a concrete mechanism (configuration
  overrides or targeted ignores) to be settled when the project is scaffolded in
  Construction. If `ty` proves unworkable, changing the type checker is a
  practice change to bring back to the owner, not a silent swap.
- **Coverage effort on Spark code.** Reaching 80% line coverage over the Spark
  pipeline and model-training modules on fixture data is feasible but a real
  effort, and those layers are tested after implementation. This is a risk to
  watch in Construction, not a reason to lower the floor.
- **Lookup-speed check.** The 200 ms check (TC-4) needs the full-size index, so
  it sits outside the default suite and the pre-merge check; when and how it
  runs is left to the NFR and build-and-test stages.
- **GitHub Actions switch-on.** The workflow is set up but inactive; there is no
  date for pushing to GitHub. Until then the local check command is the only
  gate.
- **Construction Verification Command.** Chosen and authorized by the owner
  during Construction, not here. A candidate is a single end-to-end pytest test
  that runs the skeleton pipeline on the sample data and then calls the
  similar-artist endpoint.

## Assumptions & Open Questions

- [assumption] Adding `pytest`, `pytest-cov` and `ty` as dev dependencies does
  not break the fixed-toolset rule in `project.md`, because they are
  development tools the owner chose (Q3, Q6) and the runtime stack is unchanged.
- No open questions remain for this stage; every interview point (Q1 to Q8) is
  answered and the summary was confirmed.

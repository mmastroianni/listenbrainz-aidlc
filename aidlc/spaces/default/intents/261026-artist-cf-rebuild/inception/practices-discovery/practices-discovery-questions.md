# Practices Discovery — Questions

Context: this is a new project with no team practices recorded yet, so each question offers a suggested default (from the framework defaults and the habits visible in your existing app in `../listenbrainz`). The draft is in `team-practices.md`, and what was looked at is in `evidence.md`.

## Q1. [Release engineer] Branches and where the code lives

This repository is on a branch called `master` with no commits yet, and the default here is one main branch called `main`, with each piece of work merged in as a single squashed commit. Which fits?

A. Rename to `main`, keep it local for now (suggested)
B. Rename to `main` and push to a GitHub remote
C. Keep `master` as the main branch
D. Not yet defined
X. Other (please specify)

[Answer]: A

## Q2. [Release engineer] Build a thin end-to-end slice first?

A walking skeleton is a minimal version that runs the whole way through, built first to prove the pieces connect before the real features go in. Here it would be a small sample of the dump, a tiny model, the lookup index, and one similar-artist lookup through the web app.

A. Yes, build the skeleton first (suggested)
B. No, build each piece fully in order
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Q3. [Quality engineer] When tests are written

Your existing app has no tests, so there is no habit to keep. The plan already requires 80% line coverage. When should tests be written?

A. After each layer is built (test-after) (suggested)
B. Before the code (test-driven development)
C. A mix: a few end-to-end checks first, unit tests after
D. Not yet defined
X. Other (please specify)

[Answer]: C — test-first (TDD) for search, lookup and the web layer; test-after for the data pipeline and model training

## Q4. [Quality engineer] Where the pre-merge check runs

There is no remote yet, so "checks must pass before merging" needs a place to run. Which?

A. One local check command (lint, format check, tests with coverage) (suggested)
B. GitHub Actions on every push
C. Both
D. Not yet defined
X. Other (please specify)

[Answer]: C

## Q5. [Release engineer] What counts as "released" in v1

Hosting is out of the first version. What should count as a release?

A. Merged to the main branch and the app starts locally; tag v0.1.0 when the core scope is done (suggested)
B. Merged to the main branch; no version tags
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Q6. [Developer] Code style

Your existing app uses ruff (line length 100, rules E, F, W, I, B, UP, SIM, and `ruff format`) with Python 3.12. Keep that, and add a type checker?

A. Keep the ruff settings and Python 3.12, no type checker (suggested)
B. Keep them, and add a type checker (for example mypy)
C. Not yet defined
X. Other (please specify)

[Answer]: B — with ty as the type checker (uv + ruff + ty), checking our own code; PySpark, FAISS and UMAP parts excused; pinned version; part of the pre-merge check

## Q7. [Release engineer] Hard rules (select all that apply)

Which of these should be hard rules that are never broken? The first three are things you said earlier; the last two are suggestions.

A. Never modify, move or write into the dumps in `../listenbrainz`; read them in place only
B. Never show data about individual ListenBrainz listeners; only artist-level results
C. Never add a paid service or cloud compute
D. Never commit raw dumps, intermediate data or built model files to git; and always have the pre-merge check pass before merging
E. None of these
X. Other (please specify)

[Answer]: A, B, C, D

## Q8. [Release engineer] A GitHub remote for the checks

In Q1 you chose to keep the code local for now, but in Q4 you chose to run the checks both locally and on GitHub Actions, which needs the code on GitHub. Which do you want?

A. Push to a private GitHub repository now, so GitHub Actions runs from the start
B. Local only for now; add the GitHub Actions setup but switch it on once the code is pushed later
C. Local check command only, after all
D. Not yet defined
X. Other (please specify)

[Answer]: B

## Consolidated Summary Confirmation

- Branches (Q1): rename `master` to `main`; one main branch, each piece of work squash-merged in.
- Walking skeleton (Q2): yes, build the thin end-to-end slice first.
- Tests (Q3): a mix: test-first for search, lookup and the web layer; test-after for the data pipeline and model training; 80% line coverage.
- Pre-merge checks (Q4, Q8): one local check command now; GitHub Actions set up but switched on once the code is pushed to GitHub later.
- Release (Q5): merged to `main` and the app starts locally; tag v0.1.0 when the core scope is done.
- Code style (Q6): uv + ruff (line length 100, rules E F W I B UP SIM, ruff format) + ty as type checker on our own code, Python 3.12.
- Hard rules (Q7): never modify the dumps in `../listenbrainz`; never show individual listener data; never add paid services; never commit dumps, data or model files, and always pass the pre-merge check before merging.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

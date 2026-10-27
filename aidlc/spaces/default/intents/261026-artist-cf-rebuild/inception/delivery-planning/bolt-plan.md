# Bolt Plan

A **Bolt** is one build pass over a piece of the work, ending in something that runs and is checked. The plan draws on the requirements (`inception/requirements-analysis/requirements.md`), stories (`inception/user-stories/stories.md`), mockups (`inception/refined-mockups/mockups.md`), components (`inception/domain-design/components.md`), units (`inception/units-generation/unit-of-work.md`, `unit-of-work-dependency.md`, `unit-of-work-story-map.md`), contracts (`inception/contract-design/contract-summary.md`) and team practices (`inception/practices-discovery/team-practices.md`). The order follows the unit dependency graph, and Bolts run one at a time.

## Bolt 1 — Walking skeleton (u1-skeleton)

- **Units:** U1 u1-skeleton.
- **Walking skeleton:** yes. A **walking skeleton** is a minimal version that runs the whole way through, built first to prove the pieces connect.
- **Proves:** DumpSource → ListeningDataPrep → SimilarityTraining → SimilarityIndex → WebApp, plus the C1 interfaces and the C2 file layout with its manifest.
- **Definition of Done:**
  - The project scaffold (uv, ruff, ty, pytest, pytest-cov, `.gitignore`, the GitHub Actions file switched off) and the pre-merge check command exist and pass.
  - On a small sample of the dump, one command sequence builds the files, and `GET /api/artists/{mbid}/similar` returns ranked neighbours with cosine scores.
  - The dumps are untouched and no data or model files are tracked by git.
- **Confidence hypothesis:** the rebuilt structure (six components, three contracts) works end to end with the fixed toolset.
- **Expected demo:** run the sample pipeline, start the app, call the similar-artists endpoint for a known sample artist and see neighbours.

## Bolt 2 — Full pipeline (u2-pipeline)

- **Units:** U2 u2-pipeline.
- **Definition of Done:**
  - Full prep rules (anonymisation, malformed-record counting, 5-listener cutoff), full-size training, catalogue with descriptions and genres, accent-insensitive name search, full index, and the rebuild runbook (FR1 to FR4, FR7).
  - Tests pass on fixture data with 80% coverage. The full-size build completes on the owner's machine, and a separate speed check shows lookups under 200 ms at the 95th percentile (NFR1).
- **Confidence hypothesis:** the full-size data behaves as in the current app (memory, speed, sensible neighbours).
- **Expected demo:** run the runbook on the real dumps, start the app, and get similar artists for real artists.

## Bolt 3 — Web page (u3-web)

- **Units:** U3 u3-web.
- **Definition of Done:**
  - The page per the mockups: suggestions, results with bars (cosine on hover), genres, MusicBrainz/YouTube/Spotify links, "Show more", click-to-explore, `/artist/<mbid>` addresses, all messages, phone layout and keyboard use (FR5, FR6).
  - API and page tests written first and passing, with 80% coverage.
  - The by-eye quality check: at least 4 of 5 artists at least as good as the current app (FR8.1).
- **Confidence hypothesis:** the rebuilt app is a full replacement for the current one's core.
- **Expected demo:** search "Henry Threadgill", explore two hops, use Back, open a Spotify link, view on a phone-width window.
- **Release:** tag `v0.1.0` on `main` when Bolt 3 is merged (team practices).

## Construction Settings

- **Order:** one unit at a time (unit-major), serial, with a checkpoint after each unit.
- **Verification command:** asked separately (see the completion step).

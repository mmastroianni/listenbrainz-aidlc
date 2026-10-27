# RAID Log — Artist Recommendation App Rebuild

Derived from the intent statement (`ideation/intent-capture/intent-statement.md`) and `feasibility-questions.md`.

## Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|-----------|
| R1 | The first version is the whole current app (similar artists, map, experiment and evaluation tools), which is large for an mvp | Medium | Medium | Scope Definition marks the map and experiment tools as core or stretch, and builds similar-artist search first |
| R2 | Whether the re-runnable pipeline is in the first version is undecided | Medium | Medium | Settle it in Scope Definition |
| R3 | The quality comparison is not like for like if the rebuild scores lists differently from the current app | Medium | High | Reuse the hand-labelled judgments in `../listenbrainz/results/` and the same scoring method; define the pass bar in requirements |
| R4 | Training on the full dump does not fit in 32 to 64 GB | Low | High | The current app already trained on this data; confirm in the first pipeline run |
| R5 | Lookups miss the 200 ms target | Low | Medium | Precompute neighbours or an index; measure in Build and Test |
| R6 | Moving or deleting `../listenbrainz` breaks the pipeline | Low | Medium | Make the data location a setting; document the expected files |
| R7 | With no budget or host, deploying later is constrained | Low (later) | Medium | Keep the app easy to run elsewhere; choose a host when deployment comes up |

## Assumptions

| ID | Assumption | Owner | Status |
|----|-----------|-------|--------|
| A1 | The current model was trained on the same 32 to 64 GB machine | Owner | Unvalidated |
| A2 | The dump licences allow personal use and a later small shared deployment | Owner | Unvalidated |
| A3 | How the few other users reach the first version is undecided; for now only the owner uses it (from Intent Capture) | Owner | Accepted as assumption |

## Issues

| ID | Issue | Status |
|----|-------|--------|
| I1 | None open | — |

## Dependencies

| ID | Dependency | Type | Notes |
|----|-----------|------|-------|
| D1 | ListenBrainz statistics dump extracted in `../listenbrainz` | Data | Read in place (Q1) |
| D2 | MusicBrainz database dump extracted in `../listenbrainz/data/musicbrainz/` | Data | Read in place (Q1) |
| D3 | Hand-labelled relevance judgments in `../listenbrainz/results/` | Data | Needed for the quality comparison |
| D4 | A Java runtime on the machine | Tooling | Required by the current tools (Q2) |

## Assumptions & Open Questions

- [assumption] A1 and A2 above remain unvalidated until the first pipeline run and a licence check.

# Constraint Register — Artist Recommendation App Rebuild

Derived from the intent statement (`ideation/intent-capture/intent-statement.md`) and `feasibility-questions.md`.

## Technical Constraints

| ID | Constraint | Impact | Source |
|----|-----------|--------|--------|
| TC-1 | Use the same tools as the current app; this is a rebuild of the same design | Design stages choose structure, not new technology | Q2 |
| TC-2 | Read the ListenBrainz and MusicBrainz dumps already in `../listenbrainz`, in place | The data location must be configurable; the dumps are inputs, never modified | Q1 |
| TC-3 | The data pipeline runs on a machine with 32 to 64 GB of memory | Training and indexing must fit that memory | Q3 |
| TC-4 | A similar-artist lookup answers in under 200 ms on the owner's machine | Lookups must not do heavy work per request | Intent statement |
| TC-5 | The first version runs locally only | No hosting, scaling or operations work in the first version | Intent statement |

## Organizational Constraints

| ID | Constraint | Impact | Source |
|----|-----------|--------|--------|
| OC-1 | Solo project: the owner builds it and makes every decision | No sign-off chain; approvals are the owner's alone | Intent statement (stakeholder map) |
| OC-2 | No deadline; work happens on evenings and weekends | Favour small, independently finished pieces of work | Q4 |
| OC-3 | No budget: free and local only | No paid services or cloud compute | Q5 |
| OC-4 | No cloud account or host yet | Deployment is designed for later, not built now | Q7 |

## Regulatory and Data Constraints

| ID | Constraint | Impact | Source |
|----|-----------|--------|--------|
| RC-1 | Only artist-level results are shown; nothing about individual ListenBrainz users | Listener-level data stays inside the pipeline and never reaches the app | Q6 |
| RC-2 | No user accounts in the first version | No personal data is collected from the app's own users | Intent statement |
| RC-3 | Data licence terms of the dumps apply | **Assumption:** they allow personal use; verify before public hosting | Assumption |

## Assumptions & Open Questions

- [assumption] The dump licences allow personal use and a later small shared deployment (RC-3).

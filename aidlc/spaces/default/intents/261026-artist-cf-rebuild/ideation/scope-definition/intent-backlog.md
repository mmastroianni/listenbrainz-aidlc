# Intent Backlog — Artist Recommendation App Rebuild

Prioritised with MoSCoW and ordered by dependency (Q5). Derived from the intent statement (`ideation/intent-capture/intent-statement.md`), the feasibility assessment (`ideation/feasibility/feasibility-assessment.md`), the constraint register (`ideation/feasibility/constraint-register.md`) and `scope-definition-questions.md`. These are proto-units: Units Generation turns them into units of work.

## Backlog

| ID | Item | Priority | Depends on | Source |
|----|------|----------|-----------|--------|
| IB-1 | Prepare listening data from the dumps in `../listenbrainz` (location is a setting, dumps are never modified) | Must | — | Constraint register TC-2 |
| IB-2 | Learn artist similarity from the prepared listening data, within 32 to 64 GB of memory | Must | IB-1 | Intent statement; constraint register TC-3 |
| IB-3 | Artist details: names, popularity and MusicBrainz genre tags | Must | — | Q4 |
| IB-4 | Artist name search and similar-artist lookup, under 200 ms | Must | IB-2, IB-3 | Intent statement; constraint register TC-4 |
| IB-5 | Web screens: type an artist, see similar artists with genres | Must | IB-4 | Intent statement; Q4 |
| IB-6 | Re-run runbook: documented steps to rebuild everything from a new dump | Must | IB-1, IB-2, IB-3, IB-4 | Q1 |
| IB-7 | By-eye quality check against the current app's result lists | Must | IB-5 | Q7 |
| IB-8 | Visual map of how artists relate | Could (stretch) | IB-2, IB-3 | Q2 |
| IB-9 | Experiment and evaluation tools in the web app (genre reranking, scoring against the hand-labelled judgments), for the owner and the friends | Could (stretch) | IB-4, IB-5 | Q2, Q3 |

## Won't Have (this time)

| Item | Source |
|------|--------|
| Public hosting, deployment or deployment packaging | Intent statement; Q6 |
| User accounts or sign-in | Intent statement |
| Listener-level data in the app | Constraint register RC-1 |

## Capacity Check

There is no deadline and the work happens on evenings and weekends (constraint register OC-2), so there is no capacity limit to cut against. Must-have items are 7 of 9; keeping the map and experiment tools as stretch is what keeps the core small (feasibility assessment, risk on scope size).

## Assumptions & Open Questions

None.

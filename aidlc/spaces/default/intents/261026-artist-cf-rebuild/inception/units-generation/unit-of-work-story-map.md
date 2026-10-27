# Unit Story Map

Every story in `inception/user-stories/stories.md`, mapped to the units in `unit-of-work.md` (requirements from `inception/requirements-analysis/requirements.md`, components from `inception/domain-design/components.md`).

| Story | Unit ID | Directory |
|-------|---------|-----------|
| US1.1 | U2; U3 | u2-pipeline; u3-web |
| US1.2 | U2; U3 | u2-pipeline; u3-web |
| US2.1 | U1; U3 | u1-skeleton; u3-web |
| US2.2 | U3 | u3-web |
| US2.3 | U3 | u3-web |
| US2.4 | U3 | u3-web |
| US3.1 | U3 | u3-web |
| US3.2 | U3 | u3-web |
| US4.1 | U1; U2 | u1-skeleton; u2-pipeline |
| US4.2 | U1; U2 | u1-skeleton; u2-pipeline |
| US4.3 | U2 | u2-pipeline |
| US4.4 | U1 | u1-skeleton |
| US5.1 | U3 | u3-web |

## Cross-Unit Stories

- **US1.1, US1.2:** U2 builds the name search in ArtistCatalog; U3 shows suggestions.
- **US2.1:** U1 returns similar artists from the index; U3 adds details, bars, links and the page.
- **US4.1, US4.2:** U1 does the sample-sized path; U2 adds the full rules and full-size data.

## Order Within Each Unit

- **U1:** scaffold and pre-merge check → DumpSource → sample prep → tiny training → index → names → one endpoint and startup check.
- **U2:** full prep rules → full training → catalogue details and genres → name search → full index and speed check → runbook.
- **U3:** suggestion endpoint → similar-artists endpoint with paging → page and states → links and addresses → keyboard and phone → quality check.

## Coverage

All 13 stories are assigned; every unit has rows (U1: 4, U2: 5, U3: 9).

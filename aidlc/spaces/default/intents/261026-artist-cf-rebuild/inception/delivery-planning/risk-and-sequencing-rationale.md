# Risk and Sequencing Rationale

A **Bolt** is one build pass over a piece of the work, ending in something that runs. The units and their dependency graph are in `inception/units-generation/unit-of-work-dependency.md`, and the Bolts in `bolt-plan.md`.

## Heuristic

**Walking skeleton first** (Cockburn), then **risk first** (Boehm), with no formal scoring model. A **walking skeleton** is a minimal version that runs end to end, built first to prove the pieces connect.

- **Bolt 1 (u1-skeleton)** is first because the team practices require it and the dependency graph puts it first.
- **Bolt 2 (u2-pipeline)** comes before Bolt 3 (Q1, risk first): the full-size data is where any surprise would show up.
- **Bolt 3 (u3-web)** is last. It can be tested on fixture data, but its quality check needs the full-size files from Bolt 2.

The order follows the dependency graph; there is no deviation to justify. Bolts run one at a time because the project is solo.

## Risks

The owner reported that memory, lookup speed and recommendation quality were not problems in the current app (Q3). They are therefore rated low and are checked inside Bolt 2's normal Definition of Done rather than by extra early work.

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Full-size training does not fit in 32 to 64 GB | Low | High | Proven in the current app; confirmed by the Bolt 2 full-size run |
| Lookups slower than 200 ms | Low | Medium | Proven in the current app; Bolt 2 speed check |
| Results worse than the current app | Low | High | Same approach as the current app; Bolt 3 by-eye check |
| ty or the coverage floor slows Spark-heavy code | Medium | Low | Excuse PySpark/FAISS/UMAP call sites in ty; fixture-data tests (team practices) |
| Construction effort and cost higher than expected | Medium | Medium | Three units only; one Bolt at a time; the owner can stop at any checkpoint |

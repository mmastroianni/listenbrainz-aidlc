# Delivery Planning — Questions

Context: there are three units of work (`inception/units-generation/unit-of-work.md`): u1-skeleton, u2-pipeline and u3-web. A **Bolt** is one build pass over a piece of the work, ending in something that runs. The walking skeleton (a thin version that runs end to end) is on, so u1-skeleton is always built first. After it, u2 and u3 can come in either order. You work solo with no deadline, and everything (the dumps, the tools) is already on your machine, so nothing outside the project can hold the work up.

## Q1. [Delivery lead] What comes after the skeleton

A. The full pipeline (u2) next: tackle the biggest unknowns first (does full-size training fit in memory, are lookups under 200 ms, are results as good as the current app's) (recommended: risk first)
B. The full web page (u3) next: see and use the real page sooner, on sample data, and do the full-size data last (value first)
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Q2. [Delivery lead] How big a Bolt is

A. One Bolt per unit: three Bolts, each ending with its unit working and checked (recommended)
B. Split the bigger units into smaller Bolts (more checkpoints, more back-and-forth)
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Q3. [Delivery lead] What worries you most (select all that apply)

Whatever you pick gets checked as early as possible.

A. Full-size training not fitting in 32 to 64 GB of memory
B. Lookups slower than 200 ms
C. Recommendations not as good as the current app's
D. The AI-DLC process itself (time and cost) more than the code
X. Other (please specify)

[Answer]: X — "None of these were problems in the original app"

## Consolidated Summary Confirmation

- Order (Q1): u1-skeleton first, then u2-pipeline (risk first), then u3-web.
- Bolt size (Q2): one Bolt per unit, three Bolts in all.
- Worries (Q3): none of the listed risks were problems in the original app, so they are treated as low risk and simply checked in u2's normal tests rather than front-loaded.
- Execution: one Bolt at a time (solo); no outside dependencies.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

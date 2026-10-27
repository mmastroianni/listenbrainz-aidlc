# Scope Definition — Questions

Context: the intent statement puts similar-artist search, the artist map and the experiment and evaluation tools in the first version, and leaves out public hosting and user accounts. The feasibility assessment flagged two open scope points (the re-runnable pipeline, and whether the map and experiment tools are core) and a medium risk that the first version is large for an mvp. There is no deadline.

## Q1. [Product owner] The re-runnable pipeline

You gave "a pipeline I can re-run easily when a new ListenBrainz dump comes out" as a reason for the rebuild, but it is not yet in or out of the first version. Which fits?

A. Must-have: one command rebuilds everything from a new dump
B. Must-have, but a few steps run in a documented order (like now) is fine
C. Not in the first version: run the pipeline once now, make it re-runnable later
D. Not yet defined
X. Other (please specify)

[Answer]: B

## Q2. [Product owner] Core or stretch: the map and the experiment tools

Both are in the first version. To keep the mvp small, should either be a stretch item (built only after the core works)?

A. Both are must-have
B. Map must-have, experiment tools stretch
C. Experiment tools must-have (they measure the quality metric), map stretch
D. Both stretch: similar-artist search is the only core
X. Other (please specify)

[Answer]: D

## Q3. [Product owner] Who uses the experiment and evaluation tools

The friends only want similar artists, so the experiment tools (genre reranking, relevance scoring) are probably for you. How should they be used?

A. Only by me, from the command line
B. Only by me, inside the web app
C. By me and the friends, inside the web app
D. Not yet defined
X. Other (please specify)

[Answer]: C

## Q4. [Product owner] Genre tags on results

The current app shows MusicBrainz genre tags beside artists. Is that part of the first version?

A. Must-have: show genres with every result
B. Nice-to-have
C. Not needed
D. Not yet defined
X. Other (please specify)

[Answer]: A

## Q5. [Delivery] Build order

With no deadline, what should be built first?

A. Value first: similar-artist search working end to end, then the rest
B. Risk first: the data pipeline and model training, then the app on top
C. Dependency order: whatever the others need first
D. Not yet defined
X. Other (please specify)

[Answer]: C

## Q6. [Delivery] Getting ready for deployment later

Hosting is out of the first version. Should the first version do anything now to make deploying later easier?

A. Nothing: local only, deal with it later
B. Keep it easy to run elsewhere (settings in one place, no machine-specific paths)
C. Package it so it could be deployed as-is (for example a container), but do not deploy
D. Not yet defined
X. Other (please specify)

[Answer]: A

## Q7. [Product owner] Measuring quality when the experiment tools are stretch

One of your success metrics (from Intent Capture) is that recommendation quality at least matches the current app on your hand-labelled judgments. Measuring that needs some way to score result lists against the judgments, and in Q2 you made the experiment and evaluation tools stretch. How should quality be checked in the core first version?

A. Scoring against the judgments is core (a small check, no web screens); only the genre-reranking experiments and the tools' web screens are stretch
B. The quality check moves to stretch too, and stops being a core success metric
C. Check quality by eye: compare a few result lists with the current app
D. Not yet defined
X. Other (please specify)

[Answer]: C

## Consolidated Summary Confirmation

- Re-runnable pipeline (Q1): must-have; a few steps run in a documented order is fine.
- Map and experiment tools (Q2): both stretch; similar-artist search is the only core.
- Experiment tools' users (Q3): when built, used by you and the friends inside the web app.
- Genre tags (Q4): must-have; genres shown with every result.
- Build order (Q5): dependency order.
- Deployment prep (Q6): nothing in v1; local only.
- Quality check in core v1 (Q7): by eye, comparing a few result lists with the current app.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

# Intent Capture & Framing — Questions

## Sources

- [desc] Initial description: "Rebuild an existing app (located at ../listenbrainz) that does collaborative filtering for musical artists, from scratch using AI-DLC. The user has never built an app from scratch in AI-DLC before."
- [scope] Workflow-selected scope: `mvp`.

## Q1. [Product owner] Why rebuild it

The existing app (`../listenbrainz`) already recommends artists, so it helps to know what this rebuild is really for. Everything later (requirements, design, what counts as "done") depends on it. (select all that apply)

A. Learn AI-DLC on a problem I already understand (the rebuild is mainly practice)
B. Turn the existing prototype into a cleaner, more maintainable app
C. Make it usable by people other than me
D. Get better recommendations than the current version gives
E. Not yet defined
X. Other (please specify)

[Answer]: A, B — "mostly want to learn ai-dlc but also maybe clean it up a bit. also right now it only runs on localhost at some point i will want to make it possible to deploy it somewhere"

## Q2. [Product owner] Who the app is for

Who is the main user of the rebuilt app? This decides how much polish, hosting and account handling it needs.

A. Just me (a personal tool)
B. Me plus a few friends or colleagues
C. Any ListenBrainz user, publicly
D. A portfolio or demo audience (people who look at it to see what I built)
E. Not yet defined
X. Other (please specify)

[Answer]: B

## Q3. [Product owner] What the user wants to do

What does the user come to the app to do? (select all that apply)

A. Type in an artist they like and get similar artists
B. Get recommendations based on their own ListenBrainz listening history
C. Explore a visual map of how artists relate to each other
D. Judge and compare recommendation quality (research and evaluation)
E. Not yet defined
X. Other (please specify)

[Answer]: A

## Q4. [Product owner] What success looks like

How will you know the rebuild worked? Pick the outcomes you would measure. (select all that apply)

A. Everything the current app does (artist search, similar artists, map) works end to end in the new one
B. Recommendation quality at least matches the current app on your hand-labelled relevance judgments (the `results/` files)
C. A similar-artist lookup answers within a target time (for example under 1 second)
D. I finish a full AI-DLC run and understand how to use the method on my next project
E. Not yet defined
X. Other (please specify)

[Answer]: A, B, C, D

## Q5. [Product owner] Why now

What prompted the rebuild at this point?

A. I want to learn AI-DLC and this is a good first project
B. The current code grew experimentally and is hard to extend
C. I want a pipeline I can re-run easily when a new ListenBrainz dump comes out
D. I plan to share or host it and the current version is not ready for that
E. Not yet defined
X. Other (please specify)

[Answer]: A, C, D

## Q6. [Product owner] Who has a say

Who are the people involved, and who makes the calls on scope and priority?

A. Only me: I build it and I decide everything
B. Me as the decider, with one or more people giving input (name them)
C. Someone else decides scope or priority (name them)
D. Not identified
X. Other (please specify)

[Answer]: A

## Q7. [Product owner] Reporting and communication

Does anyone need updates on this work?

A. None: it is a solo project
B. A write-up or blog post when it is done
C. Regular progress updates to someone (say who and how often)
D. Not applicable
X. Other (please specify)

[Answer]: A

## Q8. [Product owner] What this first version leaves out

The plan is already set to `mvp` (ship the core, skip operations). Within that, what should the first version of the app NOT do? (select all that apply)

A. Public hosting or cloud deployment (it runs locally)
B. User accounts or sign-in
C. The experiment and evaluation tools (genre reranking, relevance scoring)
D. The visual artist map
E. None: everything the current app does carries over
X. Other (please specify)

[Answer]: A, B

## Q9. [Product owner] The artist map and the experiment tools

In Q3 you said users come to the app to find similar artists, but in Q8 you did not leave out the visual artist map or the experiment and evaluation tools. Which of them belong in the first version? (select all that apply)

A. The visual artist map
B. The experiment and evaluation tools (genre reranking, relevance scoring)
C. Neither: the first version is artist search and similar artists only
D. Not yet defined
X. Other (please specify)

[Answer]: A, B

## Q10. [Product owner] How the few other people reach it

In Q2 you said the app is for you plus a few others, and in Q8 that the first version is not publicly hosted. How will those others use it in the first version?

A. They don't yet: only I use it until it is deployed
B. On my machine or home network, while I run it
C. They run it themselves from the code
D. Not yet defined
X. Other (please specify)

[Answer]: D

## Q11. [Product owner] How fast a lookup must be

In Q4 you chose a response-time target for similar-artist lookups. What target should the first version meet, measured on your own machine?

A. Under 200 milliseconds
B. Under 1 second
C. Under 3 seconds
D. Not yet defined (pick one later, in requirements)
X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Why rebuild (Q1): mainly to learn AI-DLC, and also to clean up the existing app; you will want to deploy it somewhere at some point.
- Who it is for (Q2): you plus a few friends or colleagues.
- What users do (Q3): type in an artist and get similar artists.
- Success (Q4): feature parity end to end; recommendation quality at least matches the current app on your hand-labelled judgments; fast lookups; you finish a full AI-DLC run.
- Why now (Q5): learning AI-DLC, a pipeline you can re-run on new ListenBrainz dumps, and a plan to share or host it.
- Decider (Q6): only you.
- Updates (Q7): none, solo project.
- Left out of v1 (Q8): public hosting and user accounts.
- Also in v1 (Q9): the visual artist map and the experiment and evaluation tools.
- How others use v1 (Q10): not yet defined.
- Lookup speed (Q11): under 200 milliseconds on your own machine.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

## Assumption Confirmation

The artifacts carry these assumptions:

- How the few other users reach the app while it is not publicly hosted is not yet defined (Q10); until it is settled, the first version is treated as used only on the owner's machine, and the friends or colleagues as future users.

A. Accept assumptions
B. Convert to follow-up questions

[Answer]: A. Accept assumptions

# Feasibility & Constraints — Questions

Context: the intent statement (`ideation/intent-capture/intent-statement.md`) sets a rebuild of the artist recommender, run locally for now, with a lookup-speed target of under 200 milliseconds and recommendation quality at least matching the current app.

## Q1. [Developer] Which data the rebuild starts from

The current app in `../listenbrainz` already has a ListenBrainz statistics dump (about 21 GB compressed, extracted beside it) and an extracted MusicBrainz dump. Which data should the rebuild use?

A. Reuse those same downloaded files where they are
B. Copy or move them into this new project
C. Download fresh dumps for the rebuild
D. Not yet defined
X. Other (please specify)

[Answer]: A

## Q2. [Developer] How free the technology choices are

The current app uses Python with Spark (needs Java), FAISS, FastAPI and UMAP. How much of that is fixed for the rebuild?

A. Keep the same tools: it is a rebuild of the same design
B. Keep Python, but any tool can be replaced if something simpler or faster fits
C. Open to any language and tools
D. Not yet defined
X. Other (please specify)

[Answer]: A

## Q3. [Developer] The machine it runs on

Training on the full dump is the heaviest step, so the machine sets what is feasible. How much memory does the machine that runs the data pipeline have?

A. 16 GB or less
B. 32 to 64 GB
C. More than 64 GB
D. Not sure
X. Other (please specify)

[Answer]: B

## Q4. [Product owner] Timeline

Is there a date this needs to be done by?

A. No deadline: evenings and weekends, at my own pace
B. Within about a month
C. Within about three months
D. Not yet defined
X. Other (please specify)

[Answer]: A

## Q5. [Product owner] Money for paid services

Is there a budget for anything that costs money (cloud compute for training, hosting later, paid APIs)?

A. None: free and local only
B. A small monthly amount (under about $20)
C. More than that is fine if it is worth it
D. Not yet defined
X. Other (please specify)

[Answer]: A

## Q6. [Compliance] Data about individual listeners

The statistics dump is built from individual users' listening. Should the app ever show or keep anything about individual ListenBrainz users, or only artist-level results?

A. Only artist-level results: nothing about individual users is shown
B. User-level data may be shown (for example "listeners like you")
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Q7. [Operations] Where it would be deployed later

You want to deploy it somewhere at some point. Is there a cloud account or host already in use?

A. No cloud account or host yet
B. AWS
C. Another cloud provider or a VPS (say which)
D. Not decided
X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Data (Q1): reuse the ListenBrainz and MusicBrainz dumps already downloaded in `../listenbrainz`, in place.
- Tools (Q2): keep the same tools as the current app; it is a rebuild of the same design.
- Machine (Q3): the pipeline runs on a machine with 32 to 64 GB of memory.
- Timeline (Q4): no deadline; evenings and weekends.
- Budget (Q5): none; free and local only.
- Listener data (Q6): only artist-level results; nothing about individual ListenBrainz users is shown.
- Hosting (Q7): no cloud account or host yet.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

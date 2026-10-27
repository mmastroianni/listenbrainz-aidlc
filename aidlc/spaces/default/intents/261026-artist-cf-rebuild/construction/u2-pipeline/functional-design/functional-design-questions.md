# Functional Design (u2-pipeline) — Questions

Context: u2-pipeline is the full batch side (`inception/units-generation/unit-of-work.md`). u1-skeleton already built the sample-sized path, so most choices are settled. Looking up the current app in `../listenbrainz` answers these, which are recorded as decisions in the design rather than asked again:

- Training settings at full size: the current app uses rank 64, 10 iterations, regularisation 0.1, alpha 20, implicit feedback on log1p of listen counts (`pipeline/train_als.py`).
- Genres: the current app keeps MusicBrainz tags that are on MusicBrainz's list of recognised genres and have a positive vote count, ranked by votes (`pipeline/build_artist_tags.py`, `update_artist_metadata.py`).
- Descriptions: the MusicBrainz artist table's short description column (the "comment" column, for example "Japanese reggae singer").
- Index: an exact (not approximate) cosine index, as in the current app (`pipeline/build_index.py`).
- Artist names: where one artist id appears under several spellings in the listening dump, the most common spelling is used.

Two choices need your judgement.

## Q1. [Architect] What "closest text match first" means in name search

Requirement FR4.2 says suggestions come closest text match first, then most listeners first. The current app does not do this (it orders by shortest name), so the meaning of "closest" is new. For the text "thr", which would you want to see first?

A. Four tiers, best first: the name is exactly the text; the name starts with the text; every typed word starts some word of the name ("henry thr" finds "Henry Threadgill"); then within each tier the artist with more listeners first (recommended: an exact or starting match always beats a match in the middle of a name)
B. Two tiers: the name starts with the text, then any word match; within each tier more listeners first
C. Also forgive small typos ("henri threadgil" still finds "Henry Threadgill"), on top of the tiers in A (more work and slower; not required by the requirements)
X. Other (please specify)

[Answer]: A

## Q2. [Product owner] Artists in the listening data that MusicBrainz has no record of

Some artist ids in the listening dump are missing from the MusicBrainz artist table (for example ids that were merged or removed). They still have listeners and take part in the similarity model, but there is no description or genre for them, and the MusicBrainz link may lead nowhere. What should the app do with them?

A. Keep them everywhere: name taken from the listening dump, no description, "no genres listed" (recommended: nothing is lost from similar-artist lists, and the current app does the same)
B. Drop them from the whole app, so every artist shown has MusicBrainz details (changes which artists the model learns from)
C. Keep them in similar-artist lists but leave them out of name suggestions
X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Name search (Q1): four tiers — exact name, name starts with the text, every typed word starts a word of the name — then more listeners first within each tier.
- Artists missing from MusicBrainz (Q2): kept everywhere, name from the listening dump, no description, "no genres listed".

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

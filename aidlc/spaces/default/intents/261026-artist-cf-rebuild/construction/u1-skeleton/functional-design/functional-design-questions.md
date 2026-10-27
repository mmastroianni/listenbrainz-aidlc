# Functional Design (u1-skeleton) — Questions

Context: u1-skeleton is the thin slice through every component (`inception/units-generation/unit-of-work.md`). Looking at the listening dump (`lbdump/statistics/artists_all_time.jsonl`, about 3.5 GB) shows each line is one listener, `{"user_id": <number>, "data": [{"listen_count", "artist_name", "artist_mbid"}, ...]}`. Listeners are already numbers rather than names, and every artist comes with its name. Two choices for the skeleton are still open.

## Q1. [Architect] The skeleton's sample

The skeleton runs on a small sample so it finishes in seconds.

A. The first 5,000 listener lines of the real dump, read in place (recommended: real data, and it proves the read-only path)
B. A small made-up fixture file only
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Q2. [Architect] Where the skeleton gets artist names

A. From the listening dump itself, which carries each artist's name next to its id; MusicBrainz descriptions and genres come in u2-pipeline (recommended: keeps the skeleton small)
B. From the MusicBrainz artist table already in the skeleton
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Sample (Q1): the first 5,000 listener lines of the real dump, read in place.
- Names (Q2): from the listening dump; MusicBrainz descriptions and genres come in u2-pipeline.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

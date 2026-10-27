# Refined Mockups — Questions

Context: the wireframes, user flow, stories and requirements already settle the layout, states, devices, keyboard use and look (the current app's style). Two details are still open.

## Q1. [Designer] A text value beside the similarity bar

The underlying score is the cosine similarity between two artists' learned vectors (from -1 to 1; in practice the closest artists score roughly 0.5 to 0.95). The bar is that score scaled so the closest artist in the list is full. Should a number also appear, so it can be read without seeing the bar (for example on a screen reader or a small phone)?

A. Show the raw cosine score beside the bar (for example 0.87)
B. Bar only on screen, with the raw cosine score available to screen readers and as a tooltip
C. Bar only
D. Not yet defined
X. Other (please specify)

[Answer]: B

## Q2. [Designer] The selected-artist heading

Above the results, what should the heading show about the artist you picked?

A. Name, MusicBrainz description, genres and a MusicBrainz link
B. Name only ("Artists like Henry Threadgill")
C. Not yet defined
X. Other (please specify)

[Answer]: B

## Q3. [Designer] Links on each similar artist

The requirements so far give each result one MusicBrainz link. The current app gives each similar artist a MusicBrainz link and a YouTube search link. A Spotify search link (opening Spotify's search for the artist's name) needs no sign-in; only Spotify's data API needs authentication. Which links should each result have?

A. MusicBrainz and YouTube search, like the current app
B. MusicBrainz, YouTube search and Spotify search
C. MusicBrainz only, as the requirements say now
D. Not yet defined
X. Other (please specify)

[Answer]: B — shown as three small icon links at the end of each row, each with a text label for screen readers and on hover

## Consolidated Summary Confirmation

- Similarity number (Q1): the bar on screen; the raw cosine score appears on hover and is read by screen readers.
- Heading (Q2): name only, "Artists like Henry Threadgill".
- Links (Q3): MusicBrainz page, YouTube search and Spotify search, as three small labelled icons on each result (no sign-in needed). This changes requirement FR5.2, which named a MusicBrainz link only.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

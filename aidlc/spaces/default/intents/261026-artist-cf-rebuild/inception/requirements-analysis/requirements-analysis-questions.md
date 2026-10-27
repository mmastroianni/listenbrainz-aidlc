# Requirements Analysis — Questions

Context: the intent statement, scope document, wireframes and team practices already settle most of the core first version (type an artist, get 20 similar artists with genres in under 200 ms, explore by clicking, local only). These questions cover the details still missing to make each requirement testable.

## Q1. [Product owner] Pass bar for the by-eye quality check

The scope says quality is checked by eye against the current app. To make that a pass/fail check, how many artists do you compare, and what counts as a pass?

A. 5 artists I know well; it passes if the new lists are at least as good for 4 of the 5
B. 10 artists; it passes if the new lists are at least as good for 8 of the 10
C. A gut check with no fixed number
D. Not yet defined
X. Other (please specify)

[Answer]: A

## Q2. [Product owner] Which artists are included

Very obscure artists have too little listening data to give useful similar artists. Which artists should the app know about?

A. The same cutoff as the current app (I'll read it from `../listenbrainz`)
B. Only artists with at least a set number of listeners (say which number)
C. Every artist in the dump
D. Not yet defined
X. Other (please specify)

[Answer]: A — the current app keeps artists with at least 5 listeners (`MIN_LISTENERS = 5` in `../listenbrainz/src/listenbrainz_recs/pipeline/train_als.py`)

## Q3. [Designer] How far "Show more" goes

The wireframes show 20 results, then "Show more" adds 20 at a time. Where does it stop?

A. At 100 results
B. At 200 results
C. No cap: until the list runs out
D. Not yet defined
X. Other (please specify)

[Answer]: C

## Q4. [Designer] Telling same-name artists apart in suggestions

Several artists can share a name. Besides the genre, what should a suggestion show to tell them apart?

A. MusicBrainz's short description of the artist (for example "US jazz saxophonist"), when it has one
B. Genre only
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Q5. [Designer] Order of suggestions

When several artists match what the user typed, which comes first?

A. Closest text match first, then most popular
B. Most popular first
C. Alphabetical
D. Not yet defined
X. Other (please specify)

[Answer]: A

## Q6. [Designer] What the similarity bar means

The wireframes show a bar for how similar each artist is. What does it measure?

A. Relative within this list: the closest artist gets the fullest bar
B. An absolute similarity score that can be compared across searches
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Q7. [Designer] Links and the back button

Should each artist's results have their own web address, so the back button returns to the previous artist and a link can be bookmarked or sent to a friend?

A. Yes: each artist's results have their own address
B. No: one page, the back button leaves the app
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Q8. [Release engineer] How long a full rebuild may take

The re-run steps rebuild everything from a new dump on your 32 to 64 GB machine. How long is acceptable for a full rebuild?

A. Any length: overnight is fine
B. Under about 2 hours
C. Under about 30 minutes
D. Not yet defined
X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Quality check (Q1): compare 5 artists you know well; it passes if the new lists are at least as good for 4 of the 5.
- Artists included (Q2): the current app's cutoff, at least 5 listeners.
- Show more (Q3): no cap; it keeps adding 20 until the list runs out.
- Same-name artists (Q4): suggestions show MusicBrainz's short description, when it has one, beside the genre.
- Suggestion order (Q5): closest text match first, then most popular.
- Similarity bar (Q6): relative within the list; the closest artist gets the fullest bar.
- Addresses (Q7): each artist's results have their own web address, so Back and bookmarks work.
- Rebuild time (Q8): any length; overnight is fine.

Does this all look correct before I generate the requirements artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

# User Stories

Derived from `inception/requirements-analysis/requirements.md` (FR and NFR IDs in brackets), `personas.md`, and `user-stories-questions.md`. They are grouped by what users do (Q2). Search, lookup and web stories are written so their acceptance criteria can become tests first (`inception/practices-discovery/team-practices.md`, Testing Posture).

## US1 Find an Artist

### US1.1 Suggestions as I type — Must Have

As a friend, I want matching artists suggested as I type, so that I can start from an artist without spelling the full name. [FR4.1, FR4.2, FR4.3, FR4.5, NFR1]

- **AC1.1.1** Given I have typed "henry thr", when suggestions appear, then "Henry Threadgill" is among them.
- **AC1.1.2** Given two artists match equally well, when suggestions appear, then the one with more listeners comes first.
- **AC1.1.3** Given I type "bjork", when suggestions appear, then "Björk" is among them.
- **AC1.1.4** Given I type "zzqqxx", when suggestions are fetched, then I see "No artists match 'zzqqxx'".
- **AC1.1.5** Given I type only spaces, when the box updates, then no suggestions are shown.
- **AC1.1.6** Given the full-size data, when 100 different suggestion lookups run on the owner's machine, then 95% answer in under 200 ms.

INVEST: independent of the results view (it only needs the artist list); small; each criterion is testable.

### US1.2 Tell same-name artists apart — Should Have

As a friend, I want each suggestion to show a genre and a short description, so that I pick the right artist when several share a name. [FR4.4]

- **AC1.2.1** Given two artists named "Nirvana" with different MusicBrainz descriptions, when I type "nirvana", then both appear, each with its own description.
- **AC1.2.2** Given an artist with no description, when it is suggested, then it shows its name and genre only, with no empty placeholder.

## US2 See Similar Artists

### US2.1 See 20 similar artists — Must Have

As a friend, I want to see the 20 artists most similar to the one I picked, with their genres, so that I can discover music like what I already enjoy. [FR5.1, FR5.2, FR5.3, FR3.1, FR3.2, FR5.9, NFR1, NFR3]

- **AC2.1.1** Given I pick "Henry Threadgill", when results load, then 20 artists are listed most similar first, and "Henry Threadgill" is not among them.
- **AC2.1.2** Given a result row, when it is shown, then it has the name, genre tags, a similarity bar and a link that opens the artist's MusicBrainz page.
- **AC2.1.3** Given a result list, when bars are drawn, then the first result's bar is full and no later bar is longer.
- **AC2.1.4** Given a result artist with no genre tags, when it is shown, then "no genres listed" appears in place of genres.
- **AC2.1.5** Given any results response, when it is inspected, then it contains no listener names or other listener details.
- **AC2.1.6** Given the full-size data, when 100 different similar-artist lookups run on the owner's machine, then 95% answer in under 200 ms.

### US2.2 Show more — Should Have

As a friend, I want to load more similar artists, so that I can dig deeper than the first 20. [FR5.4]

- **AC2.2.1** Given 45 similar artists are available, when I click "Show more" twice, then 45 are shown and "Show more" is gone.
- **AC2.2.2** Given exactly 20 are available, when results load, then "Show more" is not shown.

### US2.3 Clear messages when results can't be shown — Must Have

As a friend, I want a plain message when there are no results or something fails, so that I know what happened and what to do next. [FR5.7, FR5.8, FR6.5]

- **AC2.3.1** Given an artist with too little data, when I pick it, then I see "Not enough listening data to find artists like <name>." and the search box still works.
- **AC2.3.2** Given an address for an artist the app does not know, when I open it, then I see "We don't know this artist" and the search box still works.
- **AC2.3.3** Given the lookup fails, when results were expected, then I see "Something went wrong finding similar artists. Try again." with a Retry button and no error codes.

### US2.4 Use it on a phone or by keyboard — Should Have

As a friend, I want the page to work on my phone and by keyboard, so that I can use it however I browse. [FR6.1, FR6.2, FR6.3, FR6.4, FR6.6]

- **AC2.4.1** Given a 375-pixel-wide screen, when results show, then they sit in one column with no sideways scrolling.
- **AC2.4.2** Given the page has just loaded, when I start typing, then the text goes into the search box.
- **AC2.4.3** Given suggestions are open, when I press Down then Enter, then the highlighted artist is picked; when I press Escape, then the list closes.
- **AC2.4.4** Given results are shown, when I press Tab repeatedly, then I reach every name, link and the "Show more" button.
- **AC2.4.5** Given an artist name longer than the row, when it is shown, then it wraps and is not cut off mid-word.

## US3 Explore

### US3.1 Click to explore — Must Have

As a friend, I want to click a similar artist to see artists like them, so that I can wander from one discovery to the next. [FR5.5]

- **AC3.1.1** Given results for artist A, when I click artist B's name, then results for B are shown.
- **AC3.1.2** Given results for artist A, when I click B's external link, then B's MusicBrainz page opens and A's results stay on screen.

### US3.2 Back, bookmark and share — Should Have

As a friend, I want each artist's results to have their own address, so that Back takes me to the previous artist and I can send a find to someone. [FR5.6]

- **AC3.2.1** Given I went from A to B, when I press Back, then A's results are shown again.
- **AC3.2.2** Given the address of B's results, when I open it in a new tab, then B's results are shown.

## US4 Rebuild on a New Dump (owner)

### US4.1 Prepare the data from the dumps in place — Must Have

As the owner, I want the dumps read where they already are and turned into listen counts, so that I never copy 20+ GB or risk damaging them. [FR1.1, FR1.2, FR1.3, FR1.4, NFR5]

- **AC4.1.1** Given the data-location setting points at `../listenbrainz`, when data preparation runs, then it reads the dumps there and the dump files are unchanged afterwards.
- **AC4.1.2** Given the setting is missing or points at a folder without the expected files, when preparation starts, then it stops with a message naming the setting and the missing file, and writes nothing.
- **AC4.1.3** Given a sample with one malformed line among valid ones, when preparation runs, then every valid line is processed and 1 skipped record is reported.
- **AC4.1.4** Given artists with 4 and 5 listeners, when preparation runs, then only the one with 5 is kept.
- **AC4.1.5** Given preparation has run, when its output is inspected, then it holds only internal listener numbers, artist identifiers and listen counts.
- **AC4.1.6** Given preparation has run, when `git status` is checked, then no data or model files are listed as new.

### US4.2 Learn artist similarity — Must Have

As the owner, I want similarity learned the same way as in the current app, so that recommendations are comparable. [FR2.1, FR2.2]

- **AC4.2.1** Given the prepared data, when training runs, then it produces one vector per kept artist.
- **AC4.2.2** Given the full dump on the owner's machine, when training runs, then it finishes without running out of memory (any duration).

### US4.3 Documented rebuild steps — Must Have

As the owner, I want written steps that rebuild everything from a new dump in order, so that refreshing the data is routine. [FR7.1, FR7.2]

- **AC4.3.1** Given a new dump in the data location, when I follow the documented steps in order, then the app serves results from the new data.
- **AC4.3.2** Given I run a step before the one it depends on, when it starts, then it stops with a message naming the missing input.

### US4.4 Start the app with one command — Must Have

As the owner, I want to start the app with one documented command, so that I can use it any time without remembering details. [NFR2, NFR8]

- **AC4.4.1** Given all model and data files are built, when I run the start command, then the page opens on my machine.
- **AC4.4.2** Given a model file is missing, when I run the start command, then it fails at once with a message naming the file and the step that builds it.

## US5 Check Quality (owner)

### US5.1 Compare with the current app — Must Have

As the owner, I want to compare the new app's lists with the current app's for 5 artists I know well, so that I know the rebuild is at least as good. [FR8.1]

- **AC5.1.1** Given 5 chosen artists, when I compare both apps' similar-artist lists, then I record pass or fail for each.
- **AC5.1.2** Given the records, when at least 4 of the 5 are at least as good, then the quality check passes; otherwise it fails.

## Dependencies

- US1.1 and US2.1 depend on US4.1 and US4.2 (no data, no results).
- US2.2, US2.3, US2.4, US3.1 and US3.2 build on US2.1's results view.
- US5.1 depends on US2.1 and the current app being runnable.

## Priority Summary

| Priority | Stories |
|----------|---------|
| Must Have | US1.1, US2.1, US2.3, US3.1, US4.1, US4.2, US4.3, US4.4, US5.1 |
| Should Have | US1.2, US2.2, US2.4, US3.2 |
| Could Have | none (the map and experiment tools are stretch and have no stories yet) |

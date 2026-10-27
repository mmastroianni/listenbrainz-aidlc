# Requirements — Artist Recommendation App Rebuild (v1 core)

Sources: the intent statement (`ideation/intent-capture/intent-statement.md`), the scope document (`ideation/scope-definition/scope-document.md`, with the intent backlog IB-1 to IB-9), the constraint register (`ideation/feasibility/constraint-register.md`), the wireframes and user flow (`ideation/rough-mockups/`), the team practices (`inception/practices-discovery/team-practices.md`), and `requirements-analysis-questions.md`.

## Intent Analysis

The owner is rebuilding their artist recommender from scratch, mainly to learn AI-DLC and also to clean it up (intent statement). The core first version does one thing well: a user types an artist they like and sees similar artists with their genres, quickly, and can keep exploring from artist to artist (scope document). Everything is built on the ListenBrainz and MusicBrainz dumps already on the machine, read in place, and runs locally only (constraint register TC-2, TC-5). The map and the experiment tools are stretch and are not specified here (scope document; project rule on stretch items).

## Functional Requirements

### FR1 Data preparation (IB-1)

- **FR1.1** The system shall read the ListenBrainz statistics dump and the MusicBrainz dump from a location given by one setting, and never write to, move or modify them (constraint TC-2; hard rule).
  - Given the data-location setting points at `../listenbrainz`, when data preparation runs, then it reads the dumps there and the dumps' files are unchanged afterwards.
  - Given the setting is missing or points at a folder without the expected files, when data preparation starts, then it stops with a message naming the setting and the missing file, and writes nothing.
- **FR1.2** The system shall turn the dump into a table of listener-artist listen counts that keeps no listener names or other listener details beyond an internal number (hard rule: no listener data).
  - Given the dump, when preparation finishes, then the output holds only internal listener numbers, artist identifiers and listen counts.
- **FR1.3** The system shall skip malformed records in the dump, count them, and process every valid record.
  - Given a dump sample with one malformed line among valid ones, when preparation runs, then the valid lines are all processed and the run reports 1 skipped record.
- **FR1.4** The system shall keep only artists with at least 5 listeners, the same cutoff as the current app (Q2).
  - Given an artist with 4 listeners and one with 5, when preparation runs, then only the artist with 5 listeners is kept.

### FR2 Learning artist similarity (IB-2)

- **FR2.1** The system shall learn artist similarity from the prepared listen counts with the same collaborative-filtering approach as the current app (project rule: same toolset).
  - Given the prepared table, when training runs, then it produces one vector per kept artist.
- **FR2.2** Training on the full dump shall complete within the memory of the owner's 32 to 64 GB machine; there is no time limit (constraint TC-3; Q8).
  - Given the full dump, when training runs on the owner's machine, then it finishes without running out of memory.

### FR3 Artist details and genres (IB-3)

- **FR3.1** The system shall store, for every kept artist, its name, its MusicBrainz identifier, its MusicBrainz short description when one exists, its listener count, and its MusicBrainz genre tags (scope document; Q4).
  - Given an artist kept by FR1.4, when details are built, then all five fields are present, with the description and genres allowed to be empty.
- **FR3.2** An artist with no genre tags shall be shown with the text "no genres listed", never a blank (wireframes).
  - Given an artist with no genre tags, when it appears in results, then "no genres listed" is shown in place of genres.

### FR4 Finding an artist by name (IB-4)

- **FR4.1** The system shall suggest matching artists as the user types (wireframes; rough-mockups Q2).
  - Given the user has typed "henry thr", when suggestions appear, then they include "Henry Threadgill".
- **FR4.2** Suggestions shall be ordered closest text match first, then by listener count (Q5).
  - Given two artists that match equally well, when suggestions appear, then the one with more listeners comes first.
- **FR4.3** Matching shall ignore case and accents, so "bjork" finds "Björk".
  - Given the user types "bjork", when suggestions appear, then "Björk" is among them.
- **FR4.4** Each suggestion shall show the artist's name, its first genre, and its MusicBrainz short description when it has one, so same-name artists can be told apart (Q4).
  - Given two artists named "Nirvana" with different descriptions, when the user types "nirvana", then both appear with different descriptions.
- **FR4.5** When nothing matches, the suggestion list shall say "No artists match '<text>'", and whitespace-only input shall show no suggestions.
  - Given the user types "zzqqxx", when suggestions are fetched, then "No artists match 'zzqqxx'" is shown.

### FR5 Similar artists (IB-4, IB-5)

- **FR5.1** When the user picks an artist, the system shall show the 20 most similar artists, most similar first (wireframes; rough-mockups Q4).
  - Given the user picks "Henry Threadgill", when results load, then 20 artists are listed in order of decreasing similarity, and "Henry Threadgill" is not among them.
- **FR5.2** Each result shall show the artist's name, genre tags (FR3.2 when empty), a similarity bar, and a link to the artist's MusicBrainz page (rough-mockups Q3).
  - Given a result row, when it is shown, then it has all four parts and the link opens the artist's MusicBrainz page.
- **FR5.3** The similarity bar shall be relative within the list: the most similar artist gets the fullest bar (Q6).
  - Given a result list, when bars are drawn, then the first result's bar is full and no later bar is longer.
- **FR5.4** "Show more" shall add the next 20 results each time and disappear when the list runs out; there is no cap (Q3).
  - Given 45 similar artists are available, when the user clicks "Show more" twice, then 45 are shown and "Show more" is gone.
- **FR5.5** Clicking a similar artist's name shall make it the new search (rough-mockups Q5).
  - Given results for artist A, when the user clicks artist B's name, then results for B are shown.
- **FR5.6** Each artist's results shall have their own web address, so the browser's back button returns to the previous artist and the address can be bookmarked or shared (Q7).
  - Given the user went from A to B, when they press Back, then A's results are shown again; given the address for B is opened directly, then B's results are shown.
- **FR5.7** An artist with too little data for similar artists shall show "Not enough listening data to find artists like <name>." (wireframes).
- **FR5.8** An address for an artist the system does not know shall show "We don't know this artist" with the search box still usable.
- **FR5.9** The results shall never include anything about individual listeners (hard rule).

### FR6 Web page (IB-5)

- **FR6.1** Search and results shall be on one page, with the search box at the top (rough-mockups Q1).
- **FR6.2** The page shall work in desktop and phone browsers; on a phone, results stack in one column (rough-mockups Q6).
  - Given a 375-pixel-wide screen, when results show, then there is no sideways scrolling.
- **FR6.3** The page shall be usable by keyboard: the search box is focused on load, Up and Down move through suggestions, Enter picks, Escape closes, and every link and button is reachable with Tab (rough-mockups Q7).
- **FR6.4** The page shall follow the current app's look (rough-mockups Q8).
- **FR6.5** When a lookup fails, the page shall show "Something went wrong finding similar artists. Try again." with a Retry button, and no error codes (wireframes).
- **FR6.6** Long artist names shall wrap and never be cut off mid-word (wireframes).

### FR7 Re-running on a new dump (IB-6)

- **FR7.1** The project shall document the steps that rebuild everything from a new dump, in the order they run (scope document Q1).
  - Given a new dump in the data location, when the owner follows the documented steps in order, then the app serves results from the new data.
- **FR7.2** Each step shall stop with a clear message naming the missing input when the step before it has not been run.

### FR8 Quality check (IB-7)

- **FR8.1** The owner shall compare the similar-artist lists for 5 artists they know well against the current app's lists; v1 passes when the new lists are at least as good for at least 4 of the 5 (Q1; scope document metric change).
  - Given 5 chosen artists, when the owner compares both apps' lists, then the result (pass or fail, and the count) is recorded.

## Non-Functional Requirements

- **NFR1 Lookup speed**: a similar-artist lookup and a suggestion lookup each answer in under 200 ms on the owner's machine, measured as the 95th percentile over 100 lookups of different artists against the full-size data (intent statement; constraint TC-4).
- **NFR2 Startup**: the app starts with one documented command and, when model or data files are missing, fails at startup with a message naming the missing file and the step that builds it.
- **NFR3 Privacy**: no listener names or other listener details appear in the app, its responses or its logs (hard rule).
- **NFR4 Cost**: no paid service or cloud compute is used (hard rule; constraint OC-3).
- **NFR5 Repository hygiene**: dumps, intermediate data and model files are never committed to git (hard rule).
- **NFR6 Code quality**: every merge passes the pre-merge check (`ruff check`, `ruff format --check`, `ty`, `pytest` with at least 80% line coverage) (team practices).
- **NFR7 Testing**: tests run on small fixture data and never on the full dumps; search, lookup and web code is written test-first, and pipeline and training code is tested after (team practices).
- **NFR8 Local only**: the app runs on the owner's machine and is not reachable as a public service in v1 (constraint TC-5).

## Constraints

- Same toolset as the current app (Python 3.12, Spark, FAISS, FastAPI, UMAP), plus uv, ruff, ty, pytest and pytest-cov as development tools (project rule; team practices).
- Dumps read in place from `../listenbrainz`, never modified (constraint TC-2).
- Solo project with no deadline and no budget (constraint register OC-1 to OC-3).

## Assumptions

- [assumption] How the friends reach the first version is undecided; for now only the owner uses it (intent statement).
- [assumption] The external link in each result goes to the artist's MusicBrainz page, because every artist has a MusicBrainz identifier; a ListenBrainz link can be added later.
- [assumption] The full-size similar-artist index fits in memory on the owner's machine, as it does for the current app.

## Out of Scope

- The artist map and the experiment and evaluation tools (stretch; scope document).
- Public hosting, deployment preparation, user accounts and sign-in (scope document).
- Personalised recommendations from a user's own listening history (not chosen in Intent Capture).

## Open Questions

None.

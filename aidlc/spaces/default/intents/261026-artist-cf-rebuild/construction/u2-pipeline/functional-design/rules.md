# Business Rules — u2-pipeline

Sources: `inception/requirements-analysis/requirements.md`, `inception/user-stories/stories.md`, `inception/contract-design/contract-summary.md`, `inception/domain-design/components.md`, `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`, `functional-design-questions.md` (Q1, Q2), the skeleton's rules (`construction/u1-skeleton/functional-design/rules.md`) and the current app in `../listenbrainz`.

```yaml
rules:
  - id: BR1.1
    statement: The data location comes from one setting and must hold every expected dump file.
    category: validation
    applies_to: DumpLocation
    trigger: start of the prepare and catalogue steps
    logic: IF the setting is missing OR the listening dump OR any needed MusicBrainz table is absent THEN stop
    violation: stop with a message naming the setting and the missing file; write nothing
    source: FR1.1
  - id: BR1.2
    statement: Dump files are only ever opened for reading, and the dump folder is never written to.
    category: constraint
    applies_to: DumpSource
    trigger: any dump access
    logic: IF code opens a dump file THEN it opens it read-only; all output goes to the data and models folders
    violation: not reachable; a write attempt is a defect, caught by a test that compares dump files before and after a run
    source: FR1.1
  - id: BR1.3
    statement: A malformed listening line is skipped and counted; every valid line is processed.
    category: validation
    applies_to: ListenerRecord
    trigger: reading the listening dump
    logic: IF a line is not valid JSON OR has no listener number OR its data is not a list THEN skip the line and add 1 to skippedRecords ELSE process it
    violation: line dropped; the run continues and reports the count
    source: FR1.3
  - id: BR1.4
    statement: An entry with no artist id or a listen count below 1 is skipped and counted apart from skipped lines.
    category: validation
    applies_to: ListenerRecord entries
    trigger: reading a valid line
    logic: IF artistMbid is empty OR listenCount < 1 THEN skip the entry and add 1 to skippedEntries
    violation: entry dropped; the other entries of the line are kept
    source: FR1.3
  - id: BR1.5
    statement: Prepared data keeps only the listener number, artist id and listen count; artist names go to a separate artist file.
    category: constraint
    applies_to: ListenCount, ArtistName
    trigger: writing prepared data
    logic: FOR each entry keep (listenerNumber, artistMbid, listenCount) and nothing else about the listener; write names per artist, never per listener
    violation: n/a
    source: FR1.2, NFR3
  - id: BR1.6
    statement: Repeated entries for the same listener and artist are added together.
    category: calculation
    applies_to: ListenCount
    trigger: building the listen counts
    logic: GROUP BY (listenerNumber, artistMbid) AND sum listenCount
    violation: n/a
    source: FR1.2
  - id: BR1.7
    statement: Only artists with at least 5 distinct listeners are kept.
    category: constraint
    applies_to: ListenCount, Artist
    trigger: after skipping and summing, before anything is written for training or the catalogue
    logic: count distinct listenerNumber per artistMbid; keep rows of artists with count >= 5; 4 listeners is out, 5 is in
    violation: artist and all its rows dropped
    source: FR1.4
  - id: BR1.8
    statement: Every prepare run writes and prints a PrepReport.
    category: policy
    applies_to: PrepReport
    trigger: end of the prepare step
    logic: report validRecords, skippedRecords, skippedEntries and keptArtists
    violation: n/a
    source: FR1.3
  - id: BR1.9
    statement: Prepared data and built files live in git-ignored folders.
    category: constraint
    applies_to: project layout
    trigger: always
    logic: the data and models folders are listed in .gitignore, and no step writes anywhere else inside the project
    violation: n/a
    source: NFR5
  - id: BR2.1
    statement: Training produces one vector per kept artist; an artist whose vector has zero length is left out and counted.
    category: calculation
    applies_to: ArtistVector
    trigger: training
    logic: learn vectors; keep one per artistMbid; drop zero-length vectors and report how many
    violation: n/a
    source: FR2.1
  - id: BR2.2
    statement: Training uses the current app's settings, held in one place.
    category: policy
    applies_to: SimilarityTraining
    trigger: training
    logic: collaborative filtering on implicit feedback over log(1 + listen count), rank 64, 10 iterations, regularisation 0.1, alpha 20, fixed random seed
    violation: n/a
    source: FR2.1
  - id: BR2.3
    statement: Full-size training stays within the owner's machine memory and has no time limit.
    category: constraint
    applies_to: SimilarityTraining
    trigger: full-size training
    logic: Spark is given an explicit memory setting that fits within 32 GB; data stays in Spark and Parquet files and is never collected into Python lists
    violation: if memory runs out, stop with a message naming the memory setting to raise
    source: FR2.2
  - id: BR2.4
    statement: Training reads only the prepared data, so it can be re-run without the dump.
    category: policy
    applies_to: SimilarityTraining
    trigger: training
    logic: input is the prepared listen counts; the dump is not opened
    violation: n/a
    source: FR2.1
  - id: BR3.1
    statement: Every kept artist has a name, MusicBrainz id, description (may be none), listener count and genres (may be none).
    category: constraint
    applies_to: Artist
    trigger: catalogue build
    logic: build one Artist per kept artistMbid with all five fields present
    violation: n/a
    source: FR3.1
  - id: BR3.2
    statement: An artist's name is the spelling used by the most listeners in the listening dump.
    category: calculation
    applies_to: ArtistName
    trigger: prepare, naming kept artists
    logic: count listeners per (artistMbid, name); pick the highest; break ties alphabetically
    violation: n/a
    source: FR3.1
  - id: BR3.3
    statement: The description is the MusicBrainz short description, or none when it is empty or blank.
    category: policy
    applies_to: Artist
    trigger: catalogue build
    logic: IF the MusicBrainz artist row has a non-blank comment THEN description = comment trimmed ELSE none
    violation: n/a
    source: FR3.1, FR4.4
  - id: BR3.4
    statement: Genres are the artist's MusicBrainz tags that are recognised genres with positive votes, most voted first.
    category: calculation
    applies_to: ArtistGenre
    trigger: catalogue build
    logic: lower-case and trim tag names; keep tags whose name is on the genre list and whose votes are above 0; sum votes per (artist, genre); rank by votes descending, then name ascending
    violation: n/a
    source: FR3.1
  - id: BR3.5
    statement: A kept artist with no MusicBrainz record is kept everywhere, with its name from the listening dump, no description and no genres.
    category: policy
    applies_to: Artist
    trigger: catalogue build
    logic: IF the artistMbid is not in the MusicBrainz artist table THEN description = none AND genres = []
    violation: n/a
    source: functional-design-questions Q2
  - id: BR4.1
    statement: Name matching ignores case and accents and treats punctuation as a space.
    category: calculation
    applies_to: SearchEntry
    trigger: building the search table and reading typed text
    logic: decompose accents and drop the marks, fold case, turn every character that is not a letter or digit into a space, collapse spaces; "bjork" matches "Björk"
    violation: n/a
    source: FR4.3
  - id: BR4.2
    statement: Typed text that is empty or only spaces gives no suggestions.
    category: validation
    applies_to: ArtistCatalog.suggest
    trigger: suggestion lookup
    logic: IF the normalised text has no words THEN return an empty list
    violation: n/a
    source: FR4.5
  - id: BR4.3
    statement: An artist matches when every typed word is the start of some word in its name.
    category: calculation
    applies_to: ArtistCatalog.suggest
    trigger: suggestion lookup
    logic: split the normalised text into words; match artists where each typed word starts at least one word of the normalised name; "henry thr" matches "Henry Threadgill"
    violation: n/a
    source: FR4.1
  - id: BR4.4
    statement: Matches are ordered closest first in four steps, then by listeners.
    category: policy
    applies_to: ArtistCatalog.suggest
    trigger: ordering suggestions
    logic: tier 0 the normalised name equals the normalised text; tier 1 the name starts with the text; tier 2 every typed word starts a name word; within a tier more listeners first, then name ascending, then id ascending so the order never changes between runs
    violation: n/a
    source: FR4.2, functional-design-questions Q1
  - id: BR4.5
    statement: A suggestion lookup returns at most 10 artists.
    category: constraint
    applies_to: ArtistCatalog.suggest
    trigger: suggestion lookup
    logic: limit defaults to 10 and is capped at 10 (contract C1)
    violation: a larger request is capped, not refused
    source: FR4.1
  - id: BR4.6
    statement: Each suggestion carries the name, the genres in rank order (so the first genre is the top one) and the description when there is one; same-name artists are separate suggestions.
    category: policy
    applies_to: ArtistCatalog.suggest
    trigger: suggestion lookup
    logic: return ArtistSummary for each match; a description of none stays none, never an empty placeholder; artists are told apart by id, not name
    violation: n/a
    source: FR4.4
  - id: BR4.7
    statement: No match returns an empty list; the "No artists match" message is shown by the caller.
    category: policy
    applies_to: ArtistCatalog.suggest
    trigger: suggestion lookup
    logic: IF nothing matches THEN return []
    violation: n/a
    source: FR4.5
  - id: BR4.8
    statement: The search table is built in the catalogue step from the normalised names of the kept artists.
    category: policy
    applies_to: SearchEntry
    trigger: catalogue build
    logic: one SearchEntry per Artist, normalised by BR4.1, stored in artist_search (contract C2)
    violation: n/a
    source: contract C2
  - id: BR5.1
    statement: The index ranks by cosine similarity, exactly, highest first, without the artist itself.
    category: calculation
    applies_to: Neighbour
    trigger: index build and neighbour lookup
    logic: scale each vector to length 1; score = inner product = cosine; exact search over all artists; sort descending; drop sourceMbid
    violation: n/a
    source: FR5.1, NFR1
  - id: BR5.2
    statement: The id file and the index agree, and every indexed artist is in the catalogue.
    category: constraint
    applies_to: SimilarityIndex
    trigger: end of the index build
    logic: line n of artist_ids.txt is index row n; every id is in artists.sqlite; the number of ids equals the number of index rows
    violation: stop without writing the manifest, naming the first id that is missing
    source: contract C2
  - id: BR5.3
    statement: At full size, 95% of 100 lookups of different artists answer in under 200 ms, for similar artists and for suggestions.
    category: constraint
    applies_to: SimilarityIndex, ArtistCatalog
    trigger: the speed check command, run on the owner's machine after a full build
    logic: pick 100 different artists; time one lookup each of neighbours and suggest; compute the 95th percentile; pass when under 200 ms; print the numbers
    violation: report fail with the measured 95th percentile; the check is not part of the default test run
    source: NFR1
  - id: BR5.4
    statement: The full-size index build reads the vectors in batches and does not hold them as Python lists.
    category: constraint
    applies_to: SimilarityIndex
    trigger: index build
    logic: read vector files as arrays batch by batch into the index
    violation: n/a
    source: FR2.2
  - id: BR5.5
    statement: An unknown artist id is reported as unknown, distinct from an artist with no neighbours.
    category: validation
    applies_to: SimilarityIndex
    trigger: neighbour lookup
    logic: IF the id is not in the index THEN raise UnknownArtist; IF it has no neighbours THEN return an empty list with no more pages
    violation: unknown id reaches the web app as a 404
    source: FR5.7, FR5.8
  - id: BR6.1
    statement: Built files are written under a temporary name and renamed when complete.
    category: constraint
    applies_to: BuildManifest
    trigger: end of every step
    logic: write to a temporary name, then rename
    violation: an interrupted step leaves the old file or no file, never half a file
    source: contract C2
  - id: BR6.2
    statement: The steps run in a fixed order: prepare, train, catalogue, index.
    category: policy
    applies_to: pipeline
    trigger: the owner runs the steps
    logic: prepare reads the dumps; train reads prepare; catalogue reads prepare and the MusicBrainz dump; index reads train and catalogue and writes the manifest last
    violation: see BR6.3
    source: FR7.1
  - id: BR6.3
    statement: A step stops with a clear message when the step before it has not been run.
    category: validation
    applies_to: pipeline
    trigger: start of train, catalogue and index
    logic: IF the previous step's marker is missing THEN stop, naming the missing input and the step that builds it; write nothing
    violation: message such as "Missing the trained vectors; run the train step first"
    source: FR7.2
  - id: BR6.4
    statement: A step refuses to use an input that was made before a newer run of its earlier step.
    category: validation
    applies_to: pipeline
    trigger: start of train, catalogue and index
    logic: each marker stores the run id of the marker it read; IF the input's marker is not the one this step expects THEN stop, naming the step to re-run
    violation: message naming the stale input and the step to run again
    source: FR7.2
  - id: BR6.5
    statement: The rebuild steps are documented in order, each with its command, input, output and a check that it worked.
    category: policy
    applies_to: project documentation
    trigger: always
    logic: the README has a section "Rebuild from a new dump" listing the four steps, then the start command and the speed check
    violation: n/a
    source: FR7.1
  - id: BR6.6
    statement: The manifest is written last, so an interrupted rebuild leaves the app unable to start.
    category: constraint
    applies_to: BuildManifest
    trigger: end of the index step
    logic: write artists.sqlite, the index and the id file first, then the manifest; remove the old manifest before starting a rebuild of the index
    violation: the app refuses to start and names the step to run
    source: contract C2, NFR2
```

| Rule | Summary |
|------|---------|
| BR1.1–BR1.9 | Data location checks, read-only dumps, skipping and counting bad lines and entries, anonymous counts, summed repeats, 5-listener cutoff, run report, git-ignored output |
| BR2.1–BR2.4 | One vector per kept artist, current app's settings, memory limit, training without the dump |
| BR3.1–BR3.5 | Artist details, name choice, description, ranked genres, artists missing from MusicBrainz kept |
| BR4.1–BR4.8 | Case and accent-blind word-prefix search, four-tier ordering, 10 results, suggestion contents, empty list for no match |
| BR5.1–BR5.5 | Exact cosine ranking, id and row agreement, 200 ms check, batch build, unknown vs no neighbours |
| BR6.1–BR6.6 | Atomic files, fixed step order, missing and stale input checks, documented runbook, manifest last |

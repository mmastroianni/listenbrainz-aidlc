# Business Rules — u1-skeleton

Sources: `inception/requirements-analysis/requirements.md`, `inception/user-stories/stories.md`, `inception/contract-design/contract-summary.md`, `inception/domain-design/components.md`, `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`, and `functional-design-questions.md`.

```yaml
rules:
  - id: BR1.1
    statement: The data location comes from one setting and must point at a folder containing the listening dump.
    category: validation
    applies_to: DumpLocation
    trigger: start of any pipeline step
    logic: IF the setting is missing OR the listening dump file is absent THEN stop
    violation: stop with a message naming the setting and the missing file; write nothing
    source: FR1.1
  - id: BR1.2
    statement: Dump files are only ever opened for reading.
    category: constraint
    applies_to: DumpSource
    trigger: any dump access
    logic: IF code opens a dump file THEN it opens it read-only
    violation: not reachable; any write attempt is a defect caught by tests
    source: FR1.1
  - id: BR1.3
    statement: The skeleton reads only the first 5,000 listener lines.
    category: policy
    applies_to: ListenerRecord
    trigger: skeleton data preparation
    logic: IF 5,000 lines have been read THEN stop reading
    violation: n/a
    source: functional-design-questions Q1
  - id: BR1.4
    statement: Prepared data keeps only the listener number, artist id and listen count.
    category: constraint
    applies_to: ListenCount
    trigger: writing prepared data
    logic: FOR each entry keep (userId, artistMbid, listenCount) and nothing else about the listener
    violation: n/a
    source: FR1.2
  - id: BR1.5
    statement: Entries with no artist id or a listen count below 1 are skipped.
    category: validation
    applies_to: ListenerRecord entries
    trigger: data preparation
    logic: IF artistMbid is empty OR listenCount < 1 THEN skip the entry
    violation: entry dropped silently from output, counted in the run summary
    source: FR1.3
  - id: BR2.1
    statement: Training produces one vector per artist present in the prepared data.
    category: calculation
    applies_to: ArtistVector
    trigger: training
    logic: learn vectors with collaborative filtering on implicit listen counts; one vector per artistMbid
    violation: n/a
    source: FR2.1
  - id: BR3.1
    statement: Neighbours are ranked by cosine similarity, highest first, excluding the artist itself.
    category: calculation
    applies_to: Neighbour
    trigger: neighbour lookup
    logic: normalise vectors to unit length; score = inner product = cosine; sort descending; drop sourceMbid
    violation: n/a
    source: FR5.1
  - id: BR3.2
    statement: An unknown artist id is reported as unknown, distinct from an artist with no neighbours.
    category: validation
    applies_to: SimilarityIndex
    trigger: neighbour lookup
    logic: IF mbid not in the index THEN report UnknownArtist; IF it has no neighbours THEN return an empty list
    violation: unknown → 404 at the endpoint
    source: FR5.7, FR5.8
  - id: BR4.1
    statement: Built files are written under a temporary name and renamed when complete; the manifest is written last.
    category: constraint
    applies_to: BuildManifest
    trigger: end of each pipeline step
    logic: write to temp name THEN rename; write manifest after all other files
    violation: an interrupted run leaves no manifest, so the app refuses to start
    source: contract C2
  - id: BR4.2
    statement: The app refuses to start when a built file or the manifest is missing or the format version differs.
    category: validation
    applies_to: WebApp startup
    trigger: app start
    logic: IF any C2 file is missing OR formatVersion != expected THEN fail at startup
    violation: message naming the missing file or version and the pipeline step that builds it
    source: NFR2
  - id: BR4.3
    statement: The app starts with one documented command.
    category: policy
    applies_to: WebApp
    trigger: owner starts the app
    logic: one command starts the web app against the built files
    violation: n/a
    source: NFR2
  - id: BR5.1
    statement: The similar-artists endpoint returns ranked neighbours with their cosine scores and names.
    category: policy
    applies_to: WebApp
    trigger: GET similar artists for an mbid
    logic: ask SimilarityIndex for neighbours, then ArtistCatalog for names; return in rank order
    violation: unknown artist → 404
    source: FR5.1, contract C3
  - id: BR5.2
    statement: No response contains listener numbers or any listener data.
    category: constraint
    applies_to: WebApp responses
    trigger: every response
    logic: responses are built only from Artist and Neighbour fields
    violation: n/a
    source: FR5.9, NFR3
  - id: BR6.1
    statement: Prepared data and built files live in git-ignored folders.
    category: constraint
    applies_to: project layout
    trigger: always
    logic: data and model folders are listed in .gitignore
    violation: n/a
    source: NFR5
```

| Rule | Summary |
|------|---------|
| BR1.1–BR1.5 | Data location, read-only dumps, 5,000-line sample, anonymous listen counts, skip bad entries |
| BR2.1 | One vector per artist |
| BR3.1–BR3.2 | Cosine ranking without self; unknown vs no neighbours |
| BR4.1–BR4.3 | Atomic files, manifest last, startup checks, one start command |
| BR5.1–BR5.2 | Endpoint result, no listener data |
| BR6.1 | Data and models git-ignored |

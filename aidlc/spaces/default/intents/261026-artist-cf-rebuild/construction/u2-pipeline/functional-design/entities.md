# Entities — u2-pipeline

Entity ownership follows `inception/domain-design/components.md`; file shapes follow contract C2 in `inception/contract-design/contract-summary.md`. This is the full-size data model for the stories mapped to u2-pipeline in `inception/units-generation/unit-of-work-story-map.md` (`inception/user-stories/stories.md`), under `inception/requirements-analysis/requirements.md`. It extends the skeleton's model (`construction/u1-skeleton/functional-design/entities.md`) and keeps the C1 and C2 shapes unchanged. Choices come from `functional-design-questions.md` (Q1, Q2) and from the current app in `../listenbrainz`.

```yaml
entities:
  - name: DumpLocation
    owner: DumpSource
    description: Where the dumps live; read-only.
    attributes:
      - { name: path, type: path, required: true, constraints: "must exist and contain every expected dump file" }
      - { name: listeningDumpFile, type: path, required: true, default: "lbdump/statistics/artists_all_time.jsonl under path" }
      - { name: musicbrainzFiles, type: "list of path", required: true, constraints: "the artist, artist_tag, tag and genre tables of the MusicBrainz dump" }
  - name: ListenerRecord
    owner: ListeningDataPrep
    description: One line of the listening dump, transient (never stored).
    attributes:
      - { name: userId, type: integer, required: true, constraints: "the dump's own listener number" }
      - { name: entries, type: "list of {artistMbid, artistName, listenCount}", required: true }
  - name: ListenCount
    owner: ListeningDataPrep
    description: Anonymous listener-artist listen count, after skipping, summing repeats and the 5-listener cutoff.
    attributes:
      - { name: listenerNumber, type: integer, required: true, constraints: "the dump's userId; no other listener detail" }
      - { name: artistMbid, type: string, required: true, constraints: "kept exactly as in the dump" }
      - { name: listenCount, type: integer, required: true, min: 1 }
    constraints: ["(listenerNumber, artistMbid) is unique", "every artistMbid has at least 5 distinct listenerNumbers"]
  - name: ArtistName
    owner: ListeningDataPrep
    description: The one name chosen for each kept artist from the spellings in the listening dump.
    attributes:
      - { name: artistMbid, type: string, required: true, unique: true }
      - { name: name, type: string, required: true, constraints: "the spelling used by the most listeners; ties broken alphabetically" }
  - name: PrepReport
    owner: ListeningDataPrep
    description: What one prepare run did; printed and stored next to the prepared data.
    attributes:
      - { name: runId, type: string, required: true, unique: true }
      - { name: runTimestamp, type: timestamp (UTC), required: true }
      - { name: validRecords, type: integer, required: true, min: 0, constraints: "listener lines processed" }
      - { name: skippedRecords, type: integer, required: true, min: 0, constraints: "whole lines that were malformed" }
      - { name: skippedEntries, type: integer, required: true, min: 0, constraints: "single artist entries with no artist id or a count below 1; added beside the catalogue's PrepReport fields" }
      - { name: keptArtists, type: integer, required: true, min: 0 }
  - name: ArtistVector
    owner: SimilarityTraining
    attributes:
      - { name: artistMbid, type: string, required: true, unique: true }
      - { name: vector, type: "list of float", required: true, constraints: "fixed length (64) for the run" }
  - name: Artist
    owner: ArtistCatalog
    description: Everything the app shows about a kept artist.
    attributes:
      - { name: mbid, type: string, required: true, unique: true }
      - { name: name, type: string, required: true, constraints: "from ArtistName" }
      - { name: description, type: string, required: false, default: null, constraints: "MusicBrainz short description; blank counts as none" }
      - { name: listenerCount, type: integer, required: true, min: 5, constraints: "distinct listeners" }
      - { name: genres, type: "list of string", required: true, default: [], constraints: "ordered by ArtistGenre rank; may be empty" }
    constraints: ["an artist missing from MusicBrainz is still an Artist, with no description and no genres"]
  - name: ArtistGenre
    owner: ArtistCatalog
    attributes:
      - { name: mbid, type: string, required: true, references: Artist }
      - { name: genre, type: string, required: true, constraints: "lower-case, trimmed; on MusicBrainz's list of recognised genres" }
      - { name: votes, type: integer, required: true, min: 1 }
      - { name: rank, type: integer, required: true, min: 1, constraints: "1 is the most voted; ties broken alphabetically" }
    constraints: ["(mbid, genre) is unique", "(mbid, rank) is unique"]
  - name: SearchEntry
    owner: ArtistCatalog
    description: The searchable form of an artist's name.
    attributes:
      - { name: mbid, type: string, required: true, unique: true, references: Artist }
      - { name: normalisedName, type: string, required: true, constraints: "lower-case, accent-free, punctuation turned to spaces, spaces collapsed" }
  - name: Neighbour
    owner: SimilarityIndex
    attributes:
      - { name: sourceMbid, type: string, required: true }
      - { name: neighbourMbid, type: string, required: true, constraints: "never equal to sourceMbid" }
      - { name: cosine, type: float, required: true, min: -1, max: 1 }
      - { name: rank, type: integer, required: true, min: 1 }
  - name: StepMarker
    owner: SimilarityIndex
    description: A small file each pipeline step writes when it finishes, so the next step can check its input.
    attributes:
      - { name: step, type: "prepare | train | catalogue | index", required: true }
      - { name: runId, type: string, required: true }
      - { name: inputRunId, type: string, required: false, constraints: "the runId of the step it read; empty for prepare" }
      - { name: completedAt, type: timestamp (UTC), required: true }
  - name: BuildManifest
    owner: SimilarityIndex
    description: The C2 manifest, written last.
    attributes:
      - { name: formatVersion, type: integer, required: true, default: 1 }
      - { name: builtAt, type: timestamp (UTC), required: true }
      - { name: sourceDump, type: string, required: true }
      - { name: artistCount, type: integer, required: true, min: 1 }
relationships:
  - "Artist 1 — 0..1 ArtistVector (by mbid; an artist whose vector had zero length has none)"
  - "Artist 1 — 0..many ArtistGenre"
  - "Artist 1 — 1 SearchEntry"
  - "Artist 1 — 1 ArtistName"
  - "ArtistVector 1 — many Neighbour (as source)"
  - "ListenCount many — 1 Artist (by artistMbid)"
```

The full-size model has 13 entities. ListenerRecord is transient. ArtistName is an intermediate file between prepare and the catalogue step. StepMarker and BuildManifest are the only entities that describe the build rather than the music. `skippedEntries` is a new optional PrepReport field; the owning component's catalogue entry lists the other three.

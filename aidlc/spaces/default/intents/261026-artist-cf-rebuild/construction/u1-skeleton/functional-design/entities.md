# Entities — u1-skeleton

Entity ownership follows `inception/domain-design/components.md`. Shapes follow contract C2 in `inception/contract-design/contract-summary.md`. Scope is the skeleton only (`inception/units-generation/unit-of-work.md`, U1), covering the stories mapped to U1 in `inception/units-generation/unit-of-work-story-map.md` and `inception/user-stories/stories.md`, under `inception/requirements-analysis/requirements.md`.

```yaml
entities:
  - name: DumpLocation
    owner: DumpSource
    description: Where the dumps live; read-only.
    attributes:
      - { name: path, type: path, required: true, constraints: "must exist and contain the listening dump file" }
      - { name: listeningDumpFile, type: path, required: true, default: "lbdump/statistics/artists_all_time.jsonl under path" }
  - name: ListenerRecord
    owner: ListeningDataPrep
    description: One line of the listening dump, transient (never stored).
    attributes:
      - { name: userId, type: integer, required: true, constraints: "the dump's own listener number" }
      - { name: entries, type: list of {artistMbid, artistName, listenCount}, required: true }
  - name: ListenCount
    owner: ListeningDataPrep
    description: Anonymous listener-artist listen count.
    attributes:
      - { name: listenerNumber, type: integer, required: true, constraints: "the dump's userId; no other listener detail" }
      - { name: artistMbid, type: string, required: true, constraints: "kept exactly as in the dump" }
      - { name: listenCount, type: integer, required: true, min: 1 }
    constraints: ["(listenerNumber, artistMbid) is unique"]
  - name: ArtistVector
    owner: SimilarityTraining
    attributes:
      - { name: artistMbid, type: string, required: true, unique: true }
      - { name: vector, type: list of float, required: true, constraints: "fixed length for the run" }
  - name: Artist
    owner: ArtistCatalog
    description: Skeleton subset of the catalogue entity.
    attributes:
      - { name: mbid, type: string, required: true, unique: true }
      - { name: name, type: string, required: true, constraints: "from the listening dump" }
      - { name: description, type: string, required: false, default: null, constraints: "filled by u2-pipeline" }
      - { name: listenerCount, type: integer, required: true, min: 1 }
      - { name: genres, type: list of string, required: true, default: [], constraints: "filled by u2-pipeline" }
  - name: Neighbour
    owner: SimilarityIndex
    attributes:
      - { name: sourceMbid, type: string, required: true }
      - { name: neighbourMbid, type: string, required: true, constraints: "never equal to sourceMbid" }
      - { name: cosine, type: float, required: true, min: -1, max: 1 }
      - { name: rank, type: integer, required: true, min: 1 }
  - name: BuildManifest
    owner: SimilarityIndex
    description: The C2 manifest written last by the pipeline.
    attributes:
      - { name: formatVersion, type: integer, required: true, default: 1 }
      - { name: builtAt, type: timestamp (UTC), required: true }
      - { name: sourceDump, type: string, required: true }
      - { name: artistCount, type: integer, required: true }
relationships:
  - "Artist 1 — 0..1 ArtistVector (by mbid)"
  - "ArtistVector 1 — many Neighbour (as source)"
  - "ListenCount many — 1 Artist (by artistMbid)"
```

The skeleton has seven entities. ListenerRecord is transient. Artist's description and genres stay empty until u2-pipeline fills them. BuildManifest is placed with SimilarityIndex because the index build is the last pipeline step, and the manifest is written after it.

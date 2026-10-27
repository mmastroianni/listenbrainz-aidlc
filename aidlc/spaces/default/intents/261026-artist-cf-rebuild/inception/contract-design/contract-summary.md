# Contract Summary

Sources: the units and their dependencies (`inception/units-generation/unit-of-work.md`, `unit-of-work-dependency.md`), the components and entities (`inception/domain-design/components.md`), the requirements (`inception/requirements-analysis/requirements.md`), and `contract-design-questions.md` (Q1 to Q3).

## Contracts

| # | Provider Unit | Consumer | Mechanism | Owner |
|---|---------------|----------|-----------|-------|
| C1 | U1 u1-skeleton (ArtistCatalog and SimilarityIndex interfaces) | U2 u2-pipeline, U3 u3-web | In-process Python interfaces (shared schema) | U1 |
| C2 | U2 u2-pipeline (built files) | U3 u3-web (read at startup) | Shared files on disk with a manifest | U2 |
| C3 | U3 u3-web (HTTP endpoints) | External: the app's own web page in the browser | Synchronous HTTP/JSON | U3 |

## C1 — Catalogue and Index Interfaces

U1 defines these interfaces. U2 fills in the full behaviour, and U3 calls them. Artist ids are MusicBrainz ids (strings, kept exactly as given).

```yaml
shared-schema: C1
version: 1
interfaces:
  ArtistCatalog:
    suggest:
      input: { text: string, limit: int (default 10, max 10) }
      output: list of ArtistSummary, closest text match first then listenerCount descending
      rules: [case and accent insensitive (FR4.3), whitespace-only text returns [] (FR4.5)]
    get_many:
      input: { mbids: list of string }
      output: map of mbid to ArtistSummary; unknown mbids are absent from the map
    get:
      input: { mbid: string }
      output: ArtistSummary or none
  SimilarityIndex:
    neighbours:
      input: { mbid: string, offset: int >= 0, limit: int 1..100 }
      output: { items: list of { mbid: string, cosine: float }, has_more: bool }
      rules:
        - ordered by cosine descending; the queried artist is never in items (FR5.1)
        - unknown mbid raises UnknownArtist (FR5.8)
        - an artist with no neighbours returns items [] and has_more false (FR5.7)
types:
  ArtistSummary:
    mbid: string
    name: string
    description: string or null
    listener_count: int
    genres: list of string (may be empty)
```

## C2 — Built Files

The pipeline commands write these files into a models folder outside git (hard rule). The web app reads them at startup.

```yaml
shared-schema: C2
format_version: 1
location: one setting, default models/ in the project folder (git-ignored)
files:
  manifest.json:
    fields: { format_version: int, built_at: ISO-8601 UTC timestamp, source_dump: string, artist_count: int }
    rule: the app refuses to start when the file is missing or format_version differs from the version the code expects, naming the pipeline step to re-run (Q2, NFR2)
  artists.sqlite:
    tables:
      artist: { mbid: text primary key, name: text, description: text null, listener_count: integer }
      artist_genre: { mbid: text, genre: text, rank: integer }
      artist_search: name search table over normalised (lower-case, accent-free) names
  artists.faiss:
    content: inner-product index over L2-normalised artist vectors, so scores are cosine similarity
  artist_ids.txt:
    content: one mbid per line, line n is index row n
rules:
  - files contain no listener names or listener-level data (NFR3)
  - every mbid in artist_ids.txt is present in artists.sqlite
  - files are written to a temporary name and renamed when complete, so the app never reads a half-written file
```

## C3 — HTTP Endpoints

Used only by the app's own page (Q3).

```yaml
openapi: 3.0.3
info: { title: Similar Artists, version: "1" }
paths:
  /api/suggest:
    get:
      parameters:
        - { name: q, in: query, required: true, schema: { type: string, maxLength: 200 } }
      responses:
        "200":
          description: up to 10 suggestions; empty list for no match or whitespace-only q
          content: { application/json: { schema: { type: array, items: { $ref: "#/components/schemas/ArtistSummary" } } } }
  /api/artists/{mbid}/similar:
    get:
      parameters:
        - { name: mbid, in: path, required: true, schema: { type: string } }
        - { name: offset, in: query, schema: { type: integer, minimum: 0, default: 0 } }
        - { name: limit, in: query, schema: { type: integer, minimum: 1, maximum: 100, default: 20 } }
      responses:
        "200":
          description: a page of similar artists; items empty when there is not enough data
          content:
            application/json:
              schema:
                type: object
                properties:
                  artist: { $ref: "#/components/schemas/ArtistSummary" }
                  items:
                    type: array
                    items:
                      type: object
                      properties:
                        artist: { $ref: "#/components/schemas/ArtistSummary" }
                        cosine: { type: number }
                        bar: { type: number, description: "cosine / top cosine of this artist's list, 0..1" }
                        links: { type: object, properties: { musicbrainz: { type: string }, youtube: { type: string }, spotify: { type: string } } }
                  has_more: { type: boolean }
        "404": { description: unknown artist }
        "422": { description: invalid offset or limit }
  /:
    get: { responses: { "200": { description: the page (HTML) } } }
  /artist/{mbid}:
    get: { responses: { "200": { description: the page (HTML), loads that artist's results } } }
components:
  schemas:
    ArtistSummary:
      type: object
      properties:
        mbid: { type: string }
        name: { type: string }
        description: { type: string, nullable: true }
        genres: { type: array, items: { type: string } }
```

Responses never include listener data (FR5.9). Errors return a short JSON message and no stack trace (FR6.5).

## Contract Ownership Rules

- **C1** is owned by U1. U2 and U3 change it only by agreement recorded in the unit's Functional Design. Adding optional fields or methods is safe; removing or renaming them is a breaking change.
- **C2** is owned by U2. Any change to file layout bumps `format_version`, and the app then refuses to start until the files are rebuilt (Q2).
- **C3** is owned by U3. It changes together with the page; consumers ignore unknown fields.
- Timeouts and retries: C1 and C2 are in-process and local, so they have none. In C3 the page retries a failed request only when the user presses Retry (interaction spec).

## Open Questions

| Contract | Question | Blocks |
|----------|----------|--------|
| — | None | — |

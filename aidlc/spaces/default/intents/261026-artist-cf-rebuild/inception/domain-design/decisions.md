# Architecture Decisions — Domain Design

Sources: `inception/requirements-analysis/requirements.md`, `inception/user-stories/stories.md`, `inception/practices-discovery/team-practices.md`, `domain-design-questions.md`. Components are in `components.md`.

## ADR-001: Six components along the data flow

## Status: Accepted

- **Context** — The work splits into batch steps (read dumps, prepare data, train, build index) and a serving side (search, lookup, page). The owner rebuilds from new dumps step by step (FR7.1) and works solo.
- **Decision** — Six components: DumpSource, ListeningDataPrep, SimilarityTraining, ArtistCatalog, SimilarityIndex, WebApp.
- **Consequences** — Each rebuild step maps to one component, which keeps the runbook and tests simple. Six pieces is more structure than a single script, but each stays small.
- **Alternatives Rejected** — (1) One pipeline component plus one app: simpler, but mixes listener handling with artist data and makes partial re-runs hard. (2) Finer split (separate genre and description components): no distinct lifecycle to justify it.
- **Security and compliance** — Listener identities only ever exist inside ListeningDataPrep (NFR3).

## ADR-002: Name search lives in ArtistCatalog

## Status: Accepted

- **Context** — Suggestions need names, descriptions, genres and listener counts, all owned by the catalogue (FR4.1 to FR4.5).
- **Decision** — Search is a query inside ArtistCatalog (Q1 A).
- **Consequences** — One copy of artist names; search and details change together. Search cannot be scaled separately, which a local single-user app does not need.
- **Alternatives Rejected** — A separate search component with its own copy of names (Q1 B): independent evolution, but two copies must be kept in step for no current benefit.
- **Security and compliance** — No listener data is involved.

## ADR-003: Data preparation and training are separate

## Status: Accepted

- **Context** — Reading the 20+ GB dump is slow; training settings may change more often (FR2.1, FR7.1).
- **Decision** — ListeningDataPrep and SimilarityTraining are separate components (Q2 A), connected by the prepared listen counts.
- **Consequences** — Training can be re-run without re-reading the dump, and each is its own runbook step. The prepared data must be stored between steps (outside git, NFR5).
- **Alternatives Rejected** — One combined component (Q2 B): fewer pieces, but every training change re-reads the dump.
- **Security and compliance** — The stored listen counts hold only internal listener numbers (FR1.2).

## ADR-004: WebApp composes results; SimilarityIndex knows only ids and scores

## Status: Accepted

- **Context** — A result needs neighbours and scores plus details and links (FR5.1 to FR5.3).
- **Decision** — WebApp asks SimilarityIndex for neighbour ids and cosine scores, then ArtistCatalog for details (Q3 A).
- **Consequences** — The index stays pure and fast to test against the 200 ms target (NFR1); the catalogue and index never depend on each other. WebApp makes two calls per result page.
- **Alternatives Rejected** — The index returns detailed results (Q3 B): one call, but couples the index to the catalogue and mixes speed-critical and display code.
- **Security and compliance** — WebApp is the single point that checks no listener data leaves the system (FR5.9).

## ADR-005: All dump access goes through DumpSource

## Status: Accepted

- **Context** — A hard rule forbids modifying, moving or writing into the dumps; both ListeningDataPrep and ArtistCatalog read them (FR1.1).
- **Decision** — DumpSource is the only component that opens dump files, and it opens them read-only.
- **Consequences** — The rule is enforced and tested in one place, and so are the missing-file messages. Other components cannot read dumps directly.
- **Alternatives Rejected** — Each component reads the dumps itself: fewer pieces, but the read-only guarantee and location setting would be duplicated.
- **Security and compliance** — Enforces the read-only hard rule.

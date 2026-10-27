# Units of Work

Built from the component catalogue and ADRs (`inception/domain-design/components.md`, `decisions.md`), the requirements (`inception/requirements-analysis/requirements.md`), the stories (`inception/user-stories/stories.md`) and `units-generation-questions.md` (Q1, Q2, plan approved). The walking skeleton is on, so U1 is the thin end-to-end slice.

## Units

| Unit ID | Directory | Kind | Complexity | Deployment |
|---------|-----------|------|-----------|-----------|
| U1 | u1-skeleton | service | M | Embedded: becomes the base of the web app process and the pipeline commands |
| U2 | u2-pipeline | library | L | Pipeline commands run by hand in documented order |
| U3 | u3-web | service | M | The one web app process |

## U1 — u1-skeleton

**Description:** the smallest working slice through every component, on a small sample of the dump.

**Boundaries and responsibilities:**
- Project scaffold: `src/` package, `pyproject.toml` with uv, ruff, ty, pytest, pytest-cov; the pre-merge check command; `.gitignore` for data and model files; the GitHub Actions workflow file, switched off.
- DumpSource: the data-location setting, read-only opening, missing-file errors (FR1.1).
- ListeningDataPrep: minimal read of a sample of the listening dump into anonymous listen counts (FR1.2).
- SimilarityTraining: tiny collaborative-filtering model on the sample (FR2.1).
- SimilarityIndex: nearest-neighbour index with cosine scores (FR5.1).
- ArtistCatalog: names only, enough to label results.
- WebApp: one endpoint that returns similar artists for an artist id, and a startup check (NFR2).

**Implementation notes:** runs on fixture or sample data only; proves the pieces connect. The Construction Verification Command (chosen by the owner during Construction) runs the slice end to end.

## U2 — u2-pipeline

**Description:** the full batch side: everything needed to rebuild the real data from a new dump.

**Boundaries and responsibilities:**
- ListeningDataPrep: malformed-record skipping and counting, 5-listener cutoff, PrepReport (FR1.2 to FR1.4).
- SimilarityTraining: full-size training within 32 to 64 GB (FR2.2).
- ArtistCatalog: names, MusicBrainz descriptions, listener counts and genre tags (FR3.1, FR3.2); name search ignoring case and accents, ordered by match then listeners (FR4.1 to FR4.5).
- SimilarityIndex: full-size build; lookups under 200 ms (NFR1).
- Rebuild runbook and step-order checks (FR7.1, FR7.2).

**Implementation notes:** written test-after on fixture data (team practices); never writes to the dumps or commits data (hard rules).

## U3 — u3-web

**Description:** the full one-page site.

**Boundaries and responsibilities:**
- WebApp endpoints for suggestions and paged similar artists; composing index scores with catalogue details (ADR-004).
- The page: search with suggestions, results with bars (cosine on hover), genres, MusicBrainz/YouTube/Spotify links, "Show more", click-to-explore, per-artist addresses, messages for no match, not enough data, unknown artist and errors, phone layout and keyboard use (FR5.x, FR6.x).
- The by-eye quality check against the current app (FR8.1).

**Implementation notes:** written test-first (team practices); follows `inception/refined-mockups/`.

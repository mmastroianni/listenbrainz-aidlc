<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-27T00:55:00Z — u2-pipeline: moved the artist-file write out of the index step into its own catalogue step so the index step can check ids against the catalogue and the manifest stays last; C2 layout unchanged.
- 2026-10-27T00:55:00Z — u2-pipeline: added optional PrepReport field skippedEntries beside skippedRecords, to keep bad lines and bad entries apart.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-27T00:55:00Z — u2-pipeline: owner left Q1 (search tiers) and Q2 (artists missing from MusicBrainz) to me; chose the four-tier search and keep-everywhere, matching the current app for Q2.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->

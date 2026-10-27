# External Dependency Map

## Summary

A **Bolt** is one build pass over a piece of the work, ending in something that runs (see `bolt-plan.md`). Nothing outside the project can hold up a Bolt: the dumps, the current app and all tools are already on the owner's machine (`inception/requirements-analysis/requirements.md`, constraints).

## Dependencies

| Dependency | Owner | Lead time | Needed by | If it slips |
|-----------|-------|-----------|-----------|-------------|
| ListenBrainz and MusicBrainz dumps in `../listenbrainz` | Owner (already downloaded) | None | Bolt 1 (sample), Bolt 2 (full) | n/a |
| A Java runtime for Spark | Owner (already installed for the current app) | None | Bolt 1 | Install a JDK before Bolt 1 |
| The current app runnable, for the by-eye comparison | Owner | None | Bolt 3 | Compare against saved result lists instead |

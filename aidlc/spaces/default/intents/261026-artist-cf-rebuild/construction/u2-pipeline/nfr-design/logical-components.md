# Logical Components — u2-pipeline

Bridges the NFR requirements (`construction/u2-pipeline/nfr-requirements/security-requirements.md`, `tech-stack-decisions.md`) with the components in `inception/domain-design/components.md` and the functional design in `construction/u2-pipeline/functional-design/functional-spec.md`. u2-pipeline is a library unit, so the performance, scalability, reliability and observability designs are written below instead of in files of their own. The project is local, so there is no infrastructure beyond the machine.

## Components

| Logical component | Runs as | Failure domain | Where NFR patterns apply |
|-------------------|---------|----------------|--------------------------|
| Prepare command | One process (Spark local) | Its own run; writes under temporary names and leaves the earlier files if it fails | Read-only dump access; counts-only output; bad line and entry counts inside Spark; step summary |
| Train command | One process (Spark local) | Its own run | Marker check; memory setting; atomic writes; step summary |
| Catalogue command | One process (Spark for the MusicBrainz tables, then Python and SQLite) | Its own run | Marker check; popularity numbering; atomic write of `artists.sqlite`; step summary |
| Index command | One process (Python, FAISS) | Its own run; removes the old manifest first, writes the new one last | Marker and consistency checks; batch reading; atomic writes; step summary |
| Speed command | One process, started by hand after a full build | Its own run; read-only | Timing of 100 lookups of each kind; prints two 95th percentiles and pass or fail |
| Catalogue module | Library inside the web app process | The web app process | Name search over the sorted name index and the search table; bound parameters |
| Index module | Library inside the web app process | The web app process | Exact search over the in-memory index; unknown id and no-neighbour answers |
| Built files folder (git-ignored) | Shared folder on disk | The disk | Written by commands, read-only to the web app |

**Blast radius:** a failed command never damages the dumps or the last good files, and never leaves a manifest that points at half-built files. A rebuild in progress makes the web app refuse to start (the manifest is gone), which is intended. **Shared resource:** the built files folder is the only thing the processes share.

## Performance design (NFR1.5 to NFR1.9)

- **Similar artists (NFR1.5):** the exact inner-product index over unit-length vectors, loaded once and kept in memory by the web app. The full-size check decides whether it is fast enough; only if it fails does a later change consider an approximate index, and that would change this design.
- **Suggestions (NFR1.6):** the catalogue step sorts the kept artists by listener count (most first), then name, then id, and gives each a popularity number starting at 1. That number is the row number of the full-text search table and the key of a sorted name index. Three queries then run, each stopping early:
  - Tier 0: the sorted name index where the normalised name equals the text, in popularity order.
  - Tier 1: the sorted name index over the range of names that start with the text, in popularity order, stopping after 10 rows.
  - Tier 2: the full-text search for every typed word as a word start, read in row-number order, which is popularity order, stopping after 10 rows.
  The results are merged tier by tier, dropping artists already returned, until 10 are collected. Because every query returns rows in the final within-tier order, the first 10 rows are the right ones and nothing is sorted at lookup time. This keeps even one-letter texts fast.
- **Memory (NFR1.7):** the Spark driver memory has one setting with a default of 24 GB, set before the session starts. Prepare keeps its tables in Spark. Training reads Parquet and writes Parquet. The index step reads the vector files with a Parquet reader in batches, scales each batch to unit length, drops zero-length vectors and adds the batch to the index, so the vectors are never held as a Python list.
- **Time (NFR1.8):** nothing is tuned for duration; each step reports it.
- **Fixture guard (NFR1.9):** a test runs the same two lookups on the fixture build and expects each under 200 ms.

## Scalability design (NFR8.6, NFR1.10)

- Each command is one process and the owner runs them one at a time; there is no queue or lock between them beyond the marker check.
- The catalogue file and the index are read-only once built. The web app opens one read-only SQLite connection per request and shares the in-memory index, so five lookups at once need no locking.
- Prepare reads the listening file with an explicit column layout rather than guessing it, and does its counting and filtering in Spark, so growth in the dump is a longer run, not a larger Python memory footprint.

## Reliability design (NFR2.8 to NFR2.12)

- **Markers (NFR2.8):** every step writes a small marker file as its last act. It holds the step name, a run id, the run id of the marker it read, and the time. A step checks that its input marker exists (missing input) and that its recorded input run id matches the marker the earlier step wrote (stale input), and stops naming the step to run.
- **Atomic writes (NFR2.9, NFR2.10):** a step writes a folder or file under a temporary name beside the target and renames it when complete, replacing the old one only then. The index step first removes the manifest, then writes the index, the id file and finally the manifest.
- **Errors (NFR2.11):** file and Parquet reads, SQLite opens and Spark failures are caught at the step's top level and shown as one message naming the file or setting; unexpected errors keep their stack trace in the console. Two failure paths per step are tested.
- **Memory stop (NFR2.12):** a Spark out-of-memory error is caught and replaced by a message naming the memory setting to raise.
- **Recovery:** re-run the steps in order; nothing else needs backing up.

## Observability design (NFR2.13 to NFR2.15)

- Standard Python logging to the console. Each step ends with one summary line built from counts only: rows read, lines skipped, entries skipped, artists kept, output files and duration.
- The prepare report is saved as a small JSON file next to the prepared data and read back by a test.
- The speed command prints, for each lookup kind, the number of lookups, the 95th percentile in milliseconds and pass or fail against 200 ms.
- No dashboards, alerts or tracing: the app is local and the Operation phase is skipped.

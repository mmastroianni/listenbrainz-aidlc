# NFR Design (u2-pipeline) — Questions

Context: the targets are set (`construction/u2-pipeline/nfr-requirements/`) and the stack is fixed, so no new questions were needed. Please confirm the design choices below.

## Consolidated Summary Confirmation

- Suggestion speed: the catalogue numbers artists by listeners (most first) and uses that number as the search table's row number, so any search returns its matches already in listener order and can stop after a few hundred rows. Exact-name and starts-with matches use a separate sorted name index, so a rare exact match is never missed.
- Similar-artist speed: the exact index, loaded once and kept in memory; its length is checked by the speed command, and an approximate index is considered only if that check fails.
- Memory: Spark's memory setting defaults to 24 GB and can be changed in one place; the prepare step counts bad lines and entries inside Spark rather than collecting them; the index step reads vectors from the Parquet files in batches and adds each batch to the index.
- Security: only counts leave the prepare step's logs; each built file is checked by tests for listener fields; the dump folder is opened read-only through one function; typed search text is normalised to letters and digits before it reaches a query.
- Scale: one process per step, one at a time; read-only catalogue and index, so five lookups at once need no locks.
- Reliability: each step writes to a temporary name and renames; each marker records the run it read, so a step refuses stale or missing input; the index step removes the old manifest first and writes the new one last.
- Observability: one summary line per step through standard logging, the stored prepare report, and a speed command that prints both 95th percentiles.
- Logical components: four pipeline commands plus a speed command, and two library modules the web app calls; the built files folder is the only shared resource.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

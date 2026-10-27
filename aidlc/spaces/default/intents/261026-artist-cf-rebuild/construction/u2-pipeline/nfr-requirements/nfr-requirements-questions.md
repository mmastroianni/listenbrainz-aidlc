# NFR Requirements (u2-pipeline) — Questions

Context: every target for the full-size pipeline is already set by the requirements (NFR1 to NFR8, FR2.2), the team practices, the contracts and the skeleton's NFR requirements (`construction/u1-skeleton/nfr-requirements/`), so no new questions were needed. The owner's machine has 62 GB of memory and 20 processor cores (checked with `free` and `nproc`). Please confirm the targets below.

## Consolidated Summary Confirmation

- Speed: at full size, similar-artist lookups and suggestion lookups each answer in under 200 ms at the 95th percentile over 100 lookups of different artists, checked by a separate speed command. Training and preparation have no time limit; each step prints how long it took.
- Memory: training and the index build stay under 32 GB peak, the low end of the owner's 32 to 64 GB range; vectors are read in batches, never collected into Python lists.
- Security and privacy: no listener numbers in the catalogue, index files, manifest or step output; prepared data holds only listener number, artist and count; dumps opened read-only and unchanged after a run; no network calls and no Spark web page; data and models git-ignored.
- Scale: one local user; pipeline steps run one at a time; the 5-listener cutoff and streaming reads keep the full dump workable.
- Reliability: each step refuses missing or stale input with a message naming the step to run; files written whole and the manifest last; a failed step leaves earlier files usable.
- Observability: each step prints one summary line (rows read, skipped lines and entries, artists kept, output files, duration); the prepare report is stored; the speed command prints its numbers.
- Tech stack: unchanged from the skeleton (Python 3.12, uv, PySpark ALS, FAISS exact cosine, SQLite with its full-text search, FastAPI, Parquet, ruff, ty, pytest); no new runtime dependency.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

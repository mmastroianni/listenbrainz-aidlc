# NFR Requirements (u1-skeleton) — Questions

Context: every target for the skeleton is already set by the requirements, team practices and contracts, so no new questions were needed. Please confirm the targets below.

## Consolidated Summary Confirmation

- Speed: skeleton lookups under 200 ms (95th percentile, 100 lookups) on the sample; the full-size check stays in u2-pipeline; the skeleton build finishes in under 5 minutes.
- Security: no listener data in built files, responses or logs; dumps opened read-only; no network or paid services; data and models git-ignored; the app listens on 127.0.0.1 only; bad artist ids return 404 or 422, never a server error.
- Scale: one local user, 5 concurrent requests; steps stream the dump so u2 can scale to full size.
- Reliability: the app fails fast at startup naming any missing file or version mismatch; files are written atomically with the manifest last; each step refuses to run without its input.
- Observability: one summary line per pipeline step, console request logs, and a `/api/health` endpoint showing the build date.
- Tech stack: Python 3.12, uv, PySpark ALS, FAISS (cosine), SQLite, FastAPI and uvicorn, Parquet for interim data, ruff, ty, pytest; UMAP not added yet.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

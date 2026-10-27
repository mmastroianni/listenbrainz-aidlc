# NFR Design (u1-skeleton) — Questions

Context: the targets are set (`construction/u1-skeleton/nfr-requirements/`) and the stack is fixed, so no new questions were needed. Please confirm the design choices below.

## Consolidated Summary Confirmation

- Speed: load the SQLite file and FAISS index once at startup and keep them in memory; no cache layer is needed for one local user. FAISS runs an exact inner-product search, which is fast at skeleton size, and u2 revisits the index type if the full-size check needs it.
- Security: one input-validation layer at the web boundary (artist id format, paging limits); responses are built from an allow-list of fields, so listener data cannot leak; dump files are opened through one read-only function; the server binds to 127.0.0.1.
- Scale: pipeline steps stream and write in batches; the web app is stateless apart from the read-only loaded files.
- Reliability: fail-fast startup checks (files and manifest version); temp-name-then-rename writes with the manifest last; each step checks its input marker; no retries or circuit breakers, because there are no remote calls.
- Observability: standard Python logging, one summary line per pipeline step, a request log line per call (path, status, duration), and `/api/health` showing the build date.
- Logical components: pipeline commands (prepare, train, index) and one web app process, sharing the built files folder; the failure domain of each is its own process.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

# Scalability Design — u1-skeleton

Designs `construction/u1-skeleton/nfr-requirements/scalability-requirements.md` (NFR8.3, NFR1.4), using the functional spec (`construction/u1-skeleton/functional-design/functional-spec.md`), the tech stack decisions and `inception/contract-design/contract-summary.md`.

- **Concurrency (NFR8.3):** the web app holds only read-only loaded data, so concurrent requests share it safely. FastAPI runs the lookup handlers in its worker threadpool; each request opens its own SQLite read connection.
- **Data growth (NFR1.4):** prepare streams the dump and writes in batches; training and indexing read prepared data. No step needs the whole dump in memory.
- **Scaling out:** not needed in v1. The design leaves the door open because the app is stateless: another process could load the same files.

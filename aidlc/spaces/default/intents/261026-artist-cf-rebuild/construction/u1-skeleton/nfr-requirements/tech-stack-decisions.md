# Tech Stack Decisions — u1-skeleton

The stack is fixed by the project rule (same tools as the current app) and the team practices. It is recorded here for the skeleton, with the requirements from `inception/requirements-analysis/requirements.md`, the functional design (`construction/u1-skeleton/functional-design/functional-spec.md`, `rules.md`) and the contracts in `inception/contract-design/contract-summary.md`.

| Concern | Choice | Why |
|---------|--------|-----|
| Language and packaging | Python 3.12, uv, `src/` layout, uv_build | Team practices; same as the current app |
| Data preparation and training | PySpark, using its implicit-feedback ALS for collaborative filtering | Same as the current app; proven at full size |
| Nearest-neighbour index | FAISS, inner product over L2-normalised vectors (cosine) | Same as the current app; contract C2 |
| Artist details and name search | SQLite | Contract C2 (owner's choice in Contract Design) |
| Web app | FastAPI, served with uvicorn on 127.0.0.1 | Same as the current app; NFR8.1 |
| Interim data format | Parquet | Spark's native output; the current app uses it |
| Lint, format, types | ruff (line length 100, E F W I B UP SIM), ty pinned | Team practices |
| Tests | pytest, pytest-cov, FastAPI TestClient, one shared local SparkSession | Team practices |
| Pre-merge check | `scripts/check.sh` | Recorded verification command |

The map's UMAP dependency is not added in the skeleton; it is stretch scope.

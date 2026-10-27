# Observability Requirements — u1-skeleton

Derived from `inception/requirements-analysis/requirements.md` (NFR2), the functional design (`construction/u1-skeleton/functional-design/functional-spec.md`, `rules.md`) and `inception/contract-design/contract-summary.md`. The Operation phase is skipped, so observability means clear local output only.

## Requirements

| ID | Requirement | Pass criterion |
|----|-------------|----------------|
| NFR2.5 | Each pipeline step prints a one-line summary: rows read, rows skipped, artists kept, output files and duration | Visible in the step's output; asserted in an integration test |
| NFR2.6 | The app logs each request's path, status and duration at INFO, and errors with a stack trace at ERROR, to the console | Standard logging; no listener data in logs (NFR3) |
| NFR2.7 | A health endpoint reports whether the built files loaded and their manifest build date | `GET /api/health` returns 200 with `built_at` when ready |

No dashboards, alerts or tracing are needed in v1.

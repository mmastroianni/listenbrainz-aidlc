# Observability Requirements — u3-web

Derived from `inception/requirements-analysis/requirements.md` (NFR2, NFR3), the functional design (`construction/u3-web/functional-design/rules.md`) and the earlier units' observability requirements (`construction/u1-skeleton/nfr-requirements/observability-requirements.md`). The Operation phase is skipped, so observability means clear local output only.

## Requirements

| ID | Requirement | Pass criterion |
|----|-------------|----------------|
| NFR2.21 | The app logs each request's method, path, status and duration at INFO, never the query text, and errors with a stack trace at ERROR | A test captures the log lines for a suggestion request and finds the path but not the typed text (NFR3.13) |
| NFR2.22 | The health endpoint reports whether the built files loaded, their build date and the artist count | `GET /api/health` returns 200 with `status`, `built_at` and `artists` |
| NFR2.23 | The quality-check commands print counts only: how many artists were written, how many verdicts were marked, how many are better-or-equal, and the result | A test of each command reads its output |

No dashboards, alerts or tracing are needed in v1.

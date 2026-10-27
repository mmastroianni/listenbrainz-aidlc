# Observability Design — u1-skeleton

Designs `construction/u1-skeleton/nfr-requirements/observability-requirements.md` (NFR2.5 to NFR2.7), using the functional spec (`construction/u1-skeleton/functional-design/functional-spec.md`), the tech stack decisions and `inception/contract-design/contract-summary.md`. Local only; no dashboards, alerts or tracing.

- **Pipeline summaries (NFR2.5):** each command ends by printing one line: rows read, skipped, artists kept, output files and duration. Counts come from the step's own counters.
- **Request logging (NFR2.6):** one middleware logs method, path, status and duration at INFO; unhandled errors log a stack trace at ERROR. Logs hold artist ids only, never listener data.
- **Health (NFR2.7):** `GET /api/health` returns `{"status": "ok", "built_at": <manifest build date>, "artists": <count>}` once startup succeeded.
- **Correlation:** not needed for a single local process.
- **SLI:** p95 request duration is read from the log lines when checking the 200 ms target.

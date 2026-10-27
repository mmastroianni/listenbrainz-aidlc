# Observability Design — u3-web

Designs `construction/u3-web/nfr-requirements/observability-requirements.md` (NFR2.21 to NFR2.23), using the functional design (`construction/u3-web/functional-design/rules.md`: BR5.1, BR5.2) and the skeleton's observability design (`construction/u1-skeleton/nfr-design/observability-design.md`).

| Requirement | Design |
|-------------|--------|
| NFR2.21 request log | The existing request-logging middleware stays: method, path, status and duration at INFO, errors with a stack trace at ERROR, to the console through standard logging. It logs `request.url.path`, which excludes the query string, so typed text is never logged. |
| NFR2.22 health | The existing `GET /api/health` returns `status`, `built_at` and `artists`; no change. |
| NFR2.23 quality-check output | Each quality-check command prints one counts-only block: the generate command prints how many artists it wrote and where; the verdict command prints how many verdicts are marked, how many are better-or-equal, and the result (pass, fail or incomplete). |

No dashboards, alerts or tracing are needed in v1 (the Operation phase is skipped).

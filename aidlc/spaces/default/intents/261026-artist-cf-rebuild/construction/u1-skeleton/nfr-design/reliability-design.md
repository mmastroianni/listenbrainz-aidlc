# Reliability Design — u1-skeleton

Designs `construction/u1-skeleton/nfr-requirements/reliability-requirements.md` (NFR2.1 to NFR2.4), using the functional design (`construction/u1-skeleton/functional-design/rules.md`: BR4.1, BR4.2), contract C2 in `inception/contract-design/contract-summary.md` and the construction phase error-handling rules.

| Requirement | Design |
|-------------|--------|
| NFR2.1 fail fast at startup | A startup check lists the C2 files, reads the manifest and compares `format_version`. Any gap raises a startup error naming the file or version and the pipeline step that builds it. The server never starts half-loaded. |
| NFR2.2 interrupted steps | Each step writes to `<name>.tmp` and renames when complete (atomic on one filesystem). The manifest is written last, so an interrupted build has no manifest and the app refuses to start. |
| NFR2.3 step order | Each step writes a small marker beside its output (prepared, trained, built). A later step checks its input marker and stops with the missing step's name. |
| NFR2.4 boundary errors | File reads, Spark jobs, the index load and SQLite queries are wrapped so failures are logged with context and either returned as a clear message (web) or exit non-zero (commands). Recoverable cases (unknown id, no neighbours) are normal responses, not errors. |

No retries, circuit breakers or fallbacks: there are no remote calls. Recovery is to re-run the steps in order.

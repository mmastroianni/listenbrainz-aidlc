# Logical Components — u3-web

Bridges the NFR designs (`performance-design.md`, `security-design.md`, `scalability-design.md`, `reliability-design.md`, `observability-design.md`) with the components in `inception/domain-design/components.md` and the functional design in `construction/u3-web/functional-design/functional-spec.md`. The project is local, so there is no infrastructure beyond the machine.

| Logical component | Runs as | Failure domain | Where NFR patterns apply |
|-------------------|---------|----------------|--------------------------|
| Web app | One uvicorn process on 127.0.0.1 | Its own process; refuses to start on bad files | Startup checks; input validation; allow-listed responses; page headers; request logging; health; one batched lookup per request |
| Suggestion endpoint | A route in the web app | The request | Text limit; catalogue order passed through; no query text in logs |
| Similar-artists endpoint | A route in the web app | The request | Paging; bar scale; missing-from-index handling; links built server-side |
| Page files (one HTML, one stylesheet, one script) | Static files served by the web app | The browser tab | Text-only rendering; no outside resources; request numbering and busy flag; plain error with Retry; 100 KB budget |
| Quality-check commands (generate and verdict) | Two short command-line runs started by hand | Their own run; read-only on the built files | Artist-level output only; counts-only printout |
| Built files folder (git-ignored) | Shared folder on disk | The disk | Written by the pipeline commands, read-only to the web app and the quality-check commands |

**Blast radius:** a failing web app does not affect the pipeline commands or the dumps; a failing page script affects one browser tab and leaves the server untouched. **Shared resource:** the built files folder is still the only thing the processes share.

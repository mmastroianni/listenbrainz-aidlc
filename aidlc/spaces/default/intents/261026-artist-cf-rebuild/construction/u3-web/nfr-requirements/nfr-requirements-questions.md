# NFR Requirements (u3-web) — Questions

Context: every target for the web unit is already set by the requirements (NFR1 to NFR8), the refined mockups' accessibility checklist, the team practices and the contracts, and carried over from the earlier units' NFR requirements (`construction/u1-skeleton/nfr-requirements/`, `construction/u2-pipeline/nfr-requirements/`), so no new questions were needed. Please confirm the targets below.

## Consolidated Summary Confirmation

- Speed: at full size, the suggestion endpoint and the similar-artists endpoint each answer in under 200 ms at the 95th percentile over 100 different lookups, checked by the speed command from u2-pipeline plus an endpoint timing test on the fixture build; the page's own files stay under 100 KB in total.
- Security and privacy: responses and logs carry no listener data; the page puts response values on screen as text only; error answers are short JSON with no stack trace or file path; the page is served with a content security policy that allows only its own files; typed text is not written to logs.
- Cost and hygiene: no paid or remote service; the page loads nothing from other websites; the quality-check sheet holds artist-level data only and nothing under the data and models folders is committed.
- Local only and scale: the app listens on 127.0.0.1 by default; every id, text length, offset and limit is validated (404 for unknown, 422 for invalid); one local user and 5 requests at once without errors.
- Reliability: the app refuses to start naming the missing file; failures reach the page as a plain message with Retry; an artist missing from the index shows "not enough data" rather than an error; a late suggestion reply never replaces a newer one and Show more never adds twice.
- Observability: one log line per request (method, path, status, duration, never the query text), the health endpoint with the build date, and a counts-only printout from the quality-check commands.
- Tech stack: unchanged and nothing new at run time or in development (FastAPI serves plain HTML, CSS and JavaScript files; tests use the existing test client); the keyboard and phone pass is by hand before `v0.1.0`.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

# Reliability Design — u3-web

Designs `construction/u3-web/nfr-requirements/reliability-requirements.md` (NFR2.16 to NFR2.20), using the functional design (`construction/u3-web/functional-design/rules.md`: BR2.3, BR2.5, BR4.2, BR4.8, BR4.9) and the earlier units' reliability designs (`construction/u1-skeleton/nfr-design/reliability-design.md`, `construction/u2-pipeline/nfr-design/logical-components.md`).

| Requirement | Design |
|-------------|--------|
| NFR2.16 fail fast at startup | The app builds its endpoints only after the store loads and checks the built files, as in u1-skeleton and u2-pipeline; any missing file, table or version stops the start with a message naming the file and the step. The page is never served by a half-started app. |
| NFR2.17 plain failure on the page | The page treats any answer that is not a success, and any network failure, as the one error state: it shows "Something went wrong finding similar artists. Try again." and a Retry button, and never prints a status code, path or the server's wording. Retry repeats the failed request and nothing else. |
| NFR2.18 missing from the index | When the index raises "unknown" for an id, the endpoint asks the catalogue; if the catalogue has the artist it returns the artist with no items and no more pages (the page shows "not enough data"), otherwise it answers 404. |
| NFR2.19 late replies and double clicks | The script keeps a counter, increases it for each suggestion request, and shows a reply only when its number is still the newest. It keeps a busy flag during a results request: Show more is disabled while the flag is set and ignored if clicked. A Back or a new pick while a request runs bumps a results counter so the older reply is dropped in the same way. |
| NFR2.20 boundary errors | A failing catalogue or index read raises through the existing unexpected-error handler: a short 500 answer with no detail, and a stack trace at ERROR in the console log. Tests cover two failure paths per endpoint (a closed catalogue connection and an index read error). |

**Recovery:** rebuild by running the pipeline steps in order; the app holds no data of its own.

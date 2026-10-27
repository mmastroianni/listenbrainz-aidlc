# Reliability Requirements — u3-web

Derived from `inception/requirements-analysis/requirements.md` (NFR2), the functional design (`construction/u3-web/functional-design/rules.md`: BR2.3, BR2.5, BR4.2, BR4.8, BR4.9) and the earlier units' reliability requirements (`construction/u1-skeleton/nfr-requirements/reliability-requirements.md`).

## Availability

There is no uptime target: the app is local and started by hand.

## Requirements

| ID | Requirement | Pass criterion |
|----|-------------|----------------|
| NFR2.16 | The app fails fast at startup when a built file is missing, a table is missing or the manifest version differs, naming the file and the step that builds it | Carried from u1-skeleton and u2-pipeline; a test starts the app against files with each part missing |
| NFR2.17 | A failure on either endpoint reaches the page as a plain message with a Retry button, never a code, path or stack text | A test forces a server error and checks the short JSON; the served page script is checked for the message and Retry (BR4.9) |
| NFR2.18 | An artist in the catalogue but not in the index shows "not enough data", not an error | A test queries such an artist and gets the artist with no items and no more pages (BR2.3) |
| NFR2.19 | A late suggestion reply never replaces a newer one, and Show more never adds a page twice | The page script's request numbering and busy flag are checked in the manual pass and by a review of the script against BR4.2 and BR4.8 |
| NFR2.20 | Errors at boundaries (catalogue read, index read) are surfaced as a short answer and logged with a stack trace at ERROR | Tests cover two failure paths per endpoint |

## Recovery

Rebuilding is the recovery: re-run the pipeline steps in order. The app holds no data of its own.

# Security Requirements — u3-web

Derived from `inception/requirements-analysis/requirements.md` (NFR3, NFR4, NFR5, NFR8), the project hard rules, the functional design (`construction/u3-web/functional-design/rules.md`), contract C3 in `inception/contract-design/contract-summary.md`, and the earlier units' security requirements (`construction/u1-skeleton/nfr-requirements/security-requirements.md`, `construction/u2-pipeline/nfr-requirements/security-requirements.md`).

## Context

The app is local, anonymous and read-only, with no accounts and no secrets. This unit is the only one that serves content to a browser, so the new risks are leaking listener data in responses, running text from the dumps as page markup, and the page reaching other websites.

## Requirements

| ID | Requirement | Pass criterion |
|----|-------------|----------------|
| NFR3.9 | No response, from either endpoint, holds listener numbers or listener details | A test inspects the suggestion and similar-artists responses and the health response and finds only the allow-listed fields (BR1.3) |
| NFR3.10 | Artist names and descriptions reach the screen as text only | A test finds none of `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write` or `eval` in the page script (BR3.3) |
| NFR3.11 | Errors are short JSON messages with no stack trace, file path or internal code | Tests send bad ids, bad paging and over-long text and find plain messages only (BR1.2, BR2.5) |
| NFR3.12 | The page is served with a content security policy that allows only its own files, forbids framing, and sets no-sniff | A test reads the response headers of `/` and `/artist/<id>` |
| NFR3.13 | Typed search text and ids are not written to logs | A test makes requests and finds no query text in the captured log lines |
| NFR4.3 | The page loads nothing from another website | A test finds no `http://` or `https://` address in the HTML, stylesheet or script except the three result-link templates (BR3.2) |
| NFR5.3 | The quality-check sheet holds artist-level data only, and nothing under the data and models folders is committed | A test of the generate command finds no listener fields in the sheet (BR5.3); `.gitignore` and the check script cover the folders |
| NFR8.7 | The app listens on 127.0.0.1 unless the owner passes another address | The start command's default host is tested (carried from u1-skeleton) |
| NFR8.8 | Every id, text length, offset and limit is validated; unknown ids are 404 and invalid input is 422, never a server error | Tests send malformed and out-of-range values to both endpoints (BR1.2, BR2.5) |

## Threats Considered

- **Listener data leaking through a response or log:** handled by NFR3.9 and NFR3.13.
- **Markup in an artist name or description running in the browser:** handled by NFR3.10 and NFR3.12; the dumps are public data but not trusted.
- **The page calling out to other websites:** handled by NFR4.3 and NFR3.12.
- **Network exposure:** handled by NFR8.7; public hosting is out of scope.
- **Malformed input causing errors:** handled by NFR8.8 and NFR3.11. Ids and text are only lookup keys, never file paths or query text (NFR8.5 in u2-pipeline).

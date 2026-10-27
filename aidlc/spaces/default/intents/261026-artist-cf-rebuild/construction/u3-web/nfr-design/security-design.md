# Security Design — u3-web

Designs `construction/u3-web/nfr-requirements/security-requirements.md` (NFR3.9 to NFR3.13, NFR4.3, NFR5.3, NFR8.7, NFR8.8), using the functional design (`construction/u3-web/functional-design/rules.md`), contract C3 in `inception/contract-design/contract-summary.md`, the skeleton's security design (`construction/u1-skeleton/nfr-design/security-design.md`) and the project hard rules.

| Requirement | Design |
|-------------|--------|
| NFR3.9 no listener data in responses | Every artist in a response is built by the existing allow-list function (id, name, description, genres); the suggestion endpoint uses the same function. The catalogue's own listener count is read but never copied into a response. A test compares the key sets of both responses to the allow-list. |
| NFR3.10 text only on the page | The script builds elements with `createElement`, sets `textContent` and attributes, and builds addresses with `encodeURIComponent`. It never uses `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write` or `eval`; a test searches the script for them. |
| NFR3.11 plain errors | The existing handlers turn validation, unknown-id and unexpected errors into short JSON; the page shows its own wording, never the server's message text for failures. |
| NFR3.12 page headers | A middleware adds to every response: `Content-Security-Policy: default-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`, `X-Content-Type-Options: nosniff` and `Referrer-Policy: no-referrer` (so opening a result link does not tell another website the local address). Inline scripts and styles are not used, so the policy needs no exceptions. Result links are ordinary navigation, which the policy does not restrict. |
| NFR3.13 no query text in logs | The request log uses the path only; the query string is never logged. For the suggestion endpoint the typed text travels in the query string, so it stays out. A test captures the log and finds no typed text. |
| NFR4.3 nothing from other sites | No font, script, image or stylesheet is loaded from another address. The only addresses in the files are the three result-link patterns, which the page also checks (below). A test scans the three files for `http://` and `https://`. |
| NFR5.3 sheet and repository hygiene | The quality-check commands write names, ids, genres and verdicts only. The sheet is written to a tracked `docs/` folder, outside `data/` and `models/`; the check script already fails when a file under those folders is tracked. |
| NFR8.7 localhost only | The start command keeps its 127.0.0.1 default (carried from u1-skeleton). |
| NFR8.8 input validation | Path ids must match the 36-character id pattern; `offset` and `limit` are range-checked; the suggestion text is limited to 200 characters. Invalid input answers 422 and an unknown id 404. Ids and text are only lookup keys and bound parameters. |

**Result links:** the links come from the server, but the script uses a link only when it begins with `https://musicbrainz.org/artist/`, `https://www.youtube.com/results?search_query=` or `https://open.spotify.com/search/`; otherwise the link is left out. Links open with `target="_blank"` and `rel="noopener noreferrer"`.

No authentication, encryption or secrets are needed: the app is local, anonymous and read-only. Names and descriptions come from public dumps and are treated as untrusted text.

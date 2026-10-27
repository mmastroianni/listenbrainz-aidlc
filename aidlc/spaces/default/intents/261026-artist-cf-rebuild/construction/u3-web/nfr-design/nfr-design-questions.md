# NFR Design (u3-web) — Questions

Context: the targets are set (`construction/u3-web/nfr-requirements/`) and the stack is fixed, so no new questions were needed. Please confirm the design choices below.

## Consolidated Summary Confirmation

- Speed: both endpoints do one catalogue or index call plus one batched artist lookup and no caching; the page is one HTML file, one stylesheet and one script, with a 150 ms pause before each suggestion request and one similar-artists request per pick or Show more.
- Security: every response is built from the allow-list of fields; the page script writes values with text-only calls and builds no markup from responses; the page is served with `default-src 'self'`, no framing, no-sniff and no referrer sent when a result link is opened; result links must start with one of the three expected web addresses before the page uses them; logs hold the path, never the query.
- Scale: each request is stateless; the catalogue's one read-only connection is shared behind its lock, which is fast enough for 5 requests at once.
- Reliability: the endpoint turns an index "unknown" into "not enough data" when the catalogue knows the artist; the page numbers each suggestion request and ignores older replies, locks Show more while a request is running, and shows the plain error with Retry for any other failure.
- Observability: the existing request log line and health endpoint stay as they are; the quality-check commands print counts only.
- Logical components: the web app process serving the endpoints and the page files, plus two small quality-check commands; the built files folder is still the only shared resource.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

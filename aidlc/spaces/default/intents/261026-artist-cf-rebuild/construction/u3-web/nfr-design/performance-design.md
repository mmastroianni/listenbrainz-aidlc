# Performance Design — u3-web

Designs `construction/u3-web/nfr-requirements/performance-requirements.md` (NFR1.11 to NFR1.15), using the functional design (`construction/u3-web/functional-design/rules.md`), contract C3 in `inception/contract-design/contract-summary.md` and u2-pipeline's performance design (`construction/u2-pipeline/nfr-design/logical-components.md`).

| Requirement | Design |
|-------------|--------|
| NFR1.11 suggestion speed | The endpoint makes one call to the catalogue's name search, which does its own early-stopping queries (u2-pipeline), then returns the artists as they come. No extra query, loop or sort is added in the web layer. Full-size timing comes from u2-pipeline's speed command. |
| NFR1.12 similar-artists speed | One index search for the page (plus one for the top score when the page is not the first), then one batched catalogue lookup for the artist and every neighbour (at most 101 ids). Bars and links are computed in a single pass over at most 100 rows. The index and catalogue handles are opened once at startup and kept. |
| NFR1.13 fixture guard | A timing test runs 20 lookups of each endpoint through the test client and expects each under 200 ms; it fails on a slow regression and is not a substitute for the full-size check. |
| NFR1.14 page size | One HTML file, one stylesheet and one script, written by hand with no framework and no bundled font or image; icons are small inline SVG. A test adds the three file sizes and expects under 100 KB. |
| NFR1.15 request count | The script waits 150 ms after the last keystroke before asking for suggestions, asks nothing for blank text, and sends one similar-artists request per pick, click or Show more. A running Show more request makes further clicks do nothing. |

No cache layer is added: the work per request is already small, there is one local user, and a cache would add staleness after a rebuild. The page files are served with the framework's normal conditional-request support, so a reload is cheap.

If the full-size speed check ever fails, the first thing to look at is the starts-with query in the catalogue (noted in `construction/u2-pipeline/code-generation/code-summary.md`), not the web layer.

# Performance Requirements — u3-web

Derived from `inception/requirements-analysis/requirements.md` (NFR1), the functional design (`construction/u3-web/functional-design/functional-spec.md`, `rules.md`), contract C3 in `inception/contract-design/contract-summary.md`, and the earlier units' performance requirements (`construction/u1-skeleton/nfr-requirements/performance-requirements.md`, `construction/u2-pipeline/nfr-requirements/tech-stack-decisions.md`). No questions were needed; every target is already set upstream.

## Targets

| ID | Requirement | Target | Measured by |
|----|-------------|--------|-------------|
| NFR1.11 | Suggestion endpoint latency at full size | Under 200 ms at the 95th percentile over 100 lookups of different typed texts on the owner's machine | The speed command from u2-pipeline (catalogue lookup), run by hand after a full rebuild (BR1.4) |
| NFR1.12 | Similar-artists endpoint latency at full size, including composing names, bars and links | Under 200 ms at the 95th percentile over 100 lookups of different artists | The speed command, run by hand after a full rebuild (BR1.4, BR2.2) |
| NFR1.13 | The same two endpoints on the fixture build | Under 200 ms for each in the default test run, as a guard against slow code | A timing test through the test client |
| NFR1.14 | Size of the page's own files | Under 100 KB in total, uncompressed (one HTML file, one stylesheet, one script) | A test sums the file sizes |
| NFR1.15 | Request count per user action | One suggestion request per pause in typing (150 ms) and one similar-artists request per pick, click or Show more | A review of the page script against BR4.2 and BR4.8 |

## Notes

NFR1.11 and NFR1.12 are the owner-run full-size checks that the earlier units left open (AC1.1.6, AC2.1.6); they pass or fail only on the full build. The page adds no work per request beyond one catalogue or index call and a small amount of composing, so the full-size result is the catalogue's and the index's.

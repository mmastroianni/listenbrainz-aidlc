# Security Test Instructions

Covers the security targets in each unit's `nfr-requirements/` (u1-skeleton NFR3.1 to NFR3.3, NFR4.1, NFR5.1, NFR8.1 to NFR8.3; u2-pipeline NFR3.4 to NFR3.8, NFR4.2, NFR5.2, NFR8.4 to NFR8.6; u3-web NFR3.9 to NFR3.13, NFR4.3, NFR5.3, NFR8.7 to NFR8.10) and the project hard rules in `aidlc/spaces/default/memory/project.md`. The app is local, anonymous and read-only, so the tests are about data leaks, dump safety, repository hygiene and input handling, not authentication.

## Checks

| Concern | Check | Where |
|---------|-------|-------|
| No listener data in built files, responses or logs | Inspect the built files, both endpoint responses, the health response and the captured logs for listener fields | `tests/u2_pipeline/test_privacy_and_hygiene.py`, `tests/u3_web/test_suggest_endpoint.py`, `test_similar_endpoint.py`, `test_headers_logs_concurrency.py` |
| Dumps unchanged | Checksums and modification times of the fixture dump before and after each step; a run on a read-only copy | `tests/u2_pipeline/test_privacy_and_hygiene.py`, `test_dump_source_full.py` |
| Real dumps unchanged | Modification times of the real dump files before and after the full rebuild (Build and Test records them) | by hand, Build and Test |
| Data and models never committed | `.gitignore` lists them; the check script fails when a tracked file sits under them; `git status` shows no new data or model files | `scripts/check.sh`, `tests/u2_pipeline/test_privacy_and_hygiene.py` |
| Text on the page is never markup | The page script uses no `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write` or `eval` | `tests/u3_web/test_page_files.py` |
| Nothing loaded from other sites | No `http://` or `https://` address in the page files except the three link patterns | `tests/u3_web/test_page_files.py` |
| Page headers | Policy, no-sniff and no-referrer headers on `/`, an artist address and an endpoint | `tests/u3_web/test_headers_logs_concurrency.py` |
| Input handling | Malformed ids, over-long text, bad paging and odd characters give 422, 404 or normal answers, never a server error | `tests/u3_web/`, `tests/u2_pipeline/test_search.py` |
| No outside network from the pipeline | Local Spark master, web page off, driver on 127.0.0.1, no HTTP client imported | `tests/u2_pipeline/test_privacy_and_hygiene.py` |

## Run

```bash
bash scripts/check.sh
uv run pytest tests/u2_pipeline/test_privacy_and_hygiene.py tests/u3_web/test_headers_logs_concurrency.py tests/u3_web/test_page_files.py -q
```

SAST and DAST tools are not part of this project: there is no deployment, no authentication and no remote service, and the dev toolset is fixed by the team practices.

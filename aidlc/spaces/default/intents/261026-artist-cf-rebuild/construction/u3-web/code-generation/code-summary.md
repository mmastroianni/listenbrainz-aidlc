# Code Summary — u3-web

Built from the approved plan (`code-generation-plan.md`) and the tests described in `unit-test-instructions.md`, following the functional design (`construction/u3-web/functional-design/`), the NFR designs (`construction/u3-web/nfr-design/`), the page designs in `inception/refined-mockups/` and contract C3 (`inception/contract-design/contract-summary.md`).

## Files Created

| Area | Files |
|------|-------|
| Page | `src/listenbrainz_recs/app/static/{index.html,style.css,app.js}` (23,535 bytes in total; limit 100 KB) |
| Quality check | `src/listenbrainz_recs/quality.py` (the sheet and verdict commands) |
| Docs | `docs/manual-checks.md` (the owner's keyboard, phone, speed and quality-check boxes) |
| Tests | `tests/u3_web/test_{suggest_endpoint,similar_endpoint,headers_logs_concurrency,page_files,quality_check,u3_runner_ready}.py`, `tests/fixtures/web_models.py` (hand-made built files for the web tests) |

## Files Modified

`src/listenbrainz_recs/app/main.py`, `pyproject.toml` (the commands `listenbrainz-recs-quality-sheet` and `listenbrainz-recs-quality-verdict`), `README.md` (the page and addresses, the suggestion endpoint, "Quality check against the current app"), and `tests/conftest.py` (four session fixtures: `search_models`, `paging_models`, `exact_page_models`, `gap_models`). No skeleton or u2-pipeline test was changed.

## Key Implementation Decisions

- **Endpoints:** `GET /api/suggest` (text limit 200, up to 10 artists through the existing allow-list); the similar-artists endpoint turns an index "unknown" into the artist with no items when the catalogue has it, otherwise 404.
- **Headers:** a middleware adds the content security policy, no-sniff and no-referrer headers to every answer that passes through it. A 500 produced by the catch-all handler does not get them.
- **Pages:** `/` and `/artist/{mbid}` serve the same `index.html` (even for a malformed id); `/static` serves the package folder. `create_app` exposes `app.state.store` so tests can close the catalogue connection.
- **Icons:** the three link icons are `<svg>` elements inside a `<template>` in `index.html`, cloned by the script, so the script needs no namespace address and the "no outside address" test stays simple.
- **Page script:** only `createElement`, `textContent` and `setAttribute`; the bar width is set through `style.width`, which the policy allows.
- **Quality check:** an artist name must match exactly (ignoring case and accents), so a typo stops the command instead of picking another artist. Verdict lines read `Verdict: unset | better-or-equal | worse`; the verdict command exits 0 on pass and 1 on fail, incomplete or an unreadable sheet.

## Test Coverage Summary

- `bash scripts/check.sh` passes (re-run by the conductor): ruff check, ruff format --check, ty with no checks disabled, and 277 pytest tests at 94.52% coverage against the 80% floor. Per-file coverage of the new code: `main.py` 97%, `quality.py` 98%.
- New tests per file: suggest_endpoint 16, similar_endpoint 18, headers_logs_concurrency 17, page_files 17, quality_check 14, u3_runner_ready 4, which is 86 (the plan estimated about 55).
- Red steps were run before any code: the endpoint tests gave 32 failed and 23 passed (for example `/api/suggest` answering 404 and the static folder missing), the page tests gave 15 failed and 1 passed, and the quality tests failed at collection with `ModuleNotFoundError: No module named 'listenbrainz_recs.quality'`.
- Sample run on the u2-pipeline sample build (`models/sample`): the page and an artist address (Björk) answered 200 in 34 ms and 4 ms with all three headers; `/api/suggest?q=bjork` took 2.8 ms with Björk first; similar-artist pages 1 and 2 took 21.7 ms and 36.2 ms with 20 items each and the bar scale carried over (page 1 top 1.0, page 2 starting at 0.924); an unknown id gave 404 and 201 characters of text gave 422; the request log showed paths only; `node --check` on the script passed (Node v20).

## Tests Written but Not Executed in This Stage

- The page script is never executed by a test. It is covered by text and structure checks, a syntax pass and a code read, so its keyboard, history, Show more and error behaviour have not been seen in a browser. The keyboard and phone pass in `docs/manual-checks.md` is the owner's, before `v0.1.0`.
- The full-size speed check (AC1.1.6, AC2.1.6, NFR1.11, NFR1.12): the owner runs `uv run listenbrainz-recs-speed` after a full rebuild.
- The quality check (AC5.1.1, AC5.1.2) needs the owner to run the sheet and verdict commands on real artists; only the commands' logic is tested.
- The GitHub Actions workflow was not run; it stays switched off until the code is pushed.

## Deviations from the Plan

- The runner test is named `test_u3_runner_ready.py`, because `tests/u2_pipeline` already has a `test_runner_ready.py` and `tests/` has no package files, so two files of the same name would clash.
- The endpoint code (step 4) was verified together with the page files (step 6), because the static folder has to exist when the app is built; there is no endpoints-only Green run.
- After Green, three of the new tests were corrected: the log test checks only the app's own loggers (the test client's own log prints the URL), the "Show more" and "Retry" check moved from the script to the HTML where those buttons live, and one quality test compares its message ignoring case.
- 86 tests were written instead of about 55.
- The developer agent edited `main.py` once through a shell heredoc, against the instruction to use file tools, and a sample-run command wrote server output to a log file in the project root, which was deleted. The conductor read the first 120 lines of `main.py` (imports, constants, headers, logging) and found nothing amiss; the rest of the file is covered by the 97% test coverage but was not read line by line.

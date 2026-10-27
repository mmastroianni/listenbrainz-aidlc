# Security Requirements — u1-skeleton

Derived from `inception/requirements-analysis/requirements.md` (NFR3, NFR4, NFR5, NFR8), the project hard rules, the functional design (`construction/u1-skeleton/functional-design/functional-spec.md`, `rules.md`) and contract C3 in `inception/contract-design/contract-summary.md`.

## Context

The app is local only, with no accounts and no secrets. The main risks are leaking listener data, damaging the dumps, and committing data to git.

## Requirements

| ID | Requirement | Pass criterion |
|----|-------------|----------------|
| NFR3.1 | Built files and API responses hold no listener numbers or listener details | A test inspects the built artist file and an API response and finds no listener fields (BR1.4, BR5.2) |
| NFR3.2 | Prepared data keeps only the dump's listener number, never any other listener attribute | Schema test on the prepared data (BR1.4) |
| NFR3.3 | Dump files are opened read-only | A test runs the prepare step on a read-only copy of a fixture and passes; the dumps' modification times are unchanged after a skeleton run (BR1.2) |
| NFR4.1 | No paid or remote service is called | No network calls in the pipeline or app; review of dependencies |
| NFR5.1 | Data and model folders are git-ignored | `.gitignore` lists them; `git status` after a run shows no new data files (BR6.1) |
| NFR8.1 | The app listens on localhost only by default | The start command binds to 127.0.0.1 |
| NFR8.2 | Path and query inputs are validated | An unknown or malformed artist id returns 404 or 422, never a server error (contract C3) |

## Threats Considered

- **Data leak via responses:** handled by NFR3.1.
- **Accidental dump damage:** handled by NFR3.3.
- **Network exposure:** handled by NFR8.1; public hosting is out of scope.
- **Malformed input causing errors or traversal:** handled by NFR8.2. Ids are only used as lookup keys, never as file paths.

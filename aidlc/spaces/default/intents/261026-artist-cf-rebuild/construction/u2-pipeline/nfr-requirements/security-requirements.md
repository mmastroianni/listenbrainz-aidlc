# Security Requirements — u2-pipeline

Derived from `inception/requirements-analysis/requirements.md` (NFR3, NFR4, NFR5, NFR8), the project hard rules, the functional design (`construction/u2-pipeline/functional-design/functional-spec.md`, `rules.md`), contract C2 in `inception/contract-design/contract-summary.md`, and the skeleton's security requirements (`construction/u1-skeleton/nfr-requirements/security-requirements.md`). `nfr-requirements-questions.md` records the owner's confirmation; no new questions were needed.

## Context

This unit is the batch side and the catalogue and index code. It has no accounts, no secrets and no network. It is the only unit that reads the dumps, and so the only one that ever sees listener identities (`inception/domain-design/components.md`, ListeningDataPrep). The risks are leaking listener data, damaging the dumps, committing data to git and opening a network port.

## Requirements

| ID | Requirement | Pass criterion |
|----|-------------|----------------|
| NFR3.4 | The prepared listen counts hold only listener number, artist id and listen count; artist names are stored per artist, never per listener | Schema test on the prepared data and the artist name file (BR1.5) |
| NFR3.5 | The catalogue, the search table, the index, the id file and the manifest hold no listener numbers or listener details | A test opens each built file from the fixture build and finds no listener field or value (BR1.5, BR3.1) |
| NFR3.6 | Pipeline output, reports and logs show counts only, never a listener number or a listener's list of artists | A test captures the output of each step on the fixture and finds no listener number (BR1.8) |
| NFR3.7 | Dump files are only opened for reading and are unchanged after a run | A test compares checksums and modification times of fixture dump files before and after every step; a run on a read-only copy of the fixture passes (BR1.2) |
| NFR3.8 | A missing or wrong data location stops before anything is written | A test points the setting at an empty folder and finds no output files (BR1.1) |
| NFR4.2 | No paid or remote service is called by any pipeline step | Spark runs with a local master; no download or upload code; review of dependencies and of the step code |
| NFR5.2 | Every step writes only inside the git-ignored data and models folders | `.gitignore` lists them; `git status` after a fixture run lists no new files; a test lists the files each step created and finds all under those folders (BR1.9) |
| NFR8.4 | The pipeline opens no network port | Spark's web page is off and the Spark driver binds to 127.0.0.1 (already set in `spark.py`); a test reads the session's settings |
| NFR8.5 | Typed text and ids passed to the catalogue and index are only ever used as values in queries and lookups, never as file paths or query text | Suggestion text is passed as a bound parameter or built only from letters and digits; a test sends quotes, percent signs and `OR 1=1` as typed text and gets an empty list or normal matches, never an error (BR4.1) |

## Threats Considered

- **Listener data leak through built files or output:** handled by NFR3.4 to NFR3.6.
- **Accidental damage to the dumps:** handled by NFR3.7 and NFR3.8; the dumps are the source of truth and the only backup.
- **Committing data or models:** handled by NFR5.2.
- **Network exposure by the pipeline:** handled by NFR4.2 and NFR8.4; the web app's own binding is covered in the skeleton and u3-web.
- **Odd characters in typed search text breaking the search table query:** handled by NFR8.5.
- **Untrusted dump content:** artist names and descriptions come from public data and are only stored and shown as text; the web unit is responsible for escaping them on the page.

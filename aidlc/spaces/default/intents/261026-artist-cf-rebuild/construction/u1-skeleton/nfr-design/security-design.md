# Security Design — u1-skeleton

Designs `construction/u1-skeleton/nfr-requirements/security-requirements.md` (NFR3.x, NFR4.1, NFR5.1, NFR8.x), using the functional design (`construction/u1-skeleton/functional-design/rules.md`), contract C3 in `inception/contract-design/contract-summary.md` and the project hard rules.

| Requirement | Design |
|-------------|--------|
| NFR3.1, NFR3.2 no listener data | Prepare keeps only (listener number, artist id, count). The catalogue file is built from artist-level fields only. Responses are built from an allow-list of fields (id, name, description, genres, cosine, links), so listener fields cannot be returned even by mistake. |
| NFR3.3 dumps read-only | All dump access goes through DumpSource, which opens files in read mode only. A test confirms nothing writes under the data location. |
| NFR4.1 no remote services | No HTTP client library is a dependency; links are plain strings built from artist data. |
| NFR5.1 git-ignored data | `.gitignore` lists the data and models folders; the check script fails if a tracked file sits under them. |
| NFR8.1 localhost only | The start command binds 127.0.0.1; changing the host is a deliberate flag. |
| NFR8.2 input validation | Artist id must match the MusicBrainz id format (a 36-character UUID); `offset` and `limit` are range-checked (0 or more, 1 to 100). Invalid values return 422; unknown ids return 404. Ids are lookup keys only, never file paths. |

No authentication, encryption or secrets are needed: the app is local, anonymous and read-only. Error responses carry a short message and never a stack trace.

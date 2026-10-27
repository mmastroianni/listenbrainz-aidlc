# Scalability Design — u3-web

Designs `construction/u3-web/nfr-requirements/scalability-requirements.md` (NFR8.9, NFR8.10), using the functional design (`construction/u3-web/functional-design/functional-spec.md`) and the skeleton's scalability design (`construction/u1-skeleton/nfr-design/scalability-design.md`).

| Requirement | Design |
|-------------|--------|
| NFR8.9 five requests at once | Endpoint functions are plain synchronous functions, so the framework runs them in its worker threads. The index search is read-only. The catalogue's one read-only SQLite connection is shared across threads behind its lock; each lookup holds the lock for a few milliseconds, so five requests at once queue briefly and never fail. A test sends 5 parallel requests to each endpoint and checks every answer. |
| NFR8.10 no per-user state | Nothing is stored between requests: no sessions, cookies or in-memory caches. The only state is the read-only loaded files. The page keeps its own state in the browser while it is open. |

If the lock ever becomes a limit, the fix is one connection per worker thread; it is not needed for one local user.

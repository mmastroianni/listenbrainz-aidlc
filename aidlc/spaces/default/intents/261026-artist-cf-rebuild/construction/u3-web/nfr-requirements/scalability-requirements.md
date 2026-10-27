# Scalability Requirements — u3-web

Derived from `inception/requirements-analysis/requirements.md` (NFR1, NFR8), the functional design (`construction/u3-web/functional-design/functional-spec.md`, `rules.md`) and `inception/contract-design/contract-summary.md`.

## Load

The app has one local user, with a few requests at once when the page asks for suggestions while results load. There is no growth target in v1 (NFR8).

## Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR8.9 | Concurrent requests | Handles 5 concurrent requests to either endpoint without errors or wrong answers |
| NFR8.10 | The web app holds no per-user state | Every answer depends only on the request and the built files; no sessions, cookies or caches that grow |

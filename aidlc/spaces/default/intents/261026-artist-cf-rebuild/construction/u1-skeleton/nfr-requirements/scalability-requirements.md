# Scalability Requirements — u1-skeleton

Derived from `inception/requirements-analysis/requirements.md` (NFR1, NFR8), the functional design (`construction/u1-skeleton/functional-design/functional-spec.md`, `rules.md`) and `inception/contract-design/contract-summary.md`.

## Load

The app has one local user, a few concurrent requests at most, and no growth target in v1 (NFR8).

## Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR8.3 | Concurrent requests | Handles 5 concurrent requests without errors |
| NFR1.4 | Data growth | The skeleton's design must not prevent u2-pipeline scaling to the full dump: steps stream the dump instead of loading it whole, and the index is built from vectors, not raw listens |

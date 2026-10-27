# Performance Requirements — u1-skeleton

Derived from `inception/requirements-analysis/requirements.md` (NFR1), the functional design (`construction/u1-skeleton/functional-design/functional-spec.md`, `rules.md`) and contract C3 in `inception/contract-design/contract-summary.md`. No questions were needed; every target is already set upstream.

## Targets

| ID | Requirement | Target | Measured by |
|----|-------------|--------|-------------|
| NFR1.1 | Similar-artists endpoint latency on the skeleton sample | Under 200 ms at the 95th percentile over 100 lookups on the owner's machine | API test timing on the sample build |
| NFR1.2 | Full-size lookup latency (the real NFR1 target) | Under 200 ms at the 95th percentile over 100 lookups | Deferred to u2-pipeline's speed check |
| NFR1.3 | Skeleton build time (prepare, train, index on 5,000 listener lines) | Under 5 minutes end to end | The verification command run |

## Notes

The skeleton proves the path, not full-size speed. NFR1.2 stays with u2-pipeline, as the Bolt plan says.

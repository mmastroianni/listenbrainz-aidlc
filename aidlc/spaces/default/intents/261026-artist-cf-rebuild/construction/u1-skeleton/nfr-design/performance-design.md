# Performance Design — u1-skeleton

Designs the targets in `construction/u1-skeleton/nfr-requirements/performance-requirements.md` (NFR1.1 to NFR1.4), using the functional spec (`construction/u1-skeleton/functional-design/functional-spec.md`), the tech stack decisions and contract C2/C3 in `inception/contract-design/contract-summary.md`.

| Requirement | Design |
|-------------|--------|
| NFR1.1 lookup under 200 ms | At startup the app loads the SQLite artist file handle, the FAISS index and the id list once, then answers each request from memory. A lookup is one exact inner-product search over normalised vectors plus one batched SQLite read for the result names. No cache layer: one local user does not need one. |
| NFR1.2 full-size speed | Deferred to u2-pipeline. If exact search is too slow at full size, u2 switches the index type behind the same SimilarityIndex interface. |
| NFR1.3 skeleton build under 5 min | Spark runs locally on a 5,000-line sample; one shared SparkSession per command; a small ALS rank and few iterations for the skeleton. |
| NFR1.4 data growth | Prepare streams the dump line by line and writes Parquet in batches. Training reads the prepared counts, not the raw dump. The index is built from vectors only. |

## Budget for one similar-artists request

| Step | Budget |
|------|--------|
| Validate id and paging | 1 ms |
| Neighbour search | 50 ms |
| Name lookup (one batched SQLite query) | 20 ms |
| Build response | 10 ms |
| Headroom | 119 ms |

# Code Generation Plan Approval

AI-DLC writes this file when it asks you to approve the plan. To answer here
instead of in chat, write your answer after `[Answer]:` and tell me in chat when you are done.

## Plan Approval

Approve the code plan for u2-pipeline?

- Builds: the full-size pipeline (prepare with all the rules, full-size training, a new catalogue step with MusicBrainz details and genres, a batch-reading index step), four-tier name search, a speed...
- Touches: `src/listenbrainz_recs/` (prep, train, index, artists, store, settings, paths, spark, plus new `steps.py`, `musicbrainz.py`, `catalogue.py`, `speed.py`), `tests/u2_pipeline/`, `tests/u1_sk...
- Tests: about 70 new tests (unit, integration on fixture data, and a fixture-size timing guard), search tests written before the code and pipeline tests after it, all under the 80% coverage floor.
- Inputs: `construction/u2-pipeline/functional-design/` (BR1.1 to BR6.6, W1 to W6), `construction/u2-pipeline/nfr-requirements/` and `nfr-design/` (NFR1.5 to NFR8.6), contracts C1 and C2 in `inceptio...
- Already changed before you approved (13 files): .python-version, data/artist_names/part-0.parquet, data/interactions/part-0.parquet, data/prepared.json, data/serve.log, data/trained.json, data/vectors/._SUCCESS.crc, data/vectors/.part-00000-469cbd20-8a91-4b75-bd3c-45d11f690aa4-c000.snappy.parquet.crc, data/vectors/_SUCCESS, data/vectors/part-00000-469cbd20-8a91-4b75-bd3c-45d11f690aa4-c000.snappy.parquet (and 3 more).

Full plan: aidlc/spaces/default/intents/261026-artist-cf-rebuild/construction/u2-pipeline/code-generation/code-generation-plan.md
Test instructions: aidlc/spaces/default/intents/261026-artist-cf-rebuild/construction/u2-pipeline/code-generation/unit-test-instructions.md

[Approval Fingerprint]: sha256:v3:a616b309c8d9dc9ffb31f9ed0dad2946dcbff58cd30d842884f8f5d484e64d42
[Planned Source]: d7bdf24e3ef557cbb51dde1bca64a117bed8067af822274c155c0bba02c949a4

- A. Approve Plan
- B. Request Changes
- C. I'll edit the files

[Answer]: A. Approve Plan

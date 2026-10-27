# Feasibility Assessment — Artist Recommendation App Rebuild

Inputs: the intent statement (`ideation/intent-capture/intent-statement.md`) and the answers in `feasibility-questions.md`. No market research was run for this plan.

## Verdict

**Feasible, with low technical risk.** This is a rebuild of an app that already works on the owner's machine, with the same tools (Q2), the same data (Q1) and no deadline (Q4). The open risks are about scope and measurement, not about whether it can be built.

## Technical Viability

| Area | Assessment | Basis |
|------|-----------|-------|
| Data | Available now. The ListenBrainz statistics dump and the MusicBrainz dump are already downloaded and extracted in `../listenbrainz`, and the rebuild reads them in place. | Q1; observed in `../listenbrainz` |
| Tools | Proven for this problem: the current app already does collaborative filtering, similar-artist lookup, the artist map and the evaluation tools with them. Keeping them (Q2) removes most technical uncertainty. | Q2; intent statement |
| Compute | **Hypothesis:** 32 to 64 GB of memory (Q3) is enough to train on the full dump, because the current app's model was trained (assumption: on this same machine). To be confirmed in the first pipeline run. | Q3 |
| Lookup speed | **Hypothesis:** under 200 ms per similar-artist lookup on the owner's machine (intent statement) is reachable, because lookups read a precomputed index rather than training anything per request. To be measured in Build and Test. | Intent statement success metrics |
| Quality parity | Measurable: hand-labelled relevance judgments exist in `../listenbrainz/results/`, and the current app already scores lists against them. The rebuild needs the same scoring method so the comparison is like for like. | Intent statement; observed in `../listenbrainz` |
| Cost | Zero. Everything runs locally and there is no budget (Q5), which matches a first version without public hosting (intent statement). | Q5 |
| Privacy | Low exposure: only artist-level results are shown (Q6), there are no user accounts in the first version (intent statement), and no listener-level data leaves the pipeline. | Q6 |

## Risk Analysis

Key risks (full list in `raid-log.md`):

- **Scope size for an mvp (medium).** The first version includes the artist map and the experiment and evaluation tools as well as similar-artist search (intent statement). That is the whole current app, not just its core.
- **Undecided re-runnable pipeline (medium).** The intent lists a re-runnable pipeline for new dumps as a reason for the rebuild, but not as an in-scope or out-of-scope item. Scope Definition should settle it.
- **Dependence on files in another folder (low).** Reading the dumps in place (Q1) ties the rebuild to `../listenbrainz`; its location must be a setting, not a hard-coded path.
- **Deploying later with no budget (low, later).** You want to deploy eventually (intent statement), but there is no budget and no host yet (Q5, Q7). Not a first-version concern, but it may limit hosting choices later.

## Recommendation

Proceed to Scope Definition, and settle there whether the re-runnable pipeline is in the first version and whether the map and experiment tools are core or stretch.

## Assumptions & Open Questions

- [assumption] The current app's model was trained on the same 32 to 64 GB machine, so the same pipeline fits in memory.
- [assumption] The licences of the ListenBrainz and MusicBrainz dumps allow personal use and, later, a small shared deployment. Check the exact terms before any public hosting.

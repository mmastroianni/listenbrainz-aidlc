# Intent Statement — Artist Recommendation App Rebuild

## Problem Statement

An app that recommends musical artists through collaborative filtering already exists at `../listenbrainz`, and it is to be rebuilt from scratch using AI-DLC. [desc]

The main purpose of the rebuild is to learn AI-DLC on a problem the owner already understands; a secondary purpose is to clean up the existing app. [Q1]

The current app runs only on localhost, and the owner wants to be able to deploy it somewhere at some point. [Q1]

## Target Customer

The rebuilt app is for the owner plus a few friends or colleagues. [Q2]

Those users come to the app to type in an artist they like and get similar artists back. [Q3]

The first version also includes a visual map of how artists relate to each other, and the experiment and evaluation tools (genre reranking and relevance scoring). [Q9]

## Success Metrics

| Metric | Pass criterion | Source |
|--------|----------------|--------|
| Feature parity | Artist search, similar artists, the artist map, and the experiment and evaluation tools all work end to end in the new app | [Q4] [Q9] |
| Recommendation quality | Quality is at least equal to the current app's, measured on the owner's hand-labelled relevance judgments | [Q4] |
| Lookup speed | A similar-artist lookup answers in under 200 milliseconds on the owner's own machine | [Q4] [Q11] |
| Method learned | The owner completes a full AI-DLC run and can use the method on a next project | [Q4] |

## Initiative Trigger

The rebuild is happening now because the owner wants to learn AI-DLC and sees this as a good first project. [Q5]

The owner also wants a pipeline that can be re-run easily when a new ListenBrainz dump comes out. [Q5]

The owner plans to share or host the app, and the current version is not ready for that. [Q5]

## Initial Scope Signal

**Workflow-selected scope:** `mvp` (ship the core, skip operations). [scope]

**User-confirmed product boundary for the first version:**

- Out of the first version: public hosting or cloud deployment, and user accounts or sign-in. [Q8]
- In the first version: artist search with similar artists, the visual artist map, and the experiment and evaluation tools. [Q3] [Q9]

## Assumptions & Open Questions

- [assumption] How the few other users reach the app while it is not publicly hosted is not yet defined (Q10 answered "Not yet defined"); until it is settled, the first version is treated as used only on the owner's machine.

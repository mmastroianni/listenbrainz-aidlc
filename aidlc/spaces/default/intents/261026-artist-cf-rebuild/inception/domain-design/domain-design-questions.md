# Domain Design — Questions

Context: the requirements (`inception/requirements-analysis/requirements.md`) and stories (`inception/user-stories/stories.md`) point to these building blocks: data preparation from the dumps, learning artist similarity, artist details and genres, name search, similar-artist lookup, and the web page. Three boundary choices have more than one sensible answer. Each lists my recommendation first.

## Q1. [Architect] Where name search lives

Name search (suggestions as you type) looks up artists by name, and the artist catalogue already owns names, descriptions, genres and listener counts.

A. Part of the artist catalogue: search is a query over data the catalogue already owns; one place to change when names change (recommended)
B. A separate search component with its own copy of names: can change independently, but two copies of artist names must stay in step
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Q2. [Architect] Data preparation and training: one block or two

Preparing listen counts from the dump and learning similarity from them are both heavy batch steps.

A. Two components: each is its own documented rebuild step, and training can be re-run (for example with new settings) without re-reading the 20+ GB dump (recommended)
B. One component: fewer pieces, but any training change means re-running the whole dump read
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Q3. [Architect] Who combines similarity scores with artist details

A similar-artists result needs both the nearest neighbours (from the similarity index) and names, genres and links (from the catalogue).

A. The web layer asks the index for neighbour ids and scores, then asks the catalogue for details: the index knows nothing about names or genres (recommended)
B. The similarity index returns fully detailed results itself: one call, but the index then depends on the catalogue
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Name search (Q1): part of the artist catalogue, one copy of artist names.
- Batch steps (Q2): two components, data preparation and similarity training, so training can be re-run without re-reading the dump.
- Combining results (Q3): the web layer asks the similarity index for neighbour ids and scores, then the catalogue for details; the index knows nothing about names or genres.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

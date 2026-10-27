# Units Generation — Questions

Context: Domain Design defined six components (`inception/domain-design/components.md`): DumpSource, ListeningDataPrep, SimilarityTraining, ArtistCatalog, SimilarityIndex and WebApp. Units of work group them for building. The walking skeleton is on (team practices), so the first unit must be a thin slice that runs end to end. Each unit later goes through its own design, code and test steps, so the number of units also drives how long and how costly Construction is.

## Q1. [Architect] How many units

How should the six components be grouped?

A. Three units: (1) the walking skeleton, a thin slice through every component on sample data; (2) the full data pipeline and artist catalogue (all prep rules, full-size training, genres, name search, rebuild steps); (3) the full web page (suggestions, results, show more, links, addresses, messages, phone and keyboard) (recommended: fewest rounds of Construction)
B. Six units: the skeleton, then one unit per component (finer control, about twice the Construction work)
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Q2. [Architect] How it runs

How should the finished system be run?

A. One web app process for the page and its endpoints, plus pipeline commands run by hand in documented order (like the current app) (recommended)
B. Separate processes for search, lookup and the page
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Units (Q1): three units: u1-skeleton (thin slice through every component on sample data), u2-pipeline (full data prep, full-size training, artist catalogue with genres and name search, rebuild steps), u3-web (the full page: suggestions, results, show more, links, addresses, messages, phone and keyboard).
- Running (Q2): one web app process for the page and its endpoints, plus pipeline commands run by hand in documented order.
- Dependencies: u2-pipeline and u3-web each build on u1-skeleton and do not depend on each other.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

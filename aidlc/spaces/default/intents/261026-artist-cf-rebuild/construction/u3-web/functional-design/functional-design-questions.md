# Functional Design (u3-web) — Questions

Context: u3-web is the one-page site and its endpoints (`inception/units-generation/unit-of-work.md`). The page's look, states, links and keyboard behaviour were settled in Refined Mockups (`inception/refined-mockups/`), the endpoints in contract C3, and the way the page is tested in the accessibility checklist (page and endpoint tests where possible, plus a manual keyboard pass before `v0.1.0`). The skeleton already answers `GET /api/artists/{mbid}/similar` with names, bars and links, and u2-pipeline has built the name search. Looking at the current app (`../listenbrainz/src/listenbrainz_recs/app/static/`) answers the remaining build choices, so they are recorded as decisions in the design rather than asked again:

- The page is plain HTML, CSS and JavaScript files served by the web app, like the current app; there is no framework or build step.
- The page loads nothing from other websites (no fonts, scripts or images from elsewhere).
- Artist names and descriptions are put on the page as text, never as markup.
- The look uses the current app's colours, fonts and spacing, listed in `inception/refined-mockups/design-system-mapping.md`.
- The current app's extras (the 10, 20 or 50 selector, saved artists, the map link) are not part of the core scope and are left out.

One gap found while reading u2-pipeline's build: an artist can be in the catalogue (so suggestions show it) but have no vector in the index, because its vector had zero length. The skeleton's endpoint would answer "unknown artist" for it. The design treats it as "not enough listening data" instead, because the app does know the artist. No question is needed, but it is part of what you are confirming.

No other choice needs your judgement, so there are no questions.

## Consolidated Summary Confirmation

- Build: plain HTML, CSS and JavaScript served by the web app; nothing loaded from other sites; names and descriptions shown as text only.
- Endpoints: a new `GET /api/suggest?q=` returning up to 10 artists (name, description, genres, id), empty for no match or blank text; the similar-artists endpoint keeps its shape, with "show more" paging 20 at a time.
- Pages: `/` and `/artist/<id>` serve the same page; the page reads the address to know which artist to show, and Back and bookmarks work through the browser history.
- Missing from the index: an artist in the catalogue but not in the index gets "Not enough listening data to find artists like <name>."; an id in neither gets "We don't know this artist."
- Behaviour: the search box is focused on load; suggestions appear 150 ms after the last keystroke and a late reply is discarded; Down, Up, Enter and Escape work; results show five placeholder rows while loading; errors show the plain message and a Retry button; Show more is disabled while loading and disappears when the list ends.
- Quality check (FR8.1): a small command writes a sheet with the new app's top 20 for up to 5 artists you name; you add the current app's verdicts by eye; a second command reads the sheet and says pass or fail (at least 4 of 5 at least as good). The 5 artists are chosen when you run it, not now.
- Testing: endpoint tests with the test client written first; page tests check the served HTML and files (labels, roles, no outside links); the keyboard and phone pass is done by hand before `v0.1.0`, as the accessibility checklist says.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

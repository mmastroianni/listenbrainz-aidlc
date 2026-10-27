# Business Rules — u3-web

Sources: `inception/requirements-analysis/requirements.md`, `inception/user-stories/stories.md`, `inception/contract-design/contract-summary.md` (C1, C3), `inception/refined-mockups/` (mockups, interaction spec, accessibility checklist, design mapping), `functional-design-questions.md`, and the skeleton's and u2-pipeline's rules (`construction/u1-skeleton/functional-design/rules.md`, `construction/u2-pipeline/functional-design/rules.md`).

```yaml
rules:
  - id: BR1.1
    statement: The suggestion endpoint returns up to 10 artists for the typed text, in the order the catalogue gives, or an empty list.
    category: policy
    applies_to: SuggestRequest
    trigger: GET /api/suggest
    logic: ask ArtistCatalog.suggest for the text with limit 10 and return its artists unchanged in order, each as a PublicArtist; no match or blank text gives []
    violation: n/a
    source: FR4.1, FR4.2, FR4.3, FR4.5, contract C3
  - id: BR1.2
    statement: Typed text longer than 200 characters is refused.
    category: validation
    applies_to: SuggestRequest
    trigger: GET /api/suggest
    logic: IF q is missing OR longer than 200 characters THEN refuse with 422
    violation: a short JSON message naming q; no stack trace
    source: contract C3
  - id: BR1.3
    statement: No response contains listener data.
    category: constraint
    applies_to: PublicArtist, SimilarItem
    trigger: every response
    logic: build every artist from the allow-list mbid, name, description, genres; other fields are never copied
    violation: n/a
    source: FR5.9, NFR3
  - id: BR1.4
    statement: Both endpoints add no work beyond one catalogue or index call and a small amount of composing.
    category: constraint
    applies_to: WebApp
    trigger: every request
    logic: no scan of the catalogue, no per-row remote call, and no per-request file reads beyond the open read-only handles
    violation: n/a
    source: NFR1
  - id: BR2.1
    statement: Similar artists come 20 at a time, most similar first, never including the artist itself, and the list ends exactly when the artists run out.
    category: policy
    applies_to: SimilarPage
    trigger: GET /api/artists/{mbid}/similar
    logic: ask SimilarityIndex for offset and limit (default 0 and 20); has_more is true only when more artists exist beyond this page, so exactly 20 available gives has_more false
    violation: n/a
    source: FR5.1, FR5.4
  - id: BR2.2
    statement: The bar is the cosine divided by the top cosine of the artist's list, on the same scale for every page.
    category: calculation
    applies_to: SimilarItem
    trigger: composing a page
    logic: top = cosine of the artist's first neighbour (looked up again when offset > 0); bar = clamp(cosine / top, 0, 1); bar = 0 when top is not above 0
    violation: n/a
    source: FR5.3
  - id: BR2.3
    statement: An artist the catalogue knows but the index does not has too little data, not an unknown identity.
    category: validation
    applies_to: SimilarPage
    trigger: the index reports the id as unknown
    logic: IF the id is in the catalogue THEN return the artist with items [] and has_more false ELSE see BR2.5
    violation: n/a
    source: FR5.7
  - id: BR2.4
    statement: Each result carries three plain links built from the id and the URL-encoded name.
    category: policy
    applies_to: SimilarItem
    trigger: composing a page
    logic: musicbrainz = https://musicbrainz.org/artist/<id>; youtube = https://www.youtube.com/results?search_query=<name>; spotify = https://open.spotify.com/search/<name>; the app makes no call to any of them
    violation: n/a
    source: FR5.2 as changed in Refined Mockups
  - id: BR2.5
    statement: An id the app does not know at all is reported as unknown.
    category: validation
    applies_to: SimilarPage
    trigger: the id is in neither the index nor the catalogue
    logic: answer 404 with a short message; an id that is not a 36-character id, or a bad offset or limit, answers 422
    violation: the page shows "We don't know this artist."
    source: FR5.8
  - id: BR3.1
    statement: The root address and every artist address serve the same page.
    category: policy
    applies_to: WebApp pages
    trigger: GET / and GET /artist/{mbid}
    logic: return the one page for both; the page reads the id from the address and loads that artist's results; a malformed id is not refused by the page route, so the page itself shows the unknown message
    violation: n/a
    source: FR5.6, FR6.1
  - id: BR3.2
    statement: The page loads nothing from any other website.
    category: constraint
    applies_to: page files
    trigger: always
    logic: every script, stylesheet and image is served by the app itself; the only outside addresses are the three result links, which open only when the user clicks
    violation: n/a
    source: NFR4, NFR8
  - id: BR3.3
    statement: Artist names and descriptions are shown as text, never as markup.
    category: constraint
    applies_to: page behaviour
    trigger: putting any response value on the page
    logic: set text content only; build addresses with encoding; never insert response values as HTML
    violation: n/a
    source: NFR3
  - id: BR4.1
    statement: The search box is focused when the page loads.
    category: policy
    applies_to: ArtistSearch
    trigger: page load
    logic: focus the box on load, so typing goes into it
    violation: n/a
    source: FR6.3
  - id: BR4.2
    statement: Suggestions are fetched 150 ms after the last keystroke, only the newest reply is shown, and blank text shows nothing and asks for nothing.
    category: policy
    applies_to: SuggestionState
    trigger: typing
    logic: wait 150 ms without input; IF the text is blank THEN close the list and send no request ELSE ask /api/suggest and tag the request with the next number; show a reply only when its number is the newest
    violation: a late older reply is dropped
    source: FR4.1, FR4.5
  - id: BR4.3
    statement: No match shows "No artists match '<text>'" in the suggestion list.
    category: policy
    applies_to: SuggestionState
    trigger: an empty reply for non-blank text
    logic: show the message with the typed text, as text
    violation: n/a
    source: FR4.5
  - id: BR4.4
    statement: The page works by keyboard.
    category: policy
    applies_to: ArtistSearch, ResultsList
    trigger: key presses
    logic: Down and Up move the highlight through the suggestions; Enter picks the highlighted one; Escape closes the list; Tab leaves the list and reaches every result name, every link and the Show more button in visual order; every focusable element shows the focus ring
    violation: n/a
    source: FR6.3
  - id: BR4.5
    statement: Each suggestion shows the name, the first genre and the description when there is one.
    category: policy
    applies_to: SuggestionState
    trigger: showing suggestions
    logic: line one the name; line two the description (omitted when none) and the first genre (omitted when none), joined by a dot; same-name artists are separate rows
    violation: n/a
    source: FR4.4
  - id: BR4.6
    statement: Picking an artist moves to its own address and adds a history entry.
    category: policy
    applies_to: PageState
    trigger: picking a suggestion or clicking a result's name
    logic: push /artist/<id> onto the browser history, load that artist, clear the suggestions, and move focus to the results heading; Back and Forward load the artist in the address without a new entry
    violation: n/a
    source: FR5.5, FR5.6
  - id: BR4.7
    statement: Each result row shows rank, name, bar, genres and links.
    category: policy
    applies_to: ResultsList
    trigger: results returned
    logic: heading "Artists like <name>"; each row has its rank, the name as a button, a bar whose width is bar times 100 percent with the tooltip and screen-reader text "similarity <cosine to two decimals>" (never a percentage, never colour alone), up to 3 genres or "no genres listed" in the muted colour, and the three links each opening in a new tab with rel noopener and a label such as "Anthony Braxton on YouTube"
    violation: n/a
    source: FR5.2, FR5.3, FR3.2
  - id: BR4.8
    statement: Show more adds the next 20, once per click, and disappears when the list ends.
    category: policy
    applies_to: PageState
    trigger: clicking Show more
    logic: IF busy THEN ignore ELSE set busy, ask for offset = shown, append the rows, move focus to the first new row, announce the new rows politely, set hasMore from the reply; the button is disabled while busy and removed when hasMore is false; the address does not change
    violation: n/a
    source: FR5.4
  - id: BR4.9
    statement: Every state has a plain message and the search box stays usable.
    category: policy
    applies_to: ResultsList
    trigger: loading, empty, unknown or failed results
    logic: loading shows 5 placeholder rows; an empty list shows "Not enough listening data to find artists like <name>."; a 404 shows "We don't know this artist."; any other failure shows "Something went wrong finding similar artists. Try again." with a Retry button that repeats the failed request once per click; no status code, path or stack text is ever shown
    violation: n/a
    source: FR5.7, FR5.8, FR6.5
  - id: BR4.10
    statement: The clear button empties the box and keeps the results.
    category: policy
    applies_to: ArtistSearch
    trigger: clicking the clear button
    logic: empty the text, close the suggestions, keep the current results and the address
    violation: n/a
    source: refined mockups (closes review finding R-03)
  - id: BR4.11
    statement: Clicking a similar artist's name explores it; clicking its external link leaves the results alone.
    category: policy
    applies_to: ResultRow
    trigger: clicking a name or a link
    logic: a name click follows BR4.6; a link click opens a new tab and changes nothing on the page
    violation: n/a
    source: FR5.5
  - id: BR4.12
    statement: The page fits a 375 pixel phone and wraps long names.
    category: constraint
    applies_to: page styles
    trigger: any screen width
    logic: below 768 px the results stack in one column (name, bar, then genres and links); long names and descriptions wrap on word breaks and are never cut mid-word, except suggestion descriptions on a phone, which end with an ellipsis; nothing causes sideways scrolling at 375 px or at 200% zoom; touch targets for links are at least 44 by 44 px on phones
    violation: n/a
    source: FR6.2, FR6.6
  - id: BR4.13
    statement: The page follows the current app's look.
    category: policy
    applies_to: page styles
    trigger: always
    logic: use the colours, fonts, radii and focus ring in design-system-mapping.md; one h1 for the page and one h2 for the results; the page language is declared; status messages sit in a polite live region
    violation: n/a
    source: FR6.4
  - id: BR5.1
    statement: A command writes the quality-check sheet from the new app's lists.
    category: policy
    applies_to: QualityCheckSheet
    trigger: the owner runs the generate command with up to 5 artist names or ids
    logic: for each artist find it by name (or take the id), list the new app's top 20 names with genres, and write a markdown sheet with a verdict line per artist left unset; stop with a message when an artist name matches nothing; more than 5 artists is refused
    violation: message naming the artist that matched nothing
    source: FR8.1
  - id: BR5.2
    statement: The check passes when at least 4 of the 5 artists are marked at least as good.
    category: calculation
    applies_to: QualityCheckSheet
    trigger: the owner runs the verdict command on the filled sheet
    logic: count verdicts better-or-equal; IF any verdict is unset THEN result incomplete ELSE pass when the count is at least 4, otherwise fail; print the count and the result
    violation: an unreadable sheet stops with a message naming the line
    source: FR8.1
  - id: BR5.3
    statement: The sheet holds only artist-level data.
    category: constraint
    applies_to: QualityCheckSheet
    trigger: writing the sheet
    logic: write names, ids, genres and verdicts only; no listener numbers or counts
    violation: n/a
    source: FR5.9, NFR3
```

| Rule | Summary |
|------|---------|
| BR1.1–BR1.4 | Suggestion endpoint, text limit, no listener data, no extra per-request work |
| BR2.1–BR2.5 | Paging, bar scale, missing-from-index vs unknown, links, 404 and 422 |
| BR3.1–BR3.3 | One page for both addresses, nothing from other sites, text only |
| BR4.1–BR4.13 | Focus, suggestions, keyboard, history, rows, Show more, states, clear button, phone layout, look |
| BR5.1–BR5.3 | Quality-check sheet, pass rule, artist-level data only |

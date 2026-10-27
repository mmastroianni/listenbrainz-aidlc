# Manual checks before v0.1.0

The page script is not run by any automated test (there is no browser in the test run), so this
keyboard and phone pass is done by hand once, before tagging `v0.1.0`. It follows
`aidlc/spaces/default/intents/261026-artist-cf-rebuild/inception/refined-mockups/accessibility-checklist.md`.

Setup: build the data (or use a sample build), start `uv run listenbrainz-recs-serve`, and open
`http://127.0.0.1:8000/` in a browser. For the phone items use the browser's device mode at 375 px
wide, or a phone on the same network only if you start the app with `--host` on purpose.

## Keyboard

- [ ] The search box is focused when the page loads; typing goes straight into it (AC2.4.2).
- [ ] Down and Up move through the suggestions, Enter picks the highlighted one, Escape closes the list (AC2.4.3).
- [ ] Tab reaches every result name, every icon link and "Show more" in visual order (AC2.4.4).
- [ ] Every focusable element shows the focus ring (a light blue 3 px outline).
- [ ] There is no keyboard trap: Tab always leaves the suggestions list.
- [ ] After "Show more", focus moves to the first new row.
- [ ] After picking an artist, focus moves to the "Artists like ..." heading.

## Behaviour

- [ ] Typing quickly sends one suggestion request per pause (watch the network panel); blank text sends none.
- [ ] A slow or late suggestion reply never replaces the newest one.
- [ ] Clicking "Show more" twice quickly adds only one page of 20.
- [ ] The clear button empties the box and keeps the results.
- [ ] Picking an artist changes the address to `/artist/<id>`; Back and Forward return to earlier artists; opening `/artist/<id>` directly shows that artist.
- [ ] Clicking a similar artist's name explores that artist; clicking an icon link opens a new tab and leaves the results alone.
- [ ] A made-up address such as `/artist/not-an-id` shows "We don't know this artist." and the search box still works.
- [ ] With the app stopped, picking an artist shows "Something went wrong finding similar artists. Try again." and a Retry button; Retry works once the app is back.

## Screen readers (good practice)

- [ ] The search box is announced with the label "Artist" as a combobox with a list of suggestions.
- [ ] Each similarity bar is read as "similarity 0.87" (the number, not a percentage).
- [ ] Each icon link is read with its label, for example "Anthony Braxton on YouTube".
- [ ] Status messages (no match, not enough data, new rows after "Show more") are announced politely.
- [ ] The page has one main heading and one results heading, and its language is English.

## Visual and phone (375 px)

- [ ] Text contrast is readable; the similarity is never shown by colour alone.
- [ ] Long names wrap on word breaks and are not cut mid-word.
- [ ] At 375 px wide there is no sideways scroll, and also at 200% zoom.
- [ ] On the phone layout each row stacks the name, the bar, then the genres and links.
- [ ] Suggestion descriptions end with an ellipsis on a phone rather than wrapping.
- [ ] The three icon links are at least 44 by 44 px touch targets on the phone layout.

## Speed (after a full-size rebuild)

- [ ] `uv run listenbrainz-recs-speed` passes: both lookups under 200 ms at the 95th percentile (AC1.1.6, AC2.1.6).

## Quality check

- [ ] The quality-check sheet is filled in and `uv run listenbrainz-recs-quality-verdict` says `pass` (see the README).

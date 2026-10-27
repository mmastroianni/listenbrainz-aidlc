# Interaction Specification

Component specs for the one page in `mockups.md`, following the component-spec template. Sources: the wireframes and user flow (`ideation/rough-mockups/`), the stories (`inception/user-stories/stories.md`), the requirements (`inception/requirements-analysis/requirements.md`) and the team practices (`inception/practices-discovery/team-practices.md`).

## Addresses and Navigation

| Address | Shows |
|---------|-------|
| `/` | Start state |
| `/artist/<mbid>` | Results for that artist (FR5.6, US3.2) |

- Picking a suggestion or clicking a result's name moves to `/artist/<mbid>` and adds a browser history entry, so Back returns to the previous artist (AC3.2.1).
- Opening `/artist/<mbid>` directly loads that artist's results (AC3.2.2); an unknown id shows "We don't know this artist." (FR5.8).
- "Show more" does not change the address; returning by Back shows the first 20 again.

## ArtistSearch

| Field | Value |
|---|---|
| Component | ArtistSearch |
| Description | Search box with suggestions as you type |
| Category | input |

### States

| State | Description | Trigger |
|---|---|---|
| default | Empty box, focused on page load | page load |
| typing | Suggestions fetched after 150 ms without a keystroke | input |
| suggestions-open | Up to 10 suggestions listed | suggestions returned |
| no-match | "No artists match '<text>'" | zero suggestions |
| blank | No list shown | whitespace-only text |

### Props / Inputs

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| query | string | yes | "" | Text typed |
| onPick | function | yes | — | Called with the chosen artist |

### Responsive Behaviour

| Breakpoint | Behaviour |
|---|---|
| mobile (<768px) | Full width; long descriptions cut with an ellipsis |
| desktop (>1024px) | 800 px column |

### Accessibility

| Requirement | Implementation |
|---|---|
| ARIA role | `combobox` with a `listbox` of suggestions |
| Keyboard interaction | Down/Up move, Enter picks, Escape closes, Tab leaves |
| Label / aria-label | Visible label "Artist" |
| Contrast ratio | WCAG AA (4.5:1 text, 3:1 UI components) |
| Screen reader | Announces the number of suggestions and the highlighted one |
| Focus management | After a pick, focus moves to the results heading |

Only the most recent request's suggestions are shown; an older response arriving late is discarded.

## ResultsList

| Field | Value |
|---|---|
| Component | ResultsList |
| Description | Similar artists for the chosen artist |
| Category | display |

### States

| State | Description | Trigger |
|---|---|---|
| loading | 5 placeholder rows | request in flight |
| populated | 20 rows, then 20 more per "Show more" | results returned |
| not-enough-data | Message from FR5.7 | artist has no neighbours |
| unknown | "We don't know this artist." | unknown id |
| error | Error message and Retry | request failed |

### Props / Inputs

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| artistId | string | yes | — | MusicBrainz id of the chosen artist |
| pageSize | number | no | 20 | Rows per page |

### Responsive Behaviour

| Breakpoint | Behaviour |
|---|---|
| mobile (<768px) | Name, bar, then genres and links stacked |
| desktop (>1024px) | Name, bar and links on one line, genres below |

### Accessibility

| Requirement | Implementation |
|---|---|
| ARIA role | Ordered list; heading `h2` "Artists like <name>" |
| Keyboard interaction | Tab reaches each name, each link and "Show more" |
| Label / aria-label | Each link labelled "<artist> on MusicBrainz / YouTube / Spotify" |
| Contrast ratio | WCAG AA |
| Screen reader | Bar read as "similarity 0.87"; new rows after "Show more" announced politely |
| Focus management | After "Show more", focus moves to the first new row |

## ResultRow

| Field | Value |
|---|---|
| Component | ResultRow |
| Description | One similar artist |
| Category | display |

- **Name** (button-styled link): moves to `/artist/<mbid>` (US3.1).
- **Bar:** width = score / top score; tooltip and accessible text "similarity <cosine to 2 decimals>" (Q1).
- **Genres:** up to 3 tags, else "no genres listed" (FR3.2).
- **Links:** MusicBrainz `https://musicbrainz.org/artist/<mbid>`; YouTube `https://www.youtube.com/results?search_query=<name>`; Spotify `https://open.spotify.com/search/<name>`; names URL-encoded; all `target="_blank"` with `rel="noopener"`.

## ShowMore and Retry

- **ShowMore:** button; fetches the next 20; disabled while loading so a double click never adds twice; removed when no more results exist (FR5.4).
- **Retry:** button; repeats the failed request once per click.

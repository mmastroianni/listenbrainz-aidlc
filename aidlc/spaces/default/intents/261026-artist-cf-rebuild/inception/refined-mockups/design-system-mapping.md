# Design System Mapping

The look follows the current app (rough-mockups answer Q8; `ideation/rough-mockups/wireframes.md`). Its stylesheet in `../listenbrainz/src/listenbrainz_recs/app/static/style.css` is the reference; there is no separate component library. Applies to the screens in `mockups.md`, the stories in `inception/user-stories/stories.md` and the requirements in `inception/requirements-analysis/requirements.md`, with the team's code style from `inception/practices-discovery/team-practices.md`.

## Design Tokens (from the current app)

| Token | Value | Use |
|-------|-------|-----|
| `--ink` | `#1d2939` | Body text |
| `--muted` | `#617184` | Genres, hints, status text |
| `--line` | `#e2e8ef` | Borders, row dividers |
| `--accent` | `#176b80` | Eyebrow, bars, focus |
| `--surface` | `#fff` | Panels |
| `--bg` | `#f5f7f9` | Page background |
| Focus ring | `3px solid #93d3e1`, offset 2px | Every focusable element |
| Font | `system-ui` stack, 16px / 1.5 | All text |
| Panel radius | 14px | Search and results panels |
| Input radius | 9px | Search box, suggestions |

## Component Mapping

| Component (interaction-spec.md) | Current app element |
|---------------------------------|---------------------|
| Page shell | `.shell` (max width 800px) |
| ArtistSearch | `.search-area`, `input[type=search]`, `.suggestions` |
| ResultsList | `.results`, `.recommendations` |
| ResultRow | `.recommendations li`, `.rank`, `.artist-link` |
| Status messages | `.status` |
| Links | New: three icon links, 24 px, `--muted` turning `--accent` on hover |
| Similarity bar | New: 6 px tall, `--accent` on `--line` track |

## New Elements

- **Icon links:** a MusicBrainz mark, a play triangle (YouTube) and a music note (Spotify) as inline SVG with `aria-label`; no brand logos are bundled, so no licensing issue.
- **Similarity bar:** a plain element sized by width percentage of the top score; the colour is never the only signal (the tooltip and screen-reader text carry the value).

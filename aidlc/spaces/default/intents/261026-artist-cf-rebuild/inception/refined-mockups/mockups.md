# Mockups — Similar Artists Page (Mid Fidelity)

Builds on the wireframes and user flow (`ideation/rough-mockups/wireframes.md`, `user-flow.md`), the stories (`inception/user-stories/stories.md`), the requirements (`inception/requirements-analysis/requirements.md`) and the team practices (`inception/practices-discovery/team-practices.md`). The look follows the current app's style (`design-system-mapping.md`). Core scope only: no map, no experiment tools.

## Change to the Requirements

Each result now carries **three links**: the artist's MusicBrainz page, a YouTube search and a Spotify search (refined-mockups-questions.md Q3). FR5.2 and AC2.1.2 named a MusicBrainz link only. Both search links are plain web addresses that need no sign-in or API key, so the no-paid-services and no-listener-data rules are unaffected.

## Page Layout (desktop, width 800 px centred)

```
+--------------------------------------------------------------+
| SIMILAR ARTISTS (eyebrow)                                    |
| Find artists like the ones you love           (h1)           |
| Based on what ListenBrainz listeners play.    (intro)        |
|                                                              |
| +----------------------------------------------------------+ |
| | Artist                                         (label)   | |
| | +------------------------------------------------------+ | |
| | | Henry Threadgill                                 [x] | | |
| | +------------------------------------------------------+ | |
| +----------------------------------------------------------+ |
|                                                              |
| +----------------------------------------------------------+ |
| | Artists like Henry Threadgill                   (h2)     | |
| |                                                          | |
| |  1  Anthony Braxton        ########..     [MB][>][S]     | |
| |     free jazz, avant-garde jazz                          | |
| |  2  Muhal Richard Abrams   #######...     [MB][>][S]     | |
| |     avant-garde jazz, jazz                               | |
| |  ...                                                     | |
| | 20  Steve Coleman          #####.....     [MB][>][S]     | |
| |     jazz                                                 | |
| |                                                          | |
| |                  [ Show more ]                           | |
| +----------------------------------------------------------+ |
+--------------------------------------------------------------+
```

- **Heading:** name only, "Artists like Henry Threadgill" (Q2).
- **Similarity bar:** the cosine score scaled so the first result's bar is full (requirements FR5.3). The raw cosine (for example 0.87) shows as a tooltip on hover and is read out by screen readers; it is never shown as a percentage (Q1).
- **Links:** `[MB]` opens `https://musicbrainz.org/artist/<mbid>`, `[>]` opens a YouTube search for the artist's name, `[S]` opens a Spotify search for the artist's name. All open in a new tab.
- **Clear button `[x]`:** empties the search box, closes suggestions and keeps the current results (closes review finding R-03 from Rough Mockups).

## Suggestions Open (desktop)

```
| +------------------------------------------------------+ |
| | henry thr|                                            | |
| +------------------------------------------------------+ |
| | Henry Threadgill                                     | |
| |   US jazz saxophonist and composer · jazz            | |
| | Henry Threadgill Sextett                             | |
| |   jazz                                               | |
| +------------------------------------------------------+ |
```

Each suggestion shows the name, then the MusicBrainz description (when one exists) and the first genre (FR4.4). Up to 10 suggestions show, closest text match first, then by listener count (FR4.2).

## Phone (375 px)

```
+-----------------------------+
| Find artists like the       |
| ones you love               |
| +-------------------------+ |
| | henry thr|          [x]  | |
| +-------------------------+ |
| | Henry Threadgill        | |
| |   US jazz saxophonist...| |
| +-------------------------+ |
+-----------------------------+

+-----------------------------+
| Artists like                |
| Henry Threadgill            |
|                             |
| 1 Anthony Braxton           |
|   ########..                |
|   free jazz   [MB][>][S]    |
| 2 Muhal Richard Abrams      |
|   #######...                |
|   avant-garde jazz [MB][>][S]|
|      [ Show more ]          |
+-----------------------------+
```

On a phone the suggestions list fills the width under the box and long descriptions are cut with an ellipsis. Each row stacks name, bar, then genres and links, with no sideways scroll (FR6.2; closes Rough Mockups finding R-04).

## States

| State | Mockup |
|-------|--------|
| Start | Search box focused, results panel hidden, intro text visible |
| Loading | Results panel shows 5 grey placeholder rows (rarely seen under 200 ms) |
| Populated | As above |
| No match | Suggestions list shows "No artists match 'zzqqxx'" |
| Not enough data | Results panel shows "Not enough listening data to find artists like <name>." |
| Unknown artist address | Results panel shows "We don't know this artist." |
| Error | Results panel shows "Something went wrong finding similar artists. Try again." and a [Retry] button |
| Show more exhausted | "Show more" button removed |
| No genres | "no genres listed" in the muted colour |

## Story Coverage

| Story | Where |
|-------|-------|
| US1.1, US1.2 | Suggestions open |
| US2.1 | Page layout (rows, bar, links) |
| US2.2 | "Show more" |
| US2.3 | States |
| US2.4 | Phone layout; `accessibility-checklist.md` |
| US3.1, US3.2 | `interaction-spec.md` (click and addresses) |
| US4.x, US5.1 | No screens (owner command-line work) |

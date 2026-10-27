# Wireframes — Similar Artists (Low Fidelity)

Inputs: the intent statement (`ideation/intent-capture/intent-statement.md`), the scope document and the intent backlog (`ideation/scope-definition/scope-document.md`, `intent-backlog.md`: items IB-4 and IB-5), and `rough-mockups-questions.md`. Only the core first version is sketched. The artist map and the experiment tools are stretch, so they are not drawn here.

## Information Architecture

One page (Q1), with no navigation beyond it:

```
Similar Artists (single page)
  |
  +-- Search box with suggestions
  |
  +-- Selected artist header
  |
  +-- Similar artists list (20, then "Show more")
```

The look follows the current app's style (Q8). The layout works on desktop and phone browsers (Q6).

## Screen 1: Start (empty state)

The user has not picked an artist yet.

```
+------------------------------------------------------+
| Similar Artists                                      |
+------------------------------------------------------+
|  Find artists like...                                |
|  +------------------------------------------------+  |
|  | Type an artist name                            |  |
|  +------------------------------------------------+  |
|                                                      |
|  Start typing an artist you like to see similar      |
|  artists, based on what ListenBrainz listeners play. |
+------------------------------------------------------+
```

Accessibility: h1 "Similar Artists"; landmarks header and main; keyboard entry point is the search box, focused on page load.

## Screen 2: Typing (suggestions)

Suggestions appear as the user types, and they pick one (Q2).

```
+------------------------------------------------------+
| Similar Artists                                      |
+------------------------------------------------------+
|  +------------------------------------------------+  |
|  | henry thr|                                     |  |
|  +------------------------------------------------+  |
|  | Henry Threadgill                     jazz      |  |
|  | Henry Threadgill Sextett             jazz      |  |
|  | Henry Threadgill & Make a Move       jazz      |  |
|  +------------------------------------------------+  |
+------------------------------------------------------+
```

- Each suggestion shows a genre beside the name, so users can tell apart artists who share a name.
- No matches: the list reads "No artists match 'xyz'".

Accessibility: suggestions are reachable by keyboard (Up and Down move, Enter picks, Escape closes) (Q7).

## Screen 3: Results (populated state)

```
+------------------------------------------------------+
| Similar Artists                                      |
+------------------------------------------------------+
|  +------------------------------------------------+  |
|  | Henry Threadgill                           [x] |  |
|  +------------------------------------------------+  |
|                                                      |
|  Artists like Henry Threadgill                       |
|  jazz, avant-garde jazz, free jazz     [MusicBrainz] |
|                                                      |
|   1. Anthony Braxton        ########..   [link]      |
|      free jazz, avant-garde jazz                     |
|   2. Muhal Richard Abrams   #######...   [link]      |
|      avant-garde jazz, jazz                          |
|   3. Roscoe Mitchell        #######...   [link]      |
|      free jazz                                       |
|  ...                                                 |
|  20. Steve Coleman          #####.....   [link]      |
|      jazz                                            |
|                                                      |
|              [ Show more ]                           |
+------------------------------------------------------+
```

- Each row shows the name, genre tags, how similar it is as a bar (Q3), and a link to the artist's MusicBrainz or ListenBrainz page (Q3).
- Clicking the name makes that artist the new search, so users can keep exploring (Q5). The external link opens separately.
- 20 results first, with "Show more" for more (Q4).
- An artist with no genre tags shows "no genres listed" rather than a blank.

Accessibility: h1 page title, h2 "Artists like ..."; results are an ordered list; the name and link are separate keyboard stops.

## Screen 3 on a phone

```
+--------------------------+
| Similar Artists          |
+--------------------------+
| +----------------------+ |
| | Henry Threadgill [x] | |
| +----------------------+ |
| Artists like             |
| Henry Threadgill         |
|                          |
| 1. Anthony Braxton       |
|    ########..   [link]   |
|    free jazz             |
| 2. Muhal Richard Abrams  |
|    #######...   [link]   |
|    avant-garde jazz      |
| ...                      |
|      [ Show more ]       |
+--------------------------+
```

Single column, with genres and the bar stacked under each name; tap targets stay large.

## Other States

| State | What the user sees |
|-------|--------------------|
| Loading | The results area shows placeholder rows. Lookups are meant to take under 200 ms (scope document), so this is rarely seen. |
| No similar artists | "Not enough listening data to find artists like X." The search box stays usable. |
| Error | "Something went wrong finding similar artists. Try again." with a Retry button. No error codes are shown. |
| Show more exhausted | "Show more" disappears when there are no more results. |
| Long names | Names wrap onto a second line and are never cut off mid-word. |

## Assumptions & Open Questions

- [assumption] The similarity bar is relative within one result list. It is not an absolute score comparable across searches; Requirements Analysis can confirm.
- [assumption] "Show more" adds 20 more each time, up to a cap set in requirements.

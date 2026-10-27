# User Flow — Find and Explore Similar Artists

Inputs: the intent statement (`ideation/intent-capture/intent-statement.md`), the scope document and intent backlog (`ideation/scope-definition/scope-document.md`, `intent-backlog.md`), and `rough-mockups-questions.md`. Screens are in `wireframes.md`.

## Core Flow

```
Flow: Find similar artists
Persona: the owner, or a friend who likes an artist (intent statement)
Trigger: opens the page wanting artists like one they already know
Steps:
  1. Start screen -> types part of an artist name -> suggestions appear (Q2)
  2. Suggestions  -> picks an artist (click or Enter) -> 20 similar artists with genres, similarity bar and link (Q3, Q4)
  3. Results      -> clicks a similar artist's name -> that artist becomes the new search (Q5); back to step 2's results for it
  4. Results      -> clicks "Show more" -> 20 more appear below (Q4)
  5. Results      -> clicks an external link -> the artist's MusicBrainz or ListenBrainz page opens
Success outcome: the user sees artists like the one they chose and can keep exploring
Error paths:
  - No suggestion matches -> "No artists match ..." -> user edits the text
  - Not enough data for the artist -> "Not enough listening data ..." -> user searches another artist
  - Lookup fails -> "Something went wrong ... Try again" -> Retry
```

## Flow Diagram

```
[Start] --type--> [Suggestions] --pick--> [Results: 20 similar]
                       |                      |    |     |
                  no match                    |    |     +--show more--> [Results: +20]
                       v                      |    |
              [No artists match]              |    +--external link--> [MusicBrainz / ListenBrainz page]
                                              |
                                              +--click a name--> [Results for that artist]
```

## Assumptions & Open Questions

- [assumption] The browser back button returns to the previous artist's results after exploring; Requirements Analysis can confirm.

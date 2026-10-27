# Entities — u3-web

Entity ownership follows `inception/domain-design/components.md` (WebApp owns no catalogue entities; it composes and presents). Shapes follow contracts C1 and C3 in `inception/contract-design/contract-summary.md`. This is the model for the stories mapped to u3-web in `inception/units-generation/unit-of-work-story-map.md` (`inception/user-stories/stories.md`), under `inception/requirements-analysis/requirements.md`. It builds on the skeleton's and u2-pipeline's models (`construction/u1-skeleton/functional-design/entities.md`, `construction/u2-pipeline/functional-design/entities.md`). The entities here are the request and response shapes, the page's state, and the quality-check sheet; none is stored by the app.

```yaml
entities:
  - name: PublicArtist
    owner: WebApp
    description: The allow-listed view of an Artist that leaves the app. No listener data.
    attributes:
      - { name: mbid, type: string, required: true, constraints: "MusicBrainz id, lower-case" }
      - { name: name, type: string, required: true }
      - { name: description, type: string, required: false, default: null, constraints: "MusicBrainz short description; null when none" }
      - { name: genres, type: "list of string", required: true, default: [], constraints: "in rank order; may be empty" }
  - name: SuggestRequest
    owner: WebApp
    description: One typed-text lookup from the search box.
    attributes:
      - { name: q, type: string, required: true, max: 200, constraints: "longer text is refused with 422; blank text is allowed and returns an empty list" }
  - name: SimilarRequest
    owner: WebApp
    attributes:
      - { name: mbid, type: string, required: true, constraints: "a 36-character MusicBrainz id" }
      - { name: offset, type: integer, required: false, default: 0, min: 0 }
      - { name: limit, type: integer, required: false, default: 20, min: 1, max: 100 }
  - name: SimilarItem
    owner: WebApp
    description: One row of a results page.
    attributes:
      - { name: artist, type: PublicArtist, required: true }
      - { name: cosine, type: float, required: true, min: -1, max: 1 }
      - { name: bar, type: float, required: true, min: 0, max: 1, constraints: "cosine divided by the top cosine of this artist's whole list, so page two continues the same scale" }
      - { name: links, type: "{musicbrainz, youtube, spotify}", required: true, constraints: "plain web addresses built from the id and the URL-encoded name" }
  - name: SimilarPage
    owner: WebApp
    attributes:
      - { name: artist, type: PublicArtist, required: true, constraints: "the artist the results are for" }
      - { name: items, type: "list of SimilarItem", required: true, constraints: "empty when the artist has too little data" }
      - { name: has_more, type: boolean, required: true }
  - name: ErrorMessage
    owner: WebApp
    description: A short JSON message for a refused or failed request.
    attributes:
      - { name: error, type: string, required: true, constraints: "plain words; never a stack trace, a file path or an internal code" }
  - name: PageState
    owner: WebApp
    description: What the page is showing; held only in the browser while the page is open.
    attributes:
      - { name: view, type: "start | loading | populated | not-enough-data | unknown | error", required: true }
      - { name: artistId, type: string, required: false, constraints: "from the address; empty in the start view" }
      - { name: shown, type: integer, required: true, min: 0, constraints: "rows listed so far; the next Show more asks for offset = shown" }
      - { name: hasMore, type: boolean, required: true }
      - { name: busy, type: boolean, required: true, constraints: "true while a request is in flight" }
  - name: SuggestionState
    owner: WebApp
    description: What the suggestion list is showing.
    attributes:
      - { name: text, type: string, required: true }
      - { name: view, type: "blank | suggestions-open | no-match", required: true }
      - { name: highlighted, type: integer, required: false, constraints: "index of the highlighted suggestion, or none" }
      - { name: requestNumber, type: integer, required: true, constraints: "increases with each lookup; only the newest reply is shown" }
  - name: QualityCheckSheet
    owner: WebApp
    description: The owner's by-eye comparison with the current app (FR8.1); a text file in the project, not app data.
    attributes:
      - { name: artists, type: "list of {name, mbid, newTop20, verdict}", required: true, constraints: "up to 5 entries" }
      - { name: verdict, type: "better-or-equal | worse | unset", required: true, constraints: "one per artist, written by the owner" }
      - { name: result, type: "pass | fail | incomplete", required: true, constraints: "derived: pass when at least 4 of 5 verdicts are better-or-equal" }
relationships:
  - "SimilarPage 1 — 1 PublicArtist (the subject) and 0..many SimilarItem"
  - "SimilarItem 1 — 1 PublicArtist"
  - "PageState 0..1 — 1 SimilarPage (the one last loaded)"
  - "QualityCheckSheet 1 — 1..5 artists, each tied to one SimilarPage"
```

The model has nine entities. PublicArtist and the request and response shapes are the only things that cross the HTTP boundary (C3). PageState and SuggestionState exist only in the browser. QualityCheckSheet lives in a file the owner edits; it holds artist-level data only.

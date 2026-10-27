# Personas

Derived from `inception/requirements-analysis/requirements.md` and `user-stories-questions.md` (Q1).

## Persona 1: The Owner

- **Role:** builds and runs the app on their own machine; also uses it to find music.
- **Goals:** learn AI-DLC on a familiar problem; get recommendations at least as good as the current app's; rebuild everything easily when a new ListenBrainz dump comes out.
- **Pain points:** the current app grew experimentally and is hard to extend; rebuilding is a manual sequence of steps.
- **Tech comfort:** high.
- **Frequency:** daily while building; occasionally afterwards, plus a rebuild for each new dump.

## Persona 2: The Friend

- **Role:** a friend or colleague who likes music and uses the app to discover artists.
- **Goals:** type an artist they like and quickly find others like it; keep exploring from artist to artist; send a link to an interesting find.
- **Pain points:** generic "similar artists" lists that miss niche taste.
- **Tech comfort:** medium; uses a desktop or phone browser.
- **Frequency:** occasional.
- **Note:** how friends reach the first version is still undecided; for now only the owner runs it (assumption carried from Intent Capture).

## Relationships and Priority

1. **The Owner** is the primary persona: the only one who runs the app in v1, and the only one for the rebuild and quality stories.
2. **The Friend** is secondary: every search and explore story serves both, written from the friend's view because that is the narrower need.

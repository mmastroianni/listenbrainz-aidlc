# Tech Stack Decisions — u3-web

The stack is fixed by the project rule (same tools as the current app) and the team practices, and carries over unchanged from `construction/u1-skeleton/nfr-requirements/tech-stack-decisions.md` and `construction/u2-pipeline/nfr-requirements/tech-stack-decisions.md`. It is recorded here for the web unit, with the requirements from `inception/requirements-analysis/requirements.md`, the functional design (`construction/u3-web/functional-design/functional-spec.md`, `rules.md`) and the contracts in `inception/contract-design/contract-summary.md`.

| Concern | Choice | Why |
|---------|--------|-----|
| Web app and endpoints | FastAPI, served with uvicorn on 127.0.0.1 | Same as the current app; NFR8.7 |
| The page | Plain HTML, CSS and JavaScript files served by the app (one page, one stylesheet, one script); no framework, no build step | The current app does the same; keeps NFR1.14 and NFR4.3 easy to check |
| Look | The current app's colours, fonts, radii and focus ring (`inception/refined-mockups/design-system-mapping.md`) | Requirement FR6.4 |
| Browser behaviour | The browser's own history, fetch and keyboard events; no library | Nothing to install, nothing to load from elsewhere |
| Icons | Small inline SVG with text labels | No logos bundled; no outside files |
| Quality-check commands | Two small Python commands in the same package, writing and reading a markdown sheet | Keeps the check repeatable with no new tool |
| Tests | pytest with FastAPI's `TestClient` for endpoints, headers, served files and the page script's text checks; the keyboard and phone pass by hand before `v0.1.0` | Team practices; the accessibility checklist names this split |

No new runtime or development dependency is added. UMAP and the artist map stay out; they are stretch scope.

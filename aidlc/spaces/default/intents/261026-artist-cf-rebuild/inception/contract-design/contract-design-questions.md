# Contract Design — Questions

Context: there are three units (`inception/units-generation/unit-of-work.md`). U2 and U3 each build on U1's interfaces. At run time the web app (U3) reads files the pipeline commands (U2) build. The page talks to the web app over HTTP. So there are three contracts to pin down: the in-code interfaces, the built files, and the HTTP endpoints. Each question lists my recommendation first.

## Q1. [Architect] Format of the built files

The pipeline builds files that the web app reads at startup (artist details, the similarity index, the id mapping).

A. Same as the current app: a SQLite file for artist details and name search, a FAISS index file, and an id list (recommended: proven, and fast name search)
B. Parquet files for everything, loaded into memory at startup
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Q2. [Architect] Keeping the built files and the app in step

If the code changes the file layout but the files were built by an older version, the app could start and misbehave.

A. The pipeline writes a small manifest with a format version and build date; the app refuses to start on a mismatch and names the step to re-run (recommended)
B. No version check: it is a solo project in one repository
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Q3. [Architect] The web endpoints

The page calls the web app for suggestions and similar artists. Only our own page uses these endpoints.

A. Plain JSON endpoints under `/api/` with no version number, changed together with the page (recommended)
B. Versioned endpoints under `/api/v1/`, for future outside users
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Built files (Q1): like the current app: SQLite for artist details and name search, a FAISS index file, and an id list.
- Version check (Q2): the pipeline writes a manifest with a format version and build date; the app refuses to start on a mismatch and names the step to re-run.
- Endpoints (Q3): plain JSON endpoints under `/api/`, no version number, changed together with the page.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

# listenbrainz-recs

Similar-artist recommendations from ListenBrainz listening data: Spark ALS collaborative
filtering, a FAISS cosine index, a SQLite artist catalogue with name search, and a small FastAPI
app. Everything runs locally; there are no remote services.

The pipeline has four steps, run in this order: prepare, train, catalogue, index. The app reads
the files they build. It serves one web page and answers `GET /api/suggest` and
`GET /api/artists/{mbid}/similar` (see "The page and its endpoints").

## Prerequisites

- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- A Java runtime (Spark needs it): `java -version`
- The ListenBrainz statistics dump and the MusicBrainz tables (`artist`, `artist_tag`, `tag`,
  `genre`), read in place and never modified

## Getting the data

The app needs two public dumps. Neither is in this repository; the pipeline reads them in place and
never changes them. Put both under one folder (the examples call it `/path/to/listenbrainz`) and
point `LISTENBRAINZ_DATA_ROOT` at it.

| Dump | File to download | Size |
|------|------------------|------|
| ListenBrainz **statistics** dump | [`listenbrainz-statistics-dump-20261015-000002.tar.zst`](https://data.metabrainz.org/pub/musicbrainz/listenbrainz/fullexport/listenbrainz-dump-2723-20261015-000002-full/) (in the `fullexport/listenbrainz-dump-<id>-<date>-full/` folder; there is a `.sha256` file beside it) | 23 GB packed, about 140 GB extracted |
| MusicBrainz database dump | [`mbdump.tar.bz2`](https://data.metabrainz.org/pub/musicbrainz/data/fullexport/) (in the newest dated folder under `data/fullexport/`; `LATEST` names it) | about 7 GB packed |

Take the **statistics** dump. The folder it sits in also holds a 233 GB listens dump and a 232 GB
spark dump; the pipeline does not use those. The file names carry the dump's date, so newer dumps
have different names.

Extract the ListenBrainz archive (needs `zstd`) and only the four MusicBrainz tables the app reads
(`artist`, `artist_tag`, `tag`, `genre`):

```bash
cd /path/to/listenbrainz
tar --zstd -xf listenbrainz-statistics-dump-20261015-000002.tar.zst
mkdir -p data/musicbrainz
tar -xjf mbdump.tar.bz2 -C data/musicbrainz mbdump/artist mbdump/artist_tag mbdump/tag mbdump/genre
```

The folder the pipeline expects then looks like this:

```
/path/to/listenbrainz/
  listenbrainz-statistics-dump-20261015-000002/lbdump/statistics/artists_all_time.jsonl
  data/musicbrainz/mbdump/{artist,artist_tag,tag,genre}
```

If more than one `listenbrainz-statistics-dump-*` folder is there, the newest is used. A missing
file stops the first step with a message naming it.

The full dump needs a lot of memory and disk: a full rebuild took about 13 minutes with 24 GB given
to Spark (training peaked near 13 GB). For a first try, use the sample run below.

## Settings (environment variables)

| Variable | Meaning | Default |
|----------|---------|---------|
| `LISTENBRAINZ_DATA_ROOT` | Folder holding the dumps: a `listenbrainz-statistics-dump-*` folder (or a folder containing one) and `data/musicbrainz/mbdump/` | none: required by the prepare and catalogue steps |
| `LISTENBRAINZ_WORK_DIR` | Intermediate data | `data/` (git-ignored) |
| `LISTENBRAINZ_MODELS_DIR` | Built files read by the app | `models/` (git-ignored) |
| `LISTENBRAINZ_SPARK_MEMORY` | Spark driver memory, for example `24g` or `8192m` | `24g` |
| `LISTENBRAINZ_PREP_MAX_LINES` | Read only this many listener lines of the dump (a sample run) | unset: the whole dump |

## Rebuild from a new dump

Run the four steps in order. Each prints one summary line with counts only, and exits non-zero
with a message when something is wrong. Each step writes a marker file in the work folder as its
last act, and checks the marker of the step before it.

```bash
uv sync
export LISTENBRAINZ_DATA_ROOT=/path/to/listenbrainz
```

| # | Command | Reads | Writes | Check that it worked |
|---|---------|-------|--------|----------------------|
| 1 | `uv run listenbrainz-recs-prepare` | the listening dump and the MusicBrainz folder (location check) | `data/interactions/`, `data/artist_names/`, `data/artist_listeners/`, `data/prepare_report.json`, `data/prepared.json` | the line `prepare: read N lines (S skipped) ... A artists kept`; `A` is the artists with at least 5 listeners |
| 2 | `uv run listenbrainz-recs-train` | the prepared data only | `data/vectors/`, `data/trained.json` | the line `train: A artist vectors of rank 64`, with `A` equal to step 1's artists unless some were dropped |
| 3 | `uv run listenbrainz-recs-catalogue` | the prepared data and the MusicBrainz tables | `models/artists.sqlite`, `data/catalogued.json` | the line `catalogue: A artists (D with a description, G with genres)` |
| 4 | `uv run listenbrainz-recs-index` | the trained vectors and the catalogue | `models/artists.faiss`, `models/artist_ids.txt`, `models/manifest.json` (last), `data/indexed.json` | the line `index: A artists indexed`, and the manifest exists |

Then start the app and check the speed:

```bash
uv run listenbrainz-recs-serve     # http://127.0.0.1:8000
uv run listenbrainz-recs-speed     # 100 lookups of each kind; exits non-zero above 200 ms
```

Sample run: set `LISTENBRAINZ_PREP_MAX_LINES=5000` before step 1 to build everything from the
first 5,000 listener lines (a few minutes instead of a long run). Unset it for the full dump. If a
step reports it ran out of memory, raise `LISTENBRAINZ_SPARK_MEMORY` (it must fit in the machine's
memory) and run that step again.

### What the stop messages look like

- Missing input (a step run before the one it needs):
  `Missing the prepared listen counts in data; run the prepare step first: uv run listenbrainz-recs-prepare`
- Stale input (an earlier step was run again after the one you are running was built):
  `The trained vectors in data was made from an older prepare run than the current one; run the train step again: uv run listenbrainz-recs-train`
  Re-run the steps after the one you changed, in order.
- A missing or bad setting names the variable, for example `The LISTENBRAINZ_DATA_ROOT setting is not set`.
- The app refuses to start, naming the step to re-run, when a built file is missing, the manifest
  is absent (an interrupted index step) or its format version differs.

Built data and model files are never committed; rebuilding is how you get them back.

## The page and its endpoints

After the four pipeline steps, start the app and open it in a browser:

```bash
uv run listenbrainz-recs-serve     # listens on 127.0.0.1:8000 only
```

| Address | Shows |
|---------|-------|
| `http://127.0.0.1:8000/` | The search page: type an artist, pick a suggestion, see similar artists |
| `http://127.0.0.1:8000/artist/<musicbrainz-id>` | The same page, already showing that artist's similar artists (bookmarkable; Back and Forward work) |

The page is plain HTML, CSS and JavaScript served by the app itself (`src/listenbrainz_recs/app/static/`);
it loads nothing from other websites. Keyboard: Down and Up move through suggestions, Enter picks,
Escape closes the list, Tab reaches every result name, link and "Show more".

### Suggestion endpoint

`GET /api/suggest?q=<typed text>` returns up to 10 artists, closest text match first and then the
most listened to, as a JSON list of `{mbid, name, description, genres}`. Case, accents and
punctuation are ignored. Blank text or no match gives `[]`; text longer than 200 characters is
refused with 422.

```bash
curl 'http://127.0.0.1:8000/api/suggest?q=henry%20thr'
```

`GET /api/artists/{mbid}/similar?offset=0&limit=20` returns the artist, 20 similar artists at a
time (each with `cosine`, a `bar` scaled to the list's top score, and three links) and `has_more`.
An artist the catalogue knows but the index does not (too little data) returns an empty `items`
list; an id the app does not know at all is 404; a malformed id or paging value is 422.

The manual keyboard and phone pass to do before tagging `v0.1.0` is in `docs/manual-checks.md`.

## Quality check against the current app

A by-eye check that the new lists are at least as good as the current app's (requirement FR8.1).
You choose up to 5 artists; the check passes when at least 4 of them are marked at least as good.

```bash
# 1. Write the sheet: the new app's top 20 with genres for each artist (name or MusicBrainz id).
uv run listenbrainz-recs-quality-sheet "Henry Threadgill" "Björk" "Anthony Braxton"
#    -> docs/quality-check.md (use --output PATH to write elsewhere)

# 2. Open the same artists in the current app (../listenbrainz), compare the lists by eye, and in
#    the sheet change each "Verdict: unset" line to "Verdict: better-or-equal" or "Verdict: worse".

# 3. Read the sheet: prints how many verdicts are marked and the result.
uv run listenbrainz-recs-quality-verdict            # exit 0 on pass, 1 on fail or incomplete
```

The result is `pass` (at least 4 better-or-equal), `fail`, or `incomplete` while any verdict is
still `unset`. More than 5 artists, or a name that matches nothing, stops the first command with a
message naming the problem. The sheet holds artist names, ids and genres only, and both commands
print counts only.

## Checks

```bash
bash scripts/check.sh                  # ruff check, ruff format --check, ty, pytest + 80% coverage
uv run pytest tests/u2_pipeline -q     # the pipeline unit's tests only
uv run pytest tests/u3_web -q          # the web unit's tests only
uv run pytest tests/u1_skeleton -q     # the walking skeleton's tests only
```

GitHub Actions runs the same check (`.github/workflows/ci.yml`) on every push and pull request.

## Rules this project follows

Dumps are read-only; no listener-level data leaves the pipeline; no paid or remote services; dumps,
data and model files are never committed.

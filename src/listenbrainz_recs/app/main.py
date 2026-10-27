"""WebApp: the page, the suggestion and similar-artists endpoints, health (contract C3).

Serves `/` and `/artist/{mbid}` (one page, BR3.1), `GET /api/suggest` (BR1.1, BR1.2),
`GET /api/artists/{mbid}/similar` (BR2.1 to BR2.5) and `GET /api/health`. Every answer carries the
page headers (NFR3.12), and the request log holds the path only, never the query (NFR3.13).

Start it with `uv run listenbrainz-recs-serve`. It binds 127.0.0.1 unless told otherwise.
"""

import argparse
import logging
import sys
import time
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from urllib.parse import quote, quote_plus

import uvicorn
from fastapi import FastAPI, Query, Request
from fastapi import Path as PathParam
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from listenbrainz_recs.artists import ArtistCatalog, ArtistSummary
from listenbrainz_recs.errors import StartupError, UnknownArtist
from listenbrainz_recs.settings import load_settings
from listenbrainz_recs.similarity import MAX_LIMIT, SimilarityIndex
from listenbrainz_recs.store import load_store

DEFAULT_HOST = "127.0.0.1"  # NFR8.1: local only; changing it is a deliberate flag
DEFAULT_PORT = 8000
DEFAULT_LIMIT = 20
MAX_QUERY_LENGTH = 200  # BR1.2
STATIC_DIR = Path(__file__).parent / "static"
# NFR3.12: only the app's own files, no framing, no sniffing, no referrer sent to link targets.
PAGE_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}
MBID_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"

access_log = logging.getLogger("listenbrainz_recs.access")
error_log = logging.getLogger("listenbrainz_recs.app")


def public_artist(artist: ArtistSummary) -> dict[str, object]:
    """The allow-list of artist fields a response may carry (BR5.2): no listener data."""
    return {
        "mbid": artist.mbid,
        "name": artist.name,
        "description": artist.description,
        "genres": list(artist.genres),
    }


def artist_links(artist: ArtistSummary) -> dict[str, str]:
    """Plain link strings built from artist data; the app itself makes no remote calls."""
    return {
        "musicbrainz": f"https://musicbrainz.org/artist/{artist.mbid}",
        "youtube": f"https://www.youtube.com/results?search_query={quote_plus(artist.name)}",
        "spotify": f"https://open.spotify.com/search/{quote(artist.name)}",
    }


def error_response(status: int, message: str) -> JSONResponse:
    """A short JSON message and never a stack trace (FR6.5)."""
    return JSONResponse(status_code=status, content={"error": message})


def create_app(models_dir: Path | None = None) -> FastAPI:
    """Build the app, loading and checking the built files first (raises `StartupError`)."""
    store = load_store(models_dir if models_dir is not None else load_settings().models_dir)
    similarity = SimilarityIndex(store)
    catalog = ArtistCatalog(store)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        yield
        store.close()

    app = FastAPI(title="Similar Artists", version="1", lifespan=lifespan)
    app.state.store = store

    @app.middleware("http")
    async def add_page_headers(request: Request, call_next) -> Response:  # noqa: ANN001
        response = await call_next(request)
        response.headers.update(PAGE_HEADERS)
        return response

    @app.middleware("http")
    async def log_requests(request: Request, call_next) -> Response:  # noqa: ANN001
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed = (time.perf_counter() - started) * 1000
            access_log.error("%s %s 500 %.1fms", request.method, request.url.path, elapsed)
            raise
        elapsed = (time.perf_counter() - started) * 1000
        access_log.info(
            "%s %s %d %.1fms", request.method, request.url.path, response.status_code, elapsed
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0]
        where = ".".join(str(part) for part in first.get("loc", ()) if part != "query")
        if first.get("type") == "string_pattern_mismatch":
            reason = "must be a MusicBrainz artist id (a 36-character UUID)"
        else:
            reason = str(first.get("msg", "invalid value"))
        return error_response(422, f"Invalid request: {where}: {reason}")

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return error_response(exc.status_code, str(exc.detail))

    @app.exception_handler(UnknownArtist)
    async def unknown_artist(_request: Request, exc: UnknownArtist) -> JSONResponse:
        return error_response(404, str(exc))

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception) -> JSONResponse:
        error_log.error("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
        return error_response(500, "Internal error")

    @app.get("/api/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "built_at": store.manifest.built_at,
            "artists": store.manifest.artist_count,
        }

    @app.get("/api/suggest")
    def suggest(q: Annotated[str, Query(max_length=MAX_QUERY_LENGTH)]) -> list[dict[str, object]]:
        """Up to 10 artists for the typed text, in the catalogue's order (BR1.1)."""
        return [public_artist(artist) for artist in catalog.suggest(q, limit=10)]

    @app.get("/api/artists/{mbid}/similar")
    def similar(
        mbid: Annotated[str, PathParam(pattern=MBID_PATTERN)],
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    ) -> dict[str, object]:
        mbid = mbid.lower()
        try:
            page = similarity.neighbours(mbid, offset=offset, limit=limit)
        except UnknownArtist:
            # BR2.3: known to the catalogue but not the index means too little data, not unknown.
            known = catalog.get(mbid)
            if known is None:
                raise  # BR2.5: unknown everywhere, answered 404
            return {"artist": public_artist(known), "items": [], "has_more": False}
        top = page.items[0].cosine if offset == 0 and page.items else None
        if top is None and offset > 0:
            first = similarity.neighbours(mbid, offset=0, limit=1).items
            top = first[0].cosine if first else None

        artists = catalog.get_many([mbid, *(n.mbid for n in page.items)])
        subject = artists.get(mbid)
        if subject is None:
            raise UnknownArtist(mbid)

        items = []
        for neighbour in page.items:
            artist = artists.get(neighbour.mbid) or ArtistSummary(
                neighbour.mbid, neighbour.mbid, None, 0
            )
            bar = max(0.0, min(1.0, neighbour.cosine / top)) if top and top > 0 else 0.0
            items.append(
                {
                    "artist": public_artist(artist),
                    "cosine": neighbour.cosine,
                    "bar": bar,
                    "links": artist_links(artist),
                }
            )
        return {"artist": public_artist(subject), "items": items, "has_more": page.has_more}

    @app.get("/", include_in_schema=False)
    @app.get("/artist/{mbid}", include_in_schema=False)
    def page(mbid: str = "") -> FileResponse:
        """The one page for both addresses; it reads the id itself (BR3.1)."""
        return FileResponse(STATIC_DIR / "index.html", media_type="text/html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


def main(argv: Sequence[str] | None = None) -> int:
    """Command entry point: `uv run listenbrainz-recs-serve`."""
    parser = argparse.ArgumentParser(description="Start the similar-artists web app.")
    parser.add_argument(
        "--host", default=DEFAULT_HOST, help="address to bind (default: %(default)s)"
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--models-dir", type=Path, default=None, help="built files folder")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    try:
        app = create_app(args.models_dir)
    except StartupError as exc:
        print(f"Cannot start: {exc}", file=sys.stderr)
        return 1
    uvicorn.run(app, host=args.host, port=args.port, log_level="info", access_log=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())

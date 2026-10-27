"""Page headers, request log, parallel requests, timing guard and failure paths.

Written before the code (Red): BR3.1, BR1.4, NFR1.13, NFR2.20, NFR3.12, NFR3.13, NFR8.9.
"""

import logging
import sqlite3
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fixtures.sample_data import artist_mbid

from listenbrainz_recs.app.main import create_app
from listenbrainz_recs.artists import ArtistCatalog
from listenbrainz_recs.similarity import SimilarityIndex

A1 = artist_mbid(1)
POLICY = "default-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
SUGGEST = "/api/suggest?q=henry"
SIMILAR = f"/api/artists/{A1}/similar"


@pytest.fixture
def app(search_models: Path) -> FastAPI:
    return create_app(search_models)


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.mark.parametrize(
    "path", ["/", f"/artist/{A1}", "/artist/not-an-id", SUGGEST, SIMILAR, "/api/health"]
)
def test_every_answer_carries_the_page_headers(client: TestClient, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["content-security-policy"] == POLICY
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_refusals_carry_the_page_headers_too(client: TestClient) -> None:
    for path in ("/api/suggest", f"/api/artists/{artist_mbid(404)}/similar", "/api/nothing"):
        response = client.get(path)
        assert response.status_code in (404, 422)
        assert response.headers["content-security-policy"] == POLICY


def test_the_root_and_artist_addresses_serve_the_same_page(client: TestClient) -> None:
    root = client.get("/")
    artist = client.get(f"/artist/{A1}")
    malformed = client.get("/artist/not-an-id")
    assert root.headers["content-type"].startswith("text/html")
    assert root.text == artist.text == malformed.text
    assert "<html" in root.text


def test_the_log_holds_the_path_and_never_the_typed_text(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO):
        client.get("/api/suggest", params={"q": "secrettypedtext"})
    lines = [r.getMessage() for r in caplog.records if r.name == "listenbrainz_recs.access"]
    assert lines and lines[0].startswith("GET /api/suggest 200 ")
    # The test client's own httpx log line shows its URL; only the app's loggers are checked.
    app_lines = [r.getMessage() for r in caplog.records if r.name.startswith("listenbrainz_recs")]
    assert app_lines and all("secrettypedtext" not in line for line in app_lines)
    assert all("?" not in line for line in app_lines)


def _parallel(app: FastAPI, path: str) -> list[tuple[int, object]]:
    def fetch(_n: int) -> tuple[int, object]:
        response = TestClient(app).get(path)
        return response.status_code, response.json()

    with ThreadPoolExecutor(max_workers=5) as pool:
        return list(pool.map(fetch, range(5)))


@pytest.mark.parametrize("path", [SUGGEST, SIMILAR])
def test_five_parallel_requests_all_succeed_with_the_same_answer(
    app: FastAPI, client: TestClient, path: str
) -> None:
    expected = client.get(path).json()
    results = _parallel(app, path)
    assert [status for status, _ in results] == [200] * 5
    assert all(body == expected for _, body in results)


@pytest.mark.parametrize("path", [SUGGEST, SIMILAR])
def test_twenty_lookups_each_answer_in_under_200_ms_on_fixtures(
    client: TestClient, path: str
) -> None:
    client.get(path)  # warm up
    for _ in range(20):
        started = time.perf_counter()
        assert client.get(path).status_code == 200
        assert time.perf_counter() - started < 0.2


def _close_catalogue(app: FastAPI) -> None:
    app.state.store.db.close()


def _raise_sqlite(*_args: object, **_kwargs: object) -> None:
    raise sqlite3.DatabaseError("secret catalogue detail")


def _raise_index(*_args: object, **_kwargs: object) -> None:
    raise RuntimeError("secret index detail")


@pytest.mark.parametrize(
    ("path", "break_it", "secret"),
    [
        (SUGGEST, _close_catalogue, None),
        (SIMILAR, _close_catalogue, None),
        (
            SUGGEST,
            lambda _app: setattr(ArtistCatalog, "suggest", _raise_sqlite),
            "secret catalogue",
        ),
        (
            SIMILAR,
            lambda _app: setattr(SimilarityIndex, "neighbours", _raise_index),
            "secret index",
        ),
    ],
    ids=["suggest-closed-db", "similar-closed-db", "suggest-read-error", "similar-index-error"],
)
def test_a_failing_read_gives_a_short_500_and_an_error_log(
    app: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    path: str,
    break_it: Callable[[FastAPI], None],
    secret: str | None,
) -> None:
    # monkeypatch undoes the class changes made by the lambdas
    monkeypatch.setattr(ArtistCatalog, "suggest", ArtistCatalog.suggest)
    monkeypatch.setattr(SimilarityIndex, "neighbours", SimilarityIndex.neighbours)
    break_it(app)
    client = TestClient(app, raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR):
        response = client.get(path)
    assert response.status_code == 500
    assert response.json() == {"error": "Internal error"}
    assert "Traceback" not in response.text
    if secret:
        assert secret not in response.text
        assert any(secret in (r.exc_text or r.getMessage()) for r in caplog.records)
    assert any(r.levelno == logging.ERROR and r.exc_info for r in caplog.records)

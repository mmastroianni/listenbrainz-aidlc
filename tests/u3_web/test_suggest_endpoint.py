"""Suggestion endpoint: order, limit, blank text, text limit, allow-list (BR1.1 to BR1.3).

Written before the endpoint code (Red). Built files are hand-made, so no Spark is needed.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fixtures.sample_data import artist_mbid

from listenbrainz_recs.app.main import create_app

ARTIST_FIELDS = {"mbid", "name", "description", "genres"}


@pytest.fixture
def client(search_models: Path) -> TestClient:
    return TestClient(create_app(search_models))


def test_henry_thr_suggests_the_artists_in_the_catalogues_order(client: TestClient) -> None:
    response = client.get("/api/suggest", params={"q": "henry thr"})
    assert response.status_code == 200
    body = response.json()
    assert [a["mbid"] for a in body] == [artist_mbid(1), artist_mbid(2)]
    assert body[0]["name"] == "Henry Threadgill"
    assert body[0]["description"] == "US jazz saxophonist and composer"
    assert body[0]["genres"] == ["jazz"]


def test_bjork_without_the_accent_finds_bjork_first(client: TestClient) -> None:
    body = client.get("/api/suggest", params={"q": "bjork"}).json()
    assert [a["name"] for a in body] == ["Björk", "Bjork Tribute Band"]


def test_at_most_ten_suggestions_are_returned(paging_models: Path) -> None:
    client = TestClient(create_app(paging_models))
    body = client.get("/api/suggest", params={"q": "artist"}).json()
    assert len(body) == 10
    assert body[0]["name"] == "Artist 01"


def test_no_match_gives_an_empty_list(client: TestClient) -> None:
    response = client.get("/api/suggest", params={"q": "zzqqxx"})
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("text", ["", "   ", "\t", "!!!"])
def test_blank_or_symbol_only_text_gives_an_empty_list(client: TestClient, text: str) -> None:
    response = client.get("/api/suggest", params={"q": text})
    assert response.status_code == 200
    assert response.json() == []


def test_text_of_200_characters_is_accepted_and_201_is_refused(client: TestClient) -> None:
    assert client.get("/api/suggest", params={"q": "a" * 200}).status_code == 200
    response = client.get("/api/suggest", params={"q": "a" * 201})
    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"error"}
    assert "q" in body["error"] and "Traceback" not in response.text


def test_missing_text_is_refused_with_a_short_message(client: TestClient) -> None:
    response = client.get("/api/suggest")
    assert response.status_code == 422
    assert set(response.json()) == {"error"}


def test_suggestions_carry_only_the_allow_listed_fields(client: TestClient) -> None:
    body = client.get("/api/suggest", params={"q": "henry"}).json()
    assert body and all(set(a) == ARTIST_FIELDS for a in body)
    assert body[1]["genres"] == ["jazz", "free jazz"]  # rank order kept
    assert body[1]["description"] is None
    assert "listener" not in str(body).lower()


def test_markup_in_names_comes_back_as_plain_json_text(client: TestClient) -> None:
    body = client.get("/api/suggest", params={"q": "script alert"}).json()
    assert [a["name"] for a in body] == ["<script>alert(1)</script>"]
    assert body[0]["description"] == "<b>bold</b>"


@pytest.mark.parametrize("text", ['"*) OR 1=1 --', "'; DROP TABLE artist; --", "NEAR(a b)", '"'])
def test_query_syntax_in_typed_text_is_treated_as_plain_text(client: TestClient, text: str) -> None:
    assert client.get("/api/suggest", params={"q": text}).status_code == 200
    assert client.get("/api/suggest", params={"q": "henry"}).json()  # catalogue still intact

"""Similar-artists endpoint: paging, bar scale, missing from index, validation (BR2.1 to BR2.5).

Written before the endpoint changes (Red).
"""

import math
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fixtures.sample_data import artist_mbid
from fixtures.web_models import GAP_ID

from listenbrainz_recs.app.main import create_app

ARTIST_FIELDS = {"mbid", "name", "description", "genres"}
ITEM_FIELDS = {"artist", "cosine", "bar", "links"}
A1 = artist_mbid(1)


@pytest.fixture
def paging_client(paging_models: Path) -> TestClient:
    return TestClient(create_app(paging_models))


def _ids(body: dict) -> list[str]:
    return [item["artist"]["mbid"] for item in body["items"]]


def test_first_page_holds_20_in_order_and_says_there_are_more(paging_client: TestClient) -> None:
    body = paging_client.get(f"/api/artists/{A1}/similar").json()
    assert _ids(body) == [artist_mbid(n) for n in range(2, 22)]
    assert body["has_more"] is True
    assert body["artist"]["name"] == "Artist 01"
    assert A1 not in _ids(body)


def test_three_pages_show_45_and_the_last_has_no_more(paging_client: TestClient) -> None:
    shown: list[str] = []
    flags = []
    for offset in (0, 20, 40):
        body = paging_client.get(
            f"/api/artists/{A1}/similar", params={"offset": offset, "limit": 20}
        ).json()
        shown += _ids(body)
        flags.append(body["has_more"])
    assert len(shown) == 45 and len(set(shown)) == 45
    assert flags == [True, True, False]


def test_exactly_20_available_gives_has_more_false(exact_page_models: Path) -> None:
    client = TestClient(create_app(exact_page_models))
    body = client.get(f"/api/artists/{A1}/similar").json()
    assert len(body["items"]) == 20
    assert body["has_more"] is False


def test_bar_on_page_two_is_scaled_against_the_first_pages_top_score(
    paging_client: TestClient,
) -> None:
    first = paging_client.get(f"/api/artists/{A1}/similar").json()
    second = paging_client.get(
        f"/api/artists/{A1}/similar", params={"offset": 20, "limit": 20}
    ).json()
    assert first["items"][0]["bar"] == pytest.approx(1.0)
    top = first["items"][0]["cosine"]
    assert top == pytest.approx(math.cos(0.01), abs=1e-5)
    for item in second["items"]:
        assert item["bar"] == pytest.approx(item["cosine"] / top, abs=1e-6)
    assert second["items"][0]["bar"] < 1.0
    assert all(0.0 <= item["bar"] <= 1.0 for item in second["items"])


def test_an_artist_in_the_catalogue_but_not_in_the_index_gets_no_items(gap_models: Path) -> None:
    client = TestClient(create_app(gap_models))
    response = client.get(f"/api/artists/{GAP_ID}/similar")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == [] and body["has_more"] is False
    assert body["artist"]["name"] == "Lonely"
    assert set(body["artist"]) == ARTIST_FIELDS


def test_an_id_in_neither_the_index_nor_the_catalogue_is_404(gap_models: Path) -> None:
    client = TestClient(create_app(gap_models))
    response = client.get(f"/api/artists/{artist_mbid(404)}/similar")
    assert response.status_code == 404
    assert set(response.json()) == {"error"}
    assert "Traceback" not in response.text


@pytest.mark.parametrize(
    "query",
    ["offset=-1", "limit=0", "limit=101", "limit=abc", "offset=1.5"],
)
def test_bad_paging_is_422(paging_client: TestClient, query: str) -> None:
    response = paging_client.get(f"/api/artists/{A1}/similar?{query}")
    assert response.status_code == 422
    assert set(response.json()) == {"error"}


@pytest.mark.parametrize("bad_id", ["not-a-uuid", A1[:-1], A1 + "0", "..%5C..%5Cetc"])
def test_a_malformed_id_is_422_not_a_server_error(paging_client: TestClient, bad_id: str) -> None:
    response = paging_client.get(f"/api/artists/{bad_id}/similar")
    assert response.status_code == 422
    assert response.json()["error"].startswith("Invalid request")


def test_similar_responses_carry_only_allow_listed_fields(paging_client: TestClient) -> None:
    body = paging_client.get(f"/api/artists/{A1}/similar").json()
    assert set(body) == {"artist", "items", "has_more"}
    assert set(body["artist"]) == ARTIST_FIELDS
    for item in body["items"]:
        assert set(item) == ITEM_FIELDS
        assert set(item["artist"]) == ARTIST_FIELDS
        assert set(item["links"]) == {"musicbrainz", "youtube", "spotify"}
    assert "listener" not in str(body).lower()


def test_health_response_carries_only_its_three_fields(paging_client: TestClient) -> None:
    body = paging_client.get("/api/health").json()
    assert set(body) == {"status", "built_at", "artists"}
    assert body["artists"] == 46


def test_limit_of_100_is_allowed_and_returns_all_45(paging_client: TestClient) -> None:
    body = paging_client.get(f"/api/artists/{A1}/similar", params={"limit": 100}).json()
    assert len(body["items"]) == 45 and body["has_more"] is False

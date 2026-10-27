"""WebApp: similar-artists endpoint, health, validation, startup checks (BR4.2 to BR5.2).

Written before the code (Red).
"""

import json
import logging
import shutil
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fixtures.sample_data import artist_mbid

from listenbrainz_recs.app.main import DEFAULT_HOST, create_app, main
from listenbrainz_recs.errors import StartupError
from listenbrainz_recs.paths import ARTISTS_DB_FILE, C2_FILES, MANIFEST_FILE
from listenbrainz_recs.similarity import SimilarityIndex

A1, A2, A3, A4, A5 = (artist_mbid(n) for n in range(1, 6))
ARTIST_FIELDS = {"mbid", "name", "description", "genres"}
FORBIDDEN_WORDS = ("listener", "user_id", "user_name", "listen_count")


@pytest.fixture
def client(tiny_models: Path) -> TestClient:
    return TestClient(create_app(tiny_models))


def _keys(node: object) -> set[str]:
    if isinstance(node, dict):
        return set(node) | {k for v in node.values() for k in _keys(v)}
    if isinstance(node, list):
        return {k for v in node for k in _keys(v)}
    return set()


def test_similar_returns_ranked_neighbours_with_names_and_cosine(client: TestClient) -> None:
    response = client.get(f"/api/artists/{A1}/similar")
    assert response.status_code == 200
    body = response.json()
    assert body["artist"]["mbid"] == A1 and body["artist"]["name"] == "Alpha"
    assert [i["artist"]["mbid"] for i in body["items"]] == [A2, A3, A4, A5]
    assert body["items"][0]["artist"]["name"] == "Béta"
    assert body["items"][0]["cosine"] == pytest.approx(0.99388, abs=1e-4)
    assert body["has_more"] is False


def test_bar_is_cosine_relative_to_the_top_of_the_list(client: TestClient) -> None:
    body = client.get(f"/api/artists/{A1}/similar").json()
    assert body["items"][0]["bar"] == pytest.approx(1.0)
    assert body["items"][1]["bar"] == pytest.approx(0.70711 / 0.99388, abs=1e-3)
    assert body["items"][3]["bar"] == 0.0  # negative cosine is clamped to 0
    later = client.get(f"/api/artists/{A1}/similar", params={"offset": 1, "limit": 1}).json()
    assert later["items"][0]["bar"] == pytest.approx(0.70711 / 0.99388, abs=1e-3)


def test_links_are_plain_strings_built_from_artist_data(client: TestClient) -> None:
    links = client.get(f"/api/artists/{A1}/similar").json()["items"][0]["links"]
    assert links["musicbrainz"] == f"https://musicbrainz.org/artist/{A2}"
    assert links["youtube"].startswith("https://www.youtube.com/results?search_query=")
    assert links["spotify"].startswith("https://open.spotify.com/search/")
    assert "B%C3%A9ta" in links["youtube"]


def test_responses_contain_only_allow_listed_fields(client: TestClient) -> None:
    body = client.get(f"/api/artists/{A1}/similar").json()
    assert set(body["artist"]) == ARTIST_FIELDS
    assert all(set(item["artist"]) == ARTIST_FIELDS for item in body["items"])
    assert {k for k in _keys(body) if any(w in k for w in FORBIDDEN_WORDS)} == set()
    assert "listener" not in json.dumps(body).lower()


def test_paging(client: TestClient) -> None:
    page = client.get(f"/api/artists/{A1}/similar", params={"offset": 1, "limit": 2}).json()
    assert [i["artist"]["mbid"] for i in page["items"]] == [A3, A4]
    assert page["has_more"] is True
    last = client.get(f"/api/artists/{A1}/similar", params={"offset": 3, "limit": 2}).json()
    assert [i["artist"]["mbid"] for i in last["items"]] == [A5]
    assert last["has_more"] is False


def test_uppercase_ids_are_accepted(client: TestClient) -> None:
    assert client.get(f"/api/artists/{A1.upper()}/similar").status_code == 200


def test_unknown_artist_is_404_with_a_short_message(client: TestClient) -> None:
    response = client.get(f"/api/artists/{artist_mbid(404)}/similar")
    assert response.status_code == 404
    assert set(response.json()) == {"error"}
    assert "Traceback" not in response.text


@pytest.mark.parametrize(
    "path",
    [
        f"/api/artists/{A1}/similar?offset=-1",
        f"/api/artists/{A1}/similar?limit=0",
        f"/api/artists/{A1}/similar?limit=101",
        f"/api/artists/{A1}/similar?limit=abc",
        "/api/artists/not-a-uuid/similar",
        "/api/artists/..%5C..%5Cetc%5Cpasswd/similar",
        f"/api/artists/{A1}x/similar",
    ],
)
def test_invalid_input_is_422(client: TestClient, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 422
    assert set(response.json()) == {"error"}


def test_bad_id_message_is_short_and_readable(client: TestClient) -> None:
    error = client.get("/api/artists/xyz/similar").json()["error"]
    assert error.startswith("Invalid request: path.mbid: must be a MusicBrainz artist id")


def test_path_like_ids_never_reach_a_lookup(client: TestClient) -> None:
    # An encoded slash splits the path, so the route does not match at all.
    response = client.get("/api/artists/..%2F..%2Fetc%2Fpasswd/similar")
    assert response.status_code == 404
    assert set(response.json()) == {"error"}


def test_artist_without_neighbours_gets_an_empty_page(single_artist_models: Path) -> None:
    client = TestClient(create_app(single_artist_models))
    body = client.get(f"/api/artists/{A1}/similar").json()
    assert body["items"] == [] and body["has_more"] is False
    assert body["artist"]["name"] == "Only One"


def test_health_reports_build_date_and_artist_count(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok" and body["artists"] == 5
    assert body["built_at"].endswith("Z")


def test_lookup_on_fixtures_is_far_inside_the_200ms_budget(client: TestClient) -> None:
    client.get(f"/api/artists/{A1}/similar")  # warm up
    started = time.perf_counter()
    client.get(f"/api/artists/{A1}/similar", params={"limit": 20})
    assert time.perf_counter() - started < 0.2


def test_requests_are_logged_with_method_path_status_and_duration(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="listenbrainz_recs.access"):
        client.get(f"/api/artists/{A1}/similar")
    line = next(r.getMessage() for r in caplog.records if r.name == "listenbrainz_recs.access")
    assert line.startswith(f"GET /api/artists/{A1}/similar 200 ")
    assert line.endswith("ms")


def test_unexpected_errors_are_500_with_no_stack_trace_and_are_logged(
    tiny_models: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def boom(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(SimilarityIndex, "neighbours", boom)
    client = TestClient(create_app(tiny_models), raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR):
        response = client.get(f"/api/artists/{A1}/similar")
    assert response.status_code == 500
    assert response.json() == {"error": "Internal error"}
    assert "secret internal detail" not in response.text
    assert any("secret internal detail" in (r.exc_text or r.getMessage()) for r in caplog.records)


@pytest.mark.parametrize("missing", C2_FILES)
def test_app_refuses_to_start_when_a_built_file_is_missing(
    tiny_models: Path, tmp_path: Path, missing: str
) -> None:
    models = tmp_path / "models"
    shutil.copytree(tiny_models, models)
    (models / missing).unlink()
    with pytest.raises(StartupError) as caught:
        create_app(models)
    assert missing in str(caught.value)
    # Changed by u2-pipeline: the artist file is built by the catalogue step, the rest by index.
    step = "catalogue" if missing == ARTISTS_DB_FILE else "index"
    assert f"listenbrainz-recs-{step}" in str(caught.value)


def test_app_refuses_to_start_on_a_wrong_format_version(tiny_models: Path, tmp_path: Path) -> None:
    models = tmp_path / "models"
    shutil.copytree(tiny_models, models)
    manifest = json.loads((models / MANIFEST_FILE).read_text(encoding="utf-8"))
    manifest["format_version"] = 99
    (models / MANIFEST_FILE).write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(StartupError, match="format version 99"):
        create_app(models)


def test_app_refuses_to_start_on_a_garbled_manifest(tiny_models: Path, tmp_path: Path) -> None:
    models = tmp_path / "models"
    shutil.copytree(tiny_models, models)
    (models / MANIFEST_FILE).write_text("{not json", encoding="utf-8")
    with pytest.raises(StartupError, match="unreadable"):
        create_app(models)


def test_start_command_binds_localhost_by_default() -> None:
    assert DEFAULT_HOST == "127.0.0.1"


def test_start_command_reports_startup_errors_and_exits_non_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["--models-dir", str(tmp_path / "nothing")]) == 1
    err = capsys.readouterr().err
    assert "Missing built file(s)" in err and "Traceback" not in err


def test_start_command_runs_uvicorn_on_the_given_host_and_port(
    tiny_models: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: dict[str, object] = {}

    def fake_run(app: object, **kwargs: object) -> None:
        calls.update(kwargs, app=app)

    monkeypatch.setattr("listenbrainz_recs.app.main.uvicorn.run", fake_run)
    assert main(["--models-dir", str(tiny_models), "--port", "8123"]) == 0
    assert calls["host"] == "127.0.0.1" and calls["port"] == 8123

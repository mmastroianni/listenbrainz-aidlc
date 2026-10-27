"""End to end: build every file from the fixture sample, then ask the endpoint (the slice works)."""

import json
from pathlib import Path

from fastapi.testclient import TestClient
from fixtures.sample_data import ARTISTS_PER_GROUP, artist_mbid, group_of

from listenbrainz_recs.app.main import create_app
from listenbrainz_recs.paths import C2_FILES


def test_pipeline_output_answers_a_similar_artists_request(
    pipeline_outputs: tuple[Path, Path],
) -> None:
    _, models = pipeline_outputs
    assert all((models / name).is_file() for name in C2_FILES)

    client = TestClient(create_app(models))
    assert client.get("/api/health").json()["artists"] == 3 * ARTISTS_PER_GROUP + 1

    subject = artist_mbid(2)
    body = client.get(f"/api/artists/{subject}/similar", params={"limit": 7}).json()
    assert body["artist"]["name"] == "Test Artist 02"
    assert len(body["items"]) == 7 and body["has_more"] is True

    cosines = [item["cosine"] for item in body["items"]]
    assert cosines == sorted(cosines, reverse=True)
    assert subject not in {item["artist"]["mbid"] for item in body["items"]}
    # Listeners of this group listen to its artists together, so the group's other seven
    # artists should head the list.
    top = [int(item["artist"]["mbid"].rsplit("-", 1)[1]) for item in body["items"]]
    assert {group_of(n) for n in top[:5]} == {group_of(2)}
    assert "listener" not in json.dumps(body).lower()

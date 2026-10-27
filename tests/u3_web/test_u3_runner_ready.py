"""The unit-scoped runner collects this folder, and the helpers for the web tests build files."""

from pathlib import Path

import pytest
from fixtures.sample_data import artist_mbid

from listenbrainz_recs.app.main import create_app


def test_runner_collects_this_folder_and_the_app_builds_on_hand_made_files(
    gap_models: Path,
) -> None:
    app = create_app(gap_models)
    assert app.title == "Similar Artists"


def test_the_package_ships_a_static_folder_for_the_page() -> None:
    import listenbrainz_recs.app as app_package

    static = Path(app_package.__file__).parent / "static"
    assert static.is_dir()


@pytest.mark.parametrize("n", [1, 99])
def test_fixture_ids_are_stable(n: int) -> None:
    assert artist_mbid(n).endswith(f"{n:012d}")

"""The unit-scoped runner collects this folder, and the new settings and paths import."""

from pathlib import Path

import pytest

from listenbrainz_recs.errors import ConfigError
from listenbrainz_recs.paths import C2_FILES, output_paths
from listenbrainz_recs.settings import load_settings


def test_defaults_for_the_new_settings() -> None:
    settings = load_settings({})
    assert settings.spark_memory == "24g"
    assert settings.prep_max_lines is None


def test_new_settings_are_read_from_the_environment() -> None:
    settings = load_settings(
        {"LISTENBRAINZ_SPARK_MEMORY": "8G", "LISTENBRAINZ_PREP_MAX_LINES": "5000"}
    )
    assert settings.spark_memory == "8g"
    assert settings.prep_max_lines == 5000


@pytest.mark.parametrize("raw", ["lots", "0g", "24", "-3g"])
def test_bad_memory_setting_is_named_in_the_error(raw: str) -> None:
    with pytest.raises(ConfigError, match="LISTENBRAINZ_SPARK_MEMORY"):
        load_settings({"LISTENBRAINZ_SPARK_MEMORY": raw})


@pytest.mark.parametrize("raw", ["abc", "0", "-5", "1.5"])
def test_bad_line_limit_is_named_in_the_error(raw: str) -> None:
    with pytest.raises(ConfigError, match="LISTENBRAINZ_PREP_MAX_LINES"):
        load_settings({"LISTENBRAINZ_PREP_MAX_LINES": raw})


def test_output_paths_sit_under_the_work_and_models_folders(tmp_path: Path) -> None:
    work, models = tmp_path / "w", tmp_path / "m"
    paths = output_paths(work, models)
    for path in paths.all_paths():
        assert work in path.parents or models in path.parents
    assert {p.name for p in paths.all_paths() if models in p.parents} == set(C2_FILES)

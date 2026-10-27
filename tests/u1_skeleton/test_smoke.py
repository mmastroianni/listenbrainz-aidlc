"""Smoke tests: the package imports and the shared fixtures work."""

from pathlib import Path

import listenbrainz_recs
from listenbrainz_recs.settings import load_settings


def test_package_has_version() -> None:
    parts = listenbrainz_recs.__version__.split(".")
    assert len(parts) == 3 and all(p.isdigit() for p in parts)


def test_settings_defaults_have_no_hardcoded_data_root() -> None:
    settings = load_settings({})
    assert settings.data_root is None
    assert settings.work_dir == Path("data")
    assert settings.models_dir == Path("models")


def test_settings_read_environment() -> None:
    settings = load_settings(
        {
            "LISTENBRAINZ_DATA_ROOT": "/some/where",
            "LISTENBRAINZ_WORK_DIR": "w",
            "LISTENBRAINZ_MODELS_DIR": "m",
        }
    )
    assert settings.data_root == Path("/some/where")
    assert settings.work_dir == Path("w")
    assert settings.models_dir == Path("m")


def test_sample_dump_fixture_exists(sample_dump_root: Path) -> None:
    dump = sample_dump_root / "lbdump" / "statistics" / "artists_all_time.jsonl"
    assert dump.is_file()
    assert len(dump.read_text(encoding="utf-8").splitlines()) > 300

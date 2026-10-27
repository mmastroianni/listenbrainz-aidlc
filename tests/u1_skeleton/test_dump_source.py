"""DumpSource: locating, validating and reading the dump (BR1.1, BR1.2; AC4.1.1, AC4.1.2)."""

import hashlib
import os
from pathlib import Path

import pytest

from listenbrainz_recs.dump_source import dump_label, locate_listening_dump, read_lines
from listenbrainz_recs.errors import ConfigError
from listenbrainz_recs.paths import LISTENING_DUMP_RELATIVE
from listenbrainz_recs.prep import prepare


def _write_dump(folder: Path, text: str = '{"user_id": 1, "data": []}\n') -> Path:
    dump = folder.joinpath(*LISTENING_DUMP_RELATIVE)
    dump.parent.mkdir(parents=True)
    dump.write_text(text, encoding="utf-8")
    return dump


def _snapshot(root: Path) -> dict[str, tuple[str, float]]:
    return {
        str(p.relative_to(root)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_locates_dump_directly_under_the_data_root(tmp_path: Path) -> None:
    dump = _write_dump(tmp_path)
    assert locate_listening_dump(tmp_path) == dump


def test_locates_newest_dump_folder_inside_the_data_root(tmp_path: Path) -> None:
    _write_dump(tmp_path / "listenbrainz-statistics-dump-20250101-000002")
    newest = _write_dump(tmp_path / "listenbrainz-statistics-dump-20260915-000002")
    assert locate_listening_dump(tmp_path) == newest
    assert dump_label(newest) == "listenbrainz-statistics-dump-20260915-000002"


def test_missing_setting_names_the_setting() -> None:
    with pytest.raises(ConfigError, match="LISTENBRAINZ_DATA_ROOT"):
        locate_listening_dump(None)


def test_missing_folder_or_file_names_what_is_missing(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not a folder"):
        locate_listening_dump(tmp_path / "nope")
    with pytest.raises(ConfigError, match=r"artists_all_time\.jsonl"):
        locate_listening_dump(tmp_path)


def test_read_lines_stops_at_the_limit(tmp_path: Path) -> None:
    dump = _write_dump(tmp_path, "".join(f'{{"user_id": {i}, "data": []}}\n' for i in range(20)))
    assert len(list(read_lines(dump, 5))) == 5
    assert len(list(read_lines(dump))) == 20


def test_unreadable_dump_is_a_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Cannot read"):
        list(read_lines(tmp_path / "missing.jsonl"))


def test_running_prepare_leaves_the_dump_folder_unchanged(
    sample_dump_root: Path, tmp_path: Path
) -> None:
    before = _snapshot(sample_dump_root)
    prepare(sample_dump_root, tmp_path / "work")
    assert _snapshot(sample_dump_root) == before


def test_prepare_without_a_setting_writes_nothing(tmp_path: Path) -> None:
    work = tmp_path / "work"
    with pytest.raises(ConfigError):
        prepare(None, work)
    assert not work.exists()
    assert os.listdir(tmp_path) == []

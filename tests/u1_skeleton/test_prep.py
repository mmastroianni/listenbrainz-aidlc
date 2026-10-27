"""ListeningDataPrep: anonymous listen counts from a dump sample (BR1.3 to BR1.5; AC4.1.5)."""

import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from fixtures.sample_data import EDGE_LISTENER, LISTENERS, LONELY_ARTIST, artist_mbid

from listenbrainz_recs.errors import DataError
from listenbrainz_recs.paths import (
    ARTIST_NAMES_DIR,
    INTERACTIONS_DIR,
    LISTENING_DUMP_RELATIVE,
    PREPARED_MARKER,
    TRAINED_MARKER,
)
from listenbrainz_recs.prep import SAMPLE_LINES, PrepSummary, main, prepare


@pytest.fixture(scope="module")
def prepared(sample_dump_root: Path, tmp_path_factory: pytest.TempPathFactory):
    work = tmp_path_factory.mktemp("work")
    summary = prepare(sample_dump_root, work)
    return work, summary


def test_sample_size_is_five_thousand_lines() -> None:
    assert SAMPLE_LINES == 5_000


def test_counts_in_the_run_summary(prepared: tuple[Path, PrepSummary]) -> None:
    _, summary = prepared
    assert summary.lines_read == LISTENERS + 3
    assert summary.lines_skipped == 2  # not JSON, and a non-numeric listener number
    assert summary.entries_skipped == 2  # empty artist id, zero listen count
    assert summary.listeners == LISTENERS + 1  # the edge listener keeps one good entry
    assert summary.artists == 3 * 8 + 1
    assert "prepare: read" in summary.line()


def test_prepared_rows_hold_only_three_columns(prepared: tuple[Path, PrepSummary]) -> None:
    work, summary = prepared
    table = pq.read_table(work / INTERACTIONS_DIR)
    assert table.column_names == ["user_id", "artist_mbid", "listen_count"]
    assert table.num_rows == summary.rows
    assert min(table.column("listen_count").to_pylist()) >= 1


def test_no_listener_details_reach_prepared_data(prepared: tuple[Path, PrepSummary]) -> None:
    work, _ = prepared
    for path in work.rglob("*"):
        if path.is_file():
            assert b"private-listener-name" not in path.read_bytes()
    names = pq.read_table(work / ARTIST_NAMES_DIR)
    assert names.column_names == ["artist_mbid", "artist_name"]


def test_bad_entries_are_dropped_and_good_ones_kept(prepared: tuple[Path, PrepSummary]) -> None:
    work, _ = prepared
    rows = pq.read_table(work / INTERACTIONS_DIR).to_pylist()
    edge = [r for r in rows if r["user_id"] == EDGE_LISTENER]
    assert [r["artist_mbid"] for r in edge] == [artist_mbid(LONELY_ARTIST)]
    assert artist_mbid(1) not in {r["artist_mbid"] for r in edge}
    names = {
        r["artist_mbid"]: r["artist_name"]
        for r in pq.read_table(work / ARTIST_NAMES_DIR).to_pylist()
    }
    assert names[artist_mbid(0)] == "Bjørk Tëst Zero"


def test_markers_written_and_trained_marker_invalidated(
    sample_dump_root: Path, tmp_path: Path
) -> None:
    work = tmp_path / "work"
    work.mkdir()
    (work / TRAINED_MARKER).write_text("{}", encoding="utf-8")
    prepare(sample_dump_root, work)
    assert not (work / TRAINED_MARKER).exists()
    marker = json.loads((work / PREPARED_MARKER).read_text(encoding="utf-8"))
    assert marker["step"] == "prepare"
    assert not list(work.glob("*.tmp"))


def test_max_lines_limits_what_is_read(sample_dump_root: Path, tmp_path: Path) -> None:
    summary = prepare(sample_dump_root, tmp_path / "work", max_lines=10)
    assert summary.lines_read == 10
    assert summary.listeners == 10


def test_duplicate_entries_for_one_listener_are_summed(tmp_path: Path) -> None:
    root = tmp_path / "root"
    dump = root.joinpath(*LISTENING_DUMP_RELATIVE)
    dump.parent.mkdir(parents=True)
    mbid = artist_mbid(5)
    entry = {"listen_count": 4, "artist_name": "Dup", "artist_mbid": mbid}
    dump.write_text(json.dumps({"user_id": 7, "data": [entry, entry]}) + "\n", encoding="utf-8")
    prepare(root, tmp_path / "work")
    rows = pq.read_table(tmp_path / "work" / INTERACTIONS_DIR).to_pylist()
    assert rows == [{"user_id": 7, "artist_mbid": mbid, "listen_count": 8}]


def test_dump_without_usable_counts_is_an_error(tmp_path: Path) -> None:
    root = tmp_path / "root"
    dump = root.joinpath(*LISTENING_DUMP_RELATIVE)
    dump.parent.mkdir(parents=True)
    dump.write_text("garbage\n", encoding="utf-8")
    with pytest.raises(DataError, match="No usable listen counts"):
        prepare(root, tmp_path / "work")
    assert not (tmp_path / "work" / PREPARED_MARKER).exists()


def test_command_reports_failure_without_a_stack_trace(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.delenv("LISTENBRAINZ_DATA_ROOT", raising=False)
    monkeypatch.setenv("LISTENBRAINZ_WORK_DIR", str(tmp_path / "work"))
    assert main() == 1
    err = capsys.readouterr().err
    assert "LISTENBRAINZ_DATA_ROOT" in err
    assert "Traceback" not in err


def test_command_prints_one_summary_line(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    sample_dump_root: Path,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("LISTENBRAINZ_DATA_ROOT", str(sample_dump_root))
    monkeypatch.setenv("LISTENBRAINZ_WORK_DIR", str(tmp_path / "work"))
    assert main() == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1
    assert out[0].startswith("prepare:")

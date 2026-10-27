"""ListeningDataPrep on the walking-skeleton path: anonymous listen counts (BR1.3 to BR1.5).

Changed by u2-pipeline: the 5,000-line sample is now the optional `LISTENBRAINZ_PREP_MAX_LINES`
setting, artists need 5 listeners, and the summary has new field names. The detailed rule tests
are in `tests/u2_pipeline/test_prep_full.py`.
"""

import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from fixtures.sample_data import (
    EDGE_LISTENER,
    KEPT_ARTISTS,
    SKIPPED_ENTRIES,
    SKIPPED_RECORDS,
    TOTAL_LINES,
    artist_mbid,
    write_musicbrainz,
)
from pyspark.sql import SparkSession

from listenbrainz_recs.errors import DataError
from listenbrainz_recs.paths import (
    ARTIST_NAMES_DIR,
    INTERACTIONS_DIR,
    LISTENING_DUMP_RELATIVE,
    PREPARED_MARKER,
)
from listenbrainz_recs.prep import PrepSummary, main, prepare


def test_counts_in_the_run_summary(prepared_work: Path) -> None:
    marker = json.loads((prepared_work / PREPARED_MARKER).read_text(encoding="utf-8"))
    assert marker["step"] == "prepare"
    details = marker["details"]
    assert details["lines_read"] == TOTAL_LINES
    assert details["skipped_records"] == SKIPPED_RECORDS
    assert details["skipped_entries"] == SKIPPED_ENTRIES
    assert details["artists"] == KEPT_ARTISTS


def test_prepared_rows_hold_only_three_columns(prepared_work: Path) -> None:
    table = pq.read_table(prepared_work / INTERACTIONS_DIR)
    assert table.column_names == ["user_id", "artist_mbid", "listen_count"]
    assert min(table.column("listen_count").to_pylist()) >= 1


def test_no_listener_details_reach_prepared_data(prepared_work: Path) -> None:
    for path in prepared_work.rglob("*"):
        if path.is_file():
            assert b"private-listener-name" not in path.read_bytes()
    names = pq.read_table(prepared_work / ARTIST_NAMES_DIR)
    assert names.column_names == ["artist_mbid", "artist_name"]


def test_bad_entries_are_dropped_and_good_ones_kept(prepared_work: Path) -> None:
    rows = pq.read_table(prepared_work / INTERACTIONS_DIR).to_pylist()
    # The edge listener's only good entry is an artist with one listener, which the 5-listener
    # cutoff (BR1.7, new in u2) now removes; the bad entries never appear.
    assert EDGE_LISTENER not in {r["user_id"] for r in rows}
    assert artist_mbid(1) in {r["artist_mbid"] for r in rows}
    names = {
        r["artist_mbid"]: r["artist_name"]
        for r in pq.read_table(prepared_work / ARTIST_NAMES_DIR).to_pylist()
    }
    assert names[artist_mbid(0)] == "Bjørk Tëst Zero"


def test_markers_written_without_leftover_temp_files(
    sample_dump_root: Path, spark: SparkSession, tmp_path: Path
) -> None:
    work = tmp_path / "work"
    summary = prepare(sample_dump_root, work, spark)
    assert isinstance(summary, PrepSummary)
    assert (work / PREPARED_MARKER).is_file()
    assert not list(work.glob("*.tmp"))


def test_max_lines_limits_what_is_read(
    sample_dump_root: Path, spark: SparkSession, tmp_path: Path
) -> None:
    summary = prepare(sample_dump_root, tmp_path / "work", spark, max_lines=60)
    assert summary.lines_read == 60


def test_dump_without_usable_counts_is_an_error(spark: SparkSession, tmp_path: Path) -> None:
    root = tmp_path / "root"
    dump = root.joinpath(*LISTENING_DUMP_RELATIVE)
    dump.parent.mkdir(parents=True)
    dump.write_text("garbage\n", encoding="utf-8")
    write_musicbrainz(root)  # prepare checks every dump file before it writes anything
    with pytest.raises(DataError, match="No usable listener line"):
        prepare(root, tmp_path / "work", spark)
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

"""ListeningDataPrep at full rules: skipping, repeats, 5-listener cutoff, names, report, privacy
(BR1.1, BR1.3 to BR1.8, BR3.2; AC4.1.2 to AC4.1.5; NFR3.4, NFR3.6, NFR2.13, NFR2.14)."""

import json
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from fixtures.sample_data import (
    FIVE_LISTENER_ARTIST,
    FIVE_NAME_MAJORITY,
    FOUR_LISTENER_ARTIST,
    KEPT_ARTISTS,
    LONELY_ARTIST,
    PRIVATE_LISTENER_NAME,
    REPEAT_ARTIST,
    REPEAT_LISTENER,
    SKIPPED_ENTRIES,
    SKIPPED_RECORDS,
    TOTAL_LINES,
    VALID_RECORDS,
    artist_mbid,
    sample_lines,
    write_musicbrainz,
)
from pyspark.sql import SparkSession

from listenbrainz_recs import steps
from listenbrainz_recs.errors import ConfigError, DataError
from listenbrainz_recs.paths import (
    ARTIST_LISTENERS_DIR,
    ARTIST_NAMES_DIR,
    INTERACTIONS_DIR,
    LISTENING_DUMP_RELATIVE,
    PREPARE_REPORT_FILE,
    PREPARED_MARKER,
)
from listenbrainz_recs.prep import MIN_LISTENERS, PrepSummary, main, prepare


def _entry(mbid: str, count: int, name: str = "N") -> dict[str, object]:
    return {"artist_mbid": mbid, "artist_name": name, "listen_count": count}


def _make_root(root: Path, lines: list[str]) -> Path:
    dump = root.joinpath(*LISTENING_DUMP_RELATIVE)
    dump.parent.mkdir(parents=True, exist_ok=True)
    dump.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_musicbrainz(root)
    return root


def _five_listener_lines(mbid: str, name: str = "Five", first_user: int = 1) -> list[str]:
    users = range(first_user, first_user + MIN_LISTENERS)
    return [json.dumps({"user_id": u, "data": [_entry(mbid, 2, name)]}) for u in users]


def _rows(work: Path) -> list[dict[str, object]]:
    return pq.read_table(work / INTERACTIONS_DIR).to_pylist()


def _names(work: Path) -> dict[str, str]:
    table = pq.read_table(work / ARTIST_NAMES_DIR).to_pylist()
    return {r["artist_mbid"]: r["artist_name"] for r in table}


def _reference(lines: list[str]) -> tuple[dict[tuple[int, str], int], dict[str, str]]:
    """The expected counts and names, worked out in plain Python from the raw lines."""
    counts: dict[tuple[int, str], int] = defaultdict(int)
    spellings: dict[str, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict) or not isinstance(record.get("user_id"), int):
            continue
        if not isinstance(record.get("data"), list):
            continue
        for entry in record["data"]:
            mbid = entry.get("artist_mbid", "")
            count = entry.get("listen_count", 0)
            if not mbid or count < 1:
                continue
            counts[(record["user_id"], mbid)] += count
            spellings[mbid][entry["artist_name"]].add(record["user_id"])
    listeners: dict[str, int] = defaultdict(int)
    for _, mbid in counts:
        listeners[mbid] += 1
    kept = {m for m, n in listeners.items() if n >= MIN_LISTENERS}
    names = {
        m: sorted(spellings[m].items(), key=lambda kv: (-len(kv[1]), kv[0]))[0][0] for m in kept
    }
    return {k: v for k, v in counts.items() if k[1] in kept}, names


@pytest.fixture(scope="module")
def prepared(
    sample_dump_root: Path, spark: SparkSession, tmp_path_factory: pytest.TempPathFactory
) -> tuple[Path, PrepSummary]:
    work = tmp_path_factory.mktemp("work_prep_full")
    return work, prepare(sample_dump_root, work, spark)


def test_counts_in_the_run_summary(prepared: tuple[Path, PrepSummary]) -> None:
    _, summary = prepared
    assert summary.lines_read == TOTAL_LINES
    assert summary.valid_records == VALID_RECORDS
    assert summary.skipped_records == SKIPPED_RECORDS
    assert summary.skipped_entries == SKIPPED_ENTRIES
    assert summary.artists == KEPT_ARTISTS
    assert summary.line().startswith("prepare: read")
    assert summary.seconds > 0


def test_one_malformed_line_gives_one_skipped_record_and_every_valid_line_is_processed(
    tmp_path: Path, spark: SparkSession
) -> None:
    lines = _five_listener_lines(artist_mbid(1))
    lines.insert(2, "{this is broken json")
    summary = prepare(_make_root(tmp_path / "root", lines), tmp_path / "work", spark)
    assert summary.skipped_records == 1  # AC4.1.3
    assert summary.valid_records == MIN_LISTENERS
    assert len(_rows(tmp_path / "work")) == MIN_LISTENERS


def test_an_artist_with_four_listeners_is_dropped_and_one_with_five_is_kept(
    prepared: tuple[Path, PrepSummary], tmp_path: Path, spark: SparkSession
) -> None:
    work, _ = prepared
    kept = {r["artist_mbid"] for r in _rows(work)}
    assert artist_mbid(FIVE_LISTENER_ARTIST) in kept  # AC4.1.4: 5 is in
    assert artist_mbid(FOUR_LISTENER_ARTIST) not in kept  # 4 is out
    assert artist_mbid(LONELY_ARTIST) not in kept  # 1 is out
    listeners = {
        r["artist_mbid"]: r["listener_count"]
        for r in pq.read_table(work / ARTIST_LISTENERS_DIR).to_pylist()
    }
    assert listeners[artist_mbid(FIVE_LISTENER_ARTIST)] == 5
    assert set(listeners) == kept and min(listeners.values()) >= MIN_LISTENERS


def test_repeated_entries_for_one_listener_and_artist_are_added_together(
    prepared: tuple[Path, PrepSummary],
) -> None:
    work, _ = prepared
    repeat = [
        r
        for r in _rows(work)
        if r["user_id"] == REPEAT_LISTENER and r["artist_mbid"] == artist_mbid(REPEAT_ARTIST)
    ]
    assert repeat == [
        {"user_id": REPEAT_LISTENER, "artist_mbid": artist_mbid(REPEAT_ARTIST), "listen_count": 7}
    ]


def test_each_artist_gets_its_most_used_name_and_ties_go_to_the_first_alphabetically(
    prepared: tuple[Path, PrepSummary], tmp_path: Path, spark: SparkSession
) -> None:
    work, _ = prepared
    assert _names(work)[artist_mbid(FIVE_LISTENER_ARTIST)] == FIVE_NAME_MAJORITY  # 3 votes to 2
    tied = [
        json.dumps({"user_id": u, "data": [_entry(artist_mbid(7), 1, name)]})
        for u, name in zip(range(1, 7), ["Zed", "Zed", "Zed", "Abe", "Abe", "Abe"], strict=True)
    ]
    summary = prepare(_make_root(tmp_path / "root", tied), tmp_path / "work", spark)
    assert summary.artists == 1
    assert _names(tmp_path / "work") == {artist_mbid(7): "Abe"}  # 3 against 3: alphabetical
    nameless = [
        json.dumps({"user_id": u, "data": [{"artist_mbid": artist_mbid(8), "listen_count": 1}]})
        for u in range(1, 6)
    ]
    prepare(_make_root(tmp_path / "root2", nameless), tmp_path / "work2", spark)
    assert _names(tmp_path / "work2") == {artist_mbid(8): ""}  # a kept artist always has a row


def test_prepared_output_holds_only_listener_number_artist_id_and_count(
    prepared: tuple[Path, PrepSummary],
) -> None:
    work, summary = prepared
    table = pq.read_table(work / INTERACTIONS_DIR)
    assert table.column_names == ["user_id", "artist_mbid", "listen_count"]  # AC4.1.5
    assert [str(t) for t in table.schema.types] == ["int32", "string", "int32"]
    assert table.num_rows == summary.rows and min(table.column("listen_count").to_pylist()) >= 1
    assert pq.read_table(work / ARTIST_NAMES_DIR).column_names == ["artist_mbid", "artist_name"]
    assert pq.read_table(work / ARTIST_LISTENERS_DIR).column_names == [
        "artist_mbid",
        "listener_count",
    ]
    for path in work.rglob("*"):
        if path.is_file():
            assert PRIVATE_LISTENER_NAME.encode() not in path.read_bytes()


def test_output_matches_a_plain_python_reference(
    prepared: tuple[Path, PrepSummary],
) -> None:
    work, _ = prepared
    counts, names = _reference(sample_lines())
    assert {(r["user_id"], r["artist_mbid"]): r["listen_count"] for r in _rows(work)} == counts
    assert _names(work) == names


def test_the_report_is_stored_and_matches_the_marker(prepared: tuple[Path, PrepSummary]) -> None:
    work, summary = prepared
    report = json.loads((work / PREPARE_REPORT_FILE).read_text(encoding="utf-8"))
    assert report["valid_records"] == VALID_RECORDS
    assert report["skipped_records"] == SKIPPED_RECORDS
    assert report["skipped_entries"] == SKIPPED_ENTRIES
    assert report["kept_artists"] == KEPT_ARTISTS
    assert report["run_timestamp"].endswith("Z")
    marker = steps.require_marker(work, steps.PREPARE)
    assert marker.run_id == report["run_id"] == summary.run_id
    assert marker.details["source_dump"] == report["source_dump"]
    assert not list(work.glob("*.tmp"))


def test_a_sample_run_reads_only_the_first_lines(tmp_path: Path, spark: SparkSession) -> None:
    root = _make_root(tmp_path / "root", sample_lines())
    summary = prepare(root, tmp_path / "work", spark, max_lines=60)
    assert summary.lines_read == 60 and summary.skipped_records == 0
    users = {r["user_id"] for r in _rows(tmp_path / "work")}
    assert users == set(range(1, 61))


def test_the_printed_summary_shows_counts_only(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    sample_dump_root: Path,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("LISTENBRAINZ_DATA_ROOT", str(sample_dump_root))
    monkeypatch.setenv("LISTENBRAINZ_WORK_DIR", str(tmp_path / "work"))
    monkeypatch.setenv("LISTENBRAINZ_PREP_MAX_LINES", "1000")
    monkeypatch.setattr("listenbrainz_recs.prep.get_spark", _shared_spark)
    assert main() == 0
    captured = capsys.readouterr()
    out = captured.out.strip().splitlines()
    assert len(out) == 1 and out[0].startswith("prepare:")
    for number in (9001, 9101, 9111, 9201):
        assert str(number) not in captured.out + captured.err


def _shared_spark(*_args: object, **_kwargs: object) -> SparkSession:
    from pyspark.sql import SparkSession as Session

    wrapped = _NonStopping(Session.builder.getOrCreate())  # type: ignore[attr-defined]
    return wrapped  # ty: ignore[invalid-return-type]


class _NonStopping:
    """Wraps the shared session so the command's `stop()` does not end it for other tests."""

    def __init__(self, session: SparkSession) -> None:
        self._session = session

    def stop(self) -> None:
        return None

    def __getattr__(self, name: str) -> object:
        return getattr(self._session, name)


def test_a_dump_with_no_valid_line_is_an_error_and_leaves_no_marker(
    tmp_path: Path, spark: SparkSession
) -> None:
    root = _make_root(tmp_path / "root", ["garbage", "{not json", "[1, 2]"])
    with pytest.raises(DataError, match="No usable listener line.*all 3 lines were malformed"):
        prepare(root, tmp_path / "work", spark)
    assert not (tmp_path / "work" / PREPARED_MARKER).exists()
    assert not list((tmp_path / "work").glob("*.tmp"))


def test_no_artist_with_enough_listeners_is_an_error_naming_the_cutoff(
    tmp_path: Path, spark: SparkSession
) -> None:
    lines = _five_listener_lines(artist_mbid(1))[: MIN_LISTENERS - 1]
    root = _make_root(tmp_path / "root", lines)
    with pytest.raises(DataError, match="No artist has at least 5 listeners"):
        prepare(root, tmp_path / "work", spark)
    assert not (tmp_path / "work" / PREPARED_MARKER).exists()
    assert not list((tmp_path / "work").glob("*.tmp"))


def test_a_bad_location_writes_nothing(tmp_path: Path, spark: SparkSession) -> None:
    work = tmp_path / "work"
    with pytest.raises(ConfigError, match="LISTENBRAINZ_DATA_ROOT"):
        prepare(None, work, spark)  # AC4.1.2: the setting is missing
    root = _make_root(tmp_path / "root", sample_lines())
    (root / "data" / "musicbrainz" / "mbdump" / "genre").unlink()
    with pytest.raises(ConfigError, match=r"genre"):
        prepare(root, work, spark)  # a table is missing: stops before the run starts
    assert not work.exists()


def test_a_new_run_clears_the_old_marker_and_gets_a_new_run_id(
    sample_dump_root: Path, tmp_path: Path, spark: SparkSession
) -> None:
    first = prepare(sample_dump_root, tmp_path / "work", spark, max_lines=100)
    second = prepare(sample_dump_root, tmp_path / "work", spark, max_lines=100)
    assert first.run_id != second.run_id
    assert steps.require_marker(tmp_path / "work", steps.PREPARE).run_id == second.run_id

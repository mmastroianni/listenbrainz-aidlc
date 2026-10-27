"""SimilarityTraining at full rules: settings, one vector per artist, memory stop, markers
(BR2.1 to BR2.4, BR6.3, BR6.4; AC4.2.1; NFR2.8, NFR2.12, NFR2.13)."""

import json
import shutil
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import pytest
from conftest import FIXTURE_TRAIN_SETTINGS
from fixtures.sample_data import ARTISTS_PER_GROUP, KEPT_ARTISTS, group_of
from pyspark.sql import DataFrame, SparkSession

from listenbrainz_recs import steps
from listenbrainz_recs.errors import DataError, StepOrderError
from listenbrainz_recs.paths import (
    ARTIST_LISTENERS_DIR,
    PREPARE_REPORT_FILE,
    TRAINED_MARKER,
    VECTORS_DIR,
)
from listenbrainz_recs.train import (
    DEFAULT_SETTINGS,
    TrainSettings,
    TrainSummary,
    learn_vectors,
    main,
    train,
)


@pytest.fixture(scope="module")
def trained(
    prepared_work: Path, spark: SparkSession, tmp_path_factory: pytest.TempPathFactory
) -> tuple[Path, TrainSummary]:
    work = tmp_path_factory.mktemp("work_train_full")
    shutil.copytree(prepared_work, work, dirs_exist_ok=True)
    return work, train(work, spark, settings=FIXTURE_TRAIN_SETTINGS)


def _copy_prepared(prepared_work: Path, tmp_path: Path) -> Path:
    work = tmp_path / "work"
    shutil.copytree(prepared_work, work)
    return work


def _kept_ids(work: Path) -> set[str]:
    return {r["artist_mbid"] for r in pq.read_table(work / ARTIST_LISTENERS_DIR).to_pylist()}


def test_default_settings_are_the_current_apps(
    prepared_work: Path, spark: SparkSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert (
        TrainSettings(rank=64, max_iter=10, reg_param=0.1, alpha=20.0, seed=42) == DEFAULT_SETTINGS
    )
    seen: dict[str, object] = {}
    real_als = learn_vectors.__globals__["ALS"]

    def spy(**kwargs: object) -> object:
        seen.update(kwargs)
        return real_als(**kwargs)

    monkeypatch.setitem(learn_vectors.__globals__, "ALS", spy)
    interactions = spark.read.parquet(str(prepared_work / "interactions"))
    learn_vectors(interactions, TrainSettings(rank=4, max_iter=1))  # only the call is inspected
    assert seen["implicitPrefs"] is True and seen["alpha"] == 20.0
    assert seen["regParam"] == 0.1 and seen["seed"] == 42 and seen["rank"] == 4


def test_there_is_one_vector_per_kept_artist(trained: tuple[Path, TrainSummary]) -> None:
    work, summary = trained
    rows = pq.read_table(work / VECTORS_DIR).to_pylist()
    ids = [r["artist_mbid"] for r in rows]
    assert len(ids) == len(set(ids)) == summary.artists == KEPT_ARTISTS  # AC4.2.1
    assert set(ids) == _kept_ids(work)
    matrix = np.array([r["features"] for r in rows], dtype=np.float32)
    assert matrix.shape == (KEPT_ARTISTS, FIXTURE_TRAIN_SETTINGS.rank)
    assert np.isfinite(matrix).all()


def test_artists_listened_to_together_end_up_closer(trained: tuple[Path, TrainSummary]) -> None:
    work, _ = trained
    rows = pq.read_table(work / VECTORS_DIR).to_pylist()
    rows = [r for r in rows if int(r["artist_mbid"].rsplit("-", 1)[1]) < 3 * ARTISTS_PER_GROUP]
    groups = np.array([group_of(int(r["artist_mbid"].rsplit("-", 1)[1])) for r in rows])
    matrix = np.array([r["features"] for r in rows], dtype=np.float64)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    sims = matrix @ matrix.T
    same = groups[:, None] == groups[None, :]
    off_diagonal = ~np.eye(len(rows), dtype=bool)
    assert sims[same & off_diagonal].mean() > sims[~same].mean()


def test_the_marker_records_the_run_and_the_summary_line_counts(
    trained: tuple[Path, TrainSummary],
) -> None:
    work, summary = trained
    marker = steps.require_marker(work, steps.TRAIN)
    prepared = steps.require_marker(work, steps.PREPARE)
    assert marker.input_run_id == prepared.run_id and marker.details["artists"] == KEPT_ARTISTS
    assert steps.require_current(work, marker) == prepared
    line = summary.line()
    assert f"{KEPT_ARTISTS} artist vectors of rank 8" in line and "0 zero-length dropped" in line
    assert not list(work.glob("*.tmp"))


def test_training_does_not_need_the_dump(
    prepared_work: Path, spark: SparkSession, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("training must not open the dump")  # BR2.4

    for name in ("check_dump_files", "locate_listening_dump", "read_lines"):
        monkeypatch.setattr(f"listenbrainz_recs.dump_source.{name}", forbidden)
    work = _copy_prepared(prepared_work, tmp_path)
    assert train(work, spark, settings=FIXTURE_TRAIN_SETTINGS).artists == KEPT_ARTISTS


def test_training_before_prepare_names_the_missing_step(tmp_path: Path) -> None:
    with pytest.raises(StepOrderError) as caught:
        train(tmp_path)
    assert "prepared listen counts" in str(caught.value)
    assert "uv run listenbrainz-recs-prepare" in str(caught.value)
    assert not (tmp_path / VECTORS_DIR).exists()


def test_prepared_data_from_another_run_is_refused_as_stale(
    prepared_work: Path, spark: SparkSession, tmp_path: Path
) -> None:
    work = _copy_prepared(prepared_work, tmp_path)
    report = work / PREPARE_REPORT_FILE
    data = json.loads(report.read_text(encoding="utf-8"))
    data["run_id"] = "some-other-run"
    report.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(StepOrderError, match="does not belong to the current prepare run"):
        train(work, spark, settings=FIXTURE_TRAIN_SETTINGS)
    report.unlink()
    with pytest.raises(StepOrderError, match="prepare report.*missing or unreadable"):
        train(work, spark, settings=FIXTURE_TRAIN_SETTINGS)
    assert not (work / VECTORS_DIR).exists()


def test_zero_length_vectors_are_dropped_and_counted(
    prepared_work: Path, spark: SparkSession, tmp_path: Path
) -> None:
    work = _copy_prepared(prepared_work, tmp_path)

    def stand_in(interactions: DataFrame, settings: TrainSettings) -> DataFrame:
        ids = sorted(
            r["artist_mbid"] for r in interactions.select("artist_mbid").distinct().collect()
        )
        rows = [(m, [0.0, 0.0] if n < 2 else [1.0, float(n)]) for n, m in enumerate(ids)]
        return spark.createDataFrame(rows, "artist_mbid string, features array<float>")

    summary = train(work, spark, fit=stand_in)
    ids = {r["artist_mbid"] for r in pq.read_table(work / VECTORS_DIR).to_pylist()}
    assert (summary.artists, summary.dropped) == (KEPT_ARTISTS - 2, 2)
    assert len(ids) == KEPT_ARTISTS - 2
    assert "2 zero-length dropped" in summary.line()


def test_running_out_of_memory_names_the_setting_and_leaves_no_marker(
    prepared_work: Path, spark: SparkSession, tmp_path: Path
) -> None:
    work = _copy_prepared(prepared_work, tmp_path)

    def out_of_memory(_interactions: DataFrame, _settings: TrainSettings) -> DataFrame:
        raise MemoryError("java.lang.OutOfMemoryError: Java heap space")

    with pytest.raises(DataError) as caught:
        train(work, spark, fit=out_of_memory)
    assert "LISTENBRAINZ_SPARK_MEMORY" in str(caught.value) and "ran out of memory" in str(
        caught.value
    )
    assert not (work / TRAINED_MARKER).exists() and not (work / VECTORS_DIR).exists()
    assert not list(work.glob("*.tmp"))


def test_unreadable_prepared_data_is_a_clear_error(
    prepared_work: Path, spark: SparkSession, tmp_path: Path
) -> None:
    work = _copy_prepared(prepared_work, tmp_path)
    for part in (work / "interactions").glob("*.parquet"):
        part.write_text("not parquet", encoding="utf-8")
    with pytest.raises(DataError, match="train step failed in Spark"):
        train(work, spark, settings=FIXTURE_TRAIN_SETTINGS)
    assert not (work / TRAINED_MARKER).exists()


def test_the_command_reports_a_missing_input_without_a_stack_trace(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.setenv("LISTENBRAINZ_WORK_DIR", str(tmp_path / "work"))
    assert main() == 1
    err = capsys.readouterr().err
    assert "run the prepare step first" in err and "Traceback" not in err


def test_a_bad_memory_setting_stops_the_command_naming_it(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.setenv("LISTENBRAINZ_SPARK_MEMORY", "plenty")
    assert main() == 1
    err = capsys.readouterr().err
    assert "LISTENBRAINZ_SPARK_MEMORY" in err and "Traceback" not in err

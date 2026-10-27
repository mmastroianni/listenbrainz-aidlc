"""Speed command: percentile arithmetic, output, exit code, and the fixture-size guard (BR5.3)."""

import time
from pathlib import Path

import pytest
from fixtures.sample_data import KEPT_ARTISTS

from listenbrainz_recs.errors import StartupError
from listenbrainz_recs.speed import (
    LIMIT_MS,
    KindResult,
    SpeedReport,
    main,
    percentile,
    run_speed_check,
    typed_text,
)
from listenbrainz_recs.store import load_store


def test_percentile_uses_the_nearest_rank() -> None:
    values = [float(n) for n in range(1, 101)]
    assert percentile(values, 95) == 95.0
    assert percentile(list(reversed(values)), 95) == 95.0  # order does not matter
    assert percentile([7.0], 95) == 7.0
    assert percentile([1.0, 2.0, 3.0], 50) == 2.0
    with pytest.raises(ValueError, match="no values"):
        percentile([], 95)


def test_output_lines_show_count_percentile_limit_and_verdict() -> None:
    report = SpeedReport(
        count=100,
        similar=KindResult("similar artists", 12.34, 200.0),
        suggestions=KindResult("suggestions", 250.0, 200.0),
    )
    assert report.lines() == [
        "similar artists: 100 lookups, 95th percentile 12.3 ms (limit 200 ms) PASS",
        "suggestions: 100 lookups, 95th percentile 250.0 ms (limit 200 ms) FAIL",
    ]
    assert not report.passed


def test_a_forced_slow_lookup_is_reported_as_a_fail(pipeline_outputs: tuple[Path, Path]) -> None:
    _, models = pipeline_outputs
    store = load_store(models)
    try:
        report = run_speed_check(
            store, limit_ms=5.0, neighbours=lambda _mbid: time.sleep(0.02), suggest=lambda _t: None
        )
    finally:
        store.close()
    assert not report.similar.passed and report.suggestions.passed
    assert not report.passed
    assert report.similar.p95_ms >= 20.0


def test_fewer_artists_than_the_target_uses_what_exists(
    pipeline_outputs: tuple[Path, Path],
) -> None:
    _, models = pipeline_outputs
    store = load_store(models)
    try:
        report = run_speed_check(store)  # asks for 100, the fixture build holds fewer
        small = run_speed_check(store, count=3)
    finally:
        store.close()
    assert report.count == KEPT_ARTISTS and small.count == 3


def test_both_lookups_answer_under_the_limit_on_the_fixture_build(
    pipeline_outputs: tuple[Path, Path],
) -> None:
    """NFR1.9: a guard against slow code, on the fixture-sized build."""
    _, models = pipeline_outputs
    store = load_store(models)
    try:
        report = run_speed_check(store)
    finally:
        store.close()
    assert report.similar.p95_ms < LIMIT_MS
    assert report.suggestions.p95_ms < LIMIT_MS
    assert report.passed


def test_the_command_exits_zero_on_pass_and_prints_both_kinds(
    pipeline_outputs: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, models = pipeline_outputs
    monkeypatch.setenv("LISTENBRAINZ_MODELS_DIR", str(models))
    assert main() == 0
    out = capsys.readouterr().out
    assert "similar artists: 25 lookups" in out and "suggestions: 25 lookups" in out
    assert out.strip().endswith("speed check: PASS")


def test_the_command_reports_missing_built_files_without_a_stack_trace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LISTENBRAINZ_MODELS_DIR", str(tmp_path))
    assert main() == 1
    err = capsys.readouterr().err
    assert "Missing built file" in err and "Traceback" not in err
    with pytest.raises(StartupError):
        load_store(tmp_path)


def test_typed_text_is_the_start_of_the_name() -> None:
    assert typed_text("Henry Threadgill") == "Henry Th"
    assert typed_text("Bo") == "Bo"

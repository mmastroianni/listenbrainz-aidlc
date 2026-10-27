"""Step markers: missing and stale input checks, atomic writes (BR6.1, BR6.3, BR6.4; AC4.3.2)."""

from pathlib import Path

import pytest

from listenbrainz_recs import fsutil, steps
from listenbrainz_recs.errors import StepOrderError
from listenbrainz_recs.paths import PREPARED_MARKER, TRAINED_MARKER


def test_a_marker_is_written_and_read_back(tmp_path: Path) -> None:
    written = steps.write_marker(tmp_path, steps.PREPARE, details={"source_dump": "d1"})
    read = steps.read_marker(tmp_path, steps.PREPARE)
    assert read == written
    assert read is not None and read.details == {"source_dump": "d1"}
    assert read.input_run_id == "" and read.completed_at.endswith("Z")
    assert len(read.run_id) == 32


def test_missing_input_names_the_input_and_the_step_to_run(tmp_path: Path) -> None:
    with pytest.raises(StepOrderError) as caught:
        steps.require_marker(tmp_path, steps.PREPARE)
    message = str(caught.value)
    assert "prepared listen counts" in message
    assert "run the prepare step first" in message
    assert "uv run listenbrainz-recs-prepare" in message
    assert steps.read_marker(tmp_path, steps.TRAIN) is None


def test_a_marker_made_from_an_older_run_is_stale(tmp_path: Path) -> None:
    prepared = steps.write_marker(tmp_path, steps.PREPARE)
    stale = steps.write_marker(tmp_path, steps.TRAIN, input_run_id="not-the-current-run")
    with pytest.raises(StepOrderError) as caught:
        steps.require_current(tmp_path, stale)
    message = str(caught.value)
    assert "trained vectors" in message and "older prepare run" in message
    assert "run the train step again" in message
    fresh = steps.write_marker(tmp_path, steps.TRAIN, input_run_id=prepared.run_id)
    assert steps.require_current(tmp_path, fresh) == prepared


def test_rebuilding_an_earlier_step_makes_later_steps_refuse(tmp_path: Path) -> None:
    prepared = steps.write_marker(tmp_path, steps.PREPARE)
    trained = steps.write_marker(tmp_path, steps.TRAIN, input_run_id=prepared.run_id)
    catalogued = steps.write_marker(tmp_path, steps.CATALOGUE, input_run_id=prepared.run_id)
    steps.require_current(tmp_path, trained)
    steps.require_current(tmp_path, catalogued)

    steps.write_marker(tmp_path, steps.PREPARE)  # prepare is run again: a new run id
    for old in (trained, catalogued):
        with pytest.raises(StepOrderError, match=f"run the {old.step} step again"):
            steps.require_current(tmp_path, old)


def test_the_index_step_input_is_the_train_marker(tmp_path: Path) -> None:
    trained = steps.write_marker(tmp_path, steps.TRAIN, input_run_id="p")
    indexed = steps.write_marker(tmp_path, steps.INDEX, input_run_id=trained.run_id)
    assert steps.require_current(tmp_path, indexed) == trained
    steps.write_marker(tmp_path, steps.TRAIN, input_run_id="p")
    with pytest.raises(StepOrderError, match="similarity index.*older train run"):
        steps.require_current(tmp_path, indexed)


def test_markers_are_written_atomically_and_can_be_cleared(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    steps.write_marker(tmp_path, steps.PREPARE, details={"n": 1})
    assert [p.name for p in tmp_path.iterdir()] == [PREPARED_MARKER]  # no .tmp left behind

    def fail(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(fsutil, "publish", fail)
    with pytest.raises(OSError, match="disk full"):
        steps.write_marker(tmp_path, steps.PREPARE, details={"n": 2})
    monkeypatch.undo()
    marker = steps.read_marker(tmp_path, steps.PREPARE)
    assert marker is not None and marker.details == {"n": 1}  # the old marker is untouched

    steps.clear_marker(tmp_path, steps.PREPARE)
    assert steps.read_marker(tmp_path, steps.PREPARE) is None


def test_an_unreadable_marker_is_a_clear_error(tmp_path: Path) -> None:
    (tmp_path / TRAINED_MARKER).write_text("{broken", encoding="utf-8")
    with pytest.raises(StepOrderError, match="unreadable.*Run the train step again"):
        steps.read_marker(tmp_path, steps.TRAIN)
    (tmp_path / TRAINED_MARKER).write_text('{"step": "train"}', encoding="utf-8")
    with pytest.raises(StepOrderError, match="unreadable"):
        steps.read_marker(tmp_path, steps.TRAIN)

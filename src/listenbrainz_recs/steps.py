"""Step markers: how each pipeline step checks its input (BR6.1, BR6.3, BR6.4; NFR2.8).

Every step writes one small marker file as its last act. It holds the step name, a run id, the
run id of the marker the step read, and the time. A later step checks that the marker it needs
exists (missing input) and that the marker was made from the current run of the step before it
(stale input), and otherwise stops with a message naming the step to run.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from listenbrainz_recs import fsutil
from listenbrainz_recs.errors import StepOrderError
from listenbrainz_recs.paths import (
    CATALOGUE_MARKER,
    INDEX_MARKER,
    PREPARE_REPORT_FILE,
    PREPARED_MARKER,
    TRAINED_MARKER,
)

PREPARE, TRAIN, CATALOGUE, INDEX = "prepare", "train", "catalogue", "index"

MARKER_FILE = {
    PREPARE: PREPARED_MARKER,
    TRAIN: TRAINED_MARKER,
    CATALOGUE: CATALOGUE_MARKER,
    INDEX: INDEX_MARKER,
}
# What each step produces, in the words used in "missing" and "stale" messages.
INPUT_LABEL = {
    PREPARE: "prepared listen counts",
    TRAIN: "trained vectors",
    CATALOGUE: "artist catalogue",
    INDEX: "similarity index",
}
# The step whose marker each step reads (BR6.2). Prepare reads the dumps, so it has none.
INPUT_STEP = {TRAIN: PREPARE, CATALOGUE: PREPARE, INDEX: TRAIN}


@dataclass(frozen=True)
class Marker:
    """What a step wrote when it finished."""

    step: str
    run_id: str
    input_run_id: str
    completed_at: str
    details: dict[str, Any] = field(default_factory=dict)


def new_run_id() -> str:
    """A fresh run id for a step that is starting."""
    return uuid.uuid4().hex


def now_utc() -> str:
    """The current time as an ISO-8601 UTC string."""
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_command(step: str) -> str:
    """The command that runs `step`, quoted in messages."""
    return f"uv run listenbrainz-recs-{step}"


def write_marker(
    work_dir: Path,
    step: str,
    *,
    run_id: str | None = None,
    input_run_id: str = "",
    details: dict[str, Any] | None = None,
) -> Marker:
    """Write the marker for `step` atomically (BR6.1) and return it."""
    marker = Marker(
        step=step,
        run_id=run_id or new_run_id(),
        input_run_id=input_run_id,
        completed_at=now_utc(),
        details=dict(details or {}),
    )
    fsutil.write_json_atomic(
        work_dir / MARKER_FILE[step],
        {
            "step": marker.step,
            "run_id": marker.run_id,
            "input_run_id": marker.input_run_id,
            "completed_at": marker.completed_at,
            "details": marker.details,
        },
    )
    return marker


def clear_marker(work_dir: Path, step: str) -> None:
    """Remove a step's marker, so an interrupted run never looks finished."""
    fsutil.clear(work_dir / MARKER_FILE[step])


def read_marker(work_dir: Path, step: str) -> Marker | None:
    """Read a step's marker, or None when it has not been written."""
    path = work_dir / MARKER_FILE[step]
    if not path.is_file():
        return None
    try:
        raw = fsutil.read_json(path)
        details = raw.get("details", {})
        return Marker(
            step=str(raw["step"]),
            run_id=str(raw["run_id"]),
            input_run_id=str(raw.get("input_run_id", "")),
            completed_at=str(raw["completed_at"]),
            details=details if isinstance(details, dict) else {},
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise StepOrderError(
            f"The {step} marker {path} is unreadable ({exc}). "
            f"Run the {step} step again: {run_command(step)}"
        ) from exc


def require_marker(work_dir: Path, step: str) -> Marker:
    """Return the marker of `step`, or stop naming the missing input and the step to run (BR6.3)."""
    marker = read_marker(work_dir, step)
    if marker is None:
        raise StepOrderError(
            f"Missing the {INPUT_LABEL[step]} in {work_dir}; "
            f"run the {step} step first: {run_command(step)}"
        )
    return marker


def require_prepared(work_dir: Path) -> Marker:
    """The prepare marker, checked against the prepare report written with the data (BR6.3).

    The report carries the run id of the run that wrote the prepared data, so a marker that does
    not match it means the data and the marker come from different runs.
    """
    marker = require_marker(work_dir, PREPARE)
    report_path = work_dir / PREPARE_REPORT_FILE
    again = f"run the prepare step again: {run_command(PREPARE)}"
    try:
        report = fsutil.read_json(report_path)
    except (OSError, ValueError) as exc:
        raise StepOrderError(
            f"The prepare report {report_path} is missing or unreadable ({exc}); {again}"
        ) from exc
    if report.get("run_id") != marker.run_id:
        raise StepOrderError(
            f"The prepared data in {work_dir} does not belong to the current prepare run; {again}"
        )
    return marker


def require_current(work_dir: Path, marker: Marker) -> Marker:
    """Check `marker` was made from the current run of the step before it (BR6.4).

    Returns the marker of that earlier step. Raises `StepOrderError` when the earlier step was run
    again since, naming the step to run again.
    """
    earlier = require_marker(work_dir, INPUT_STEP[marker.step])
    if marker.input_run_id != earlier.run_id:
        raise StepOrderError(
            f"The {INPUT_LABEL[marker.step]} in {work_dir} was made from an older "
            f"{earlier.step} run than the current one; "
            f"run the {marker.step} step again: {run_command(marker.step)}"
        )
    return earlier

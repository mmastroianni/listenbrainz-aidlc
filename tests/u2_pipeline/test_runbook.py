"""The README's rebuild runbook names all four steps in order, then serve and speed (BR6.5)."""

from pathlib import Path

README = Path(__file__).resolve().parents[2] / "README.md"
SECTION = "## Rebuild from a new dump"
COMMANDS = [
    "uv run listenbrainz-recs-prepare",
    "uv run listenbrainz-recs-train",
    "uv run listenbrainz-recs-catalogue",
    "uv run listenbrainz-recs-index",
    "uv run listenbrainz-recs-serve",
    "uv run listenbrainz-recs-speed",
]


def _section() -> str:
    text = README.read_text(encoding="utf-8")
    assert SECTION in text
    body = text.split(SECTION, 1)[1]
    return body.split("\n## ", 1)[0]


def test_the_runbook_names_every_command_in_order() -> None:
    body = _section()
    positions = [body.find(command) for command in COMMANDS]
    assert all(p >= 0 for p in positions), positions
    assert positions == sorted(positions)


def test_the_runbook_names_the_settings_and_the_stop_messages() -> None:
    body = _section()
    for needle in (
        "LISTENBRAINZ_SPARK_MEMORY",
        "LISTENBRAINZ_PREP_MAX_LINES",
        "Missing the prepared listen counts",
        "older prepare run",
        "ran out of memory",
    ):
        assert needle in body

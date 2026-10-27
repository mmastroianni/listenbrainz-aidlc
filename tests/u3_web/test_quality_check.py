"""Quality-check sheet and verdict commands (FR8.1; BR5.1 to BR5.3; NFR2.23, NFR5.3).

Written before `quality.py` (Red). Built files are hand-made; no Spark is needed.
"""

from pathlib import Path

import pytest
from fixtures.sample_data import artist_mbid
from fixtures.web_models import GAP_ID

from listenbrainz_recs.quality import DEFAULT_SHEET, sheet_main, verdict_main

A1 = artist_mbid(1)


def _sheet(tmp_path: Path, verdicts: list[str]) -> Path:
    """A hand-written sheet with one section and verdict line per entry."""
    parts = ["# Quality check against the current app\n"]
    for n, verdict in enumerate(verdicts, start=1):
        parts.append(
            f"## {n}. Artist {n:02d} (`{artist_mbid(n)}`)\n\n1. Someone\n\nVerdict: {verdict}\n"
        )
    path = tmp_path / "sheet.md"
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def test_sheet_lists_the_top_20_with_genres_and_an_unset_verdict(
    paging_models: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "sheet.md"
    code = sheet_main(["--models-dir", str(paging_models), "--output", str(out), "Artist 01"])
    assert code == 0
    text = out.read_text(encoding="utf-8")
    assert "Artist 01" in text and A1 in text
    assert "Artist 21" in text and "Artist 22" not in text  # the top 20 neighbours only
    assert "jazz" in text  # genres shown
    assert text.count("Verdict: unset") == 1
    assert "wrote 1 artist" in capsys.readouterr().out


def test_sheet_accepts_an_id_and_several_artists(paging_models: Path, tmp_path: Path) -> None:
    out = tmp_path / "sheet.md"
    args = ["--models-dir", str(paging_models), "--output", str(out), A1, "artist 02"]
    assert sheet_main(args) == 0
    text = out.read_text(encoding="utf-8")
    assert text.count("Verdict: unset") == 2
    assert text.index("Artist 01") < text.index("Artist 02")


def test_more_than_five_artists_are_refused_and_nothing_is_written(
    paging_models: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "sheet.md"
    names = [f"Artist {n:02d}" for n in range(1, 7)]
    assert sheet_main(["--models-dir", str(paging_models), "--output", str(out), *names]) == 1
    assert "at most 5" in capsys.readouterr().err
    assert not out.exists()


def test_a_name_that_matches_nothing_stops_naming_it(
    paging_models: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "sheet.md"
    args = ["--models-dir", str(paging_models), "--output", str(out), "Artist 01", "Nobody Atall"]
    assert sheet_main(args) == 1
    assert "Nobody Atall" in capsys.readouterr().err
    assert not out.exists()


def test_an_artist_with_no_vector_in_the_index_stops_naming_it(
    gap_models: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "sheet.md"
    assert sheet_main(["--models-dir", str(gap_models), "--output", str(out), GAP_ID]) == 1
    assert "Lonely" in capsys.readouterr().err
    assert not out.exists()


def test_no_artist_given_is_a_clear_message(
    paging_models: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "sheet.md"
    assert sheet_main(["--models-dir", str(paging_models), "--output", str(out)]) == 1
    assert "name at least one artist" in capsys.readouterr().err.lower()


def test_sheet_and_printout_hold_artist_level_data_only(
    paging_models: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "sheet.md"
    sheet_main(["--models-dir", str(paging_models), "--output", str(out), "Artist 01"])
    text = out.read_text(encoding="utf-8").lower()
    assert "listener" not in text and "user" not in text and "cosine" not in text
    printed = capsys.readouterr().out
    assert "Artist 0" not in printed  # counts only: no names in the printout


def test_the_default_sheet_location_is_docs_quality_check() -> None:
    assert Path("docs/quality-check.md") == DEFAULT_SHEET


def test_verdict_passes_with_four_of_five_better_or_equal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _sheet(tmp_path, ["better-or-equal"] * 4 + ["worse"])
    assert verdict_main([str(path)]) == 0
    out = capsys.readouterr().out
    assert "5 of 5 verdicts marked" in out and "4 better-or-equal" in out and "pass" in out


def test_verdict_fails_with_three_of_five(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _sheet(tmp_path, ["better-or-equal"] * 3 + ["worse"] * 2)
    assert verdict_main([str(path)]) == 1
    out = capsys.readouterr().out
    assert "3 better-or-equal" in out and "fail" in out


def test_verdict_is_incomplete_when_any_is_unset(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _sheet(tmp_path, ["better-or-equal"] * 4 + ["unset"])
    assert verdict_main([str(path)]) == 1
    out = capsys.readouterr().out
    assert "4 of 5 verdicts marked" in out and "incomplete" in out


def test_verdict_names_the_line_it_cannot_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _sheet(tmp_path, ["better-or-equal", "meh", "worse"])
    assert verdict_main([str(path)]) == 1
    err = capsys.readouterr().err
    assert "line" in err and "meh" in err and "Traceback" not in err


def test_verdict_reports_a_missing_file_and_a_sheet_with_no_verdicts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert verdict_main([str(tmp_path / "nope.md")]) == 1
    assert "nope.md" in capsys.readouterr().err
    empty = tmp_path / "empty.md"
    empty.write_text("# nothing here\n", encoding="utf-8")
    assert verdict_main([str(empty)]) == 1
    assert "no verdict lines" in capsys.readouterr().err


def test_a_generated_sheet_reads_back_as_incomplete(
    paging_models: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "sheet.md"
    sheet_main(["--models-dir", str(paging_models), "--output", str(out), "Artist 01", "Artist 02"])
    capsys.readouterr()
    assert verdict_main([str(out)]) == 1
    assert "0 of 2 verdicts marked" in capsys.readouterr().out

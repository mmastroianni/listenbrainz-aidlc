"""Catalogue step: names, descriptions, genres, popularity numbering, atomic write (BR3, BR4.1)."""

import shutil
import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest
from fixtures.sample_data import (
    DISTINCT_LISTENER_NUMBERS,
    EXPECTED_GENRES,
    FIVE_LISTENER_ARTIST,
    FIVE_NAME_MAJORITY,
    KEPT_ARTISTS,
    MB_DESCRIPTIONS,
    MB_MISSING_ARTISTS,
    artist_mbid,
    artist_name,
)
from pyspark.sql import SparkSession

from listenbrainz_recs.catalogue import (
    CatalogueArtist,
    build_catalogue,
    popularity_order,
    write_catalogue_db,
)
from listenbrainz_recs.errors import ConfigError, DataError, StepOrderError
from listenbrainz_recs.paths import (
    ARTISTS_DB_FILE,
    CATALOGUE_MARKER,
    MANIFEST_FILE,
    PREPARED_MARKER,
)
from listenbrainz_recs.steps import CATALOGUE, PREPARE, read_marker


@pytest.fixture(scope="module")
def built(
    sample_dump_root: Path, prepared_work: Path, spark: SparkSession, tmp_path_factory
) -> Iterator[tuple[Path, Path]]:
    """(work dir, models dir) after the catalogue step on the fixture."""
    work = tmp_path_factory.mktemp("catalogue_work")
    shutil.copytree(prepared_work, work, dirs_exist_ok=True)
    models = tmp_path_factory.mktemp("catalogue_models")
    build_catalogue(sample_dump_root, work, models, spark)
    yield work, models


def _rows(models: Path, sql: str, args: tuple = ()) -> list[tuple]:
    with closing(sqlite3.connect(models / ARTISTS_DB_FILE)) as db:
        return db.execute(sql, args).fetchall()


def test_every_kept_artist_has_all_five_fields(built: tuple[Path, Path]) -> None:
    _, models = built
    rows = _rows(models, "SELECT mbid, name, description, listener_count, popularity FROM artist")
    assert len(rows) == KEPT_ARTISTS
    assert all(name and count >= 5 and number >= 1 for _, name, _, count, number in rows)
    by_id = {r[0]: r for r in rows}
    assert by_id[artist_mbid(0)][1] == artist_name(0)  # the most used listener spelling
    assert by_id[artist_mbid(FIVE_LISTENER_ARTIST)][1] == FIVE_NAME_MAJORITY
    assert by_id[artist_mbid(FIVE_LISTENER_ARTIST)][3] == 5


def test_description_comes_from_musicbrainz_and_blank_means_none(
    built: tuple[Path, Path],
) -> None:
    _, models = built
    found = {m: d for m, d in _rows(models, "SELECT mbid, description FROM artist")}
    for index, text in MB_DESCRIPTIONS.items():
        assert found[artist_mbid(index)] == text
    for index in (1, 2, 6):  # blank, null and spaces-only comments
        assert found[artist_mbid(index)] is None


def test_genres_are_filtered_by_the_list_and_ranked_by_votes_then_name(
    built: tuple[Path, Path],
) -> None:
    _, models = built
    for index, expected in EXPECTED_GENRES.items():
        genres = _rows(
            models,
            "SELECT genre FROM artist_genre WHERE mbid = ? ORDER BY rank",
            (artist_mbid(index),),
        )
        assert [g for (g,) in genres] == expected
    assert _rows(
        models,
        "SELECT votes FROM artist_genre WHERE mbid=? AND genre='electronic'",
        (artist_mbid(0),),
    ) == [(7,)]  # "electronic" and " Electronic " add up


def test_artists_missing_from_musicbrainz_are_kept_without_details(
    built: tuple[Path, Path],
) -> None:
    _, models = built
    for index in MB_MISSING_ARTISTS:
        mbid = artist_mbid(index)
        ((name, description),) = _rows(
            models, "SELECT name, description FROM artist WHERE mbid = ?", (mbid,)
        )
        assert name and description is None
        assert _rows(models, "SELECT 1 FROM artist_genre WHERE mbid = ?", (mbid,)) == []


def test_popularity_numbers_follow_listeners_then_name_then_id(built: tuple[Path, Path]) -> None:
    _, models = built
    rows = _rows(models, "SELECT listener_count, name, mbid, popularity FROM artist")
    ordered = sorted(rows, key=lambda r: (-r[0], r[1], r[2]))
    assert [r[3] for r in ordered] == list(range(1, len(rows) + 1))
    search_rowids = _rows(models, "SELECT rowid, mbid FROM artist_search ORDER BY rowid")
    assert [m for _, m in search_rowids] == [r[2] for r in ordered]


def test_marker_is_written_last_and_removes_the_old_manifest(
    sample_dump_root: Path, prepared_work: Path, spark: SparkSession, tmp_path: Path
) -> None:
    work, models = tmp_path / "w", tmp_path / "m"
    shutil.copytree(prepared_work, work)
    models.mkdir()
    (models / MANIFEST_FILE).write_text("{}", encoding="utf-8")
    summary = build_catalogue(sample_dump_root, work, models, spark)
    assert not (models / MANIFEST_FILE).exists()  # the index built earlier is now out of date
    marker = read_marker(work, CATALOGUE)
    prepared = read_marker(work, PREPARE)
    assert marker is not None and prepared is not None
    assert marker.input_run_id == prepared.run_id
    assert (work / CATALOGUE_MARKER).is_file()
    assert summary.artists == KEPT_ARTISTS
    # 24 group artists, minus 4 missing from MusicBrainz, minus 3 blank/null/space-only comments
    assert summary.described == 17
    assert "catalogue:" in summary.line() and str(KEPT_ARTISTS) in summary.line()


def test_no_listener_data_is_in_the_file(built: tuple[Path, Path]) -> None:
    _, models = built
    tables = {r[0] for r in _rows(models, "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"artist", "artist_genre", "artist_name_index", "artist_search"} <= tables
    for table in ("artist", "artist_genre", "artist_name_index"):
        columns = {r[1] for r in _rows(models, f"PRAGMA table_info({table})")}
        assert not any("user" in c or "listener_id" in c for c in columns)
    names = " ".join(r[0] for r in _rows(models, "SELECT name FROM artist"))
    assert not any(str(n) in names for n in DISTINCT_LISTENER_NUMBERS)


def test_failed_write_keeps_the_earlier_file_and_leaves_no_temp_file(tmp_path: Path) -> None:
    target = tmp_path / ARTISTS_DB_FILE
    good = [CatalogueArtist("a", "Alpha", None, 9, [])]
    write_catalogue_db(target, good)
    before = target.read_bytes()

    def broken() -> Iterator[CatalogueArtist]:
        yield CatalogueArtist("b", "Beta", None, 8, [])
        raise RuntimeError("source went away")

    with pytest.raises(RuntimeError, match="source went away"):
        write_catalogue_db(target, broken())
    assert target.read_bytes() == before
    assert not list(tmp_path.glob("*.tmp"))


def test_rows_out_of_popularity_order_and_empty_input_are_refused(tmp_path: Path) -> None:
    target = tmp_path / ARTISTS_DB_FILE
    wrong = [CatalogueArtist("a", "Alpha", None, 1, []), CatalogueArtist("b", "Beta", None, 9, [])]
    with pytest.raises(DataError, match="popularity order"):
        write_catalogue_db(target, wrong)
    with pytest.raises(DataError, match="No artists"):
        write_catalogue_db(target, [])
    assert not target.exists() and not list(tmp_path.glob("*.tmp"))


def test_popularity_order_breaks_ties_by_name_then_id() -> None:
    artists = [
        CatalogueArtist("z", "Same", None, 5, []),
        CatalogueArtist("y", "Same", None, 5, []),
        CatalogueArtist("x", "Zed", None, 5, []),
        CatalogueArtist("w", "Top", None, 50, []),
    ]
    assert [a.mbid for a in popularity_order(artists)] == ["w", "y", "z", "x"]
    assert CatalogueArtist("id-1", "  ", None, 1).display_name == "id-1"


def test_missing_musicbrainz_table_or_prepare_input_writes_nothing(
    sample_dump_root: Path, prepared_work: Path, spark: SparkSession, tmp_path: Path
) -> None:
    work, models = tmp_path / "w", tmp_path / "m"
    shutil.copytree(prepared_work, work)
    with pytest.raises(ConfigError, match="LISTENBRAINZ_DATA_ROOT"):
        build_catalogue(None, work, models, spark)
    broken_root = tmp_path / "root"
    shutil.copytree(sample_dump_root, broken_root)
    (broken_root / "data" / "musicbrainz" / "mbdump" / "genre").unlink()
    with pytest.raises(ConfigError, match="genre"):
        build_catalogue(broken_root, work, models, spark)
    assert not models.exists()
    (work / PREPARED_MARKER).unlink()
    with pytest.raises(StepOrderError, match="prepare"):
        build_catalogue(sample_dump_root, work, models, spark)
    assert not models.exists()

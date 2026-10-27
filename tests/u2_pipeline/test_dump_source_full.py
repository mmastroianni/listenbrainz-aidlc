"""DumpSource and the MusicBrainz source: locating tables, read-only access (BR1.1, BR1.2, BR3.3,
BR3.4; AC4.1.1, AC4.1.2; NFR3.7, NFR3.8)."""

import hashlib
import shutil
from pathlib import Path

import pytest
from fixtures.sample_data import (
    EXPECTED_GENRES,
    MB_DESCRIPTIONS,
    MB_MISSING_ARTISTS,
    artist_mbid,
    write_musicbrainz,
    write_sample,
)
from pyspark.sql import SparkSession

from listenbrainz_recs.dump_source import (
    check_dump_files,
    locate_musicbrainz_tables,
    read_lines,
)
from listenbrainz_recs.errors import ConfigError
from listenbrainz_recs.musicbrainz import read_descriptions, read_genres
from listenbrainz_recs.paths import LISTENING_DUMP_RELATIVE, MUSICBRAINZ_TABLES


def _snapshot(root: Path) -> dict[str, tuple[str, int]]:
    return {
        str(p.relative_to(root)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_musicbrainz_tables_are_found_in_the_real_folder_layout(sample_dump_root: Path) -> None:
    tables = locate_musicbrainz_tables(sample_dump_root)
    assert tables.folder == sample_dump_root / "data" / "musicbrainz" / "mbdump"
    assert [p.name for p in (tables.artist, tables.artist_tag, tables.tag, tables.genre)] == list(
        MUSICBRAINZ_TABLES
    )
    assert all(p.is_file() for p in (tables.artist, tables.artist_tag, tables.tag, tables.genre))


def test_the_mbdump_folder_may_sit_directly_under_the_data_location(tmp_path: Path) -> None:
    folder = write_musicbrainz(tmp_path / "src")
    (tmp_path / "root").mkdir()
    shutil.copytree(folder, tmp_path / "root" / "mbdump")
    assert locate_musicbrainz_tables(tmp_path / "root").folder == tmp_path / "root" / "mbdump"


def test_check_finds_the_listening_dump_and_the_tables(sample_dump_root: Path) -> None:
    files = check_dump_files(sample_dump_root)
    assert files.listening == sample_dump_root.joinpath(*LISTENING_DUMP_RELATIVE)
    assert files.musicbrainz.artist.name == "artist"


def test_a_missing_table_is_named_with_the_setting(tmp_path: Path) -> None:
    folder = write_musicbrainz(tmp_path)
    (folder / "tag").unlink()
    (folder / "genre").unlink()
    with pytest.raises(ConfigError) as caught:
        locate_musicbrainz_tables(tmp_path)
    message = str(caught.value)
    assert "tag, genre" in message and "LISTENBRAINZ_DATA_ROOT" in message
    assert "artist_tag" not in message.split("missing in")[1].split(":")[1]


def test_a_missing_setting_or_folder_stops_with_the_setting_named() -> None:
    with pytest.raises(ConfigError, match="LISTENBRAINZ_DATA_ROOT setting is not set"):
        check_dump_files(None)
    with pytest.raises(ConfigError, match="not a folder"):
        locate_musicbrainz_tables(Path("/definitely/not/here"))


def test_no_musicbrainz_folder_names_where_it_was_expected(tmp_path: Path) -> None:
    with pytest.raises(
        ConfigError, match=r"data/musicbrainz/mbdump.*artist, artist_tag, tag, genre"
    ):
        locate_musicbrainz_tables(tmp_path)


def test_a_failed_check_writes_nothing(tmp_path: Path) -> None:
    write_sample(tmp_path.joinpath(*LISTENING_DUMP_RELATIVE))  # the listening dump, no tables
    before = _snapshot(tmp_path)
    folders_before = sorted(p for p in tmp_path.rglob("*"))
    with pytest.raises(ConfigError):
        check_dump_files(tmp_path)
    assert _snapshot(tmp_path) == before
    assert sorted(tmp_path.rglob("*")) == folders_before


def test_reading_the_dump_files_leaves_them_unchanged(
    sample_dump_root: Path, spark: SparkSession
) -> None:
    before = _snapshot(sample_dump_root)
    files = check_dump_files(sample_dump_root)
    assert len(list(read_lines(files.listening, 10))) == 10
    kept = spark.createDataFrame([(artist_mbid(0),)], "artist_mbid string")
    read_descriptions(spark, files.musicbrainz, kept).collect()
    read_genres(spark, files.musicbrainz, kept).collect()
    assert _snapshot(sample_dump_root) == before


def test_descriptions_are_trimmed_and_blank_or_missing_ones_are_none(
    sample_dump_root: Path, spark: SparkSession
) -> None:
    tables = check_dump_files(sample_dump_root).musicbrainz
    wanted = [0, 1, 2, 3, 5, 6, 7, MB_MISSING_ARTISTS[0]]
    kept = spark.createDataFrame([(artist_mbid(n),) for n in wanted], "artist_mbid string")
    rows = {
        r["artist_mbid"]: r["description"] for r in read_descriptions(spark, tables, kept).collect()
    }
    assert len(rows) == len(wanted)
    for n in wanted:
        assert rows[artist_mbid(n)] == MB_DESCRIPTIONS.get(n)  # blank, null, spaces: None


def test_genres_are_recognised_positive_ranked_and_merged(
    sample_dump_root: Path, spark: SparkSession
) -> None:
    tables = check_dump_files(sample_dump_root).musicbrainz
    kept = spark.createDataFrame([(artist_mbid(n),) for n in range(24)], "artist_mbid string")
    rows = read_genres(spark, tables, kept).orderBy("artist_mbid", "rank").collect()
    found: dict[int, list[str]] = {}
    for row in rows:
        found.setdefault(int(row["artist_mbid"].rsplit("-", 1)[1]), []).append(row["genre"])
    # Artist 4 has only an unknown tag and non-positive votes, so it has no rows at all.
    assert found == {n: genres for n, genres in EXPECTED_GENRES.items() if genres}
    zero = next(
        r for r in rows if r["artist_mbid"] == artist_mbid(0) and r["genre"] == "electronic"
    )
    assert zero["votes"] == 7  # " Electronic " (2) and "electronic" (5) are one genre

"""Synthetic stand-ins for the dumps: the listening dump's JSON lines and the MusicBrainz tables.

Three groups of eight artists; listener `u` belongs to group `u % 3` and listens to most of that
group's artists, so ALS should place same-group artists close together. Extra lines hold the
awkward cases: malformed lines, entries with no artist id or a zero count, repeated entries for one
listener and artist, one artist with exactly 4 listeners (dropped) and one with exactly 5 (kept)
that is spelled two ways, and an artist with a single listener.

`write_musicbrainz` writes a small MusicBrainz folder in the real layout: an artist with no
description, one with a blank description, one with no genres, artists with ranked and filtered
tags, and kept artists that MusicBrainz has no record of.
"""

import json
from pathlib import Path

GROUPS = 3
ARTISTS_PER_GROUP = 8
LISTENERS = 300

LONELY_ARTIST = 99  # one listener (the edge listener): below the 5-listener cutoff
FOUR_LISTENER_ARTIST = 98  # exactly 4 listeners: dropped
FIVE_LISTENER_ARTIST = 97  # exactly 5 listeners: kept, spelled two ways
EDGE_LISTENER = 9001
FOUR_LISTENERS = (9101, 9102, 9103, 9104)
FIVE_LISTENERS = (9111, 9112, 9113, 9114, 9115)
FIVE_NAME_MAJORITY = "Five Spelled"  # used by 3 of the 5 listeners
FIVE_NAME_MINORITY = "Five Alt"  # used by the other 2
REPEAT_LISTENER = 9201  # lists artist 5 twice: 3 + 4 listens, to be summed to 7
REPEAT_ARTIST = 5

# Everything the awkward lines above add up to.
TOTAL_LINES = LISTENERS + 3 + 1 + len(FOUR_LISTENERS) + len(FIVE_LISTENERS) + 1
SKIPPED_RECORDS = 3  # not JSON, non-numeric listener number, data that is not a list
SKIPPED_ENTRIES = 2  # an empty artist id and a zero listen count
VALID_RECORDS = TOTAL_LINES - SKIPPED_RECORDS
KEPT_ARTISTS = GROUPS * ARTISTS_PER_GROUP + 1  # the 24 group artists and the 5-listener artist
PRIVATE_LISTENER_NAME = "private-listener-name"  # must never reach prepared data
# Listener numbers that are distinctive enough to search built files for.
DISTINCT_LISTENER_NUMBERS = (EDGE_LISTENER, *FOUR_LISTENERS, *FIVE_LISTENERS, REPEAT_LISTENER)


def artist_mbid(index: int) -> str:
    return f"00000000-0000-4000-8000-{index:012d}"


def artist_name(index: int) -> str:
    if index == 0:
        return "Bjørk Tëst Zero"
    return f"Test Artist {index:02d}"


def group_of(artist_index: int) -> int:
    return artist_index // ARTISTS_PER_GROUP


def _entry(index: int, count: int, name: str | None = None) -> dict[str, object]:
    return {
        "listen_count": count,
        "artist_name": artist_name(index) if name is None else name,
        "artist_mbid": artist_mbid(index),
    }


def listener_line(user_id: int) -> str:
    group = user_id % GROUPS
    entries = []
    for j in range(ARTISTS_PER_GROUP):
        if (user_id + j) % 5 == 0:
            continue
        entries.append(_entry(group * ARTISTS_PER_GROUP + j, 1 + (user_id * 7 + j * 13) % 50))
    if user_id % 10 == 0:
        other = ((group + 1) % GROUPS) * ARTISTS_PER_GROUP
        entries.append(_entry(other, 1))
    payload: dict[str, object] = {"user_id": user_id, "data": entries}
    if user_id % 50 == 0:
        payload["user_name"] = PRIVATE_LISTENER_NAME
    return json.dumps(payload)


def edge_lines() -> list[str]:
    odd_entries = [
        {"listen_count": 5, "artist_name": "No Id", "artist_mbid": ""},
        {"listen_count": 0, "artist_name": "Zero Count", "artist_mbid": artist_mbid(1)},
        _entry(LONELY_ARTIST, 3),
    ]
    lines = [
        "this is not json",
        json.dumps({"user_id": "not-a-number", "data": []}),
        json.dumps({"user_id": 9000, "data": "not a list"}),
        json.dumps({"user_id": EDGE_LISTENER, "data": odd_entries}),
    ]
    for number, user_id in enumerate(FOUR_LISTENERS):
        name = "Four B" if number % 2 else "Four A"
        lines.append(
            json.dumps({"user_id": user_id, "data": [_entry(FOUR_LISTENER_ARTIST, 2, name)]})
        )
    for number, user_id in enumerate(FIVE_LISTENERS):
        name = FIVE_NAME_MAJORITY if number < 3 else FIVE_NAME_MINORITY
        lines.append(
            json.dumps({"user_id": user_id, "data": [_entry(FIVE_LISTENER_ARTIST, 2, name)]})
        )
    repeats = [_entry(REPEAT_ARTIST, 3), _entry(REPEAT_ARTIST, 4)]
    lines.append(json.dumps({"user_id": REPEAT_LISTENER, "data": repeats}))
    return lines


def sample_lines() -> list[str]:
    lines = [listener_line(user_id) for user_id in range(1, LISTENERS + 1)]
    return lines + edge_lines()


def write_sample(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(sample_lines()) + "\n", encoding="utf-8")
    return path


# --- MusicBrainz tables -------------------------------------------------------------------------

NULL = "\\N"
MB_RELATIVE = ("data", "musicbrainz", "mbdump")
MB_NOT_KEPT_ARTIST = 500  # in MusicBrainz but not among the kept artists
MB_MISSING_ARTISTS = (20, 21, 22, 23, FIVE_LISTENER_ARTIST)  # kept, but not in MusicBrainz

# (artist index -> raw comment text exactly as it appears in the dump file)
MB_COMMENTS: dict[int, str] = {
    0: "Icelandic singer",
    1: "",  # blank: no description
    2: NULL,  # null: no description
    3: "Third artist",
    5: "jazz \\\\ blues duo",  # the dump escapes a backslash as two
    6: "   ",  # only spaces: no description
    7: "  padded  ",
}
MB_ARTIST_NAMES: dict[int, str] = {0: "Björk Test"}
MB_DESCRIPTIONS = {0: "Icelandic singer", 3: "Third artist", 5: "jazz \\ blues duo", 7: "padded"}

TAGS = {
    1: "electronic",
    2: "pop",
    3: "rock",
    4: "jazz",
    5: "blues",
    6: "soul",
    7: "folk",
    8: "iceland",
    9: " Electronic ",
    10: "seen live",
}
GENRES = ("electronic", "pop", "rock", "jazz", "blues", "soul", "Folk ")
# (artist index, tag id, votes)
ARTIST_TAGS = [
    (0, 1, 5),
    (0, 2, 3),
    (0, 8, 9),
    (0, 9, 2),
    (1, 3, 4),
    (2, 2, 1),
    (4, 10, 8),
    (4, 4, 0),
    (4, 7, -1),
    (5, 4, 2),
    (5, 5, 2),
    (5, 6, 3),
    (MB_NOT_KEPT_ARTIST, 3, 3),
]
# What the catalogue should hold as genres, best first.
EXPECTED_GENRES: dict[int, list[str]] = {
    0: ["electronic", "pop"],
    1: ["rock"],
    2: ["pop"],
    4: [],
    5: ["soul", "blues", "jazz"],
}


def _mb_artist_id(index: int) -> int:
    return 1000 + index


def _artist_row(index: int) -> str:
    name = MB_ARTIST_NAMES.get(index, artist_name(index))
    comment = MB_COMMENTS.get(index, f"Artist {index}")
    cells = [
        str(_mb_artist_id(index)),
        artist_mbid(index),
        name,
        name,
        *[NULL] * 9,
        comment,
        "0",
        "2024-01-01 00:00:00+00",
        "f",
        NULL,
        NULL,
    ]
    return "\t".join(cells)


def write_musicbrainz(root: Path) -> Path:
    """Write the four MusicBrainz tables under `root` in the real layout; return the folder."""
    folder = root.joinpath(*MB_RELATIVE)
    folder.mkdir(parents=True, exist_ok=True)
    kept = [n for n in range(GROUPS * ARTISTS_PER_GROUP) if n not in MB_MISSING_ARTISTS]
    artists = [_artist_row(n) for n in kept + [MB_NOT_KEPT_ARTIST]]
    (folder / "artist").write_text("\n".join(artists) + "\n", encoding="utf-8")
    artist_tags = [
        "\t".join([str(_mb_artist_id(a)), str(tag), str(votes), "2024-01-01 00:00:00+00"])
        for a, tag, votes in ARTIST_TAGS
    ]
    (folder / "artist_tag").write_text("\n".join(artist_tags) + "\n", encoding="utf-8")
    tags = ["\t".join([str(i), name, "1"]) for i, name in TAGS.items()]
    (folder / "tag").write_text("\n".join(tags) + "\n", encoding="utf-8")
    genres = [
        "\t".join(
            [str(i), f"00000000-0000-4000-9000-{i:012d}", name, "", "0", "2019-05-13 17:46:28+00"]
        )
        for i, name in enumerate(GENRES, start=1)
    ]
    (folder / "genre").write_text("\n".join(genres) + "\n", encoding="utf-8")
    return folder


def write_dump_folder(root: Path) -> Path:
    """The listening dump and the MusicBrainz tables under one data root; returns `root`."""
    from listenbrainz_recs.paths import LISTENING_DUMP_RELATIVE

    write_sample(root.joinpath(*LISTENING_DUMP_RELATIVE))
    write_musicbrainz(root)
    return root

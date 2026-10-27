"""Synthetic stand-in for the listening dump: the dump's JSON-lines shape, a few hundred lines.

Three groups of eight artists; listener `u` belongs to group `u % 3` and listens to most of that
group's artists, so ALS should place same-group artists close together. A few extra lines hold
the awkward cases (malformed JSON, entries with no artist id or a zero count, extra fields).
"""

import json
from pathlib import Path

GROUPS = 3
ARTISTS_PER_GROUP = 8
LISTENERS = 300

LONELY_ARTIST = 99  # listened to by exactly one listener (only in the edge lines)
EDGE_LISTENER = 9001


def artist_mbid(index: int) -> str:
    return f"00000000-0000-4000-8000-{index:012d}"


def artist_name(index: int) -> str:
    if index == 0:
        return "Bjørk Tëst Zero"
    return f"Test Artist {index:02d}"


def group_of(artist_index: int) -> int:
    return artist_index // ARTISTS_PER_GROUP


def _entry(index: int, count: int) -> dict[str, object]:
    return {
        "listen_count": count,
        "artist_name": artist_name(index),
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
        payload["user_name"] = "private-listener-name"  # must never reach prepared data
    return json.dumps(payload)


def edge_lines() -> list[str]:
    odd_entries = [
        {"listen_count": 5, "artist_name": "No Id", "artist_mbid": ""},
        {"listen_count": 0, "artist_name": "Zero Count", "artist_mbid": artist_mbid(1)},
        _entry(LONELY_ARTIST, 3),
    ]
    return [
        "this is not json",
        json.dumps({"user_id": EDGE_LISTENER, "data": odd_entries}),
        json.dumps({"user_id": "not-a-number", "data": []}),
    ]


def sample_lines() -> list[str]:
    lines = [listener_line(user_id) for user_id in range(1, LISTENERS + 1)]
    return lines + edge_lines()


def write_sample(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(sample_lines()) + "\n", encoding="utf-8")
    return path

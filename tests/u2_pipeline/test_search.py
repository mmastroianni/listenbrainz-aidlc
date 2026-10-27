"""Name search: four tiers, popularity order, 10 results, safe typed text (BR4.1 to BR4.7).

Written before the search code (Red). The catalogue is built by hand, so no Spark is needed.
"""

from collections.abc import Iterator

import numpy as np
import pytest

from listenbrainz_recs.artists import ArtistCatalog, ArtistSummary
from listenbrainz_recs.catalogue import CatalogueArtist, popularity_order, write_catalogue_db
from listenbrainz_recs.index import build_index_files
from listenbrainz_recs.paths import ARTISTS_DB_FILE
from listenbrainz_recs.store import ModelStore, load_store

HENRY = "id-henry"
BJORK = "id-bjork"
ACDC = "id-acdc"
NO_DESCRIPTION = "id-plain"


def _artists() -> list[CatalogueArtist]:
    artists = [
        CatalogueArtist(
            HENRY,
            "Henry Threadgill",
            "American jazz composer",
            100,
            [("jazz", 9), ("free jazz", 3)],
        ),
        CatalogueArtist(BJORK, "Björk", "Icelandic singer", 500, [("art pop", 7)]),
        CatalogueArtist(ACDC, "AC/DC", "Australian rock band", 800, [("hard rock", 5)]),
        CatalogueArtist(NO_DESCRIPTION, "Plain Artist", None, 7, []),
        # one tier each for the text "rock"
        CatalogueArtist("id-rock", "Rock", None, 10, []),
        CatalogueArtist("id-rock-steady", "Rock Steady", None, 900, []),
        CatalogueArtist("id-rocket", "Rocket Man", None, 700, []),
        CatalogueArtist("id-big-rock", "Big Rock Band", None, 5000, []),
        # same name, different artists; equal listeners fall back to name, then id
        CatalogueArtist("id-delta-2", "Delta Wave", "the second one", 50, []),
        CatalogueArtist("id-delta-1", "Delta Wave", "the first one", 50, []),
        CatalogueArtist("id-delta-z", "Delta Zone", None, 50, []),
        # fifteen artists for the 10-result cap
        *(
            CatalogueArtist(f"id-common-{n:02d}", f"Common Name {n:02d}", None, 20 + n, [])
            for n in range(1, 16)
        ),
    ]
    return popularity_order(artists)


@pytest.fixture(scope="module")
def store(tmp_path_factory: pytest.TempPathFactory) -> Iterator[ModelStore]:
    models = tmp_path_factory.mktemp("search_models")
    artists = _artists()
    write_catalogue_db(models / ARTISTS_DB_FILE, artists)
    vectors = np.tile(np.array([[1.0, 0.5]], dtype=np.float32), (len(artists), 1))
    build_index_files(models, [a.mbid for a in artists], vectors, "tiny-dump")
    loaded = load_store(models)
    yield loaded
    loaded.close()


@pytest.fixture
def catalog(store: ModelStore) -> ArtistCatalog:
    return ArtistCatalog(store)


def _ids(found: list[ArtistSummary]) -> list[str]:
    return [a.mbid for a in found]


def test_typed_words_find_a_name_by_word_starts(catalog: ArtistCatalog) -> None:
    assert _ids(catalog.suggest("henry thr")) == [HENRY]  # AC1.1.1
    assert _ids(catalog.suggest("threadgill henry")) == [HENRY]  # any order, each word a start
    assert _ids(catalog.suggest("HENRY")) == [HENRY]


def test_only_word_starts_match_not_text_inside_a_word(catalog: ArtistCatalog) -> None:
    assert catalog.suggest("ock") == []  # "ock" is inside "Rock", not the start of a word
    assert catalog.suggest("readgill") == []
    assert _ids(catalog.suggest("big band")) == ["id-big-rock"]  # words need not be adjacent


def test_case_and_accents_are_ignored_both_ways(catalog: ArtistCatalog) -> None:
    assert _ids(catalog.suggest("bjork")) == [BJORK]  # AC1.1.2
    assert _ids(catalog.suggest("BJÖRK")) == [BJORK]
    assert _ids(catalog.suggest("  bjo ")) == [BJORK]


def test_punctuation_counts_as_a_space(catalog: ArtistCatalog) -> None:
    for text in ("ac dc", "AC/DC", "ac-dc", "ac...dc"):
        assert _ids(catalog.suggest(text)) == [ACDC], text


def test_empty_whitespace_and_no_match_give_an_empty_list(catalog: ArtistCatalog) -> None:
    for text in ("", "   ", "\t\n", "!!!", "zzzzqx", "henry zzz"):
        assert catalog.suggest(text) == [], text


def test_exact_beats_starts_with_beats_word_match_then_listeners(catalog: ArtistCatalog) -> None:
    found = catalog.suggest("rock")
    assert _ids(found) == [
        "id-rock",  # tier 0: the name is exactly "rock", fewest listeners but closest
        "id-rock-steady",  # tier 1: starts with "rock", 900 listeners
        "id-rocket",  # tier 1: starts with "rock", 700 listeners
        "id-big-rock",  # tier 2: "rock" starts a later word, most listeners but furthest
    ]


def test_equal_listeners_fall_back_to_name_then_id_and_the_order_is_stable(
    catalog: ArtistCatalog,
) -> None:
    first = _ids(catalog.suggest("delta"))
    assert first == ["id-delta-1", "id-delta-2", "id-delta-z"]
    assert _ids(catalog.suggest("delta")) == first


def test_same_name_artists_both_appear_with_their_own_descriptions(
    catalog: ArtistCatalog,
) -> None:
    found = catalog.suggest("delta wave")
    assert [(a.mbid, a.description) for a in found] == [
        ("id-delta-1", "the first one"),
        ("id-delta-2", "the second one"),
    ]


def test_at_most_ten_results_and_a_larger_limit_is_capped(catalog: ArtistCatalog) -> None:
    assert len(catalog.suggest("common")) == 10
    assert len(catalog.suggest("common", limit=50)) == 10
    assert len(catalog.suggest("common", limit=3)) == 3
    best_first = catalog.suggest("common")
    assert [a.listener_count for a in best_first] == sorted(
        (a.listener_count for a in best_first), reverse=True
    )


def test_a_single_letter_still_returns_ten(catalog: ArtistCatalog) -> None:
    assert len(catalog.suggest("c")) == 10


def test_suggestion_carries_name_genres_in_rank_order_and_description(
    catalog: ArtistCatalog,
) -> None:
    (henry,) = catalog.suggest("henry thr")
    assert henry == ArtistSummary(
        mbid=HENRY,
        name="Henry Threadgill",
        description="American jazz composer",
        listener_count=100,
        genres=["jazz", "free jazz"],
    )


def test_no_description_stays_none_and_no_genres_is_an_empty_list(catalog: ArtistCatalog) -> None:
    (plain,) = catalog.suggest("plain artist")
    assert plain.description is None
    assert plain.genres == []


@pytest.mark.parametrize(
    "text",
    [
        '"',
        "%",
        "*",
        "' OR 1=1 --",
        '" OR "a"="a',
        "NEAR(a b)",
        "a AND b OR c",
        "col:value",
        "x" * 200,
        "\u0000",
        "💥 ✨",
    ],
)
def test_odd_typed_text_never_raises_and_returns_a_list(catalog: ArtistCatalog, text: str) -> None:
    result = catalog.suggest(text)
    assert isinstance(result, list)
    assert len(result) <= 10


def test_percent_and_star_are_not_wildcards(catalog: ArtistCatalog) -> None:
    assert catalog.suggest("%") == []
    assert catalog.suggest("*") == []
    assert catalog.suggest("r%ck") == []  # "r" and "ck" are two words; no name has a "ck" word
    assert catalog.suggest("ro*") == catalog.suggest("ro")
    assert _ids(catalog.suggest("rock'")) == _ids(catalog.suggest("rock"))

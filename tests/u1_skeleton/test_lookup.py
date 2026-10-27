"""SimilarityIndex and ArtistCatalog (BR3.1, BR3.2; AC2.1.1). Written before the code (Red)."""

from pathlib import Path

import pytest
from fixtures.sample_data import artist_mbid

from listenbrainz_recs.artists import ArtistCatalog, ArtistSummary
from listenbrainz_recs.errors import UnknownArtist
from listenbrainz_recs.similarity import SimilarityIndex
from listenbrainz_recs.store import load_store

A1, A2, A3, A4, A5 = (artist_mbid(n) for n in range(1, 6))


@pytest.fixture
def similarity(tiny_models: Path) -> SimilarityIndex:
    return SimilarityIndex(load_store(tiny_models))


@pytest.fixture
def catalog(tiny_models: Path) -> ArtistCatalog:
    return ArtistCatalog(load_store(tiny_models))


def test_neighbours_are_ranked_by_cosine_and_exclude_the_artist(
    similarity: SimilarityIndex,
) -> None:
    page = similarity.neighbours(A1, offset=0, limit=10)
    assert [n.mbid for n in page.items] == [A2, A3, A4, A5]
    cosines = [n.cosine for n in page.items]
    assert cosines == sorted(cosines, reverse=True)
    assert A1 not in {n.mbid for n in page.items}
    assert page.has_more is False


def test_cosine_scores_are_true_cosine_similarity(similarity: SimilarityIndex) -> None:
    by_id = {n.mbid: n.cosine for n in similarity.neighbours(A1, 0, 10).items}
    assert by_id[A2] == pytest.approx(0.99388, abs=1e-4)
    assert by_id[A3] == pytest.approx(0.70711, abs=1e-4)
    assert by_id[A4] == pytest.approx(0.0, abs=1e-5)
    assert by_id[A5] == pytest.approx(-1.0, abs=1e-5)
    assert all(isinstance(c, float) for c in by_id.values())


def test_paging_with_offset_and_limit(similarity: SimilarityIndex) -> None:
    first = similarity.neighbours(A1, offset=0, limit=2)
    assert [n.mbid for n in first.items] == [A2, A3]
    assert first.has_more is True
    second = similarity.neighbours(A1, offset=2, limit=2)
    assert [n.mbid for n in second.items] == [A4, A5]
    assert second.has_more is False  # exactly fills the last page
    beyond = similarity.neighbours(A1, offset=10, limit=5)
    assert beyond.items == [] and beyond.has_more is False


def test_unknown_artist_raises(similarity: SimilarityIndex) -> None:
    with pytest.raises(UnknownArtist) as caught:
        similarity.neighbours(artist_mbid(404), offset=0, limit=5)
    assert caught.value.mbid == artist_mbid(404)


def test_artist_without_neighbours_returns_empty_not_an_error(
    single_artist_models: Path,
) -> None:
    page = SimilarityIndex(load_store(single_artist_models)).neighbours(A1, 0, 5)
    assert page.items == [] and page.has_more is False


@pytest.mark.parametrize(("offset", "limit"), [(-1, 10), (0, 0), (0, 101)])
def test_paging_arguments_outside_the_contract_are_rejected(
    similarity: SimilarityIndex, offset: int, limit: int
) -> None:
    with pytest.raises(ValueError, match="offset|limit"):
        similarity.neighbours(A1, offset=offset, limit=limit)


def test_get_many_maps_known_ids_and_omits_unknown_ones(catalog: ArtistCatalog) -> None:
    found = catalog.get_many([A3, artist_mbid(404), A1])
    assert set(found) == {A1, A3}
    assert found[A3] == ArtistSummary(
        mbid=A3, name="Gamma", description=None, listener_count=30, genres=[]
    )
    assert catalog.get_many([]) == {}


def test_get_returns_a_summary_or_none(catalog: ArtistCatalog) -> None:
    summary = catalog.get(A2)
    assert summary is not None and summary.name == "Béta"
    assert catalog.get(artist_mbid(404)) is None


def test_suggest_ignores_case_and_accents_and_blank_text(catalog: ArtistCatalog) -> None:
    assert [s.mbid for s in catalog.suggest("BETA")] == [A2]
    assert [s.mbid for s in catalog.suggest("  bÉt ")] == [A2]
    assert catalog.suggest("   ") == []
    assert catalog.suggest("zzz") == []


def test_suggest_orders_exact_then_prefix_then_listeners_and_caps_the_limit(
    catalog: ArtistCatalog,
) -> None:
    # Changed by u2-pipeline (BR4.3): names match by word start, so "a" now finds only Alpha;
    # Béta, Gamma and Delta contain an "a" but no word of theirs starts with it.
    assert [s.mbid for s in catalog.suggest("a")] == [A1]
    assert catalog.suggest("lph") == []  # inside a word, no longer a match
    assert [s.mbid for s in catalog.suggest("al")] == [A1]
    assert len(catalog.suggest("al", limit=1)) == 1
    assert len(catalog.suggest("al", limit=50)) <= 10  # the 10-result cap is tested in u2

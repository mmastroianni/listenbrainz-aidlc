"""SimilarityIndex: ranked cosine neighbours (contract C1; BR3.1, BR3.2)."""

from dataclasses import dataclass

import numpy as np

from listenbrainz_recs.errors import UnknownArtist
from listenbrainz_recs.store import ModelStore

MAX_LIMIT = 100


@dataclass(frozen=True)
class Neighbour:
    mbid: str
    cosine: float


@dataclass(frozen=True)
class NeighbourPage:
    items: list[Neighbour]
    has_more: bool


class SimilarityIndex:
    """Exact inner-product search over unit-length vectors, so scores are cosine similarity."""

    def __init__(self, store: ModelStore) -> None:
        self._store = store

    def neighbours(self, mbid: str, offset: int = 0, limit: int = 20) -> NeighbourPage:
        """A page of neighbours, best first, never including `mbid` itself.

        Raises `UnknownArtist` when `mbid` is not in the index, and `ValueError` for paging
        arguments outside the contract (offset >= 0, 1 <= limit <= 100).
        """
        if offset < 0:
            raise ValueError("offset must be 0 or more")
        if not 1 <= limit <= MAX_LIMIT:
            raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")
        row = self._store.row_of.get(mbid)
        if row is None:
            raise UnknownArtist(mbid)

        index = self._store.index
        wanted = offset + limit
        # +1 for the artist itself, +1 to learn whether anything lies beyond this page.
        k = min(index.ntotal, wanted + 2)
        query = index.reconstruct(row).reshape(1, -1)
        scores, labels = index.search(np.ascontiguousarray(query, dtype=np.float32), k)

        ranked = [
            Neighbour(self._store.ids[int(label)], float(score))
            for score, label in zip(scores[0], labels[0], strict=True)
            if int(label) >= 0 and int(label) != row
        ]
        return NeighbourPage(items=ranked[offset:wanted], has_more=len(ranked) > wanted)

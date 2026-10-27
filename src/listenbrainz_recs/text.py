"""Name normalisation for case- and accent-insensitive search (FR4.3)."""

import unicodedata


def normalize_name(text: str) -> str:
    """Lower-case, accent-free, single-spaced form of `text`."""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(stripped.casefold().split())

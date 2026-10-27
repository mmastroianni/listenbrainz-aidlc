"""Name normalisation for case- and accent-insensitive search (BR4.1, FR4.3).

Typed text and artist names are reduced to the same form before they are compared: case folded,
accents decomposed and dropped, every character that is not a letter or digit turned into a space,
spaces collapsed. "Björk" and "bjork" both become "bjork"; "AC/DC" becomes "ac dc". The result holds
only letters, digits and single spaces, so it is safe to quote in a search query (NFR8.5).
"""

import unicodedata


def normalize_name(text: str) -> str:
    """The search form of `text`: lower-case, accent-free, punctuation as single spaces."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    kept: list[str] = []
    for char in decomposed:
        kind = unicodedata.category(char)[0]
        if kind in ("L", "N"):
            kept.append(char)
        elif kind != "M":  # accents and other marks vanish; everything else separates words
            kept.append(" ")
    return " ".join("".join(kept).split())

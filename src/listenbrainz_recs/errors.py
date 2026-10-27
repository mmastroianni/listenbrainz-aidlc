"""Error types. Commands print their message and exit non-zero; the web layer maps them."""


class RecsError(Exception):
    """Base class for errors this package raises on purpose, with a message fit to show."""


class ConfigError(RecsError):
    """A setting is missing or points at something that does not exist (BR1.1)."""


class StepOrderError(RecsError):
    """A pipeline step ran before the step that feeds it (NFR2.3)."""


class DataError(RecsError):
    """Prepared or built data is unusable (empty, malformed, inconsistent)."""


class StartupError(RecsError):
    """The built files are missing or incompatible, so the app refuses to start (BR4.2)."""


class UnknownArtist(RecsError):  # noqa: N818 - name fixed by contract C1
    """The artist id is not in the similarity index (BR3.2, contract C1)."""

    def __init__(self, mbid: str) -> None:
        super().__init__(f"Unknown artist: {mbid}")
        self.mbid = mbid

"""Named random streams built from a master seed (SPECS §10.2)."""

from __future__ import annotations

import random

STREAM_NAMES = frozenset({"terrain", "items", "fx"})


def make_stream(master_seed: int, name: str) -> random.Random:
    """Build the named stream seeded as ``random.Random(f"{master}:{name}")``."""
    if name not in STREAM_NAMES:
        message = f"unknown RNG stream {name!r}, expected one of {sorted(STREAM_NAMES)}"
        raise ValueError(message)
    # Gameplay randomness only, never used for security-sensitive choices.
    return random.Random(f"{master_seed}:{name}")  # noqa: S311


class RngStreams:
    """Registry of named streams derived from one master seed."""

    __slots__ = ("_master_seed", "_streams")

    def __init__(self, master_seed: int) -> None:
        """Create an empty registry for the master seed."""
        self._master_seed = master_seed
        self._streams: dict[str, random.Random] = {}

    @property
    def master_seed(self) -> int:
        """Return the master seed every stream derives from."""
        return self._master_seed

    def stream(self, name: str) -> random.Random:
        """Return the named stream, creating it once on first use."""
        if name not in self._streams:
            self._streams[name] = make_stream(self._master_seed, name)
        return self._streams[name]

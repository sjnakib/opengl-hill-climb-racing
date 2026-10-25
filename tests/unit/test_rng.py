"""Unit tests for the named RNG streams (SPECS §10.2)."""

from __future__ import annotations

import random

import pytest

from hillclimb.engine.rng import STREAM_NAMES, RngStreams, make_stream


def test_make_stream_matches_the_exact_seed_string() -> None:
    expected = random.Random("1234:terrain")  # noqa: S311 - matching the contract
    actual = make_stream(1234, "terrain")
    assert [actual.random() for _ in range(5)] == [expected.random() for _ in range(5)]


def test_unknown_stream_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown RNG stream"):
        make_stream(1, "physics")


@pytest.mark.parametrize("name", sorted(STREAM_NAMES))
def test_every_contract_stream_can_be_built(name: str) -> None:
    assert make_stream(9, name).random() != make_stream(10, name).random()


def test_streams_are_cached_per_name() -> None:
    streams = RngStreams(77)
    assert streams.stream("items") is streams.stream("items")


def test_streams_are_independent_objects() -> None:
    streams = RngStreams(77)
    assert streams.stream("terrain") is not streams.stream("items")
    assert streams.stream("items") is not streams.stream("fx")


def test_same_master_seed_reproduces_every_stream() -> None:
    first = RngStreams(2026)
    second = RngStreams(2026)
    for name in sorted(STREAM_NAMES):
        assert [first.stream(name).random() for _ in range(3)] == [
            second.stream(name).random() for _ in range(3)
        ]


def test_master_seed_is_exposed() -> None:
    assert RngStreams(-5).master_seed == -5

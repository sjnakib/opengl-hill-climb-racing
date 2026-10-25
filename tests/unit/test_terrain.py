"""Unit tests for chunked terrain (SPECS §10.3)."""

from __future__ import annotations

import math
from itertools import pairwise

import pytest

from hillclimb.engine.terrain import (
    DIFFICULTY_RAMP_PX,
    MAX_DIFFICULTY_LEVEL,
    MIN_DIFFICULTY_LEVEL,
    REACHABILITY_SPAN_PX,
    SLOPE_LIMIT_DEGREES,
    Terrain,
    difficulty_at,
)


def test_heights_reproduce_for_the_same_seed() -> None:
    first = Terrain(2026)
    second = Terrain(2026)
    positions = [0.0, 1.0, 8.0, 511.9, 512.0, 4096.5, 10_000.0]
    assert [first.height_at(x) for x in positions] == [second.height_at(x) for x in positions]


def test_different_seeds_build_different_terrain() -> None:
    first = Terrain(1)
    second = Terrain(2)
    positions = [float(x) for x in range(0, 4096, 128)]
    assert [first.height_at(x) for x in positions] != [second.height_at(x) for x in positions]


@pytest.mark.parametrize("bad", [-1.0, math.nan, math.inf, -math.inf])
def test_height_and_slope_reject_bad_positions(bad: float) -> None:
    terrain = Terrain(3)
    with pytest.raises(ValueError, match="finite, non-negative"):
        terrain.height_at(bad)
    with pytest.raises(ValueError, match="finite, non-negative"):
        terrain.slope_at(bad)


def test_chunk_boundaries_are_continuous() -> None:
    terrain = Terrain(9)
    for boundary in (512.0, 1024.0, 1536.0):
        left = terrain.height_at(boundary - 1e-9)
        exact = terrain.height_at(boundary)
        right = terrain.height_at(boundary + 1e-9)
        assert left == pytest.approx(exact, abs=1e-6)
        assert right == pytest.approx(exact, abs=1e-6)


def test_cache_recycles_old_chunks() -> None:
    terrain = Terrain(11, cache_size=2)
    for chunk_index in range(6):
        terrain.height_at(chunk_index * 512.0 + 17.0)
    assert terrain.cached_chunk_count == 2


def test_cache_size_must_be_positive() -> None:
    with pytest.raises(ValueError, match="cache_size"):
        Terrain(1, cache_size=0)


def test_difficulty_grows_with_distance_and_caps() -> None:
    distances = [0.0, 5_000.0, 10_000.0, 20_000.0, 30_000.0, 45_000.0, 200_000.0]
    profiles = [difficulty_at(distance) for distance in distances]
    assert profiles[0].level == pytest.approx(MIN_DIFFICULTY_LEVEL)
    assert profiles[-1].level == pytest.approx(MAX_DIFFICULTY_LEVEL)
    assert difficulty_at(DIFFICULTY_RAMP_PX) == difficulty_at(DIFFICULTY_RAMP_PX * 10)
    for previous, current in pairwise(profiles):
        assert current.level >= previous.level
        assert current.amplitude_px >= previous.amplitude_px
        assert current.frequency_per_kpx >= previous.frequency_per_kpx
        assert current.roughness >= previous.roughness
    assert profiles[0].roughness == pytest.approx(0.0)
    assert profiles[-1].amplitude_px > profiles[0].amplitude_px


@pytest.mark.parametrize("bad", [-0.1, math.nan, math.inf])
def test_difficulty_rejects_bad_distances(bad: float) -> None:
    with pytest.raises(ValueError, match="finite, non-negative"):
        difficulty_at(bad)


def test_slope_stays_under_contract_on_a_dense_scan() -> None:
    for seed in (1, 2, 3):
        terrain = Terrain(seed)
        for step in range(0, 120_000, 8):
            assert abs(terrain.slope_at(float(step))) <= SLOPE_LIMIT_DEGREES


def test_reachability_span_holds_on_a_dense_scan() -> None:
    rise_limit = math.tan(math.radians(SLOPE_LIMIT_DEGREES)) * REACHABILITY_SPAN_PX
    for seed in (4, 5):
        terrain = Terrain(seed)
        for step in range(10_000, 60_000, 37):
            start = terrain.height_at(float(step))
            end = terrain.height_at(float(step) + REACHABILITY_SPAN_PX)
            assert end - start <= rise_limit

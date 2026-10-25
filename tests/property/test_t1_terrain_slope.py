"""T1: terrain slope stays at or under 60 degrees at difficulty 3 and above."""

from __future__ import annotations

import math

from hypothesis import given, settings
from hypothesis import strategies as st

from hillclimb.engine.terrain import (
    DIFFICULTY_RAMP_PX,
    MAX_DIFFICULTY_LEVEL,
    MIN_DIFFICULTY_LEVEL,
    SLOPE_LIMIT_DEGREES,
    Terrain,
    difficulty_at,
)

LEVEL_THREE_PX = (
    DIFFICULTY_RAMP_PX
    * (3.0 - MIN_DIFFICULTY_LEVEL)
    / (MAX_DIFFICULTY_LEVEL - MIN_DIFFICULTY_LEVEL)
)


@settings(max_examples=50)
@given(
    seed=st.integers(min_value=0, max_value=2**31 - 1),
    x=st.floats(
        min_value=LEVEL_THREE_PX,
        max_value=500_000.0,
        allow_nan=False,
        allow_infinity=False,
    ),
)
def test_t1_terrain_slope_bound(seed: int, x: float) -> None:
    terrain = Terrain(seed)
    assert difficulty_at(x).level >= 3.0
    degrees = math.degrees(math.atan(terrain.grade_at(x)))
    assert abs(degrees) <= SLOPE_LIMIT_DEGREES

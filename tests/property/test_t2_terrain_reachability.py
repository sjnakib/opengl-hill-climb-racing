"""T2: terrain stays reachable, with no step-up beyond the contact limit."""

from __future__ import annotations

import math

from hypothesis import given, settings
from hypothesis import strategies as st

from hillclimb.engine.terrain import (
    DIFFICULTY_RAMP_PX,
    MAX_DIFFICULTY_LEVEL,
    MIN_DIFFICULTY_LEVEL,
    REACHABILITY_SPAN_PX,
    SLOPE_LIMIT_DEGREES,
    Terrain,
)

LEVEL_THREE_PX = (
    DIFFICULTY_RAMP_PX
    * (3.0 - MIN_DIFFICULTY_LEVEL)
    / (MAX_DIFFICULTY_LEVEL - MIN_DIFFICULTY_LEVEL)
)
RISE_LIMIT_PX = math.tan(math.radians(SLOPE_LIMIT_DEGREES)) * REACHABILITY_SPAN_PX


@settings(max_examples=50)
@given(
    seed=st.integers(min_value=0, max_value=2**31 - 1),
    x=st.floats(
        min_value=LEVEL_THREE_PX,
        max_value=500_000.0 - REACHABILITY_SPAN_PX,
        allow_nan=False,
        allow_infinity=False,
    ),
)
def test_t2_terrain_reachability(seed: int, x: float) -> None:
    terrain = Terrain(seed)
    rise = terrain.height_at(x + REACHABILITY_SPAN_PX) - terrain.height_at(x)
    assert rise <= RISE_LIMIT_PX

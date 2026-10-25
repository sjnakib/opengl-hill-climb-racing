"""T3: fuel stays inside the closed [0, 100] range."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from hillclimb.engine.fuel import MAX_FUEL_LITRES
from hillclimb.engine.simulation import Simulation


@settings(max_examples=20, deadline=None)
@given(
    seed=st.integers(min_value=0, max_value=2**31 - 1),
    pattern=st.integers(min_value=0, max_value=3),
)
def test_t3_fuel_stays_in_range(seed: int, pattern: int) -> None:
    simulation = Simulation(seed)
    assert 0.0 <= simulation.fuel.fuel <= MAX_FUEL_LITRES
    for tick in range(600):
        phase = (tick // 60) % 4
        throttle = 1.0 if phase == pattern else 0.0
        brake = 1.0 if phase == (pattern + 2) % 4 else 0.0
        simulation.step(throttle, brake)
        assert 0.0 <= simulation.fuel.fuel <= MAX_FUEL_LITRES

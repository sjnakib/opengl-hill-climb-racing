"""S1: score never decreases during a replay and replays match."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from hillclimb.engine.simulation import InputSegment, ScriptedInput, Simulation


def plan_for(seed: int) -> ScriptedInput:
    end_drive = 240 + seed % 240
    return ScriptedInput(
        (
            InputSegment(0, end_drive, 1.0, 0.0),
            InputSegment(end_drive, 600, 0.0, 0.5),
        )
    )


@settings(max_examples=15, deadline=None)
@given(seed=st.integers(min_value=0, max_value=2**31 - 1))
def test_s1_score_is_monotonic_under_replay(seed: int) -> None:
    plan = plan_for(seed)
    simulation = Simulation(seed)
    scores = [simulation.score]
    for segment in plan.segments:
        for _ in range(segment.start_tick, segment.end_tick):
            simulation.step(segment.throttle, segment.brake)
            scores.append(simulation.score)
    assert scores == sorted(scores)
    replay = Simulation(seed).run(600, plan)
    assert replay.score == simulation.score
    assert replay.distance_px == simulation.distance_px

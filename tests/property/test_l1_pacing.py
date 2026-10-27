"""L1: frame grouping preserves the fixed-timestep tick sequence."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from hypothesis import given, settings
from hypothesis import strategies as st

from hillclimb.app.main import MAX_CATCHUP_TICKS, MAX_FRAME_TIME_S, plan_frame_ticks
from hillclimb.engine.simulation import InputSegment, RunResult, ScriptedInput, Simulation
from hillclimb.engine.vehicle import FIXED_DT

if TYPE_CHECKING:
    from collections.abc import Sequence


def _schedule(total_ticks: int) -> ScriptedInput:
    half = total_ticks // 2
    return ScriptedInput(
        (
            InputSegment(0, half, 1.0, 0.0),
            InputSegment(half, total_ticks, 0.0, 0.4),
        )
    )


def _input_at(plan: ScriptedInput, tick: int) -> tuple[float, float]:
    for segment in plan.segments:
        if segment.start_tick <= tick < segment.end_tick:
            return segment.throttle, segment.brake
    return 0.0, 0.0


def _grouped_simulation(seed: int, counts: Sequence[int], plan: ScriptedInput) -> Simulation:
    simulation = Simulation(seed)
    tick = 0
    for count in counts:
        for _ in range(count):
            throttle, brake = _input_at(plan, tick)
            simulation.step(throttle, brake)
            tick += 1
    return simulation


def _payload(result: RunResult) -> str:
    return json.dumps(
        result.canonical_payload(),
        sort_keys=True,
        separators=(",", ":"),
    )


def test_l1_120_hz_frames_produce_one_tick() -> None:
    accumulator = 0.0
    for _ in range(120):
        ticks, accumulator = plan_frame_ticks(accumulator, FIXED_DT)
        assert ticks == 1
    assert accumulator == 0.0


def test_l1_60_hz_frames_produce_two_ticks() -> None:
    accumulator = 0.0
    for _ in range(60):
        ticks, accumulator = plan_frame_ticks(accumulator, 1.0 / 60.0)
        assert ticks == 2
    assert accumulator == 0.0


def test_l1_clamps_long_frames_to_100_ms() -> None:
    ticks, remainder = plan_frame_ticks(0.0, 10.0)
    assert ticks == int(MAX_FRAME_TIME_S / FIXED_DT)
    assert remainder == 0.0


def test_l1_caps_catch_up_at_25_ticks() -> None:
    ticks, remainder = plan_frame_ticks(30.0 * FIXED_DT, MAX_FRAME_TIME_S)
    assert ticks == MAX_CATCHUP_TICKS
    assert remainder == 0.0


def test_l1_cap_can_carry_a_sub_tick_remainder() -> None:
    ticks, remainder = plan_frame_ticks(13.5 * FIXED_DT, MAX_FRAME_TIME_S)
    assert ticks == MAX_CATCHUP_TICKS
    assert 0.0 < remainder < FIXED_DT


def test_l1_carries_only_sub_tick_remainders() -> None:
    ticks, remainder = plan_frame_ticks(0.0, FIXED_DT / 2.0)
    assert ticks == 0
    assert remainder == FIXED_DT / 2.0
    ticks, remainder = plan_frame_ticks(remainder, FIXED_DT / 2.0)
    assert ticks == 1
    assert remainder == 0.0


@settings(max_examples=20, deadline=None)
@given(
    seed=st.integers(min_value=0, max_value=2**31 - 1),
    elapsed=st.lists(
        st.floats(
            min_value=FIXED_DT / 4.0,
            max_value=MAX_FRAME_TIME_S * 2.4,
            allow_nan=False,
            allow_infinity=False,
        ),
        min_size=1,
        max_size=30,
    ),
)
def test_l1_frame_grouping_matches_one_contiguous_run(seed: int, elapsed: list[float]) -> None:
    accumulator = 0.0
    counts: list[int] = []
    for seconds in elapsed:
        ticks, accumulator = plan_frame_ticks(accumulator, seconds)
        counts.append(ticks)
    plan = _schedule(total := sum(counts))
    grouped = _grouped_simulation(seed, counts, plan)
    contiguous = Simulation(seed).run(total, plan)
    assert _payload(grouped.result) == _payload(contiguous)

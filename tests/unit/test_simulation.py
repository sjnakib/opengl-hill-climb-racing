"""Tests for the headless simulation coordinator."""

from __future__ import annotations

import math

import pytest

from hillclimb.engine.fuel import MAX_FUEL_LITRES
from hillclimb.engine.simulation import InputSegment, ScriptedInput, Simulation


def test_scripted_input_validation_accepts_ordered_segments() -> None:
    plan = ScriptedInput((InputSegment(0, 10, 1.0, 0.0), InputSegment(10, 20, 0.0, 1.0)))
    plan.validate(20)


@pytest.mark.parametrize(
    "segment",
    [
        InputSegment(-1, 10, 1.0, 0.0),
        InputSegment(10, 5, 1.0, 0.0),
        InputSegment(0, 25, 1.0, 0.0),
    ],
)
def test_scripted_input_rejects_bad_ranges(segment: InputSegment) -> None:
    with pytest.raises(ValueError, match=r"outside|ordered"):
        ScriptedInput((segment,)).validate(20)


def test_scripted_input_rejects_overlaps() -> None:
    plan = ScriptedInput((InputSegment(0, 10, 1.0, 0.0), InputSegment(9, 20, 0.0, 1.0)))
    with pytest.raises(ValueError, match="ordered"):
        plan.validate(20)


def test_run_rejects_negative_length() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        Simulation(1).run(-1)


def test_simulation_runs_a_scripted_plan() -> None:
    simulation = Simulation(2026)
    plan = ScriptedInput((InputSegment(0, 120, 1.0, 0.0), InputSegment(120, 240, 0.0, 0.5)))
    result = simulation.run(240, plan)
    assert result.ticks == 240
    assert result.distance_px > 0.0
    assert result.score >= 0
    assert 0.0 <= result.fuel_litres <= MAX_FUEL_LITRES
    assert result.game_over is False
    assert result.canonical_payload() == {
        "score": result.score,
        "distance_px": format(result.distance_px, ".17g"),
    }


def test_simulation_clamps_inputs_and_handles_empty_plans() -> None:
    simulation = Simulation(3)
    simulation.step(-5.0, 5.0)
    assert simulation.elapsed_ticks == 1
    result = simulation.run(0)
    assert result.ticks == 1


def test_fuel_zero_and_rest_ends_the_run() -> None:
    simulation = Simulation(4)
    simulation.fuel.fuel = 0.0
    for _ in range(120):
        simulation.step(0.0, 0.0)
        if simulation.game_over:
            break
    assert simulation.game_over
    ticks = simulation.elapsed_ticks
    simulation.step(1.0, 0.0)
    assert simulation.elapsed_ticks == ticks


def test_head_contact_while_moving_ends_the_run() -> None:
    simulation = Simulation(5)
    simulation.vehicle.theta = math.pi
    simulation.vehicle.y = simulation.terrain.height_at(simulation.vehicle.x) - 40.0
    simulation.vehicle.vx = 100.0
    simulation.step(0.0, 0.0)
    assert simulation.game_over


def test_run_stops_early_after_game_over() -> None:
    simulation = Simulation(6)
    simulation.fuel.fuel = 0.0
    plan = ScriptedInput((InputSegment(0, 120, 0.0, 0.0),))
    result = simulation.run(120, plan)
    assert result.game_over
    assert result.ticks < 120


def test_canonical_payload_uses_exact_float_text() -> None:
    result = Simulation(7).result
    payload = result.canonical_payload()
    assert payload["distance_px"] == format(result.distance_px, ".17g")
    assert payload["score"] == result.score


def test_fuel_can_refills_the_tank() -> None:
    simulation = Simulation(8)
    simulation.world.ensure_generated_until(1_000.0)
    can = simulation.world.fuel_cans[0]
    simulation.fuel.fuel = 10.0
    simulation.vehicle.x = can.x
    simulation.vehicle.y = can.y
    simulation.step(0.0, 0.0)
    assert simulation.fuel.fuel == MAX_FUEL_LITRES


def test_run_coasts_after_the_plan_ends() -> None:
    plan = ScriptedInput((InputSegment(0, 10, 1.0, 0.0),))
    result = Simulation(9).run(20, plan)
    assert result.ticks == 20

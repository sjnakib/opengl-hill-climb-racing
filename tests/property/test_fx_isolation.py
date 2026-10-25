"""Cosmetics on the fx stream never change physics or scoring (SPECS §10.2)."""

from __future__ import annotations

import json

from hillclimb.engine.rng import RngStreams
from hillclimb.engine.simulation import InputSegment, ScriptedInput, Simulation

PLAN = ScriptedInput(
    (
        InputSegment(0, 360, 1.0, 0.0),
        InputSegment(360, 600, 0.0, 0.6),
    )
)


def payload_for(*, consume_fx: bool) -> str:
    streams = RngStreams(99)
    fx = streams.stream("fx")
    if consume_fx:
        for _ in range(10_000):
            fx.random()
    simulation = Simulation(99, streams=streams)
    for tick in range(600):
        if consume_fx:
            for _ in range(tick % 7 + 1):
                fx.random()
        segment_throttle = 1.0 if tick < 360 else 0.0
        segment_brake = 0.0 if tick < 360 else 0.6
        simulation.step(segment_throttle, segment_brake)
    return json.dumps(simulation.result.canonical_payload(), sort_keys=True)


def test_fx_draws_do_not_change_physics_or_scoring() -> None:
    assert payload_for(consume_fx=False) == payload_for(consume_fx=True)


def test_fx_draws_do_not_change_the_scripted_result() -> None:
    baseline = Simulation(99).run(600, PLAN)
    assert payload_for(consume_fx=True) == json.dumps(baseline.canonical_payload(), sort_keys=True)

"""R1: replay determinism and the committed golden replay."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from hypothesis import given, settings
from hypothesis import strategies as st

from hillclimb.engine.simulation import InputSegment, ScriptedInput, Simulation

if TYPE_CHECKING:
    from collections.abc import Sequence

GOLDEN_PATH = Path(__file__).parents[1] / "golden" / "replay_r1.json"


def canonical(seed: int, max_ticks: int, segments: Sequence[tuple[int, int, float, float]]) -> str:
    plan = ScriptedInput(tuple(InputSegment(*segment) for segment in segments))
    result = Simulation(seed).run(max_ticks, plan)
    return json.dumps(result.canonical_payload(), sort_keys=True, separators=(",", ":"))


def scripted_segments() -> tuple[tuple[int, int, float, float], ...]:
    return ((0, 240, 1.0, 0.0), (240, 480, 0.0, 0.4))


@settings(max_examples=8, deadline=None)
@given(seed=st.integers(min_value=0, max_value=2**31 - 1))
def test_r1_same_seed_and_inputs_are_byte_identical(seed: int) -> None:
    first = canonical(seed, 480, scripted_segments())
    second = canonical(seed, 480, scripted_segments())
    assert first == second


def test_r1_golden_replay_matches_exactly() -> None:
    payload = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    seed = payload["seed"]
    max_ticks = payload["max_ticks"]
    segments = tuple(tuple(segment) for segment in payload["inputs"])
    result = Simulation(seed).run(
        max_ticks, ScriptedInput(tuple(InputSegment(*s) for s in segments))
    )
    assert result.canonical_payload() == {
        "score": payload["score"],
        "distance_px": payload["distance_px"],
    }
    assert format(result.distance_px, ".17g") == payload["distance_px"]

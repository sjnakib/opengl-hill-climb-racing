"""Unit tests for the pure audio bus math (SPECS §11)."""

from __future__ import annotations

import pytest

from hillclimb.app.audio import bus_mix, master_gain, music_gain, sfx_gain
from hillclimb.config import Config


@pytest.mark.parametrize(
    ("master", "bus", "expected"),
    [
        (0, 100, 0.0),
        (100, 0, 0.0),
        (100, 100, 1.0),
        (50, 40, 0.2),
        (-10, 200, 0.0),
        (200, 200, 1.0),
        (float("inf"), 50, 0.0),
        (50, float("nan"), 0.0),
    ],
)
def test_bus_mix_is_a_closed_0_to_1_product(master: float, bus: float, expected: float) -> None:
    assert bus_mix(master, bus) == pytest.approx(expected)


def test_master_music_and_sfx_share_one_formula() -> None:
    config = Config(master_volume=50, music_volume=40, sfx_volume=80)
    assert master_gain(config) == pytest.approx(0.5)
    assert music_gain(config) == pytest.approx(0.2)
    assert sfx_gain(config) == pytest.approx(0.4)

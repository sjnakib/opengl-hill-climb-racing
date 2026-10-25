"""Tests for coins, airtime, and flips (SPECS §10.5)."""

from __future__ import annotations

import math

import pytest

from hillclimb.engine.fixedmath import TAU
from hillclimb.engine.scoring import (
    AIRTIME_BASE_POINTS,
    FLIP_POINTS,
    TICKS_PER_SECOND,
    ScoreLedger,
)


def test_coin_sums_accumulate_and_negative_values_are_rejected() -> None:
    ledger = ScoreLedger()
    assert ledger.add_coins(50) == 50
    assert ledger.add_coins(500) == 550
    assert ledger.coin_score == 550
    assert ledger.score == 550
    with pytest.raises(ValueError, match="non-negative"):
        ledger.add_coins(-1)


def test_airtime_awards_on_full_second_boundaries() -> None:
    ledger = ScoreLedger()
    for _ in range(TICKS_PER_SECOND - 1):
        ledger.advance(airborne=True, angle_radians=0.0)
    assert ledger.airtime_bonus == 0
    ledger.advance(airborne=True, angle_radians=0.0)
    assert ledger.airtime_bonus == AIRTIME_BASE_POINTS
    for _ in range(TICKS_PER_SECOND):
        ledger.advance(airborne=True, angle_radians=0.0)
    assert ledger.airtime_bonus == AIRTIME_BASE_POINTS * 3
    assert ledger.score == AIRTIME_BASE_POINTS * 3


def test_airtime_doubles_for_further_full_seconds() -> None:
    ledger = ScoreLedger()
    for _ in range(3 * TICKS_PER_SECOND):
        ledger.advance(airborne=True, angle_radians=0.0)
    assert ledger.airtime_bonus == 50 + 100 + 200
    assert ledger.airtime_seconds == 3


def test_landing_resets_the_airtime_counter() -> None:
    ledger = ScoreLedger()
    for _ in range(TICKS_PER_SECOND):
        ledger.advance(airborne=True, angle_radians=0.0)
    ledger.advance(airborne=False, angle_radians=0.0)
    for _ in range(TICKS_PER_SECOND - 1):
        ledger.advance(airborne=True, angle_radians=0.0)
    assert ledger.airtime_bonus == AIRTIME_BASE_POINTS


def test_flips_award_each_full_rotation_while_airborne() -> None:
    ledger = ScoreLedger()
    ledger.advance(airborne=True, angle_radians=0.0)
    ledger.advance(airborne=True, angle_radians=math.pi)
    ledger.advance(airborne=True, angle_radians=2.0 * math.pi - 0.01)
    assert ledger.flip_bonus == 0
    ledger.advance(airborne=True, angle_radians=2.0 * math.pi)
    assert ledger.flip_bonus == FLIP_POINTS
    assert ledger.flips == 1


def test_multiple_flips_award_in_one_tick() -> None:
    ledger = ScoreLedger()
    ledger.advance(airborne=True, angle_radians=0.0)
    ledger.advance(airborne=True, angle_radians=4.0 * TAU)
    assert ledger.flips == 4
    assert ledger.flip_bonus == 4 * FLIP_POINTS


def test_negative_rotation_counts_as_a_flip() -> None:
    ledger = ScoreLedger()
    ledger.advance(airborne=True, angle_radians=0.0)
    ledger.advance(airborne=True, angle_radians=-TAU)
    assert ledger.flips == 1
    assert ledger.flip_bonus == FLIP_POINTS


def test_grounded_ticks_do_not_award_airtime() -> None:
    ledger = ScoreLedger()
    for _ in range(TICKS_PER_SECOND):
        ledger.advance(airborne=False, angle_radians=0.0)
    assert ledger.airtime_bonus == 0
    assert ledger.flip_bonus == 0
    assert ledger.score == 0

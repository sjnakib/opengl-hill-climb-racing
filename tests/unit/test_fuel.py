"""Tests for the fuel tank (SPECS §10.5)."""

from __future__ import annotations

import pytest

from hillclimb.engine.fuel import (
    IDLE_DRAIN_LITRES_PER_SECOND,
    MAX_FUEL_LITRES,
    SPEED_DRAIN_LITRES_PER_PIXEL,
    FuelTank,
)


def test_tank_starts_full_and_clamps_initial_values() -> None:
    assert FuelTank().fuel == MAX_FUEL_LITRES
    assert FuelTank(-5.0).fuel == 0.0
    assert FuelTank(500.0).fuel == MAX_FUEL_LITRES


def test_idle_and_speed_drain_follow_the_formula() -> None:
    tank = FuelTank()
    tank.drain(1.0, 0.0, 1.0)
    assert tank.fuel == pytest.approx(MAX_FUEL_LITRES - IDLE_DRAIN_LITRES_PER_SECOND)
    tank = FuelTank()
    tank.drain(1.0, 100.0, 0.5)
    expected = MAX_FUEL_LITRES - (IDLE_DRAIN_LITRES_PER_SECOND + 1.2) * 0.5
    assert tank.fuel == pytest.approx(expected)


def test_drain_never_leaves_the_closed_range() -> None:
    tank = FuelTank(0.1)
    assert tank.drain(10.0, 500.0, 1.0) == 0.0
    assert tank.empty
    assert tank.drain(1.0, 0.0, 1.0) == 0.0


def test_refill_returns_to_full() -> None:
    tank = FuelTank(12.0)
    assert tank.refill() == MAX_FUEL_LITRES
    assert not tank.empty


def test_speed_drain_constant_is_the_pinned_value() -> None:
    assert SPEED_DRAIN_LITRES_PER_PIXEL == 0.012

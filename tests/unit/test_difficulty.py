"""Tests for the shared difficulty curves (SPECS §10.3, §10.5)."""

from __future__ import annotations

import math

import pytest

from hillclimb.engine.difficulty import (
    DIFFICULTY_RAMP_PX,
    MAX_DIFFICULTY_LEVEL,
    MIN_DIFFICULTY_LEVEL,
    OCTAVE_WAVELENGTHS_PX,
    SLOPE_BUDGET_END,
    SLOPE_BUDGET_START,
    START_WEIGHTS,
    TARGET_WEIGHTS,
    difficulty_at,
    difficulty_fraction,
    fuel_drain_factor,
    level_at,
    octave_weights,
    slope_budget,
)
from hillclimb.engine.fixedmath import TAU


def test_level_curve_hits_the_pinned_endpoints() -> None:
    assert level_at(0.0) == MIN_DIFFICULTY_LEVEL
    assert level_at(DIFFICULTY_RAMP_PX) == MAX_DIFFICULTY_LEVEL
    assert level_at(DIFFICULTY_RAMP_PX * 10.0) == MAX_DIFFICULTY_LEVEL
    assert level_at(DIFFICULTY_RAMP_PX / 2.0) == pytest.approx(5.5)


def test_fraction_clamps_and_rejects_bad_distances() -> None:
    assert difficulty_fraction(DIFFICULTY_RAMP_PX * 2.0) == 1.0
    for bad in (-1.0, math.nan, math.inf):
        with pytest.raises(ValueError, match="finite, non-negative"):
            difficulty_fraction(bad)
        with pytest.raises(ValueError, match="finite, non-negative"):
            level_at(bad)
        with pytest.raises(ValueError, match="finite, non-negative"):
            fuel_drain_factor(bad)


def test_weights_and_budgets_match_the_table() -> None:
    assert octave_weights(0.0) == START_WEIGHTS
    assert octave_weights(1.0) == TARGET_WEIGHTS
    assert sum(TARGET_WEIGHTS) == pytest.approx(1.0)
    assert slope_budget(0.0) == SLOPE_BUDGET_START
    assert slope_budget(1.0) == SLOPE_BUDGET_END


def test_drain_factor_is_level_over_ten() -> None:
    assert fuel_drain_factor(0.0) == 0.1
    assert fuel_drain_factor(DIFFICULTY_RAMP_PX) == 1.0


def test_profile_uses_the_table_weights_and_wavelengths() -> None:
    start = difficulty_at(0.0)
    end = difficulty_at(DIFFICULTY_RAMP_PX)
    assert start.level == 1.0
    assert start.roughness == 0.0
    assert start.frequency_per_kpx == pytest.approx(1000.0 / OCTAVE_WAVELENGTHS_PX[0])
    assert start.amplitude_px == pytest.approx(SLOPE_BUDGET_START / TAU * OCTAVE_WAVELENGTHS_PX[0])
    assert end.level == 10.0
    assert end.roughness == pytest.approx(0.45)
    expected_frequency = 1000.0 * sum(
        weight / wavelength
        for weight, wavelength in zip(TARGET_WEIGHTS, OCTAVE_WAVELENGTHS_PX, strict=True)
    )
    assert end.frequency_per_kpx == pytest.approx(expected_frequency)
    assert end.amplitude_px > start.amplitude_px

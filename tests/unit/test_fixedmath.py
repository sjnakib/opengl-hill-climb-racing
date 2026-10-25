"""Tests for the deterministic numeric law (SPECS §10.2)."""

from __future__ import annotations

import math

import pytest

from hillclimb.engine.fixedmath import HALF_PI, PI, TAU, cosine, sine


def test_sine_stays_within_one_e_12_of_libm() -> None:
    worst = 0.0
    for index in range(200_001):
        angle = -1_000_000.0 + index * 10.0
        worst = max(worst, abs(sine(angle) - math.sin(angle)))
    assert worst <= 1e-12


@pytest.mark.parametrize(
    "angle",
    [
        0.0,
        TAU,
        -TAU,
        TAU * 4096.0,
        PI,
        -PI,
        HALF_PI,
        -HALF_PI,
        PI + 0.25,
        -PI - 0.25,
        HALF_PI + 0.25,
        -HALF_PI - 0.25,
        1e9,
        -1e9,
    ],
)
def test_sine_matches_libm_at_boundaries(angle: float) -> None:
    assert abs(sine(angle) - math.sin(angle)) <= 1e-12


def test_cosine_uses_the_same_deterministic_kernel() -> None:
    for index in range(10_001):
        angle = -100.0 + index * 0.02
        assert abs(cosine(angle) - math.cos(angle)) <= 1e-12


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_sine_rejects_non_finite_angles(bad: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        sine(bad)
    with pytest.raises(ValueError, match="finite"):
        cosine(bad)

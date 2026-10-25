"""Shared difficulty curves from the SPECS §10.3 table."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .fixedmath import TAU

DIFFICULTY_RAMP_PX = 45_000.0
MIN_DIFFICULTY_LEVEL = 1.0
MAX_DIFFICULTY_LEVEL = 10.0

SLOPE_BUDGET_START = 0.26795
SLOPE_BUDGET_END = 1.42815

OCTAVE_WAVELENGTHS_PX = (2048.0, 1536.0, 1024.0, 768.0)
START_WEIGHTS = (1.0, 0.0, 0.0, 0.0)
TARGET_WEIGHTS = (0.55, 0.25, 0.14, 0.06)


@dataclass(frozen=True, slots=True)
class TerrainDifficulty:
    """Difficulty values at one distance along the terrain."""

    level: float
    amplitude_px: float
    frequency_per_kpx: float
    roughness: float


def _validate_distance(distance_px: float) -> None:
    if not math.isfinite(distance_px) or distance_px < 0:
        message = "distance must be a finite, non-negative pixel value"
        raise ValueError(message)


def difficulty_fraction(distance_px: float) -> float:
    """Return the clamped ramp fraction for a distance in pixels."""
    _validate_distance(distance_px)
    return min(distance_px / DIFFICULTY_RAMP_PX, 1.0)


def octave_weights(fraction: float) -> tuple[float, ...]:
    """Blend the octave weights across the difficulty ramp."""
    return tuple(
        start + (target - start) * fraction
        for start, target in zip(START_WEIGHTS, TARGET_WEIGHTS, strict=True)
    )


def slope_budget(fraction: float) -> float:
    """Return the rise-over-run slope budget at a ramp fraction."""
    return SLOPE_BUDGET_START + (SLOPE_BUDGET_END - SLOPE_BUDGET_START) * fraction


def level_at(distance_px: float) -> float:
    """Return the §10.3 difficulty level at a distance."""
    fraction = difficulty_fraction(distance_px)
    return MIN_DIFFICULTY_LEVEL + (MAX_DIFFICULTY_LEVEL - MIN_DIFFICULTY_LEVEL) * fraction


def fuel_drain_factor(distance_px: float) -> float:
    """Return the §10.5 drain factor, the level divided by ten."""
    return level_at(distance_px) / 10.0


def difficulty_at(distance_px: float) -> TerrainDifficulty:
    """Return the full terrain difficulty profile at a distance."""
    fraction = difficulty_fraction(distance_px)
    weights = octave_weights(fraction)
    budget = slope_budget(fraction)
    amplitude_px = (
        budget
        / TAU
        * sum(
            weight * wavelength
            for weight, wavelength in zip(weights, OCTAVE_WAVELENGTHS_PX, strict=True)
        )
    )
    frequency_per_kpx = 1000.0 * sum(
        weight / wavelength
        for weight, wavelength in zip(weights, OCTAVE_WAVELENGTHS_PX, strict=True)
    )
    return TerrainDifficulty(
        level=level_at(distance_px),
        amplitude_px=amplitude_px,
        frequency_per_kpx=frequency_per_kpx,
        roughness=1.0 - weights[0],
    )

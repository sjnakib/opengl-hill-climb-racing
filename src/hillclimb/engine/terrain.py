"""Chunked procedural terrain with bounded slopes (SPECS §10.3)."""

from __future__ import annotations

import math
from collections import OrderedDict
from dataclasses import dataclass

from .rng import RngStreams

_TAU = math.tau

SAMPLE_SPACING_PX = 8.0
CHUNK_SAMPLES = 64
CHUNK_WIDTH_PX = SAMPLE_SPACING_PX * CHUNK_SAMPLES
DEFAULT_CHUNK_CACHE = 32
BASE_HEIGHT_PX = 600.0

SLOPE_LIMIT_DEGREES = 60.0
REACHABILITY_SPAN_PX = 40.0

DIFFICULTY_RAMP_PX = 45_000.0
MIN_DIFFICULTY_LEVEL = 1.0
MAX_DIFFICULTY_LEVEL = 10.0

_MIN_GENERATED_SLOPE_DEGREES = 15.0
_MAX_GENERATED_SLOPE_DEGREES = 55.0
_MIN_CACHE_SIZE = 1

_OCTAVE_WAVELENGTHS_PX = (2048.0, 1536.0, 1024.0, 768.0)
_START_WEIGHTS = (1.0, 0.0, 0.0, 0.0)
_TARGET_WEIGHTS = (0.55, 0.25, 0.14, 0.06)


@dataclass(frozen=True, slots=True)
class TerrainDifficulty:
    """Difficulty values at one distance along the terrain."""

    level: float
    amplitude_px: float
    frequency_per_kpx: float
    roughness: float


def _difficulty_fraction(distance_px: float) -> float:
    return min(distance_px / DIFFICULTY_RAMP_PX, 1.0)


def _octave_weights(fraction: float) -> tuple[float, ...]:
    return tuple(
        start + (target - start) * fraction
        for start, target in zip(_START_WEIGHTS, _TARGET_WEIGHTS, strict=True)
    )


def _slope_budget(fraction: float) -> float:
    angle = (
        _MIN_GENERATED_SLOPE_DEGREES
        + (_MAX_GENERATED_SLOPE_DEGREES - _MIN_GENERATED_SLOPE_DEGREES) * fraction
    )
    return math.tan(math.radians(angle))


def difficulty_at(distance_px: float) -> TerrainDifficulty:
    """Return difficulty parameters for a non-negative distance in pixels."""
    if not math.isfinite(distance_px) or distance_px < 0:
        message = "distance must be a finite, non-negative pixel value"
        raise ValueError(message)
    fraction = _difficulty_fraction(distance_px)
    weights = _octave_weights(fraction)
    budget = _slope_budget(fraction)
    amplitude_px = (
        budget
        / _TAU
        * sum(
            weight * wavelength
            for weight, wavelength in zip(weights, _OCTAVE_WAVELENGTHS_PX, strict=True)
        )
    )
    frequency = 1000.0 * sum(
        weight / wavelength
        for weight, wavelength in zip(weights, _OCTAVE_WAVELENGTHS_PX, strict=True)
    )
    level = MIN_DIFFICULTY_LEVEL + (MAX_DIFFICULTY_LEVEL - MIN_DIFFICULTY_LEVEL) * fraction
    return TerrainDifficulty(
        level=level,
        amplitude_px=amplitude_px,
        frequency_per_kpx=frequency,
        roughness=1.0 - weights[0],
    )


class Terrain:
    """Chunked heightfield with O(1) height queries inside a loaded chunk."""

    __slots__ = ("_cache_size", "_chunks", "_phases")

    def __init__(self, master_seed: int, *, cache_size: int = DEFAULT_CHUNK_CACHE) -> None:
        """Seed the terrain stream and size the chunk cache."""
        if cache_size < _MIN_CACHE_SIZE:
            message = "cache_size must be at least 1"
            raise ValueError(message)
        self._cache_size = cache_size
        self._chunks: OrderedDict[int, tuple[float, ...]] = OrderedDict()
        stream = RngStreams(master_seed).stream("terrain")
        self._phases = tuple(stream.uniform(0.0, _TAU) for _ in _OCTAVE_WAVELENGTHS_PX)

    @property
    def cached_chunk_count(self) -> int:
        """Return how many chunks are currently cached."""
        return len(self._chunks)

    def height_at(self, x_px: float) -> float:
        """Return the interpolated terrain height in pixels at x."""
        chunk_index, lower_index, fraction = self._locate(x_px)
        samples = self._chunk(chunk_index)
        lower = samples[lower_index]
        upper = samples[lower_index + 1]
        return lower + (upper - lower) * fraction

    def slope_at(self, x_px: float) -> float:
        """Return the local slope in degrees at x."""
        chunk_index, lower_index, _ = self._locate(x_px)
        samples = self._chunk(chunk_index)
        rise = samples[lower_index + 1] - samples[lower_index]
        return math.degrees(math.atan2(rise, SAMPLE_SPACING_PX))

    def _locate(self, x_px: float) -> tuple[int, int, float]:
        if not math.isfinite(x_px) or x_px < 0:
            message = "x must be a finite, non-negative pixel position"
            raise ValueError(message)
        chunk_index = int(x_px // CHUNK_WIDTH_PX)
        position = (x_px - chunk_index * CHUNK_WIDTH_PX) / SAMPLE_SPACING_PX
        lower_index = min(int(position), CHUNK_SAMPLES - 1)
        return chunk_index, lower_index, position - lower_index

    def _chunk(self, chunk_index: int) -> tuple[float, ...]:
        cached = self._chunks.get(chunk_index)
        if cached is not None:
            self._chunks.move_to_end(chunk_index)
            return cached
        first_sample = chunk_index * CHUNK_SAMPLES
        samples = tuple(
            self._sample_height(first_sample + offset) for offset in range(CHUNK_SAMPLES + 1)
        )
        self._chunks[chunk_index] = samples
        if len(self._chunks) > self._cache_size:
            self._chunks.popitem(last=False)
        return samples

    def _sample_height(self, sample_index: int) -> float:
        distance = sample_index * SAMPLE_SPACING_PX
        fraction = _difficulty_fraction(distance)
        weights = _octave_weights(fraction)
        budget = _slope_budget(fraction)
        height = BASE_HEIGHT_PX
        for weight, wavelength, phase in zip(
            weights, _OCTAVE_WAVELENGTHS_PX, self._phases, strict=True
        ):
            amplitude = weight * budget * wavelength / _TAU
            height += amplitude * math.sin(_TAU * distance / wavelength + phase)
        return height

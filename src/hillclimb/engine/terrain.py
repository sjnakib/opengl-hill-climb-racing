"""Chunked procedural terrain with bounded slopes (SPECS §10.3)."""

from __future__ import annotations

import math
from collections import OrderedDict

from .difficulty import (
    DIFFICULTY_RAMP_PX,
    MAX_DIFFICULTY_LEVEL,
    MIN_DIFFICULTY_LEVEL,
    OCTAVE_WAVELENGTHS_PX,
    TerrainDifficulty,
    difficulty_at,
    difficulty_fraction,
    octave_weights,
    slope_budget,
)
from .fixedmath import TAU, sine
from .rng import RngStreams

__all__ = [
    "BASE_HEIGHT_PX",
    "CHUNK_SAMPLES",
    "CHUNK_WIDTH_PX",
    "DEFAULT_CHUNK_CACHE",
    "DIFFICULTY_RAMP_PX",
    "MAX_DIFFICULTY_LEVEL",
    "MIN_DIFFICULTY_LEVEL",
    "REACHABILITY_SPAN_PX",
    "SAMPLE_SPACING_PX",
    "SLOPE_LIMIT_DEGREES",
    "Terrain",
    "TerrainDifficulty",
    "difficulty_at",
]

SAMPLE_SPACING_PX = 8.0
CHUNK_SAMPLES = 64
CHUNK_WIDTH_PX = SAMPLE_SPACING_PX * CHUNK_SAMPLES
DEFAULT_CHUNK_CACHE = 32
BASE_HEIGHT_PX = 600.0

SLOPE_LIMIT_DEGREES = 60.0
REACHABILITY_SPAN_PX = 40.0

_MIN_CACHE_SIZE = 1


class Terrain:
    """Chunked heightfield with O(1) height queries inside a loaded chunk."""

    __slots__ = ("_cache_size", "_chunks", "_phases")

    def __init__(
        self,
        master_seed: int,
        *,
        cache_size: int = DEFAULT_CHUNK_CACHE,
        streams: RngStreams | None = None,
    ) -> None:
        """Seed the terrain stream and size the chunk cache."""
        if cache_size < _MIN_CACHE_SIZE:
            message = "cache_size must be at least 1"
            raise ValueError(message)
        self._cache_size = cache_size
        self._chunks: OrderedDict[int, tuple[float, ...]] = OrderedDict()
        registry = RngStreams(master_seed) if streams is None else streams
        stream = registry.stream("terrain")
        self._phases = tuple(stream.uniform(0.0, TAU) for _ in OCTAVE_WAVELENGTHS_PX)

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

    def grade_at(self, x_px: float) -> float:
        """Return the local rise over run grade at x."""
        chunk_index, lower_index, _ = self._locate(x_px)
        samples = self._chunk(chunk_index)
        return (samples[lower_index + 1] - samples[lower_index]) / SAMPLE_SPACING_PX

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
        fraction = difficulty_fraction(distance)
        weights = octave_weights(fraction)
        budget = slope_budget(fraction)
        height = BASE_HEIGHT_PX
        for weight, wavelength, phase in zip(
            weights, OCTAVE_WAVELENGTHS_PX, self._phases, strict=True
        ):
            amplitude = weight * budget * wavelength / TAU
            height += amplitude * sine(TAU * distance / wavelength + phase)
        return height

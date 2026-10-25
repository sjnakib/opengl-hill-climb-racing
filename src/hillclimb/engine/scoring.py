"""Coin, airtime, and flip scoring (SPECS §10.5)."""

from __future__ import annotations

from .fixedmath import TAU

TICKS_PER_SECOND = 120
AIRTIME_BASE_POINTS = 50
FLIP_POINTS = 100


class ScoreLedger:
    """Monotonic score state for one run."""

    __slots__ = (
        "_air_rotation",
        "_air_seconds_awarded",
        "_air_ticks",
        "_airborne",
        "_last_angle",
        "airtime_bonus",
        "coin_score",
        "flip_bonus",
        "flips",
        "score",
    )

    def __init__(self) -> None:
        """Start a run with every counter at zero."""
        self.score = 0
        self.coin_score = 0
        self.airtime_bonus = 0
        self.flip_bonus = 0
        self.flips = 0
        self._airborne = False
        self._air_ticks = 0
        self._air_seconds_awarded = 0
        self._air_rotation = 0.0
        self._last_angle = 0.0

    @property
    def airtime_seconds(self) -> int:
        """Return how many full airborne seconds have been awarded."""
        return self._air_seconds_awarded

    def add_coins(self, value: int) -> int:
        """Add a coin sum and return the new total score."""
        if value < 0:
            message = "coin value must be non-negative"
            raise ValueError(message)
        self.coin_score += value
        self.score += value
        return self.score

    def advance(self, *, airborne: bool, angle_radians: float) -> int:
        """Advance one 120 Hz tick and return the new total score."""
        if airborne:
            if not self._airborne:
                self._begin_air(angle_radians)
            self._air_ticks += 1
            self._award_full_seconds()
            self._air_rotation += angle_radians - self._last_angle
            self._award_full_flips()
        elif self._airborne:
            self._end_air()
        self._last_angle = angle_radians
        return self.score

    def _begin_air(self, angle_radians: float) -> None:
        self._airborne = True
        self._air_ticks = 0
        self._air_seconds_awarded = 0
        self._air_rotation = 0.0
        self._last_angle = angle_radians

    def _end_air(self) -> None:
        self._airborne = False
        self._air_ticks = 0
        self._air_seconds_awarded = 0
        self._air_rotation = 0.0

    def _award_full_seconds(self) -> None:
        while self._air_ticks >= (self._air_seconds_awarded + 1) * TICKS_PER_SECOND:
            bonus = AIRTIME_BASE_POINTS << self._air_seconds_awarded
            self.airtime_bonus += bonus
            self.score += bonus
            self._air_seconds_awarded += 1

    def _award_full_flips(self) -> None:
        while self._air_rotation >= TAU:
            self._air_rotation -= TAU
            self.flips += 1
            self.flip_bonus += FLIP_POINTS
            self.score += FLIP_POINTS
        while self._air_rotation <= -TAU:
            self._air_rotation += TAU
            self.flips += 1
            self.flip_bonus += FLIP_POINTS
            self.score += FLIP_POINTS

"""Fuel tank state and the §10.5 drain law."""

from __future__ import annotations

MAX_FUEL_LITRES = 100.0
IDLE_DRAIN_LITRES_PER_SECOND = 0.55
SPEED_DRAIN_LITRES_PER_PIXEL = 0.012


class FuelTank:
    """A fuel tank that never leaves the closed range shown to the player."""

    __slots__ = ("fuel",)

    def __init__(self, fuel: float = MAX_FUEL_LITRES) -> None:
        """Start with fuel clamped to the legal range."""
        self.fuel = min(max(fuel, 0.0), MAX_FUEL_LITRES)

    @property
    def empty(self) -> bool:
        """Return whether the tank has reached zero."""
        return self.fuel <= 0.0

    def drain(self, dt: float, speed_px_s: float, difficulty_factor: float) -> float:
        """Remove fuel for one tick and return the new level."""
        speed = abs(speed_px_s)
        rate = IDLE_DRAIN_LITRES_PER_SECOND + speed * SPEED_DRAIN_LITRES_PER_PIXEL
        self.fuel = max(0.0, self.fuel - rate * difficulty_factor * dt)
        return self.fuel

    def refill(self) -> float:
        """Fill the tank and return the new level."""
        self.fuel = MAX_FUEL_LITRES
        return self.fuel

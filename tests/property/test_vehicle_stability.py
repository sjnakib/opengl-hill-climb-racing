"""Suspension stability: no penetration and bounded energy over a long run."""

from __future__ import annotations

import math

from hillclimb.engine.terrain import Terrain
from hillclimb.engine.vehicle import (
    GRAVITY_PX_S2,
    MASS_KG,
    MAX_ANGULAR_SPEED,
    TOP_SPEED_PX_S,
    Vehicle,
)

BODY_SAMPLES = (
    (-56.0, -20.0),
    (0.0, -20.0),
    (56.0, -20.0),
    (-56.0, 25.0),
    (56.0, 25.0),
)
ENERGY_LIMIT = 1e9


def test_suspension_stays_stable_over_a_long_scripted_run() -> None:
    for seed in (0, 1):
        terrain = Terrain(seed)
        vehicle = Vehicle(terrain)
        start_y = vehicle.y
        for tick in range(3_600):
            phase = (tick // 180) % 4
            throttle = 1.0 if phase in (0, 1) else 0.0
            brake = 1.0 if phase == 3 else 0.0
            vehicle.step(terrain, throttle, brake)
            cos_theta = math.cos(vehicle.theta)
            sin_theta = math.sin(vehicle.theta)
            for local_x, local_y in BODY_SAMPLES:
                sample_x = vehicle.x + local_x * cos_theta - local_y * sin_theta
                sample_y = vehicle.y + local_x * sin_theta + local_y * cos_theta
                assert sample_y >= terrain.height_at(sample_x) - 1e-9
            energy = (
                0.5 * MASS_KG * vehicle.speed_px_s * vehicle.speed_px_s
                + MASS_KG * GRAVITY_PX_S2 * (vehicle.y - start_y)
            )
            assert math.isfinite(energy)
            assert abs(energy) <= ENERGY_LIMIT
            assert vehicle.speed_px_s <= TOP_SPEED_PX_S + 1e-9
            assert abs(vehicle.omega) <= MAX_ANGULAR_SPEED + 1e-9

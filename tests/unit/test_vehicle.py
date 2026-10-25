"""Tests for the two-wheel vehicle (SPECS §10.4)."""

from __future__ import annotations

import math

import pytest

from hillclimb.engine.terrain import Terrain
from hillclimb.engine.vehicle import (
    FULL_DRIVE_SPEED_PX_S,
    REVERSE_CAP_PX_S,
    TOP_SPEED_PX_S,
    Vehicle,
    drive_factor,
)


def test_drive_profile_is_full_then_tapers_to_zero() -> None:
    assert drive_factor(0.0) == 1.0
    assert drive_factor(FULL_DRIVE_SPEED_PX_S) == 1.0
    assert drive_factor(375.0) == pytest.approx(0.5)
    assert drive_factor(TOP_SPEED_PX_S) == 0.0
    assert drive_factor(900.0) == 0.0


def test_vehicle_starts_on_the_terrain() -> None:
    terrain = Terrain(4)
    vehicle = Vehicle(terrain)
    assert vehicle.y > terrain.height_at(vehicle.x)
    assert vehicle.distance_px == 0.0
    assert vehicle.speed_px_s == 0.0
    assert isinstance(vehicle.left_contact, bool)
    assert isinstance(vehicle.right_contact, bool)


def test_throttle_accelerates_and_caps_the_speed() -> None:
    terrain = Terrain(5)
    vehicle = Vehicle(terrain)
    for _ in range(1_200):
        vehicle.step(terrain, 1.0, 0.0)
    assert vehicle.speed_px_s <= TOP_SPEED_PX_S + 1e-9
    assert vehicle.distance_px > 1_000.0


def test_reverse_drive_holds_the_reverse_cap() -> None:
    terrain = Terrain(6)
    vehicle = Vehicle(terrain)
    for _ in range(600):
        vehicle.step(terrain, 0.0, 1.0)
    assert vehicle.vx >= -REVERSE_CAP_PX_S - 1e-9


def test_braking_and_gravity_never_exceed_the_speed_cap() -> None:
    terrain = Terrain(7)
    vehicle = Vehicle(terrain)
    vehicle.vx = 2_000.0
    vehicle.vy = -2_000.0
    vehicle.step(terrain, 0.0, 1.0)
    assert vehicle.speed_px_s <= TOP_SPEED_PX_S + 1e-9
    assert vehicle.vx >= -REVERSE_CAP_PX_S - 1e-9


def test_airborne_vehicle_has_no_wheel_contact() -> None:
    terrain = Terrain(8)
    vehicle = Vehicle(terrain)
    vehicle.y += 500.0
    vehicle.step(terrain, 1.0, 0.0)
    assert vehicle.airborne
    assert not vehicle.left_contact
    assert not vehicle.right_contact


def test_ground_projection_removes_penetration() -> None:
    terrain = Terrain(9)
    vehicle = Vehicle(terrain)
    vehicle.y = terrain.height_at(vehicle.x) - 80.0
    vehicle.vy = -50.0
    vehicle.step(terrain, 0.0, 0.0)
    cos_theta = math.cos(vehicle.theta)
    sin_theta = math.sin(vehicle.theta)
    for local_x, local_y in (
        (-56.0, -20.0),
        (0.0, -20.0),
        (56.0, -20.0),
        (-56.0, 25.0),
        (56.0, 25.0),
    ):
        sample_x = vehicle.x + local_x * cos_theta - local_y * sin_theta
        sample_y = vehicle.y + local_x * sin_theta + local_y * cos_theta
        assert sample_y >= terrain.height_at(sample_x) - 1e-9


def test_head_vertex_reports_terrain_contact_when_inverted() -> None:
    terrain = Terrain(10)
    vehicle = Vehicle(terrain)
    vehicle.theta = math.pi
    vehicle.y = terrain.height_at(vehicle.x) + 20.0
    assert vehicle.head_touches_terrain(terrain)


def test_head_vertex_is_clear_when_upright() -> None:
    terrain = Terrain(11)
    vehicle = Vehicle(terrain)
    assert not vehicle.head_touches_terrain(terrain)

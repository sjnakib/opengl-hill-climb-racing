"""Two-wheel rigid-chassis vehicle physics (SPECS §10.4)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .fixedmath import cosine, sine

if TYPE_CHECKING:
    from .terrain import Terrain

TICK_RATE_HZ = 120
FIXED_DT = 1.0 / TICK_RATE_HZ

TOP_SPEED_PX_S = 500.0
FULL_DRIVE_SPEED_PX_S = 250.0
REVERSE_CAP_PX_S = 150.0
REST_SPEED_PX_S = 5.0

MASS_KG = 100.0
GRAVITY_PX_S2 = 1000.0
INERTIA = 180_000.0
WHEELBASE_PX = 112.0
WHEEL_REST_LENGTH_PX = 20.0
CHASSIS_HEIGHT_PX = 50.0
SUSPENSION_SPRING = 32_000.0
SUSPENSION_DAMPING = 2_400.0
SUSPENSION_MAX_FORCE = 300_000.0
DRIVE_FORCE = 90_000.0
REVERSE_FORCE = 62_000.0
ROLLING_RESISTANCE = 2.0
AIR_DRAG = 0.08
MAX_ANGULAR_SPEED = 18.0

HEAD_X_PX = 0.0
HEAD_Y_PX = 54.0
START_OFFSET_PX = WHEELBASE_PX + 8.0

_HALF_WHEELBASE = WHEELBASE_PX / 2.0
_WHEEL_OFFSETS = (-_HALF_WHEELBASE, _HALF_WHEELBASE)
_BODY_SAMPLES = (
    (-_HALF_WHEELBASE, -WHEEL_REST_LENGTH_PX),
    (0.0, -WHEEL_REST_LENGTH_PX),
    (_HALF_WHEELBASE, -WHEEL_REST_LENGTH_PX),
    (-_HALF_WHEELBASE, CHASSIS_HEIGHT_PX / 2.0),
    (_HALF_WHEELBASE, CHASSIS_HEIGHT_PX / 2.0),
)
_CONTACT_EPSILON_PX = 0.5
_PROJECTION_PASSES = 3


def drive_factor(speed_px_s: float) -> float:
    """Return the linear drive taper from full force to the speed cap."""
    if speed_px_s <= FULL_DRIVE_SPEED_PX_S:
        return 1.0
    if speed_px_s >= TOP_SPEED_PX_S:
        return 0.0
    return (TOP_SPEED_PX_S - speed_px_s) / (TOP_SPEED_PX_S - FULL_DRIVE_SPEED_PX_S)


class _Forces:
    """Reusable force accumulator for one vehicle step."""

    __slots__ = ("torque", "x", "y")

    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.torque = 0.0

    def reset(self) -> None:
        """Clear the accumulator without allocating."""
        self.x = 0.0
        self.y = 0.0
        self.torque = 0.0


class Vehicle:
    """A two-wheel chassis integrated at a fixed 120 Hz."""

    __slots__ = (
        "_contacts",
        "_forces",
        "_start_x",
        "omega",
        "theta",
        "vx",
        "vy",
        "x",
        "y",
    )

    def __init__(self, terrain: Terrain, x_px: float = START_OFFSET_PX) -> None:
        """Place the car above the terrain at a safe starting x."""
        self.x = max(x_px, START_OFFSET_PX)
        self.y = terrain.height_at(self.x) + WHEEL_REST_LENGTH_PX
        self.vx = 0.0
        self.vy = 0.0
        self.theta = 0.0
        self.omega = 0.0
        self._start_x = self.x
        self._contacts = [False, False]
        self._forces = _Forces()

    @property
    def speed_px_s(self) -> float:
        """Return the linear speed magnitude."""
        return math.sqrt(self.vx * self.vx + self.vy * self.vy)

    @property
    def distance_px(self) -> float:
        """Return horizontal distance travelled from the start."""
        return self.x - self._start_x

    @property
    def airborne(self) -> bool:
        """Return whether neither wheel is touching the terrain."""
        return not (self._contacts[0] or self._contacts[1])

    @property
    def left_contact(self) -> bool:
        """Return whether the rear wheel is touching the terrain."""
        return self._contacts[0]

    @property
    def right_contact(self) -> bool:
        """Return whether the front wheel is touching the terrain."""
        return self._contacts[1]

    def step(self, terrain: Terrain, throttle: float, brake: float) -> None:
        """Advance one fixed tick with semi-implicit Euler."""
        self._forces.reset()
        self._forces.y -= MASS_KG * GRAVITY_PX_S2
        self._forces.x -= AIR_DRAG * self.vx * abs(self.vx)
        self._forces.y -= AIR_DRAG * self.vy * abs(self.vy)
        for index, offset in enumerate(_WHEEL_OFFSETS):
            self._add_wheel_forces(terrain, index, offset, throttle, brake)
        self.vx += self._forces.x / MASS_KG * FIXED_DT
        self.vy += self._forces.y / MASS_KG * FIXED_DT
        self.omega += self._forces.torque / INERTIA * FIXED_DT
        self.omega = min(max(self.omega, -MAX_ANGULAR_SPEED), MAX_ANGULAR_SPEED)
        self.x += self.vx * FIXED_DT
        self.y += self.vy * FIXED_DT
        self.theta += self.omega * FIXED_DT
        self._limit_speed(brake)
        self._clamp_start_boundary()
        self._project_out_of_terrain(terrain)

    def _add_wheel_forces(
        self,
        terrain: Terrain,
        index: int,
        offset: float,
        throttle: float,
        brake: float,
    ) -> None:
        cos_theta = cosine(self.theta)
        sin_theta = sine(self.theta)
        mount_x = self.x + offset * cos_theta
        mount_y = self.y + offset * sin_theta
        ground_y = terrain.height_at(mount_x)
        clearance = mount_y - ground_y
        self._contacts[index] = clearance <= WHEEL_REST_LENGTH_PX + _CONTACT_EPSILON_PX
        if not self._contacts[index]:
            return
        grade = terrain.grade_at(mount_x)
        inverse_length = 1.0 / math.sqrt(1.0 + grade * grade)
        normal_x = -grade * inverse_length
        normal_y = inverse_length
        tangent_x = inverse_length
        tangent_y = grade * inverse_length
        radius_x = mount_x - self.x
        radius_y = ground_y - self.y
        contact_vx = self.vx - self.omega * radius_y
        contact_vy = self.vy + self.omega * radius_x
        normal_speed = contact_vx * normal_x + contact_vy * normal_y
        compression = WHEEL_REST_LENGTH_PX - clearance
        spring_force = SUSPENSION_SPRING * compression - SUSPENSION_DAMPING * normal_speed
        spring_force = min(max(spring_force, 0.0), SUSPENSION_MAX_FORCE)
        tangent_speed = contact_vx * tangent_x + contact_vy * tangent_y
        drive = self._drive_force(tangent_speed, throttle, brake)
        drive -= ROLLING_RESISTANCE * tangent_speed
        force_x = normal_x * spring_force + tangent_x * drive
        force_y = normal_y * spring_force + tangent_y * drive
        self._forces.x += force_x
        self._forces.y += force_y
        self._forces.torque += radius_x * force_y - radius_y * force_x

    @staticmethod
    def _drive_force(speed_px_s: float, throttle: float, brake: float) -> float:
        force = 0.0
        if throttle > 0.0 and speed_px_s < TOP_SPEED_PX_S:
            force += DRIVE_FORCE * throttle * drive_factor(max(speed_px_s, 0.0))
        if brake > 0.0 and speed_px_s > -REVERSE_CAP_PX_S:
            force -= REVERSE_FORCE * brake
        return force

    def _limit_speed(self, brake: float) -> None:
        if brake > 0.0:
            self.vx = max(self.vx, -REVERSE_CAP_PX_S)
        speed_squared = self.vx * self.vx + self.vy * self.vy
        if speed_squared > TOP_SPEED_PX_S * TOP_SPEED_PX_S:
            scale = TOP_SPEED_PX_S / math.sqrt(speed_squared)
            self.vx *= scale
            self.vy *= scale

    def _clamp_start_boundary(self) -> None:
        if self.x < START_OFFSET_PX:
            self.x = START_OFFSET_PX
            self.vx = max(self.vx, 0.0)

    def _project_out_of_terrain(self, terrain: Terrain) -> None:
        corrected = False
        cos_theta = cosine(self.theta)
        sin_theta = sine(self.theta)
        for _ in range(_PROJECTION_PASSES):
            penetration = 0.0
            for local_x, local_y in _BODY_SAMPLES:
                sample_x = self.x + local_x * cos_theta - local_y * sin_theta
                sample_y = self.y + local_x * sin_theta + local_y * cos_theta
                depth = terrain.height_at(sample_x) - sample_y
                penetration = max(penetration, depth)
            if penetration <= 0.0:
                break
            self.y += penetration
            corrected = True
        if corrected and self.vy < 0.0:
            self.vy = 0.0

    def head_touches_terrain(self, terrain: Terrain) -> bool:
        """Return whether the driver head vertex is at or below terrain."""
        cos_theta = cosine(self.theta)
        sin_theta = sine(self.theta)
        head_x = self.x + HEAD_X_PX * cos_theta - HEAD_Y_PX * sin_theta
        head_y = self.y + HEAD_X_PX * sin_theta + HEAD_Y_PX * cos_theta
        return head_y <= terrain.height_at(head_x)

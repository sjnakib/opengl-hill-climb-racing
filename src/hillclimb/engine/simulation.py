"""Headless orchestration of one deterministic engine run."""

from __future__ import annotations

from dataclasses import dataclass

from .difficulty import fuel_drain_factor
from .fuel import FuelTank
from .rng import RngStreams
from .scoring import ScoreLedger
from .terrain import Terrain
from .vehicle import FIXED_DT, REST_SPEED_PX_S, Vehicle
from .world import World


@dataclass(frozen=True, slots=True)
class InputSegment:
    """A half-open tick range with fixed throttle and brake values."""

    start_tick: int
    end_tick: int
    throttle: float
    brake: float


@dataclass(frozen=True, slots=True)
class ScriptedInput:
    """A deterministic input schedule for tests and the selftest."""

    segments: tuple[InputSegment, ...] = ()

    def validate(self, max_ticks: int) -> None:
        """Reject schedules with negative or overlapping tick ranges."""
        previous_end = 0
        for segment in self.segments:
            if segment.start_tick < previous_end or segment.end_tick < segment.start_tick:
                message = "input segments must be ordered and non-overlapping"
                raise ValueError(message)
            if segment.start_tick < 0 or segment.end_tick > max_ticks:
                message = "input segment lies outside the run"
                raise ValueError(message)
            previous_end = segment.end_tick


@dataclass(frozen=True, slots=True)
class RunResult:
    """Final observable state of a simulated run."""

    ticks: int
    score: int
    distance_px: float
    fuel_litres: float
    game_over: bool
    coins: int
    flips: int
    airtime_bonus: int
    flip_bonus: int

    def canonical_payload(self) -> dict[str, object]:
        """Return the fields that replay tests compare across platforms."""
        return {"score": self.score, "distance_px": format(self.distance_px, ".17g")}


class Simulation:
    """Terrain, car, pickups, fuel, and score for one seed."""

    __slots__ = (
        "elapsed_ticks",
        "fuel",
        "game_over",
        "scoring",
        "terrain",
        "vehicle",
        "world",
    )

    def __init__(self, master_seed: int, *, streams: RngStreams | None = None) -> None:
        """Build every engine subsystem from one master seed."""
        registry = RngStreams(master_seed) if streams is None else streams
        self.terrain = Terrain(master_seed, streams=registry)
        self.vehicle = Vehicle(self.terrain)
        self.world = World(master_seed, self.terrain, streams=registry)
        self.fuel = FuelTank()
        self.scoring = ScoreLedger()
        self.elapsed_ticks = 0
        self.game_over = False

    @property
    def score(self) -> int:
        """Return the current score."""
        return self.scoring.score

    @property
    def distance_px(self) -> float:
        """Return horizontal distance from the starting position."""
        return self.vehicle.distance_px

    def step(self, throttle: float, brake: float) -> None:
        """Advance one fixed tick if the run is still active."""
        if self.game_over:
            return
        self.vehicle.step(
            self.terrain,
            min(max(throttle, 0.0), 1.0),
            min(max(brake, 0.0), 1.0),
        )
        factor = fuel_drain_factor(max(self.vehicle.distance_px, 0.0))
        self.fuel.drain(FIXED_DT, self.vehicle.speed_px_s, factor)
        pickups = self.world.collect(self.vehicle.x, self.vehicle.y)
        if pickups.coin_value:
            self.scoring.add_coins(pickups.coin_value)
        if pickups.fuel_cans:
            self.fuel.refill()
        self.scoring.advance(airborne=self.vehicle.airborne, angle_radians=self.vehicle.theta)
        self.elapsed_ticks += 1
        self._update_game_over()

    def run(self, max_ticks: int, plan: ScriptedInput | None = None) -> RunResult:
        """Run for at most max_ticks, following an optional scripted plan."""
        if max_ticks < 0:
            message = "max_ticks must be non-negative"
            raise ValueError(message)
        schedule = ScriptedInput() if plan is None else plan
        schedule.validate(max_ticks)
        tick = 0
        for segment in schedule.segments:
            while tick < segment.end_tick and not self.game_over:
                self.step(segment.throttle, segment.brake)
                tick += 1
            if self.game_over:
                break
        while tick < max_ticks and not self.game_over:
            self.step(0.0, 0.0)
            tick += 1
        return self.result

    @property
    def result(self) -> RunResult:
        """Snapshot the current run as an immutable result."""
        return RunResult(
            ticks=self.elapsed_ticks,
            score=self.scoring.score,
            distance_px=self.vehicle.distance_px,
            fuel_litres=self.fuel.fuel,
            game_over=self.game_over,
            coins=self.scoring.coin_score,
            flips=self.scoring.flips,
            airtime_bonus=self.scoring.airtime_bonus,
            flip_bonus=self.scoring.flip_bonus,
        )

    def _update_game_over(self) -> None:
        speed = self.vehicle.speed_px_s
        rested = self.fuel.empty and not self.vehicle.airborne and speed <= REST_SPEED_PX_S
        head_hit = speed > REST_SPEED_PX_S and self.vehicle.head_touches_terrain(self.terrain)
        if rested or head_hit:
            self.game_over = True

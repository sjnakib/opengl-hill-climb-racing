"""Application entry points. The playable loop lands in a later milestone."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, replace

from ..config import Config, ConfigStore
from ..engine.fuel import MAX_FUEL_LITRES
from ..engine.simulation import InputSegment, ScriptedInput, Simulation
from ..engine.vehicle import TICK_RATE_HZ
from .state import GameState, StateMachine

_LOGGER = logging.getLogger(__name__)

SIMULATION_HZ = TICK_RATE_HZ
SELFTEST_MAX_SECONDS = 5
SAFE_MODE_WIDTH = 800
SAFE_MODE_HEIGHT = 450
SELFTEST_DRIVE_TICKS = 4 * SIMULATION_HZ
SELFTEST_PLAN = ScriptedInput(
    (
        InputSegment(0, SELFTEST_DRIVE_TICKS, 1.0, 0.0),
        InputSegment(SELFTEST_DRIVE_TICKS, SELFTEST_MAX_SECONDS * SIMULATION_HZ, 0.0, 0.6),
    )
)


@dataclass(frozen=True, slots=True)
class LaunchOptions:
    """Options chosen by the CLI before any window is opened."""

    seed: int
    safe_mode: bool
    config: Config


def build_launch_options(
    seed: int, *, safe_mode: bool, store: ConfigStore | None = None
) -> LaunchOptions:
    """Load settings, or build default safe-mode settings without touching disk."""
    if safe_mode:
        config = replace(
            Config(),
            window_width=SAFE_MODE_WIDTH,
            window_height=SAFE_MODE_HEIGHT,
            master_volume=0,
            music_volume=0,
            sfx_volume=0,
        )
    else:
        config = (store if store is not None else ConfigStore()).load()
    return LaunchOptions(seed=seed, safe_mode=safe_mode, config=config)


def run_selftest(seed: int) -> None:
    """Drive a headless simulation for at most five simulated seconds."""
    machine = StateMachine()
    machine.transition(GameState.MENU)
    machine.transition(GameState.PLAY)
    simulation = Simulation(seed)
    result = simulation.run(SELFTEST_MAX_SECONDS * SIMULATION_HZ, SELFTEST_PLAN)
    vehicle = simulation.vehicle
    values = (vehicle.x, vehicle.y, vehicle.vx, vehicle.vy, vehicle.theta, vehicle.omega)
    if not all(math.isfinite(value) for value in values):
        message = "selftest produced a non-finite vehicle state"
        raise RuntimeError(message)
    if not 0.0 <= result.fuel_litres <= MAX_FUEL_LITRES:
        message = f"selftest fuel left the legal range: {result.fuel_litres!r}"
        raise RuntimeError(message)
    if result.ticks <= 0 or result.score < 0 or result.distance_px < 0.0:
        message = f"selftest produced an invalid result: {result!r}"
        raise RuntimeError(message)
    machine.transition(GameState.GAMEOVER)
    machine.transition(GameState.PLAY)


def run_app(options: LaunchOptions) -> int:
    """Run the game loop. A stub keeps the CLI contract testable for now."""
    _LOGGER.info(
        "game loop not implemented yet: seed=%d safe_mode=%s window=%dx%d",
        options.seed,
        options.safe_mode,
        options.config.window_width,
        options.config.window_height,
    )
    return 0

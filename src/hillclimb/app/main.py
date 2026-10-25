"""Application entry points. The playable loop lands in a later milestone."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, replace

from ..config import Config, ConfigStore
from ..engine.rng import STREAM_NAMES, RngStreams
from ..engine.terrain import Terrain
from .state import GameState, StateMachine

_LOGGER = logging.getLogger(__name__)

SIMULATION_HZ = 120
SELFTEST_MAX_SECONDS = 5
SELFTEST_SPEED_PX_PER_S = 500.0
SAFE_MODE_WIDTH = 800
SAFE_MODE_HEIGHT = 450


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
    """Run a headless simulation pass of five simulated seconds."""
    streams = RngStreams(seed)
    for name in sorted(STREAM_NAMES):
        streams.stream(name)
    terrain = Terrain(seed)
    machine = StateMachine()
    machine.transition(GameState.MENU)
    machine.transition(GameState.PLAY)
    frame_seconds = 1.0 / SIMULATION_HZ
    position_px = 0.0
    for _ in range(SELFTEST_MAX_SECONDS * SIMULATION_HZ):
        height = terrain.height_at(position_px)
        if not math.isfinite(height):
            message = f"terrain height is not finite at x={position_px:.3f}"
            raise RuntimeError(message)
        position_px += SELFTEST_SPEED_PX_PER_S * frame_seconds
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

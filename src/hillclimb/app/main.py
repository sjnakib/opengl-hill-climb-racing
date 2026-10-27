"""Application entry points and the fixed-timestep game loop (SPECS §6, §8)."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Protocol

from ..config import Config, ConfigStore
from ..engine.fuel import MAX_FUEL_LITRES
from ..engine.simulation import InputSegment, ScriptedInput, Simulation
from ..engine.vehicle import FIXED_DT, TICK_RATE_HZ
from .state import GameState, StateMachine

if TYPE_CHECKING:
    from collections.abc import Callable

type Clock = Callable[[], float]

MAX_FRAME_TIME_S = 0.1
MAX_CATCHUP_TICKS = 25

SELFTEST_MAX_SECONDS = 5
SELFTEST_MAX_FRAMES = SELFTEST_MAX_SECONDS * TICK_RATE_HZ
SAFE_MODE_WIDTH = 800
SAFE_MODE_HEIGHT = 450
SELFTEST_DRIVE_TICKS = 4 * TICK_RATE_HZ
SELFTEST_PLAN = ScriptedInput(
    (
        InputSegment(0, SELFTEST_DRIVE_TICKS, 1.0, 0.0),
        InputSegment(SELFTEST_DRIVE_TICKS, SELFTEST_MAX_FRAMES, 0.0, 0.6),
    )
)


@dataclass(frozen=True, slots=True)
class LaunchOptions:
    """Options chosen by the CLI before any window is opened."""

    seed: int
    safe_mode: bool
    config: Config


@dataclass(frozen=True, slots=True)
class InputSignals:
    """One frame of input levels and one-frame edge flags."""

    accelerate: float = 0.0
    brake: float = 0.0
    pressed_pause: bool = False
    pressed_restart: bool = False
    pressed_confirm: bool = False
    pressed_back: bool = False


@dataclass(frozen=True, slots=True)
class LoopLimits:
    """Optional bounds for one loop run."""

    max_frames: int | None = None
    stop: Callable[[], bool] | None = None


@dataclass(slots=True)
class LoopState:
    """Mutable state owned by one application session."""

    machine: StateMachine
    simulation: Simulation
    seed: int
    previous_s: float
    accumulator: float = 0.0
    frames: int = 0

    @classmethod
    def create(cls, seed: int, *, clock: Clock) -> LoopState:
        """Build a MENU session with a fresh simulation and clock origin."""
        machine = StateMachine()
        machine.transition(GameState.MENU)
        return cls(
            machine=machine,
            simulation=Simulation(seed),
            seed=seed,
            previous_s=clock(),
        )

    @property
    def state(self) -> GameState:
        """Return the current game state."""
        return self.machine.state


@dataclass(frozen=True, slots=True)
class LoopResult:
    """Observable result of a loop run."""

    state: GameState
    simulation: Simulation
    frames: int


class SyntheticClock:
    """Headless clock that advances one simulation tick per read."""

    __slots__ = ("_seconds",)

    def __init__(self) -> None:
        """Start just before the first frame."""
        self._seconds = 0.0

    def __call__(self) -> float:
        """Return the next tick boundary in seconds."""
        self._seconds += FIXED_DT
        return self._seconds


class PygameClock:
    """Clock backed by pygame's millisecond timer."""

    __slots__ = ("_get_ticks",)

    def __init__(self, get_ticks: Callable[[], int]) -> None:
        """Store the timer callback supplied by pygame."""
        self._get_ticks = get_ticks

    def __call__(self) -> float:
        """Return the current time in seconds."""
        return self._get_ticks() / 1000.0


class Presenter(Protocol):
    """Port for drawing one frame."""

    def present(self) -> None:
        """Show the current frame."""
        ...


class NullPresenter:
    """Presenter that draws nothing for headless runs."""

    __slots__ = ()

    def present(self) -> None:
        """Do nothing."""


class InputPort(Protocol):
    """Port for sampling one frame of input."""

    def sample(self) -> InputSignals:
        """Return the levels and edge flags for this frame."""
        ...


class _SelftestInput:
    """Headless input port that follows the fixed selftest schedule."""

    __slots__ = ("_confirmed", "_state")

    def __init__(self, state: LoopState) -> None:
        """Follow the simulation owned by this session."""
        self._state = state
        self._confirmed = False

    def sample(self) -> InputSignals:
        """Return this tick's levels and the initial confirm edge."""
        tick = self._state.simulation.elapsed_ticks
        accelerate = 0.0
        brake = 0.0
        for segment in SELFTEST_PLAN.segments:
            if segment.start_tick <= tick < segment.end_tick:
                accelerate = segment.throttle
                brake = segment.brake
                break
        confirm = not self._confirmed
        self._confirmed = True
        return InputSignals(
            accelerate=accelerate,
            brake=brake,
            pressed_confirm=confirm,
        )


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


def plan_frame_ticks(accumulator: float, elapsed_s: float) -> tuple[int, float]:
    """Clamp one frame and return the ticks to run plus the carried remainder."""
    elapsed = min(max(elapsed_s, 0.0), MAX_FRAME_TIME_S)
    pending = max(accumulator, 0.0) + elapsed
    ticks = min(int(pending / FIXED_DT), MAX_CATCHUP_TICKS)
    remainder = pending - ticks * FIXED_DT
    if remainder < 0.0 or remainder >= FIXED_DT:
        remainder = 0.0
    return ticks, remainder


def _play_transition(signals: InputSignals, *, game_over: bool) -> GameState | None:
    if game_over:
        return GameState.GAMEOVER
    return GameState.PAUSED if signals.pressed_pause else None


def _paused_transition(signals: InputSignals) -> GameState | None:
    if signals.pressed_pause:
        return GameState.PLAY
    return GameState.MENU if signals.pressed_back else None


def _menu_transition(signals: InputSignals) -> GameState | None:
    return GameState.PLAY if signals.pressed_confirm else None


def _gameover_transition(signals: InputSignals) -> GameState | None:
    if signals.pressed_restart:
        return GameState.PLAY
    return GameState.MENU if signals.pressed_back else None


def planned_transition(
    state: GameState, signals: InputSignals, *, game_over: bool
) -> GameState | None:
    """Return the state the loop should enter, or None to stay put."""
    if state is GameState.PLAY:
        return _play_transition(signals, game_over=game_over)
    if state is GameState.PAUSED:
        return _paused_transition(signals)
    if state is GameState.MENU:
        return _menu_transition(signals)
    if state is GameState.GAMEOVER:
        return _gameover_transition(signals)
    return None


def _restart_run(state: LoopState) -> None:
    """Replace the simulation and clear carried time for a new run."""
    state.simulation = Simulation(state.seed)
    state.accumulator = 0.0


def _apply_input(state: LoopState, signals: InputSignals) -> None:
    """Apply state-changing edges before the simulation advances."""
    current = state.machine.state
    target = planned_transition(
        current,
        signals,
        game_over=state.simulation.game_over,
    )
    if target is not None:
        state.machine.transition(target)
        if target is GameState.PLAY:
            if current is not GameState.PAUSED:
                _restart_run(state)
        else:
            state.accumulator = 0.0
        return
    if current is GameState.PLAY and signals.pressed_restart:
        _restart_run(state)


def _step_play(state: LoopState, signals: InputSignals, ticks: int) -> None:
    """Advance the simulation for this frame, stopping at game over."""
    for _ in range(ticks):
        state.simulation.step(signals.accelerate, signals.brake)
        if state.simulation.game_over:
            state.machine.transition(GameState.GAMEOVER)
            state.accumulator = 0.0
            return


def _limit_reached(state: LoopState, limits: LoopLimits) -> bool:
    """Return whether a frame limit or stop predicate ends the loop."""
    if limits.max_frames is not None and state.frames >= limits.max_frames:
        return True
    return limits.stop is not None and limits.stop()


def run_loop(
    state: LoopState,
    clock: Clock,
    input_port: InputPort,
    presenter: Presenter,
    limits: LoopLimits | None = None,
) -> LoopResult:
    """Run frames until the frame limit or stop predicate asks to quit."""
    while limits is None or not _limit_reached(state, limits):
        now = clock()
        elapsed = now - state.previous_s
        state.previous_s = now
        signals = input_port.sample()
        if limits is not None and limits.stop is not None and limits.stop():
            break
        _apply_input(state, signals)
        if state.machine.state is GameState.PLAY:
            ticks, state.accumulator = plan_frame_ticks(state.accumulator, elapsed)
            if ticks:
                _step_play(state, signals, ticks)
        else:
            state.accumulator = 0.0
        presenter.present()
        state.frames += 1
    return LoopResult(
        state=state.machine.state,
        simulation=state.simulation,
        frames=state.frames,
    )


def run_selftest(seed: int) -> None:
    """Drive the real loop headlessly for at most five simulated seconds."""
    clock = SyntheticClock()
    state = LoopState.create(seed, clock=clock)
    result = run_loop(
        state,
        clock,
        _SelftestInput(state),
        NullPresenter(),
        LoopLimits(max_frames=SELFTEST_MAX_FRAMES),
    )
    simulation = result.simulation
    vehicle = simulation.vehicle
    values = (vehicle.x, vehicle.y, vehicle.vx, vehicle.vy, vehicle.theta, vehicle.omega)
    if not all(math.isfinite(value) for value in values):
        message = "selftest produced a non-finite vehicle state"
        raise RuntimeError(message)
    run = simulation.result
    if not 0.0 <= run.fuel_litres <= MAX_FUEL_LITRES:
        message = f"selftest fuel left the legal range: {run.fuel_litres!r}"
        raise RuntimeError(message)
    if run.ticks <= 0 or run.score < 0 or run.distance_px < 0.0:
        message = f"selftest produced an invalid result: {run!r}"
        raise RuntimeError(message)


def run_app(options: LaunchOptions) -> int:
    """Run the playable application until the player closes the window."""
    import pygame  # noqa: PLC0415 - the headless selftest must not import pygame

    from .audio import AudioBackend, pre_init_mixer  # noqa: PLC0415
    from .input import PygameInput  # noqa: PLC0415
    from .render import PygamePresenter  # noqa: PLC0415

    pre_init_mixer()
    pygame.init()
    audio = AudioBackend(options.config)
    input_port: PygameInput | None = None
    try:
        input_port = PygameInput()
        presenter = PygamePresenter(options.config)
        audio.start()
        clock = PygameClock(pygame.time.get_ticks)
        state = LoopState.create(options.seed, clock=clock)
        run_loop(
            state,
            clock,
            input_port,
            presenter,
            LoopLimits(stop=input_port.quit_requested),
        )
    finally:
        audio.stop()
        if input_port is not None:
            input_port.close()
        pygame.quit()
    return 0

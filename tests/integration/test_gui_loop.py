"""Headless gui tests for the real application loop (SPECS §12)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import pygame
import pytest

from hillclimb.app import input as app_input
from hillclimb.app.audio import AudioBackend, pre_init_mixer
from hillclimb.app.input import PygameInput
from hillclimb.app.main import (
    LaunchOptions,
    LoopLimits,
    LoopState,
    SyntheticClock,
    run_app,
    run_loop,
)
from hillclimb.app.render import PygamePresenter
from hillclimb.app.state import GameState
from hillclimb.config import Config
from hillclimb.engine.simulation import Simulation

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = pytest.mark.gui

_CONFIG = Config(window_width=800, window_height=450)


@pytest.fixture(autouse=True)
def pygame_runtime() -> Iterator[None]:
    """Skip without SDL video and reset pygame after every test."""
    try:
        pygame.display.init()
    except pygame.error as error:
        pytest.skip(f"SDL video unavailable: {error}")
    pygame.init()
    pygame.event.clear()
    yield
    pygame.quit()


@pytest.fixture
def input_port() -> Iterator[PygameInput]:
    """Open a real input port and close it after the test."""
    port = PygameInput()
    yield port
    port.close()


@pytest.fixture
def presenter() -> PygamePresenter:
    """Open the configured flat-color window."""
    return PygamePresenter(_CONFIG)


def _state(seed: int = 7) -> tuple[LoopState, SyntheticClock]:
    clock = SyntheticClock()
    return LoopState.create(seed, clock=clock), clock


def _run_frames(
    state: LoopState,
    clock: SyntheticClock,
    input_port: PygameInput,
    presenter: PygamePresenter,
    count: int = 1,
) -> None:
    run_loop(
        state,
        clock,
        input_port,
        presenter,
        LoopLimits(max_frames=state.frames + count),
    )


def _post_key(key: int) -> None:
    pygame.event.post(
        pygame.event.Event(
            pygame.KEYDOWN,
            key=key,
            mod=0,
            unicode="",
            scancode=0,
        )
    )


def _post_pad(button: int) -> None:
    pygame.event.post(
        pygame.event.Event(
            pygame.CONTROLLERBUTTONDOWN,
            button=button,
            instance_id=0,
        )
    )


def _assert_state(state: LoopState, expected: GameState) -> None:
    assert state.state is expected


class _Pressed:
    __slots__ = ("_keys",)

    def __init__(self, keys: set[int]) -> None:
        self._keys = keys

    def __getitem__(self, key: int) -> bool:
        return key in self._keys


class _FakePad:
    __slots__ = ()

    def get_button(self, button: int) -> bool:
        return button in (app_input.PAD_ACCELERATE, app_input.PAD_BRAKE)


def test_gui_boot_lands_in_menu_with_a_window(
    input_port: PygameInput, presenter: PygamePresenter
) -> None:
    state, clock = _state()
    assert state.state is GameState.MENU
    assert pygame.display.get_surface() is not None
    _run_frames(state, clock, input_port, presenter)
    _assert_state(state, GameState.MENU)
    assert state.frames == 1


def test_gui_confirm_enters_play(input_port: PygameInput, presenter: PygamePresenter) -> None:
    state, clock = _state()
    _post_key(pygame.K_RETURN)
    _run_frames(state, clock, input_port, presenter)
    _assert_state(state, GameState.PLAY)
    assert state.simulation.elapsed_ticks == 1


def test_gui_escape_pauses_and_resumes_the_same_run(
    input_port: PygameInput, presenter: PygamePresenter
) -> None:
    state, clock = _state()
    _post_key(pygame.K_RETURN)
    _run_frames(state, clock, input_port, presenter)
    simulation = state.simulation
    ticks = simulation.elapsed_ticks
    _post_key(pygame.K_ESCAPE)
    _run_frames(state, clock, input_port, presenter)
    _assert_state(state, GameState.PAUSED)
    assert state.simulation is simulation
    assert simulation.elapsed_ticks == ticks
    _post_key(pygame.K_ESCAPE)
    _run_frames(state, clock, input_port, presenter, count=2)
    _assert_state(state, GameState.PLAY)
    assert state.simulation is simulation
    assert simulation.elapsed_ticks > ticks


def test_gui_restart_keeps_the_seed(input_port: PygameInput, presenter: PygamePresenter) -> None:
    state, clock = _state()
    _post_key(pygame.K_RETURN)
    _run_frames(state, clock, input_port, presenter)
    old_simulation = state.simulation
    _post_key(pygame.K_r)
    _run_frames(state, clock, input_port, presenter)
    _assert_state(state, GameState.PLAY)
    assert state.simulation is not old_simulation
    assert state.simulation.elapsed_ticks == 1
    reference = Simulation(7)
    assert state.simulation.terrain.height_at(1234.0) == reference.terrain.height_at(1234.0)


def test_gui_game_over_then_restart_starts_a_new_run(
    input_port: PygameInput, presenter: PygamePresenter
) -> None:
    state, clock = _state(seed=7)
    _post_key(pygame.K_RETURN)
    _run_frames(state, clock, input_port, presenter)
    state.simulation.fuel.fuel = 0.0
    _run_frames(state, clock, input_port, presenter, count=10)
    _assert_state(state, GameState.GAMEOVER)
    finished = state.simulation
    assert finished.game_over
    _post_key(pygame.K_r)
    _run_frames(state, clock, input_port, presenter, count=2)
    _assert_state(state, GameState.PLAY)
    assert state.simulation is not finished
    assert state.simulation.elapsed_ticks > 0


def test_gui_input_reads_keyboard_edges_and_quit(input_port: PygameInput) -> None:
    _post_key(pygame.K_ESCAPE)
    first = input_port.sample()
    assert first.pressed_pause
    assert first.pressed_back
    assert not first.pressed_restart
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r, repeat=True))
    repeated = input_port.sample()
    assert not repeated.pressed_restart
    _post_key(pygame.K_r)
    _post_key(pygame.K_KP_ENTER)
    second = input_port.sample()
    assert second.pressed_restart
    assert second.pressed_confirm
    assert not second.pressed_pause
    third = input_port.sample()
    assert not third.pressed_pause
    assert not third.pressed_restart
    assert not third.pressed_confirm
    assert not third.pressed_back
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    input_port.sample()
    assert input_port.quit_requested()


def test_gui_input_reads_held_keyboard_levels(
    input_port: PygameInput, monkeypatch: pytest.MonkeyPatch
) -> None:
    pressed = _Pressed({pygame.K_RIGHT, pygame.K_a})
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: pressed)
    signals = input_port.sample()
    assert signals.accelerate == 1.0
    assert signals.brake == 1.0


def test_gui_input_reads_gamepad_edges_and_levels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_controller(_index: int) -> _FakePad:
        return _FakePad()

    fake = SimpleNamespace(
        init=lambda: None,
        quit=lambda: None,
        get_count=lambda: 1,
        Controller=fake_controller,
    )
    monkeypatch.setattr(app_input, "controller", fake)
    port = PygameInput()
    try:
        _post_pad(app_input.PAD_PAUSE)
        _post_pad(app_input.PAD_RESTART)
        _post_pad(app_input.PAD_CONFIRM)
        _post_pad(app_input.PAD_BACK)
        signals = port.sample()
        assert signals.pressed_pause
        assert signals.pressed_restart
        assert signals.pressed_confirm
        assert signals.pressed_back
        assert signals.accelerate == 1.0
        assert signals.brake == 1.0
    finally:
        port.close()


def test_gui_audio_applies_bus_gains_and_stops() -> None:
    pygame.mixer.quit()
    pre_init_mixer()
    backend = AudioBackend(Config(master_volume=50, music_volume=60, sfx_volume=80))
    backend.stop()
    backend.apply_volumes()
    backend.start()
    try:
        if pygame.mixer.get_init() is None:
            pytest.skip("mixer unavailable")
        assert pygame.mixer.get_init() == (44100, -16, 2)
        assert pygame.mixer.get_num_channels() == 8
        assert pygame.mixer.music.get_volume() == pytest.approx(0.3, abs=1.0 / 128.0)
        assert pygame.mixer.Channel(0).get_volume() == pytest.approx(0.4, abs=1.0 / 128.0)
    finally:
        backend.stop()
    assert pygame.mixer.get_init() is None


def test_gui_audio_tolerates_a_missing_device(monkeypatch: pytest.MonkeyPatch) -> None:
    pygame.mixer.quit()

    def fail(**_kwargs: object) -> None:
        message = "no audio device"
        raise pygame.error(message)

    monkeypatch.setattr(pygame.mixer, "init", fail)
    backend = AudioBackend(Config())
    backend.start()
    backend.stop()
    assert pygame.mixer.get_init() is None


def test_gui_presenter_honors_fullscreen_flag() -> None:
    presenter = PygamePresenter(Config(window_width=800, window_height=450, fullscreen=True))
    presenter.present()
    assert pygame.display.get_surface() is not None


def test_gui_run_app_returns_zero_on_quit() -> None:
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    options = LaunchOptions(
        seed=7,
        safe_mode=True,
        config=Config(
            window_width=800,
            window_height=450,
            master_volume=0,
            music_volume=0,
            sfx_volume=0,
        ),
    )
    assert run_app(options) == 0
    assert pygame.display.get_surface() is None
    assert pygame.mixer.get_init() is None

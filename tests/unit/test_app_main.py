"""Unit tests for the headless application entry points."""

from __future__ import annotations

import math
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

import hillclimb.app.main as app_main
from hillclimb.app.main import (
    LaunchOptions,
    LoopResult,
    NullPresenter,
    PygameClock,
    SyntheticClock,
    build_launch_options,
    run_selftest,
)
from hillclimb.app.state import GameState
from hillclimb.config import Config, ConfigStore
from hillclimb.engine.simulation import Simulation
from hillclimb.engine.vehicle import FIXED_DT

if TYPE_CHECKING:
    from pathlib import Path


def test_build_launch_options_loads_the_store(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    store.save(Config(master_volume=7))
    options = build_launch_options(11, safe_mode=False, store=store)
    assert options == LaunchOptions(seed=11, safe_mode=False, config=Config(master_volume=7))


def test_safe_mode_never_reads_the_store(tmp_path: Path) -> None:
    options = build_launch_options(1, safe_mode=True, store=ConfigStore(tmp_path))
    assert options.seed == 1
    assert options.safe_mode is True
    assert options.config.window_width == 800
    assert options.config.window_height == 450
    assert options.config.master_volume == 0
    assert options.config.music_volume == 0
    assert options.config.sfx_volume == 0


@pytest.mark.parametrize("seed", [0, 1, 2026])
def test_selftest_runs_headless(seed: int) -> None:
    run_selftest(seed)


def test_selftest_does_not_load_pygame() -> None:
    script = (
        "import sys\n"
        "from hillclimb.app.main import run_selftest\n"
        "run_selftest(11)\n"
        "assert 'pygame' not in sys.modules\n"
    )
    result = subprocess.run(  # noqa: S603 - fixed interpreter and fixed script
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_synthetic_clock_advances_one_tick_per_read() -> None:
    clock = SyntheticClock()
    assert clock() == pytest.approx(FIXED_DT)
    assert clock() == pytest.approx(2.0 * FIXED_DT)


def test_pygame_clock_converts_milliseconds_to_seconds() -> None:
    assert PygameClock(lambda: 1500)() == pytest.approx(1.5)


def test_null_presenter_draws_nothing() -> None:
    NullPresenter().present()


def _stub_run_loop(monkeypatch: pytest.MonkeyPatch, simulation: Simulation) -> None:
    def fake_run_loop(*_args: object, **_kwargs: object) -> LoopResult:
        return LoopResult(state=GameState.PLAY, simulation=simulation, frames=1)

    monkeypatch.setattr(app_main, "run_loop", fake_run_loop)


def test_selftest_rejects_a_non_finite_vehicle(monkeypatch: pytest.MonkeyPatch) -> None:
    simulation = Simulation(0)
    simulation.vehicle.x = math.nan
    _stub_run_loop(monkeypatch, simulation)
    with pytest.raises(RuntimeError, match="non-finite"):
        run_selftest(0)


def test_selftest_rejects_fuel_outside_the_tank(monkeypatch: pytest.MonkeyPatch) -> None:
    simulation = Simulation(0)
    simulation.fuel.fuel = -1.0
    _stub_run_loop(monkeypatch, simulation)
    with pytest.raises(RuntimeError, match="fuel left the legal range"):
        run_selftest(0)


def test_selftest_rejects_an_empty_result(monkeypatch: pytest.MonkeyPatch) -> None:
    simulation = Simulation(0)
    _stub_run_loop(monkeypatch, simulation)
    with pytest.raises(RuntimeError, match="invalid result"):
        run_selftest(0)

"""Unit tests for the headless application entry points."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from hillclimb.app.main import LaunchOptions, build_launch_options, run_app, run_selftest
from hillclimb.config import Config, ConfigStore

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


def test_run_app_stub_returns_zero() -> None:
    assert run_app(LaunchOptions(seed=0, safe_mode=True, config=Config())) == 0

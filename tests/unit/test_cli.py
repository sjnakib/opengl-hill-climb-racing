"""Unit tests for the CLI contract (SPECS §10.7)."""

from __future__ import annotations

import pytest

import hillclimb.__main__ as cli
from hillclimb import __version__
from hillclimb.app.main import LaunchOptions
from hillclimb.config import Config, ConfigStore


def test_version_prints_installed_metadata(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["--version"]) == 0
    assert capsys.readouterr().out == f"hillclimb {__version__}\n"


def test_selftest_exits_zero() -> None:
    assert cli.main(["--selftest", "--seed", "7"]) == 0


def test_selftest_failure_exits_three(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(_seed: int) -> None:
        message = "simulated failure"
        raise RuntimeError(message)

    monkeypatch.setattr(cli, "run_selftest", fail)
    assert cli.main(["--selftest"]) == 3


def test_safe_mode_overrides_window_and_audio(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[LaunchOptions] = []

    def capture(options: LaunchOptions) -> int:
        captured.append(options)
        return 0

    monkeypatch.setattr(cli, "run_app", capture)
    assert cli.main(["--safe-mode", "--seed", "42"]) == 0
    options = captured[0]
    assert options.seed == 42
    assert options.safe_mode is True
    assert options.config.window_width == 800
    assert options.config.window_height == 450
    assert (options.config.master_volume, options.config.music_volume) == (0, 0)
    assert options.config.sfx_volume == 0


def test_normal_run_passes_built_options(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = LaunchOptions(seed=5, safe_mode=False, config=Config(master_volume=10))
    seen: list[LaunchOptions] = []

    def fake_build(
        seed: int, *, safe_mode: bool, store: ConfigStore | None = None
    ) -> LaunchOptions:
        assert seed == 5
        assert safe_mode is False
        assert store is None
        return expected

    def capture(options: LaunchOptions) -> int:
        seen.append(options)
        return 0

    monkeypatch.setattr(cli, "build_launch_options", fake_build)
    monkeypatch.setattr(cli, "run_app", capture)
    assert cli.main(["--seed", "5"]) == 0
    assert seen == [expected]


def test_default_seed_is_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    seeds: list[int] = []

    def fake_build(
        seed: int, *, safe_mode: bool, store: ConfigStore | None = None
    ) -> LaunchOptions:
        seeds.append(seed)
        assert safe_mode is False
        assert store is None
        return LaunchOptions(seed=seed, safe_mode=False, config=Config())

    monkeypatch.setattr(cli, "build_launch_options", fake_build)
    monkeypatch.setattr(cli, "run_app", lambda _options: 0)
    assert cli.main([]) == 0
    assert seeds == [0]


def test_non_integer_seed_is_rejected() -> None:
    with pytest.raises(SystemExit):
        cli.main(["--seed", "not-a-number"])

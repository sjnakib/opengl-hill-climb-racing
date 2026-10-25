"""Integration tests for the installed module entry point (SPECS §10.7)."""

from __future__ import annotations

import subprocess
import sys

from hillclimb import __version__


def run_module(*arguments: str) -> subprocess.CompletedProcess[str]:
    """Run python -m hillclimb and capture its output."""
    return subprocess.run(  # noqa: S603 - fixed interpreter and fixed arguments
        [sys.executable, "-m", "hillclimb", *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def test_module_reports_the_installed_version() -> None:
    result = run_module("--version")
    assert result.returncode == 0
    assert result.stdout.strip() == f"hillclimb {__version__}"


def test_module_selftest_is_headless_and_green() -> None:
    result = run_module("--selftest", "--seed", "11")
    assert result.returncode == 0

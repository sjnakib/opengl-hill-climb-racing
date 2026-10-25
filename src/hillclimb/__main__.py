"""Command line entry point (SPECS §10.7)."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import TYPE_CHECKING

from . import __version__
from .app.main import LaunchOptions, build_launch_options, run_app, run_selftest

if TYPE_CHECKING:
    from collections.abc import Sequence

_LOGGER = logging.getLogger(__name__)

DEFAULT_SEED = 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser with the flags required by SPECS §10.7."""
    parser = argparse.ArgumentParser(prog="hillclimb", description="Hill Climb Racing")
    parser.add_argument(
        "--version", action="store_true", help="print the installed version and exit"
    )
    parser.add_argument("--seed", type=int, default=None, metavar="N", help="deterministic seed")
    parser.add_argument(
        "--selftest", action="store_true", help="run a headless simulation pass and exit"
    )
    parser.add_argument(
        "--safe-mode",
        action="store_true",
        help="use an 800x450 window with no audio and default settings",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="raise logging verbosity to debug"
    )
    return parser


def _configure_logging(*, verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )


def _run_selftest_cli(seed: int) -> int:
    try:
        run_selftest(seed)
    except Exception:  # the CLI boundary maps any failure to exit 3
        _LOGGER.exception("selftest failed")
        return 3
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return the process exit code."""
    args = build_parser().parse_args(argv)
    _configure_logging(verbose=bool(args.verbose))
    if args.version:
        sys.stdout.write(f"hillclimb {__version__}\n")
        return 0
    seed: int = DEFAULT_SEED if args.seed is None else args.seed
    if args.selftest:
        return _run_selftest_cli(seed)
    options: LaunchOptions = build_launch_options(seed, safe_mode=bool(args.safe_mode))
    return run_app(options)


if __name__ == "__main__":
    raise SystemExit(main())

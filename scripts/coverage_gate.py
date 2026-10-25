#!/usr/bin/env python3
"""Enforce per-directory coverage floors from a coverage.py JSON report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

ENGINE_FLOOR = 97.0
ENGINE_PREFIX = "src/hillclimb/engine"


def _number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return float(value)


def _summary_totals(summary: Mapping[str, object]) -> tuple[float, float]:
    covered = _number(summary.get("covered_lines")) + _number(summary.get("covered_branches"))
    total = _number(summary.get("num_statements")) + _number(summary.get("num_branches"))
    return covered, total


def directory_coverage(payload: Mapping[str, object], prefix: str) -> float:
    """Return the covered percent for all report files under prefix."""
    files = payload.get("files")
    if not isinstance(files, dict):
        message = "coverage JSON has no files object"
        raise TypeError(message)
    covered = 0.0
    total = 0.0
    found = False
    for name, entry in files.items():
        if not isinstance(name, str) or not isinstance(entry, dict):
            continue
        normalized = name.replace("\\", "/")
        if not normalized.startswith(prefix):
            continue
        found = True
        summary = entry.get("summary")
        if not isinstance(summary, dict):
            message = f"coverage entry for {name} has no summary object"
            raise TypeError(message)
        file_covered, file_total = _summary_totals(summary)
        covered += file_covered
        total += file_total
    if not found:
        message = f"coverage JSON has no files under {prefix}"
        raise ValueError(message)
    if total == 0.0:
        return 100.0
    return 100.0 * covered / total


def main(argv: Sequence[str] | None = None) -> int:
    """Check the engine directory floor and return a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", type=Path, default=Path("coverage.json"))
    parser.add_argument("--path", dest="prefix", default=ENGINE_PREFIX)
    parser.add_argument("--floor", type=float, default=ENGINE_FLOOR)
    args = parser.parse_args(argv)
    payload: object = json.loads(args.report.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        message = "coverage JSON top level must be an object"
        raise TypeError(message)
    percent = directory_coverage(payload, args.prefix)
    print(f"{args.prefix} coverage: {percent:.2f} percent (floor {args.floor:.2f})")
    if percent < args.floor:
        print(
            f"coverage gate failed: {args.prefix} is {percent:.2f} percent, "
            f"floor is {args.floor:.2f}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

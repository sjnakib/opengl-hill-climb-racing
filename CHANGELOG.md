# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) (0.x rules apply:
minor versions add features and may break, patch versions fix bugs).

## [Unreleased]

## [0.1.1] - unreleased (target)

### Added
- Ground-up rewrite of the game under the SPECS.md engineering contract:
  procedural endless terrain, vehicle physics, coins/fuel pickups, airtime
  and flip scoring, menu/pause/game-over flow, settings with audio buses and
  remappable input (keyboard + gamepad), particles, best-score persistence.
- Deterministic simulation: fixed-timestep engine, named seeded RNG streams
  (`--seed` reproduces a run byte-for-byte on every platform).
- Dependency-free release binaries for Linux (x86_64, aarch64), macOS
  (Apple Silicon) and Windows (amd64), produced by CI on tags.

### Changed
- Replaced the CSE423-era PyOpenGL/FreeGLUT implementation (still preserved,
  untouched, in the `university/fall-2024` branch) with Python 3.14 +
  pygame-ce 2.5.8.
- Project licensing on `main` is `Copyright (c) 2026 Shafaat Jamil Nakib`;
  the all-new work is single-authored.

### Removed
- University-era deliverables from `main` (archived in
  `university/fall-2024`): game source, `lib/drawing.py`, course
  specification document, legacy `requirements.txt` approach.

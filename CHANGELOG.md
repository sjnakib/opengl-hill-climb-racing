# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Under 0.x rules: minor versions add features and may break things, patch
versions fix bugs.

## [Unreleased]

### Added
- A writing standard for all repo text (SPECS §19): plain, concise, human.
  A vale prose gate in CI enforces it (no em dashes, no emoji, no telltale
  AI vocabulary).
- A `prose` CI job running the writing checks on every repo markdown file.

### Changed
- README, CONTRIBUTING, SECURITY, and the PR template were rewritten to the
  new writing standard.

## [0.1.1] Unreleased target

### Added
- Ground-up rewrite of the game under the SPECS.md engineering contract:
  procedural endless terrain, vehicle physics, coins and fuel pickups,
  airtime and flip scoring, a menu, pause, and game-over flow, settings with
  audio buses and remappable pads, keyboard plus gamepad input, particles,
  and best-score persistence.
- Deterministic simulation: fixed-timestep engine and named seeded RNG
  streams. `--seed` reproduces a run exactly on every platform.
- Dependency-free release binaries for Linux (x86_64, aarch64), macOS
  (Apple Silicon), and Windows (amd64), built by CI on tags.

### Changed
- The CSE423-era PyOpenGL and FreeGLUT implementation is retired from
  `main`. It stays preserved, untouched, in the `university/fall-2024`
  branch. The rewrite uses Python 3.14 and pygame-ce 2.5.8.
- Licensing on `main` reads "Copyright (c) 2026 Shafaat Jamil Nakib". All
  new work is single-authored.

### Removed
- University-era deliverables, moved out of `main` into the
  `university/fall-2024` branch: the game source, `lib/drawing.py`, the
  course specification document, and the legacy `requirements.txt` approach.

# Hill Climb Racing, rewritten

A modern rewrite of a 2D hill climb game: drive over procedurally generated
hills, collect coins, manage fuel, and beat your best score.

> This project has moved on from its university days.
> It started as the CSE423: Computer Graphics course assignment at BRAC
> University in Fall 2024. The original code still lives on, untouched, in the
> [`university/fall-2024`](https://github.com/sjnakib/opengl-hill-climb-racing/tree/university/fall-2024)
> branch. That branch's README credits its authors: Shafaat Jamil Nakib,
> A.B.M. Danial, and Rabaya Farzana Sikder.
>
> The `main` branch is a clean-room rewrite toward a v0.1.1 release, written
> by Shafaat Jamil Nakib. The legacy PyOpenGL and FreeGLUT stack is gone. The
> rewrite uses current, maintained tools, and the engineering contract lives
> in [SPECS.md](SPECS.md).

## Status

In development; no release yet. The current milestone is the
[v0.1.1 release](https://github.com/sjnakib/opengl-hill-climb-racing/releases),
with its checklist in
[SPECS.md, Definition of Done](SPECS.md#17-definition-of-done-for-v011).
Downloadable, dependency-free binaries for Linux, macOS, and Windows ship
with it. The tree now holds the package skeleton with its tests: CLI, seeded
RNG, chunked terrain, settings, and saves. The playable game loop comes next.

## What v0.1.1 delivers

- A faithful remake of the original: endless procedural terrain, coins worth
  50 to 5000 points, fuel cans, fuel drain, airtime bonus, and a crash game
  over
- A complete game feel: menu, pause, settings for audio, input, and the
  window, plus gamepad support, particles, camera lookahead, and best-score
  persistence
- A deterministic engine. The same seed builds the same world on every
  platform
- 60 FPS on integrated graphics, strict test coverage, and CI quality gates
- Cross-platform release binaries with no dependencies to install

The complete, binding specifications live in [SPECS.md](SPECS.md).

## Tech stack, locked by SPECS.md §4

| Role | Technology |
| --- | --- |
| Language | Python 3.14, pinned under 3.15 |
| Framework | pygame-ce 2.5.8, the maintained SDL2 fork, not legacy pygame |
| Environment and lock | uv 0.13 or newer, with a committed `uv.lock` |
| Lint and format | ruff 0.17 or newer, strict rule set |
| Types | mypy 2.4 or newer in strict mode |
| Tests | pytest 9, coverage 7, hypothesis 6 |
| Supply chain | pip-audit against the PyPI Advisory Database |
| Prose | vale 3.25 or newer, per the writing standard in SPECS §19 |

[![CI](https://github.com/sjnakib/opengl-hill-climb-racing/actions/workflows/ci.yml/badge.svg)](https://github.com/sjnakib/opengl-hill-climb-racing/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/sjnakib/opengl-hill-climb-racing)](LICENSE)

## Development quickstart

```bash
# 1. install uv (https://docs.astral.sh/uv/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. sync the locked environment. This creates .venv with exact versions.
uv sync --all-groups

# 3. install the local git hooks
uv run pre-commit install

# 4. gates. All must be green before a PR merges (SPECS §12).
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run coverage run -m pytest
uv run coverage report
uv run pip-audit
```

[CONTRIBUTING.md](CONTRIBUTING.md) has the full workflow and commit
conventions. SPECS.md is binding; changing it requires a dedicated
spec-change commit (SPECS §18).

## Author

All post-university work is by Shafaat Jamil Nakib. The university project
keeps its own authors and license text on the
[`university/fall-2024`](https://github.com/sjnakib/opengl-hill-climb-racing/tree/university/fall-2024)
branch.

## License

MIT. See [LICENSE](LICENSE).

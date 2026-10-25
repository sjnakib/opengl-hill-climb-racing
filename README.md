# 🚗 Hill Climb Racing — v0.1.1 Rewrite

A modern ground-up rewrite of a 2D hill climb game: drive over procedurally
generated hills, collect coins, manage your fuel, and beat your best score.

> [!IMPORTANT]
> **This project has moved on from its university days.**
> It began as the **CSE423: Computer Graphics (BRAC University, Fall 2024)**
> course assignment. That original code is preserved **untouched** on the
> [`university/fall-2024`](https://github.com/sjnakib/opengl-hill-climb-racing/tree/university/fall-2024)
> branch (original authors: Shafaat Jamil Nakib, A.B.M Danial,
> Rabaya Farzana Sikder — see that branch's README).
>
> The `main` branch is a **clean-room rewrite** toward a `v0.1.1` release.
> All new work is authored by **Shafaat Jamil Nakib** only. The rewrite targets
> current, actively maintained technology and replaces the legacy
> PyOpenGL/FreeGLUT stack entirely. See [SPECS.md](SPECS.md) for the binding
> engineering contract.

## Status

🚧 **In development — no release yet.** The current milestone target is
[`v0.1.1`](https://github.com/sjnakib/opengl-hill-climb-racing/releases)
(see the [Definition of Done in SPECS.md](SPECS.md#17-definition-of-done--v011)).
Downloadable, dependency-free binaries for Linux, macOS and Windows will be
attached to that release. In the meantime, the tree is intentionally
script-free: SPECS and tooling first, code second.

## What v0.1.1 delivers

- Faithful remake of the original: endless procedural terrain, coins
  (50–5000 points), fuel cans, fuel drain, airtime bonus, crash game over
- Full game feel: menu, pause, settings (audio buses, keybinds, window),
  gamepad support, particles, camera lookahead, best-score persistence
- Deterministic engine: same seed → same world on every platform
- 60 FPS on integrated graphics; strict coverage and CI quality gates
- Cross-platform, dependency-free release binaries (Linux / macOS / Windows)

Read [SPECS.md](SPECS.md) for the complete, binding specifications.

## Tech stack (locked by SPECS.md §4)

| Role | Technology |
| --- | --- |
| Language | Python 3.14 (pinned, `<3.15`) |
| Framework | pygame-ce 2.5.8 (actively-maintained SDL2 fork, not legacy pygame) |
| Env & lock | uv 0.13+ with committed `uv.lock` |
| Lint / format | ruff 0.17+ (strict rule set) |
| Types | mypy 2.4+ in `strict` mode |
| Tests | pytest 9, coverage 7, hypothesis 6 |
| Supply chain | pip-audit against the PyPI Advisory Database |
| Packaging | PyInstaller 6.22+ `onedir` bundles per platform |

[![CI](https://github.com/sjnakib/opengl-hill-climb-racing/actions/workflows/ci.yml/badge.svg)](https://github.com/sjnakib/opengl-hill-climb-racing/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/sjnakib/opengl-hill-climb-racing)](LICENSE)

## Development quickstart

```bash
# 1. install uv (https://docs.astral.sh/uv/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. sync the locked environment (creates .venv, exact locked versions)
uv sync --all-groups

# 3. install the local git hooks
uv run pre-commit install

# 4. gates (all must be green before any PR merges — see SPECS §13)
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run coverage run -m pytest
uv run coverage report
uv run pip-audit
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow and commit
conventions. **[SPECS.md](SPECS.md) is binding** — changing it requires a
dedicated spec-change PR (SPECS §18).

## Author

- **Shafaat Jamil Nakib** — all post-university work. (The archived
  university project on
  [`university/fall-2024`](https://github.com/sjnakib/opengl-hill-climb-racing/tree/university/fall-2024)
  keeps its original authors and its own license text.)

## License

MIT — see [LICENSE](LICENSE).

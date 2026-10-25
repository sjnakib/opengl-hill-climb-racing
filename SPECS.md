# SPECS: Hill Climb Racing v0.1.1 (binding engineering contract)

Version 1.3.1. Status: binding. Set 2026-10-25. Amendments: 1.1.0 (2026-10-25) added the writing standard (§19) with its prose gate. 1.2.0 (2026-10-25) pinned the milestone B curves: the engine numeric law (§10.2), the difficulty table (§10.3), the drive profile (§10.4), and the spawn and fuel curves (§10.5). 1.3.0 (2026-10-25) added branch verification and commit lanes (§7). 1.3.1 (2026-10-25) listed the landed engine modules in the layout tree (§6).

Applies to every commit on `main` and every release from v0.1.1 onward.

This document wins over any verbally described "requirement" and over precedent from the `university/fall-2024` branch. If code and SPECS disagree, the code is wrong until SPECS is amended (§18).

CI jobs enforce the machine-checked rules. Review-enforced rules block merges through human review and are not optional.

Every version in §4 was live-verified on 2026-10-25 against PyPI, python.org release pages, and GitHub tag listings. Nothing here relies on training data.

## 1. Project card

| Field | Value |
| --- | --- |
| Package and binary name | `hillclimb` |
| Display name | "Hill Climb Racing" |
| Repo | `sjnakib/opengl-hill-climb-racing`, branch `main` |
| Author of all new work | Shafaat Jamil Nakib |
| License of new work | MIT, "Copyright (c) 2026 Shafaat Jamil Nakib" |
| Working language | English only, for code, comments, and UI strings |
| History | University-era code is preserved on branch `university/fall-2024` and is read-only history |

## 2. Mission and non-goals

Mission: a dependency-free, offline, single-player 2D side-scrolling hill climb driving game with clean, deterministic simulation and verifiable correctness, delivered as plain downloadable binaries for Linux, macOS, and Windows.

Permanent non-goals. These will also stay out later, not just for 0.1.1:

1. No network at runtime. Ever. The game must not open sockets, fetch telemetry, check for updates, or phone home in any way. CI enforces a static import ban (§13).
2. No accounts, DRM, ads, or online services of any kind.
3. No multiplayer in the 0.x series.
4. No telemetry, analytics, or crash-report uploads. Local log files only.
5. No level editor in 0.x. Procedural generation is the content.
6. No new system dependencies at run time beyond the ones PyInstaller bundles.

## 3. Supported platforms and minimums

| Platform | Target | Baseline | Notes |
| --- | --- | --- | --- |
| Windows | amd64 | Windows 10 1809 and newer | 64-bit only; no win32 builds |
| macOS | arm64, Apple Silicon | macOS 11 Big Sur and newer | x86_64 macOS is a documented non-goal for 0.1.x |
| Linux | x86_64 | glibc 2.35 or newer, the Ubuntu 22.04 / Debian 12 era | CI builds on ubuntu-22.04 |
| Linux | aarch64 | glibc 2.39 or newer, built on ubuntu-24.04-arm | best-effort tier |

SDL2, bundled by pygame-ce, needs a GPU or driver providing OpenGL 2.1+ or GLES 2.0+. That is ubiquitous on every supported OS.

## 4. Locked technology stack

Exact version resolution is committed in `uv.lock`. `pyproject.toml` carries the compatible-range constraints below.

| Concern | Package | Constraint in pyproject | Verified state, 2026-10-25 |
| --- | --- | --- | --- |
| Interpreter | Python | `>=3.14,<3.15` | 3.15.0 shipped on 2026-10-09, but pygame-ce 2.5.8 has no cp315 wheels yet. 3.14 has verified cp314 wheels for win32 and win_amd64, macOS universal2, and manylinux2014 x86_64, aarch64, and i686 |
| Game framework | `pygame-ce` | `>=2.5.8,<2.6` | The maintained SDL2 fork. Classic pygame is stale, has no 3.14 wheels, and is banned here |
| Env and lock | `uv` | `>=0.13.5` (tool, not dependency) | Lockfile is committed; sync is reproducible |
| Lint and format | `ruff` | `>=0.17.2,<0.18` | Strict select-ALL config (§7) |
| Type check | `mypy` | `>=2.4,<3` | `strict = true` |
| Unit and property tests | `pytest`, `hypothesis` | `>=9.1,<10`, `>=6.170,<7` | Property tests are mandatory (§12) |
| Coverage | `coverage[toml]` | `>=7.17,<8` | Branch coverage on; fail-under gates (§12) |
| Supply chain audit | `pip-audit` | `>=2.10,<3` | Per PR and weekly cron (§13) |
| Save and config directories | `platformdirs` | `>=4.13,<5` | The maintained successor of appdirs |
| TOML writing | `tomli-w` | `>=1.2,<2` | Reads use the stdlib `tomllib` |
| Prose lint | `vale` | `>=3.25,<4` (group `dev`) | PyPI packaging of the Go binary, released 2026-10-23; kept current through the monthly ratchet (§19) |
| Bundler | `pyinstaller` | `>=6.22.3,<7` (group `build`) | onedir mode only (§14) |
| License manifest | `pip-licenses` (group `build`) | `>=5.5,<6` | Refreshes the dependency section of `CREDITS.md` |
| Git hooks | `pre-commit` (group `dev`) | `>=4.7,<5` | Local mirror of CI lint |

Version policy.

1. Dependency bumps happen only in dedicated `chore: bump ...` PRs that run the full gate set (§12, §13). Hand edits of `uv.lock` are forbidden.
2. A scheduled monthly ratchet PR runs `uv lock --upgrade`, then `pip-audit`, then the full gates. Security advisories may be acted on immediately.
3. Interpreter upgrades: move to 3.15 only after every runtime dependency ships cp315 wheels for all four release targets and a full gate run passes.
4. pygame-ce upgrades may cross the `<2.6` bound only in a dedicated PR that documents the behavior changes relevant to this repo.

Banned legacy stack. It may not appear on `main`, in CI, or in docs:

| Banned item | Reason |
| --- | --- |
| PyOpenGL, FreeGLUT, GLUT, immediate-mode OpenGL | Legacy API, broken on modern Wayland and macOS, no maintained path |
| Classic `pygame` | Stale upstream, superseded by pygame-ce |
| `requirements.txt` as the primary packaging | Not reproducible; superseded by the uv lock |
| `PyOxidizer` | Unmaintained since 2022 |
| `appdirs`, `distutils`, `setup.py`-only packaging | Superseded or removed by PEP 632 |
| Python before 3.14 as a target | Unsupported interpreters |

Rejected alternatives, decided and not to be relitigated in PRs except through §18:

Nuitka gives good performance but brings a heavy toolchain and slower builds for a solo maintainer. cx_Freeze is the documented fallback if PyInstaller is ever blocked, with the switch recorded through §18 first. Briefcase targets app-store packaging we do not use. Godot and Unity violate the code-first, test-first mission. C++ with SDL3 costs more maintenance than a solo project gains.

## 5. Tooling and standard commands

The lockfile is the unit of reproduction. All commands run through `uv`.

| Purpose | Command |
| --- | --- |
| Full environment, dev plus build groups | `uv sync --all-groups` |
| Lint gate | `uv run ruff check .` |
| Format check, or apply | `uv run ruff format --check .` or `uv run ruff format .` |
| Type check | `uv run mypy src tests` |
| Tests plus coverage | `uv run coverage run -m pytest`, then `uv run coverage report` |
| Property tests only | `uv run pytest tests/property -q` |
| GUI-marked tests, headless | `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy uv run pytest -m gui` |
| Security audit | `uv run pip-audit` |
| Prose check, CI gate | `uv run vale README.md CHANGELOG.md CONTRIBUTING.md SECURITY.md SPECS.md .github/PULL_REQUEST_TEMPLATE.md` |
| Dev build, any OS | `uv run pyinstaller --clean --noconfirm --onedir --windowed --name hillclimb --noupx src/hillclimb/__main__.py` |
| License manifest | `uv run pip-licenses --format markdown --output-file CREDITS.autogen.md` |

## 6. Repository layout and import law

```
.
├── SPECS.md                  # this contract
├── README.md, CONTRIBUTING.md, SECURITY.md, CHANGELOG.md, LICENSE
├── pyproject.toml, uv.lock, .python-version, .vale.ini
├── styles/Hillclimb/         # prose rules (§19)
├── src/
│   └── hillclimb/
│       ├── __init__.py       # __version__ only
│       ├── __main__.py       # CLI entry (§10.7)
│       ├── engine/           # simulation: zero pygame imports
│       │   ├── terrain.py    # seeded procedural heightfield
│       │   ├── vehicle.py    # two-wheel chassis, torque, airtime
│       │   ├── world.py      # collectible spawning per chunk
│       │   ├── scoring.py    # coins, airtime, flip rules
│       │   ├── difficulty.py # ramp curves
│       │   ├── fixedmath.py  # IEEE-only trigonometry (§10.2)
│       │   ├── fuel.py       # tank state and the drain law
│       │   ├── simulation.py # headless run coordinator
│       │   └── rng.py        # named RNG stream factory (§10.2)
│       ├── app/              # pygame-ce presentation layer
│       │   ├── main.py       # game loop, fixed timestep
│       │   ├── state.py      # BOOT, MENU, PLAY, PAUSED, GAMEOVER machine
│       │   ├── render.py, hud.py, camera.py, particles.py
│       │   ├── audio.py      # music and sfx buses
│       │   └── input.py      # keyboard plus gamepad map (§10.6)
│       ├── config.py         # settings load, validate, atomic save
│       └── savedata.py       # best-score persistence
├── assets/                   # CC0 or OFL only (§11): audio, fonts, graphics
├── tests/
│   ├── unit/                 # pure engine tests
│   ├── property/             # hypothesis suites (§12)
│   ├── integration/          # headless boot, save and config round-trips
│   └── golden/               # schema migration fixtures
└── scripts/                  # coverage gate, perf check, asset audit
```

Import law, machine-checked in CI:

1. `src/hillclimb/engine/**` must not import `pygame`, `numpy`, `socket`, `urllib`, `http`, or `requests`. The CI command below must exit 0:
   ```bash
   ! grep -R -nE '^\s*(import|from)\s+(pygame|numpy|socket|http|urllib|requests)' src/hillclimb/engine/
   ```
2. `app` may import `engine`. `engine` must never import `app`.
3. Imports are explicit, like `from ..engine import terrain`. Star imports are banned.
4. The entry point is `src/hillclimb/__main__.py`. Nothing outside the package imports from inside it.

## 7. Code standards

 Machine-enforced, through `pyproject.toml`:

- ruff with `select = ALL` minus the documented ignore list. Enforced families include: `E9`, `F`, `B` for correctness and bugs; the `S` bandit subset, which bans `eval` and `exec` (`S102`) and unsafe YAML (`S506`); `T20`, which bans `print` and `pdb` outside tests; `ANN` for full annotations; `D` for Google-style docstrings; `N` for naming; `EM`, `TRY`, `EXC` for exception hygiene; `PERF` for loop efficiency; `FURB` for modern idioms; `DTZ` for timezone safety; `RET` and `PLR` for structure; `A` against builtin shadowing.
- `ruff format` with a line length of 100 is the single formatter.
- mypy with `strict = true`: untyped defs, untyped decorators, anywhere-returns, and unused ignores are all denied. `pygame.*` may need `[[tool.mypy.overrides]]` at first; loosening it is tracked cleanup, not a permanent exemption.
- pytest runs with `--strict-markers --strict-config`, and warnings are errors.

Review-enforced, through human review:

1. Functions stay at or under 40 lines as a hard target. Anything over 60 must be split, or justified in review with a note anchored in the PR description.
2. Names say what they do. Only domain-standard abbreviations are allowed, like `dt`, `fps`, and `hud`.
3. Comments explain why, never narrate obvious code, and follow §19. No commented-out code.
4. Module-level mutable globals are forbidden. That flaw is what strangled the original university code. State lives on instances, and singletons are injected, not imported.
5. Gameplay string and numeric constants live in exactly one module per concern.
6. One PR holds one focused change. Commits follow Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`, `perf:`, `release:`, `ci:`.
7. Branch verification precedes every write session: `git status -sb` and `git branch --show-current` run before any edit, any `git pull`, and any push, whichever agent or human is driving. `git pull origin main` never runs while checked out on another branch; switch first. Every push moves the current branch at HEAD, never a stale ref. Reason: a merged PR once left this working tree on its own feature branch, and a blind pull fast-forwarded the wrong branch; the rule makes that failure loud instead of silent.
8. Commit lanes map to branches: `spec:`, `docs:`, `chore:`, and `release:` commits land on `main`, while `feat:`, `fix:`, `test:`, `refactor:`, `perf:`, and `ci:` commits land on a branch carrying the matching prefix, like `feat/mB-engine`. Machine-enforced by `scripts/branch_guard.py`, wired as local pre-commit, commit-msg, and pre-push guards through `.pre-commit-config.yaml`.

## 8. Architecture and performance budgets

| Metric | Budget | Measurement |
| --- | --- | --- |
| Frame rate | 60 FPS at 1280x720 windowed on an Intel UHD 620 class iGPU | `scripts/perf_check.py`, landing with DoD (§17), replays a scripted 60 second run |
| Cold start to menu | Under 2.0 s from process exec | Same script |
| Input to visual | Under 50 ms, typical | Scripted latency probe |
| Hot-loop allocations | No per-frame object churn beyond a bounded pool | Review, plus the script |
| Release bundle size | 120 MB or less per artifact | CI asserts before upload |
| Sim determinism | Same seed and same replay give identical score and distance | Property test R1 (§12) |

The simulation runs on a fixed timestep of 120 Hz with an accumulator. Frame time is clamped at 100 ms, and at most 25 catch-up ticks run per frame, so there are no death spirals. Rendering is decoupled from simulation. Interpolation for drawing is allowed but never required. The FPS budget must never be met by lowering the simulation rate.

## 9. Data, persistence, and privacy

All user data is written under `platformdirs` paths, and nowhere else.

| OS | Settings | Saves, best score, logs |
| --- | --- | --- |
| Windows | `%APPDATA%\hillclimb\` | `%LOCALAPPDATA%\hillclimb\` |
| macOS | `~/Library/Application Support/hillclimb/` | Same directory |
| Linux | `$XDG_CONFIG_HOME/hillclimb/` | `$XDG_DATA_HOME/hillclimb/` |

- Settings are TOML in `config.toml` with a top-level `schema_version = 1`, written atomically through `tempfile` and `os.replace`. A crash must never leave a partially written file.
- Saves and best score are JSON with `schema_version`, backed by dataclasses. Migrations are pure functions covered by golden tests in `tests/golden/`. Unknown fields and values are tolerated, so newer or older schemas never crash. Corrupted files move to `*.corrupt-<timestamp>.bak` and are recreated empty.
- Logs: `hillclimb.log`, rotating at 5 MB with 3 backups through `logging`. `--verbose` raises verbosity. On crash the full traceback is logged and never shown raw in the UI.
- No telemetry fields, no machine fingerprinting, nothing beyond what the user typed.

## 10. Gameplay specification (v0.1.1)

Constants are tunable only through a PR that updates this table and the tests together, re-baselining golden values in the same change.

### 10.1 Overview

An endless procedural stage with a single car. Collect coins, keep fuel above zero, survive crashes. Distance, score, and difficulty grow without bound. One best record is persisted.

### 10.2 Determinism contract

- All randomness flows through named streams built by `engine/rng.py` from a master seed: `terrain`, `items`, `fx`. Cosmetics must never affect physics.
- Streams are `random.Random` instances seeded as `random.Random(f"{master}:{name}")`, stable across platforms for the pinned Python minor, 3.14.x.
- `--seed N` reproduces a run deterministically on every platform.
- Engine numeric law. Engine arithmetic uses only IEEE 754 exactly defined operations: addition, subtraction, multiplication, division, integer ops, `%` (fmod), `fabs`, `min` and `max`, and `sqrt` (correctly rounded by IEEE 754, so it stays legal). libm transcendentals (`sin`, `cos`, `tan`, `atan2`, `exp`, `log`, `pow`, `hypot`) differ in their last bits across platforms, so `engine/**` bans them the same way it bans pygame (§6), and the CI `rules` job gains that grep. Deterministic trig lives in `engine/fixedmath.py`: `% TAU` argument reduction plus a fixed polynomial evaluated with basic operations. The app layer may use libm freely. Milestone A's `terrain.py` switches to the helper, and its slope budget `tan` values become literals (0.26795 and 1.42815), before any R1 baseline is recorded.

### 10.3 Terrain

- The heightfield is generated chunk-wise. Height queries by x are O(1). There are no O(n) global arrays, and chunks are recycled.
- Property: absolute slope stays at or under 60 degrees at difficulty 3 and above, and terrain stays reachable: no step-up steeper than the car's ground-contact capability. Property tests T1 and T2 in §12 check this.
- Difficulty is a pure function of distance, on these binding curves:

  | Parameter | Value |
  | --- | --- |
  | Sampling | 8 px sample spacing, 512 px chunks (64 samples), LRU cache of 32 chunks |
  | Base height | 600 px |
  | Ramp distance | 45,000 px, linear blend across it |
  | Difficulty level | 1.0 at 0 px to 10.0 at 45,000 px, linear |
  | Octaves | 4 waves, wavelengths 2048, 1536, 1024, 768 px, per-seed phases from the `terrain` stream |
  | Octave weights | (1.0, 0.0, 0.0, 0.0) blending linearly to (0.55, 0.25, 0.14, 0.06) |
  | Slope budget | Rise-over-run budget 0.26795 at 0 px up to 1.42815 at 45,000 px, linear. These correspond to 15 and 55 degrees, under the 60 degree limit |
  | Roughness | 1 minus the longest-wavelength weight |

### 10.4 Car physics

- Two point wheels on a rigid chassis, the model that made the original fun, implemented properly: per-wheel ground snap, suspension damping, drive torque with a speed limiter.
- Top speed 500 px/s. Display as `round(|v|/10 × 3.6)` km/h. 10 px = 1 m.
- Game over when fuel reaches zero and the car comes to rest, or when the driver's head vertex touches terrain while the car is in motion.
- Drive force is full at or below 250 px/s and tapers linearly to zero at the 500 px/s cap. Reverse drive is capped at 150 px/s. Suspension constants are engine-internal tuning (§7 rule 5), validated by stability properties: no terrain penetration and no blow-up over a long scripted run.

### 10.5 Pickups, fuel, and scoring

| Rule | Value |
| --- | --- |
| Coin values | 50, 100, 200, 500, 1000, 5000, weighted 0.40, 0.25, 0.15, 0.12, 0.06, 0.02 |
| Airtime bonus | 50 points per full airborne second, doubling each further full second. The original mechanic, kept |
| Flip bonus | 100 points per full 360 degree rotation while airborne |
| Fuel | Max 100.0 L. Drain per second: `0.55 + |v| × 0.012 × difficulty factor`. A fuel can refills to full |
| Fuel guarantee | At the scripted nominal speed of 100 px/s, the mean gap between consecutive fuel cans is at most 4,500 px (45 s) for every seed at difficulty level 5 or lower, property tested over 100 seeds |
| Fuel drain factor | The difficulty factor in the drain formula is the §10.3 difficulty level at the car's current distance, divided by 10, so 0.1 at level 1 through 1.0 at level 10 |
| Fuel can spacing | Gaps drawn per seed from the `items` stream, uniform between 2,000 and 5,000 px, mean 3,500 px (35 s at nominal) |
| Item spacing | Items never overlap or spawn inside terrain. The minimum gap between any two coin groups, and between a group and a fuel can, is 25 m (250 px); coins inside one group sit 40 to 80 px apart |
| Coin groups | One group every uniform 700 to 1,100 px (mean 900 px), 2 to 6 coins per group, each coin's value drawn from the coin table via the `items` stream |

### 10.6 Input

| Action | Keyboard | Gamepad default |
| --- | --- | --- |
| Accelerate | Right arrow, D | A, bottom face |
| Brake or reverse | Left arrow, A | X, left face |
| Pause, menu | Esc | Start |
| Restart run | R | Y, top face |
| Menu confirm, back | Enter, Esc | A, B |

The keyboard is fully remappable in settings. Gamepad mapping uses SDL standard mapping glyphs, with no per-device `.guid` handling.

### 10.7 CLI, module `__main__.py`, required flags

| Flag | Behavior |
| --- | --- |
| `--seed N` | Deterministic run seed, used by tests and CI |
| `--version` | Print `hillclimb <semver>` from installed metadata, exit 0 |
| `--selftest` | Boot the simulation and a headless pass of at most 5 simulated seconds. Exit 0 on success, 3 on failure. Used by release smoke tests. Never opens a window |
| `--safe-mode` | 800x450 window, no audio, default settings, for troubleshooting |

## 11. Audio and assets

- Formats: OGG Vorbis for music, 16-bit 44.1 kHz WAV for sound effects. Buses: master, music, sfx, each 0 to 100 and persisted. Channels: music 1, sfx 8.
- Licenses: CC0 or OFL only. Pre-vetted candidates are the Kenney packs and OFL fonts. Every `assets/` subdirectory must contain a `LICENSE` file naming its pack origin and license, and CI fails if one is missing. MP3 and any license-uncertain asset are banned. `CREDITS.md` lists each pack with author, license, and URL.

## 12. Testing gates

Machine-enforced and all green before merge:

1. Coverage, with branch mode on. Total is at least 85 percent through `--fail-under=85`, wired from day one. The engine floor is at least 97 percent through `scripts/coverage_gate.py`: `coverage json`, then a per-directory floor enforced in CI.
2. Property tests with hypothesis in `tests/property/` are mandatory:
   - T1, terrain slope bound; T2, terrain reachability; T3, fuel stays within [0, 100].
   - R1, replay determinism: same seed with scripted inputs gives exactly the same score and distance across platforms.
   - S1, score monotonicity under replays.
   - P1, pickup spacing plus the fuel guarantee (per-seed mean inter-can gap at most 4,500 px at the 100 px/s nominal over 100 seeds).
   - M1, config and save schema round-trip plus migration property.
3. GUI tests run headless with `SDL_VIDEODRIVER=dummy`: boot to menu, PLAY to PAUSED and back, PLAY to GAMEOVER to PLAY, clean shutdown. They are marked `gui`, skipped in developer sandboxes without SDL video, and always run on CI.
4. Anti-slop rules for tests: no `time.sleep` pacing, no network, no unseeded randomness, single tests stay under 2 s except those marked `perf`, and no test may assert implementation details. Observable behavior only.
5. A change that lowers any gate must include a §18 spec-change justification in the PR body, or the PR is rejected.

## 13. Security and supply chain

- `pip-audit` runs on every PR against the locked environment and weekly on `main`. Any known vulnerability fails CI, checked against the PyPI Advisory Database.
- GitHub Actions are pinned to full commit SHAs, never tags. Dependabot monitors action updates weekly.
- No runtime network: CI runs the §6 import ban on `engine/**`, plus a `src/**` ban for `socket`, `http`, `urllib`, `requests`, `ftplib`, and `telnetlib` outside an allow-list that is empty in v0.1.1.
- Package source is PyPI only, the uv default. No wheel URLs from foreign hosts. `uv sync --locked` everywhere, so the lock never drifts silently.
- No secrets are expected, and none may ever be committed. `.env*` is gitignored.
- SECURITY.md routes reports to GitHub private security advisories.

## 14. Release engineering, cross-platform and dependency-free

- Bundling: PyInstaller `onedir` only. It starts fast, trips antivirus less than `onefile`, and never self-extracts to a temp directory. `--noupx` is mandatory, because UPX bloats and triggers antivirus flags.
- Runners: ubuntu-22.04 for x86_64, ubuntu-24.04-arm for aarch64, macos-15 for arm64, windows-2025 for amd64. `uv` prepares the environment; SDL2 and everything else ship inside the artifact.
- Artifacts, one set per tagged 0.x release:
  - `hillclimb-v{ver}-linux-x86_64.tar.gz` and `hillclimb-v{ver}-linux-aarch64.tar.gz`
  - `hillclimb-v{ver}-macos-arm64.zip`, holding a `.app` inside the zip
  - `hillclimb-v{ver}-windows-amd64.zip`
  - `SHA256SUMS.txt`, aggregated per-platform `.sha256` files
- Smoke test before upload, on each native runner: launch the packaged binary with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy` and `--selftest`, using the binary inside `.app/Contents/MacOS/` on macOS. A nonzero exit fails the release job.
- First-run guidance, unsigned by choice since there are no certificates: each release README documents the standard bypasses. macOS: `xattr -dr com.apple.quarantine`, or right-click then Open. Windows: SmartScreen, then "More info", then "Run anyway", plus how to report a false positive. Linux needs nothing beyond `chmod +x` on the tarball binary.
- Versioning: SemVer 0.x. v0.1.1 is the first public tag, and 0.2.x may break feature data compatibility. `__version__` is read from installed metadata at runtime, never duplicated in code.
- Process: tag `vX.Y.Z` on `main` once the §17 checklist is fully checked. CI creates the GitHub Release and attaches artifacts. The release notes body is copied from that tag's CHANGELOG section.

## 15. Current CI jobs

| Job | Runs | Gates |
| --- | --- | --- |
| `lint` | Every PR and push to `main` | ruff check, ruff format check |
| `prose` | Same | vale writing checks: em and en dashes, emoji, banned telltale words, on all repo markdown (§19) |
| `types` | Same | mypy strict on `src` and `tests` |
| `test` | Same | coverage run plus `--fail-under=85`, plus the per-directory engine floor gate (§12) |
| `rules` | Same | Engine purity import ban, repo-wide network import ban |
| `audit` | PRs and weekly cron | pip-audit fails on any known CVE |
| `release` | Tag `v*` push | Build plus smoke on 4 runners, attach artifacts. Fails until the entry point exists, by design |

## 16. Milestones after 0.1.1, not commitments

0.2.x candidates: a second vehicle, the upgrade shop, an additional stage. The commit path for any of them runs through a §18 spec amendment. Features never arrive unannounced.

## 17. Definition of Done for v0.1.1

- [ ] All CI jobs green on `main`: lint, prose, types, test, rules, audit.
- [ ] Engine and app code complete per §6, §8, §10, and §11. Property and golden suites pass.
- [ ] `--selftest` green on all four release platforms, from the packaged builds.
- [ ] Engine coverage at least 97 percent, total at least 85 percent, with `scripts/coverage_gate.py` wired.
- [ ] §8 performance budgets verified, with numbers recorded in the release notes.
- [ ] Assets ship with provenance (§11), and CREDITS.md is complete.
- [ ] README updated with a download table plus Gatekeeper and SmartScreen guidance.
- [ ] Every repo markdown file passes the §19 prose gate.
- [ ] CHANGELOG.md finalized for v0.1.1, tag pushed, artifacts attached, release published.

## 18. Amending this document

Any change to SPECS is its own commit titled `spec: ...`. It touches only this file, with a minimal diff, plus the tool configuration that enforces it, such as rule files or workflow lines. The commit body states what changed and why. CI must still be green, and the change must name exactly which sections were touched, so reviewers can diff quickly. Emergency changes at release time are allowed but must be re-reviewed within seven days.

## 19. Writing standards for all repo text

Position: every written artifact in this repo obeys this section. That includes SPECS, README, CHANGELOG, CONTRIBUTING, SECURITY, the PR template, issue text, commit messages, PR bodies, UI strings, and code comments.

Goal: a person reading this repo should hear a competent human, not a template. Writing must be easy to read, concise, and natural.

Machine-enforced, through the CI `prose` job with vale:

1. No em dash and no en dash anywhere in prose. Rewrite with a comma, colon, parentheses, or a new sentence. Hyphens stay legal for compound words, ranges, command flags, and markdown table rules. Rule file: `styles/Hillclimb/EmDash.yml`.
2. No emoji, dingbats, or decorative symbols in text files. Game asset filenames are exempt. Rule file: `styles/Hillclimb/Emoji.yml`.
3. No telltale AI vocabulary. The banned lexicon lives in `styles/Hillclimb/BannedWords.yml` as the single source of truth, and it grows only through a `chore: prose lexicon` commit touching that one file. The current entries:

   ```
   delve, tapestry, testament, seamless, robust, leverage, empower, elevate, unleash, cutting-edge, state-of-the-art, game-changer, world-class, holistic, myriad, plethora, comprehensive, paradigm, realm, landscape, journey, embark, foster, showcase, underscore, harness, unlock, transformative, vibrant, pivotal, crucial, symphony, beacon, cornerstone, pinnacle, treasure trove, hidden gem, look no further, rest assured, deep dive, in today's world, ever-evolving, ever-growing, moreover, furthermore, important to note, worth noting, in conclusion, in summary
   ```
4. If a new markdown file joins the repo, it joins the file list of the prose job or carries its own `[*.md]` coverage through `.vale.ini`. Never ship an unenforced document.

Review-enforced, through human review:

5. Easy to read: short sentences, one idea per sentence, concrete nouns and real numbers over abstraction. Aim under 25 words per sentence and 4 sentences per paragraph.
6. Natural: write the way a person explains things to a teammate. Second person for instructions, active voice with real subjects, no rule-of-three padding, no rhetorical flourishes, no fake openers, no "it is not X, it is Y" constructions.
7. Concise: prefer fewer words. Cut anything that does not delete meaning.
8. Headings in sentence case, short, no decorative icons. Lists only for genuine enumerations.
9. Commands and identifiers stay as code. The prose around them reads normally.
10. The same bar applies to commit messages, PR bodies, issue text, and in-code comments. Comments explain why (§7) and follow this section.

Enforcement: the vale gate must exit 0 for every file it covers. A failing `prose` job blocks merge like any other gate.

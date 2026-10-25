# SPECS — Hill Climb Racing v0.1.1 (Binding Engineering Contract)

- **Version:** 1.0.0 · **Status:** BINDING · **Set:** 2026-10-25
- **Applies to:** every commit on `main` and every release ≥ `v0.1.1`.
- **Precedence:** This document wins over any verbally described "requirement"
  and over precedent from the `university/fall-2024` branch. If code and SPECS
  disagree, the code is wrong until SPECS is amended (§18).
- **Enforcement:** CI jobs implement the "machine-enforced" rules. "Review-enforced"
  rules block merges through human review and are not optional.
- **Provenance:** every version in §4 was live-verified on 2026-10-25 against
  PyPI, python.org release pages, and GitHub tag listings — not taken from
  training data.

---

## 1. Project card

| Field | Value |
| --- | --- |
| Package / binary name | `hillclimb` |
| Display name | "Hill Climb Racing" |
| Repo | `sjnakib/opengl-hill-climb-racing` (branch `main`) |
| Author (all new work) | Shafaat Jamil Nakib |
| License of new work | MIT, `Copyright (c) 2026 Shafaat Jamil Nakib` |
| Working language | English only (code, comments, UI strings) |
| History | University-era code is preserved on branch `university/fall-2024` and is read-only history |

## 2. Mission & non-goals

**Mission.** A dependency-free, offline, single-player 2D side-scrolling hill
climb driving game with clean, deterministic simulation and verifiable
correctness — delivered as plain downloadable binaries for Linux, macOS and
Windows.

**Permanent non-goals (these will also NOT be added later):**

1. **No network at runtime. Ever.** The game must not open sockets, fetch
   telemetry, check for updates, or phone home in any way. CI enforces a
   static import ban (§13).
2. No accounts, DRM, ads, or online services of any kind.
3. No multiplayer in the 0.x series.
4. **No telemetry, analytics or crash-reporting uploads.** Local log files only.
5. No level editor in 0.x. Procedural generation is the content.
6. No new system dependencies at run time beyond the ones bundled by PyInstaller.

## 3. Supported platforms & minimums

| Platform | Target | Baseline | Notes |
| --- | --- | --- | --- |
| Windows | amd64 | Windows 10 1809+ | 64-bit only; no win32 builds |
| macOS | arm64 (Apple Silicon) | macOS 11 Big Sur+ | x86_64 macOS is a documented non-goal for 0.1.x |
| Linux | x86_64 | glibc ≥ 2.35 (Ubuntu 22.04 / Debian 12 era) | CI builds on `ubuntu-22.04` |
| Linux | aarch64 | glibc ≥ 2.39 (built on `ubuntu-24.04-arm`) | best-effort tier |

SDL2 (bundled by pygame-ce) requires a GPU/driver providing OpenGL 2.1+
or GLES 2.0+ — ubiquitous on every supported OS.

## 4. Locked technology stack

Exact version resolution is committed in `uv.lock`; `pyproject.toml` carries
the compatible-range constraints below.

| Concern | Package | Constraint (pyproject) | Verified state 2026-10-25 |
| --- | --- | --- | --- |
| Interpreter | Python | `>=3.14,<3.15` | 3.15.0 shipped 2026-10-09 but pygame-ce 2.5.8 has no cp315 wheels; 3.14 has verified cp314 wheels for win32/win_amd64, macOS universal2, manylinux2014 x86_64/aarch64/i686 |
| Game framework | `pygame-ce` | `>=2.5.8,<2.6` | the maintained SDL2 fork; classic pygame is stale (no 3.14 wheels) and is **banned** |
| Env & lock | `uv` | `>=0.13.5` (tool, not dep) | lockfile committed; reproducible sync |
| Lint+format | `ruff` | `>=0.17.2,<0.18` | strict select-ALL config (§7) |
| Type check | `mypy` | `>=2.4,<3` | `strict = true` |
| Unit/property tests | `pytest` / `hypothesis` | `>=9.1,<10` / `>=6.170,<7` | property tests mandatory (§12) |
| Coverage | `coverage[toml]` | `>=7.17,<8` | branch coverage ON; fail-under gates (§12) |
| Supply chain audit | `pip-audit` | `>=2.10,<3` | PRs + weekly cron (§13) |
| Save/config dirs | `platformdirs` | `>=4.13,<5` | maintained successor of appdirs |
| TOML writing | `tomli-w` | `>=1.2,<2` | stdlib `tomllib` reads |
| Bundler | `pyinstaller` | `>=6.22.3,<7` (group `build`) | onedir mode only (§15) |
| License manifest | `pip-licenses` (group `build`) | `>=5.5,<6` | regenerates `CREDITS.md` dependency section in CI |
| Git hooks | `pre-commit` (group `dev`) | `>=4.7,<5` | local mirror of CI lint |

**Version policy.**

1. Dependency bumps are always done through dedicated `chore: bump …` PRs that
   run the full gate set (§12/§13). Hand-edits of `uv.lock` are forbidden.
2. A scheduled monthly **ratchet PR**: `uv lock --upgrade`, then `pip-audit`,
   then full gates. Security advisories may be acted on immediately.
3. Interpreter upgrades: move to 3.15 only after every runtime dependency
   ships cp315 wheels for all four release targets and a full gate run passes.
4. pygame-ce upgrades may cross the `<2.6` bound only in a dedicated PR that
   documents behaviour diffs relevant to this repo.

**Banned (legacy) stack — shall not appear on `main`, in CI, or in docs:**

| Banned item | Reason |
| --- | --- |
| PyOpenGL / FreeGLUT / GLUT / immediate-mode OpenGL | legacy API; broken on modern Wayland/macOS; no maintained path |
| classic `pygame` | stale upstream; superseded by pygame-ce |
| `requirements.txt` as primary packaging | non-reproducible; superseded by the uv lock |
| `PyOxidizer` | unmaintained since 2022 |
| `appdirs`, `distutils`, `setup.py`-only packaging | superseded / removed by PEP 632 |
| Python `<3.14` as target | unsupported interpreters |

**Rejected alternatives (decided — do not relitigate in PRs without §18):**
Nuitka (great performance, but a heavy toolchain and slower builds for a solo
maintainer), cx_Freeze (viable fallback if PyInstaller is ever blocked — record
the switch in §18 first), Briefcase (targets app-store packaging we don't use),
Godot/Unity (violates the code-first, test-first mission), C++/SDL3
(maintenance cost without solo-dev payoff).

## 5. Tooling & standard commands

The lockfile is the unit of reproduction. All commands run through `uv`.

| Purpose | Command |
| --- | --- |
| Full env (dev + build groups) | `uv sync --all-groups` |
| Lint (CI gate) | `uv run ruff check .` |
| Format check / apply | `uv run ruff format --check .` / `uv run ruff format .` |
| Type check | `uv run mypy src tests` |
| Tests + coverage | `uv run coverage run -m pytest` then `uv run coverage report` |
| Property tests only | `uv run pytest tests/property -q` |
| GUI-marked tests (headless) | `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy uv run pytest -m gui` |
| Security audit | `uv run pip-audit` |
| Dev build (any OS) | `uv run pyinstaller --clean --noconfirm --onedir --windowed --name hillclimb --noupx src/hillclimb/__main__.py` |
| License manifest | `uv run pip-licenses --format markdown --output-file CREDITS.autogen.md` |

## 6. Repository layout & import law

```
.
├── SPECS.md                  # this contract
├── README.md, CONTRIBUTING.md, SECURITY.md, CHANGELOG.md, LICENSE
├── pyproject.toml, uv.lock, .python-version
├── src/
│   └── hillclimb/
│       ├── __init__.py       # __version__ only
│       ├── __main__.py       # CLI entry (§10.7)
│       ├── engine/           # simulation: ZERO pygame imports
│       │   ├── terrain.py    # seeded procedural heightfield
│       │   ├── vehicle.py    # two-wheel chassis, torque, airtime
│       │   ├── world.py      # collectible spawning per chunk
│       │   ├── scoring.py    # coins/airtime/flip rules
│       │   ├── difficulty.py # ramp curves
│       │   └── rng.py        # named RNG stream factory (§10.2)
│       ├── app/              # pygame-ce presentation layer
│       │   ├── main.py       # game loop (fixed timestep)
│       │   ├── state.py      # BOOT/MENU/PLAY/PAUSED/GAMEOVER machine
│       │   ├── render.py, hud.py, camera.py, particles.py
│       │   ├── audio.py      # music/sfx buses
│       │   └── input.py      # keyboard + gamepad map (§10.6)
│       ├── config.py         # settings load/validate/atomic save
│       └── savedata.py       # best-score persistence
├── assets/                   # CC0/OFL only (§11): audio/, fonts/, graphics/
├── tests/
│   ├── unit/                 # pure engine tests
│   ├── property/             # hypothesis suites (§12)
│   ├── integration/          # headless boot, save/config round-trips
│   └── golden/               # schema-migration fixtures
└── scripts/                  # coverage gate, perf check, asset audit
```

**Import law (machine-checked in CI):**

1. `src/hillclimb/engine/**` must not import `pygame`, `numpy`, `socket`,
   `urllib`, `http`, or `requests`. CI command (must exit 0):
   ```bash
   ! grep -R -nE '^\s*(import|from)\s+(pygame|numpy|socket|http|urllib|requests)' src/hillclimb/engine/
   ```
2. `app` may import `engine`; `engine` must never import `app`.
3. Imports are explicit (`from ..engine import terrain`); star-imports banned.
4. Entry point is `src/hillclimb/__main__.py`; nothing outside the package
   imports from inside it.

## 7. Code standards

**Machine-enforced (config in `pyproject.toml`):**

- ruff with `select = ALL` minus the documented ignore list. Enforced families
  include: `E9,F,B` correctness/bugs; `S` bandit subset (`S102` bans
  `eval`/`exec`, `S506` bans unsafe YAML); `T20` bans `print`/`pdb` outside
  tests; `ANN` full annotations; `D` docstrings (Google style); `N` naming;
  `EM/TRY/EXC` exception hygiene; `PERF` loop efficiency; `FURB` modern idioms;
  `DTZ` timezone safety; `RET/PLR` structure; `A` builtin shadowing.
- `ruff format` (line length 100) is the single formatter.
- mypy `strict = true` (untyped defs, untyped decorators, any-returns,
  unused-ignores all denied). `pygame.*` may need
  `[[tool.mypy.overrides]]` initially; loosening is a tracked cleanup, not a
  permanent licence.
- pytest: `--strict-markers --strict-config`; warnings are errors.

**Review-enforced (human gates):**

1. Functions ≤ 40 lines (hard target; anything > 60 must be split or justified
   in review with a comment anchored in the PR description).
2. Names say what they do; only domain-standard abbreviations (`dt`, `fps`,
   `hud`) allowed.
3. Comments explain **why**, never narrate obvious code. No commented-out code.
4. Module-level mutable globals are forbidden (this killed the original
   university code); state lives on instances. Singletons are injected, not
   imported.
5. Gameplay string/numeric constants live in exactly one module per concern.
6. One PR = one focused change; commits follow Conventional Commits
   (`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`, `perf:`,
   `release:`).

## 8. Architecture & performance budgets

| Metric | Budget | Measurement |
| --- | --- | --- |
| Frame rate | 60 FPS at 1280×720 windowed on Intel-UHD-620-class iGPU | `scripts/perf_check.py` (lands with DoD §17) replaying a scripted 60 s run |
| Cold start to menu | < 2.0 s from process exec | same script |
| Input → visual | < 50 ms typical | scripted latency probe |
| Hot-loop allocations | no per-frame object churn beyond a bounded pool (report in `perf_check.py`) | review + script |
| Release bundle size | ≤ 120 MB per artifact | CI asserts before upload |
| Sim determinism | same seed + same replay → identical score/distance | property test R1 (§12) |

**The simulation runs on a fixed timestep of 120 Hz with an accumulator.**
Frame time is clamped at 100 ms and at most 25 catch-up ticks run per frame —
no death spirals. Rendering is decoupled from simulation; interpolation for
drawing is allowed but never required. The FPS budget must never be "met" by
lowering the simulation rate.

## 9. Data, persistence & privacy

- All user data is written under `platformdirs` paths, and nowhere else:

  | OS | Settings | Saves, best score, logs |
  | --- | --- | --- |
  | Windows | `%APPDATA%\hillclimb\` | `%LOCALAPPDATA%\hillclimb\` |
  | macOS | `~/Library/Application Support/hillclimb/` | same directory |
  | Linux | `$XDG_CONFIG_HOME/hillclimb/` | `$XDG_DATA_HOME/hillclimb/` |

- Settings are TOML (`config.toml`) with top-level `schema_version = 1`,
  written atomically (`tempfile` + `os.replace`) — a crash must never leave a
  partially-written file.
- Saves/best score: JSON with `schema_version`, dataclass-backed; migrations
  are pure functions covered by golden tests (`tests/golden/`); unknown
  fields/values are tolerated (never crash on newer/older schemas); corrupted
  files are moved to `*.corrupt-<timestamp>.bak` and recreated empty.
- Logs: `hillclimb.log`, rotating (5 MB × 3) via `logging`; `--verbose` raises
  verbosity; on crash the full traceback is logged, never shown raw in-UI.
- No telemetry fields, no machine fingerprinting, no identifiers beyond what
  the user typed in.

## 10. Gameplay specification (v0.1.1)

Constants below are tune-able only via a PR that updates **this table and the
tests together** (golden values re-baselined in the same change).

### 10.1 Overview

Endless procedural stage; a single car; collect coins; keep fuel > 0; survive
crashes; distance, score and difficulty grow without bound; one best record is
persisted.

### 10.2 Determinism contract

- All randomness flows through named streams built by `engine/rng.py` from a
  master seed: `terrain`, `items`, `fx` (cosmetics must never affect physics).
- Streams are `random.Random` instances seeded as
  `random.Random(f"{master}:{name}")` — stable across platforms for the pinned
  Python minor (3.14.x).
- `--seed N` reproduces a run deterministically on every platform.

### 10.3 Terrain

- Heightfield generated chunk-wise; O(1) height queries by x (no O(n) global
  arrays; chunks are recycled).
- Property: absolute slope ≤ 60° at difficulty ≥ 3, and reachability: no
  step-up steeper than the car's ground-contact capability (property tests
  §12 T1/T2).
- Difficulty ramps with distance: amplitude, frequency and roughness grow as a
  pure function of distance.

### 10.4 Car physics

- Two point-wheels on a rigid chassis (the model that made the original fun,
  implemented properly): per-wheel ground snap, suspension damping, drive
  torque with speed limiter.
- Top speed 500 px/s. Display as `round(|v|/10 × 3.6)` km/h; **10 px = 1 m**.
- Game over when: (a) fuel reaches 0 and the car comes to rest, or
  (b) the driver's head vertex touches terrain while the car is in motion.

### 10.5 Pickups, fuel & scoring

| Rule | Value |
| --- | --- |
| Coin values | {50, 100, 200, 500, 1000, 5000} weighted {0.40, 0.25, 0.15, 0.12, 0.06, 0.02} |
| Airtime bonus | +50 per full airborne second, doubling each further full second (the original mechanic, kept) |
| Flip bonus | +100 per full 360° rotation while airborne |
| Fuel | max 100.0 L; drain/s = `0.55 + |v|·0.012·difficulty-factor`; a fuel can refills to full |
| Fuel guarantee | expected time between fuel cans ≤ 45 s for any seed at difficulty ≤ 5 (property-tested over 100 seeds) |
| Item spacing | coins and cans never overlap or spawn inside terrain; minimum inter-item gap 25 m |

### 10.6 Input

| Action | Keyboard | Gamepad default |
| --- | --- | --- |
| Accelerate | → / D | A (bottom face) |
| Brake / reverse | ← / A | X (left face) |
| Pause / menu | Esc | Start |
| Restart run | R | Y (top face) |
| Menu confirm / back | Enter / Esc | A / B |

Keyboard is fully remappable in settings. Gamepad mapping uses SDL standard
mapping glyphs — no per-device `.guid` handling.

### 10.7 CLI (module `__main__.py`), required flags

| Flag | Behaviour |
| --- | --- |
| `--seed N` | deterministic run seed (used by tests/CI) |
| `--version` | print `hillclimb <semver>` (from installed metadata) and exit 0 |
| `--selftest` | boot simulation + a headless pass (≤ 5 s simulated), exit 0 on success / 3 on failure; used by release smoke tests; never opens a window |
| `--safe-mode` | 800×450 window, no audio, default settings; troubleshooting |

## 11. Audio & assets

- Formats: OGG Vorbis for music; 16-bit 44.1 kHz WAV for SFX. Buses:
  master/music/sfx (0–100, persisted). Channels: music 1, SFX 8.
- Licenses: **CC0 or OFL only** (Kenney packs, OFL fonts are pre-vetted
  candidates). Every `assets/` subdirectory must contain a `LICENSE` file
  naming pack origin and license; CI fails if missing. MP3 and any
  license-uncertain asset are banned. `CREDITS.md` lists each pack with
  author, license and URL.

## 12. Testing gates

**Machine-enforced, all green before merge.**

1. **Coverage** (branch mode ON):
   - total ≥ 85% (`--fail-under=85`, wired from day one);
   - engine-specific ≥ 97% — the gate lands together with the first engine
     module (`scripts/coverage_gate.py`: `coverage json` → per-directory floor
     enforced in CI).
2. **Property tests** (hypothesis, `tests/property/`) are mandatory:
   - `T1` terrain slope bound; `T2` terrain reachability; `T3` fuel ∈ [0, 100];
   - `R1` replay determinism (seed + scripted inputs → exact score/distance
     equality across platforms);
   - `S1` score monotonicity under replays;
   - `P1` pickup spacing & fuel-guarantee property;
   - `M1` config/save schema round-trip + migration property.
3. **GUI tests** run headless (`SDL_VIDEODRIVER=dummy`): boot → MENU,
   PLAY⇄PAUSED→GAMEOVER→PLAY, clean shutdown. Marked `gui`; skipped in devs'
   sandboxes without SDL video, but always run on CI.
4. **Anti-slop rules for tests:** no `time.sleep` pacing, no network, no
   unseeded randomness, single test ≤ 2 s (except `perf`-marked), and no test
   may assert implementation details — observable behaviour only.
5. A change that lowers any gate must include a §18 spec-change justification
   in the PR body, or the PR is rejected.

## 13. Security & supply chain

- `pip-audit` runs on every PR against the locked environment and weekly on
  `main`; any known vulnerability fails CI (PyPI Advisory Database).
- GitHub Actions are pinned to full commit SHAs — never tags. Dependabot
  monitors action updates (weekly).
- No runtime network: CI runs the import-ban of §6 on `engine/**` and a
  `src/**` ban for `socket/http/urllib/requests/ftplib/telnetlib` outside an
  allow-list that is empty in v0.1.1.
- Package source: PyPI only (uv default); no wheel URLs from foreign hosts;
  `uv sync --locked` everywhere (no silent lock drift).
- No secrets expected; none may ever be committed; `.env*` is gitignored.
- SECURITY.md routes reports to GitHub private security advisories.

## 14. Release engineering (cross-platform, dependency-free)

- **Bundling:** PyInstaller `onedir` only — fast startup, lower
  antivirus false-positive rate than `onefile`, no self-extraction to temp.
  `--noupx` mandatory (UPX bloats and triggers AV flags).
- **Runners:** `ubuntu-22.04` (x86_64), `ubuntu-24.04-arm` (aarch64),
  `macos-15` (arm64), `windows-2025` (amd64). `uv` prepares the env; SDL2 and
  everything else come bundled inside the artifact.
- **Artifacts (one set per tagged 0.x release):**
  - `hillclimb-v{ver}-linux-x86_64.tar.gz`, `hillclimb-v{ver}-linux-aarch64.tar.gz`
  - `hillclimb-v{ver}-macos-arm64.zip` (a `.app` inside the zip)
  - `hillclimb-v{ver}-windows-amd64.zip`
  - `SHA256SUMS.txt` (aggregated per-platform `.sha256` files)
- **Smoke test before upload, on each native runner:** launch the packaged
  binary with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy` and `--selftest`
  (macOS: the binary inside `.app/Contents/MacOS/`). Nonzero exit fails the
  release job.
- **First-run guidance** (unsigned by choice — no certificates): each release
  README documents the standard bypasses: macOS `xattr -dr com.apple.quarantine`
  / right-click → Open; Windows SmartScreen → "More info" → "Run anyway"
  (plus how to report an AV false positive); Linux needs nothing beyond
  `chmod +x` on first run of the tarball binary.
- **Versioning:** SemVer 0.x — `v0.1.1` is the first public tag; `0.2.x` may
  break feature data compatibility. `__version__` is read from installed
  metadata at runtime, never duplicated in code.
- **Process:** tag `vX.Y.Z` on `main` once the §17 checklist is fully checked;
  CI creates the GitHub Release and attaches artifacts; the release notes body
  is copied from that tag's CHANGELOG section.

## 15. Current CI jobs

| Job | Runs | Gates |
| --- | --- | --- |
| `lint` | every PR + push to `main` | ruff check, ruff format --check |
| `types` | same | mypy strict (skips cleanly until `src/` exists) |
| `test` | same | coverage run + `--fail-under=85` (skips cleanly until `tests/` exists) |
| `rules` | same | engine-purity import ban, repo-wide network-import ban |
| `audit` | PRs + weekly cron | pip-audit fails on any known CVE |
| `release` | tag `v*` push | build + smoke on 4 runners, attach artifacts (fails until the entry point exists — intended) |

## 16. Milestones after 0.1.1 (not commitments)

0.2.x candidates: second vehicle, upgrade shop, additional stage. The commit
path for any of them is a §18 spec amendment — features never arrive
unannounced.

## 17. Definition of Done — v0.1.1

- [ ] All CI jobs green on `main` (lint, types, test, rules, audit).
- [ ] Engine + app code complete per §6, §8, §10, §11; property/golden suites pass.
- [ ] `--selftest` green on all four release platforms from the packaged builds.
- [ ] Engine coverage ≥ 97%, total ≥ 85%; `scripts/coverage_gate.py` wired.
- [ ] Performance budgets of §8 verified and numbers recorded in release notes.
- [ ] Assets ship with provenance (§11); CREDITS.md complete.
- [ ] README updated with a download table + Gatekeeper/SmartScreen guidance.
- [ ] CHANGELOG.md finalized for `v0.1.1`; tag pushed; artifacts attached; release published.

## 18. Amending this document

1. Any change to SPECS is its own PR titled `spec: …`, touching only this file
   (minimal diff), with a summary of what changed and why.
2. CI must still be green; the PR body must list exactly which sections were
   touched so reviewers can diff quickly.
3. Emergency changes at release time are allowed but must be re-reviewed
   within seven days.

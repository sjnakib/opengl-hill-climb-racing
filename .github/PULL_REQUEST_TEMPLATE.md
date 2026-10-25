## What

<!--
One focused change per PR. Link the issue/DoD item it implements.
State which SPECS.md sections this touches.
-->

SPECS sections affected: §

## How tested

- [ ] `uv run ruff check .` green
- [ ] `uv run ruff format --check .` green
- [ ] `uv run mypy src tests` green
- [ ] `uv run coverage run -m pytest && uv run coverage report` green (≥ 85% total)
- [ ] New/changed behavior covered by tests (unit/property/integration — listed below)
- [ ] No new runtime dependencies (or accompanied by a SPECS §4 bump PR)
- [ ] No network code paths (permanent ban — SPECS §2, §13)
- [ ] CHANGELOG.md updated (feat/fix entries as applicable)
- [ ] Assets added? → provenance + license note included (SPECS §11)

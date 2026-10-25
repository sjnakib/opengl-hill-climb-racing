## What

One focused change per PR. Link the issue or DoD item it implements, and name
the SPECS.md sections it touches.

SPECS sections affected: §

## How tested

- [ ] `uv run ruff check .` green
- [ ] `uv run ruff format --check .` green
- [ ] `uv run mypy src tests` green
- [ ] `uv run coverage run -m pytest && uv run coverage report` green, at
      least 85 percent total
- [ ] New or changed behavior covered by tests, listed below (unit, property,
      integration)
- [ ] No new runtime dependencies, or a SPECS §4 bump PR alongside
- [ ] No network code paths, permanent ban (SPECS §2, §13)
- [ ] Markdown files pass the prose gate: `uv run vale <touched files>`
      (SPECS §19)
- [ ] CHANGELOG.md updated with the feat or fix entries
- [ ] Assets added, if any, with provenance and a license note (SPECS §11)

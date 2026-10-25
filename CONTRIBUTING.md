# Contributing

`SPECS.md` is the binding contract. If behaviour and SPECS disagree, the code
is wrong — or the spec needs a dedicated amendment (SPECS §18).

## Setup

```bash
uv sync --all-groups
uv run pre-commit install
```

## Before every push

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run coverage run -m pytest && uv run coverage report
uv run pip-audit
```

## Rules of the road

1. Commits use Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`,
   `test:`, `refactor:`, `perf:`, `release:`). `main` accepts squash-merges only.
2. One PR = one change. The PR-template checklist is admission — deleting
   checklist items closes the PR.
3. No `print()` debugging; use `logging`. No `TODO` without context in SPECS
   §7 terms (rule codes allow it, review may not).
4. The engine layer **never** imports pygame (SPECS §6). If you feel you need
   it, restructure instead.
5. Coverage may never drop (85% overall floor; 97% engine floor once its gate
   lands — SPECS §12).
6. Dependencies change only through dedicated bump PRs, never "while in there".
7. Gameplay numbers change only together with the constant tables in
   SPECS §10, in the same PR.
8. The `university/fall-2024` branch is read-only history; never "modernize" it.
9. Until the first game module lands, CI's `types`/`test` jobs skip cleanly —
   don't treat the skips as green lights: SPECS §17 defines what done means.

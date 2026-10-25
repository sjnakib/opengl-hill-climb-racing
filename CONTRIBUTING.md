# Contributing

SPECS.md is the binding contract. If behavior and SPECS disagree, the code is
wrong, or the spec needs a dedicated amendment (SPECS §18).

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

Markdown changes also run through the prose gate before you push:

```bash
uv run vale README.md CHANGELOG.md CONTRIBUTING.md SECURITY.md SPECS.md \
  .github/PULL_REQUEST_TEMPLATE.md
```

## Rules of the road

1. Commits use Conventional Commits, like `feat:`, `fix:`, `docs:`, `chore:`,
   `test:`, `refactor:`, `perf:`, `release:`. Merges to `main` are squash
   merges only.
2. One PR holds one change. The PR template checklist is part of review.
   Removing checklist items can close the PR.
3. Debug with `logging`, not `print()`.
4. The engine layer never imports pygame (SPECS §6). If you feel you need it,
   restructure instead.
5. Coverage never drops. The floors stay at 85 percent overall and 97 percent
   for the engine once that gate lands (SPECS §12).
6. Dependencies change only in dedicated bump PRs, never "while you're in
   there".
7. Gameplay numbers change only together with the constant tables in
   SPECS §10, in the same PR.
8. All writing follows SPECS §19: plain, concise, natural. Markdown files
   also pass the vale gate, and new markdown files join that gate.
9. The `university/fall-2024` branch is read-only history. Never "modernize"
   it.
10. Until the first game module lands, the CI `types` and `test` jobs skip
    cleanly. Treat the skips as progress markers, not green lights. SPECS §17
    defines what done means.

# Contributing

SPECS.md is the binding contract. If behavior and SPECS disagree, the code is
wrong, or the spec needs a dedicated amendment (SPECS §18).

## Setup

```bash
uv sync --all-groups
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push
```

## Branch verification, first and every time

```bash
git status -sb
git branch --show-current
```

Run both before any edit, any pull, and any commit, and every time you
return to a terminal or a coding agent session. If the checked-out branch
is not the one the task expects, switch first. A merged PR can leave the
tree standing on its own stale feature branch.

Local guards (SPECS §7) reject the failure modes mechanically:

- Commits from a detached HEAD, or on a branch that is neither `main` nor a
  conventional prefix, are refused.
- Commit lanes map to branches: `spec:`, `docs:`, `chore:`, and `release:`
  on `main`; `feat:`, `fix:`, `test:`, `refactor:`, `perf:`, and `ci:` on a
  prefixed branch.
- Every push must move the current branch at HEAD. `git push origin main`
  from another branch is refused instead of silently pushing a stale ref,
  and deleting `main` or the `university/` archive is refused.

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
   `test:`, `refactor:`, `perf:`, `release:`, `ci:`. Changes reach `main`
   through pull requests whose final merge GitHub performs.
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
10. Every CI gate runs on every PR. The `types` and `test` jobs now check the
    package skeleton, and `test` also enforces the engine coverage floor
    (SPECS §12). SPECS §17 defines what done means.
11. Branch verification comes first: `git status -sb` and
    `git branch --show-current` before edits, pulls, and pushes. The guards
    in `scripts/branch_guard.py` refuse wrong-branch work mechanically
    (SPECS §7); if one refuses you, fix the branch context, never bypass it.

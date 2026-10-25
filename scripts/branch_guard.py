"""Branch verification guards for local git hooks (SPECS §7).

Three subcommands wire three pre-commit hooks:

- ``verify-commit`` (pre-commit): refuses to commit from a detached HEAD
  or from a branch that is neither ``main`` nor a conventional prefix.
- ``verify-lane`` (commit-msg): maps the commit subject to a branch lane.
  ``spec:``, ``docs:``, ``chore:``, and ``release:`` commits belong on
  ``main``; ``feat:``, ``fix:``, ``test:``, ``refactor:``, ``perf:``, and
  ``ci:`` commits belong on a prefixed branch. Merge subjects pass.
- ``verify-push`` (pre-push): reads pushed refs from stdin and requires
  each pushed ref to be exactly the current branch at HEAD. A stale ref,
  like pushing ``main`` while standing on a feature branch, is refused.
  Deleting ``main`` or the ``university/`` archive is refused.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

ZERO_SHA = "0" * 40

PUSH_FIELD_COUNT = 4
LANE_ARGS_COUNT = 2

PROTECTED_REMOTE_BRANCHES = ("main", "university/fall-2024")

BRANCH_SHAPE = re.compile(
    r"^(?:main$|(?:spec|docs|chore|feat|fix|test|refactor|perf|release|ci)/.+)$"
)

MAIN_ONLY_PREFIXES = ("spec:", "docs:", "chore:", "release:")
BRANCH_ONLY_PREFIXES = ("feat:", "fix:", "test:", "refactor:", "perf:", "ci:")

USAGE = "usage: branch_guard.py [verify-commit|verify-lane <msgfile>|verify-push]\n"


class GuardError(RuntimeError):
    """Raised when a guard refuses the git state."""


def _git(*args: str) -> str:
    """Run git and return its stripped stdout."""
    result = subprocess.run(("git", *args), capture_output=True, text=True, check=True)
    return result.stdout.strip()


def current_branch() -> str:
    """Return the checked-out branch name, refusing a detached HEAD."""
    branch = _git("branch", "--show-current")
    if not branch:
        message = "detached HEAD; check out a branch first (git switch main)"
        raise GuardError(message)
    return branch


def head_sha() -> str:
    """Return the full sha of the current HEAD commit."""
    return _git("rev-parse", "HEAD")


def verify_commit() -> None:
    """Refuse commits from a detached HEAD or a non-conventional branch."""
    branch = current_branch()
    if not BRANCH_SHAPE.match(branch):
        message = (
            f"branch {branch!r} is neither main nor a conventional prefix,"
            " like feat/my-feature; git switch <branch> first"
        )
        raise GuardError(message)


def _first_subject(message_text: str) -> str:
    """Return the first non-empty, non-comment line of a commit message."""
    for line in message_text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return ""


def verify_lane(message_path: str) -> None:
    """Map the commit subject's lane to the branch it must land on."""
    text = Path(message_path).read_text(encoding="utf-8")
    subject = _first_subject(text)
    branch = current_branch()
    if subject.startswith("Merge "):
        return
    lane = subject.split(":", 1)[0]
    if subject.startswith(MAIN_ONLY_PREFIXES):
        if branch != "main":
            message = f"{lane} commits belong on main; git switch main"
            raise GuardError(message)
    elif subject.startswith(BRANCH_ONLY_PREFIXES):
        if branch == "main":
            message = f"{lane} commits belong on a feature branch, not main"
            raise GuardError(message)
        if not BRANCH_SHAPE.match(branch):
            message = f"branch {branch!r} does not carry a conventional prefix"
            raise GuardError(message)
    else:
        message = (
            f"commit subject {subject!r} is not a Conventional Commit"
            " (feat:, fix:, docs:, chore:, test:, refactor:, perf:, release:, ci:)"
        )
        raise GuardError(message)


def verify_push_lines(lines: Iterable[str], *, branch: str, head: str) -> None:
    """Verify every pushed ref against the current branch at HEAD."""
    for line in lines:
        fields = line.split()
        if len(fields) != PUSH_FIELD_COUNT:
            message = f"malformed pre-push line {line!r}"
            raise GuardError(message)
        _local_ref, local_sha, remote_ref, _remote_sha = fields
        remote_branch = remote_ref.removeprefix("refs/heads/")
        if local_sha == ZERO_SHA:
            if remote_branch in PROTECTED_REMOTE_BRANCHES:
                message = f"deleting protected branch {remote_branch!r} is denied"
                raise GuardError(message)
            continue
        if remote_ref != f"refs/heads/{branch}" or local_sha != head:
            message = (
                "wrong push target: pushes move the current branch at HEAD"
                f" ({branch!r} at {head[:12]}), not {remote_ref!r};"
                " run git status -sb and switch branches first"
            )
            raise GuardError(message)


def verify_push() -> None:
    """Verify the refs git feeds this hook on stdin."""
    refs = sys.stdin.read().splitlines()
    verify_push_lines(refs, branch=current_branch(), head=head_sha())


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch the subcommands for the git hooks."""
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if args == ["verify-commit"]:
            verify_commit()
        elif len(args) == LANE_ARGS_COUNT and args[0] == "verify-lane":
            verify_lane(args[1])
        elif args == ["verify-push"]:
            verify_push()
        else:
            sys.stderr.write(USAGE)
            return 2
    except GuardError as error:
        sys.stderr.write(f"branch-guard: {error}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

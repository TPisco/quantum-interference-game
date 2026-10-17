"""Commit everything and push it to GitHub in one step.

    python tools/push.py "Add the interference curve"
    python tools/push.py "Fix typo" --branch my-feature   # push to another branch
    python tools/push.py "WIP" --no-tests                 # skip pytest

Or from Python:

    from tools.push import push_to_github
    push_to_github("Add the interference curve")

It runs the test suite first (stops if a test fails), stages every change,
commits with your message and pushes the current branch to ``origin``,
creating the branch on GitHub the first time. It uses your own git
credentials, so run it on your computer, inside the repository.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class PushError(RuntimeError):
    pass


def _git(*args: str, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise PushError(f"git {' '.join(args)} failed:\n{proc.stderr.strip() or proc.stdout.strip()}")
    return proc.stdout.strip()


def push_to_github(message: str, branch: str | None = None, run_tests: bool = True,
                   remote: str = "origin") -> str:
    """Test, stage, commit and push. Returns the pushed branch name.

    message:    commit message (required, not empty)
    branch:     branch to push to; default is the branch you are on
    run_tests:  run pytest first and stop if anything fails
    remote:     git remote name (default "origin")
    """
    if not message or not message.strip():
        raise PushError("Give a commit message, e.g. push_to_github(\"Add level 6\").")
    _git("rev-parse", "--is-inside-work-tree")
    if remote not in _git("remote").split():
        raise PushError(f"No remote named {remote!r}. Add one with: git remote add {remote} <url>")

    current = _git("symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if not current:
        raise PushError("You are not on a branch (detached HEAD). Run: git switch <branch>")
    target = branch or current
    if branch and branch != current:
        exists = _git("rev-parse", "--verify", "--quiet", branch, check=False)
        _git("switch", branch) if exists else _git("switch", "-c", branch)

    if run_tests:
        print("Running tests...")
        tests = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT)
        if tests.returncode != 0:
            raise PushError("Tests failed, nothing was committed. Fix them or use --no-tests.")

    _git("add", "-A")
    if _git("status", "--porcelain"):
        _git("commit", "-m", message.strip())
        print(f"Committed: {message.strip()}")
    else:
        print("Nothing new to commit; pushing existing commits.")

    print(f"Pushing {target} to {remote}...")
    _git("push", "-u", remote, target)
    url = _git("remote", "get-url", remote).removesuffix(".git")
    if url.startswith("git@github.com:"):
        url = "https://github.com/" + url.split(":", 1)[1]
    print(f"Done: {url}/tree/{target}")
    return target


def main() -> None:
    ap = argparse.ArgumentParser(description="Commit all changes and push them to GitHub.")
    ap.add_argument("message", help="commit message")
    ap.add_argument("--branch", help="branch to push to (default: the current branch)")
    ap.add_argument("--no-tests", action="store_true", help="do not run pytest first")
    ap.add_argument("--remote", default="origin", help="git remote (default: origin)")
    args = ap.parse_args()
    try:
        push_to_github(args.message, branch=args.branch, run_tests=not args.no_tests,
                       remote=args.remote)
    except PushError as exc:
        sys.exit(f"Error: {exc}")


if __name__ == "__main__":
    main()

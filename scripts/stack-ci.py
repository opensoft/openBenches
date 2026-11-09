"""Verify GitHub Actions checked out the exact PR merge or queue candidate."""

import argparse
import os
import re
import subprocess
import sys


def git(*args):
    return subprocess.check_output(["git", *args])


def sha(value):
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("Expected a full commit SHA")
    return value


def eligible_paths(paths):
    return bool(paths) and all(
        path == b"docs/task-set-delivery.md"
        or re.fullmatch(rb"\.specify/templates/[^/]+\.md", path)
        for path in paths
    )


def verify(mode, env):
    candidate = sha(env["GITHUB_SHA"])
    if git("rev-parse", "HEAD").decode().strip() != candidate:
        raise ValueError("Checkout does not match the candidate SHA")
    if mode == "fast":
        if env["GITHUB_EVENT_NAME"] != "pull_request":
            raise ValueError("Fast CI requires a pull_request event")
        head, base = sha(env["PR_HEAD"]), sha(env["PR_BASE"])
        # Verify the actual GitHub test-merge parents, not merely ancestry.
        parents = git("show", "-s", "--format=%P", candidate).decode().split()
        if parents != [base, head]:
            raise ValueError("Candidate parents do not match the immediate base and PR head")
        print(f"PR head: {head}; immediate base: {base}; tested: {candidate}")
    else:
        base = sha(git("rev-parse", "refs/remotes/origin/main").decode().strip())
        git("merge-base", "--is-ancestor", base, candidate)
        paths = git("diff", "--name-only", "--no-renames", "-z", base, candidate)
        if not eligible_paths(paths.split(b"\0")[:-1]):
            raise ValueError("Combined candidate is empty or outside the canary path allowlist")
        tree = git("rev-parse", f"{candidate}^{{tree}}").decode().strip()
        print(f"Queue candidate: {candidate}; main: {base}; tested tree: {tree}")
    git("diff", "--check", base, candidate)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("fast", "heavy"))
    try:
        verify(parser.parse_args().mode, os.environ)
    except (KeyError, ValueError, subprocess.CalledProcessError) as exc:
        sys.exit(f"stack-ci: {exc}")

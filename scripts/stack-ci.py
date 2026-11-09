"""Verify GitHub Actions checked out the exact PR merge or queue candidate."""

import argparse
import json
import os
import re
import subprocess
import sys


HELPER_TEST = "devBenches/devcontainer.test/test-speckit-git-feature.sh"
HELPER_PATHS = {
    b"devBenches/base-image/files/speckit-worktree/templates/specify/extensions/git/scripts/bash/get-last-worktree.sh",
    HELPER_TEST.encode(),
}
HELPER_BRANCH = "ci/stack-helpers/"
HELPER_APPROVAL = "openbenches-helper-reviewed"


def git(*args):
    return subprocess.check_output(["git", *args])


def sha(value):
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("Expected a full commit SHA")
    return value


def changed_paths(base, head, run_git=git):
    result = run_git("diff", "--name-only", "--no-renames", "-z", base, head)
    return set(result.split(b"\0")[:-1])


def docs_paths(paths):
    return bool(paths) and all(
        path == b"docs/task-set-delivery.md"
        or re.fullmatch(rb"\.specify/templates/[^/]+\.md", path)
        for path in paths
    )


def github(repo, endpoint):
    return json.loads(subprocess.check_output(
        ["gh", "api", f"repos/{repo}/{endpoint}"], timeout=30
    ))


def verify_helper_batch(base, candidate, repo, request=github, run_git=git):
    """Match the candidate's ordered merge parents to one exact reviewed stack."""
    commits = run_git("rev-list", "--first-parent", "--reverse", f"{base}..{candidate}")
    merges = commits.decode().splitlines()
    if not 2 <= len(merges) <= 3:
        raise ValueError("Helper batch must contain two or three merge commits")

    previous, immediate_base, base_ref = base, base, "main"
    approved_stack = None
    for index, merge in enumerate(merges):
        parents = run_git("show", "-s", "--format=%P", merge).decode().split()
        if len(parents) != 2 or parents[0] != previous:
            raise ValueError("Helper batch does not have the expected merge chain")
        head = sha(parents[1])
        statuses = request(repo, f"commits/{head}/status")["statuses"]
        receipts = [s for s in statuses if s["context"] == HELPER_APPROVAL]
        if len(receipts) != 1 or receipts[0]["state"] != "success":
            raise ValueError(f"Missing successful helper approval for {head}")
        receipt = re.fullmatch(
            r"base=([0-9a-f]{40}) stack=([1-9]\d*(?:,[1-9]\d*){1,2})",
            receipts[0]["description"] or "",
        )
        if not receipt or receipt[1] != immediate_base:
            raise ValueError(f"Helper approval does not match the immediate base for {head}")
        members = receipt[2].split(",")
        if (len(members) != len(merges) or len(set(members)) != len(members)
                or (approved_stack is not None and members != approved_stack)):
            raise ValueError("Helper approvals do not identify this exact batch")
        approved_stack = members

        number = members[index]
        pr = request(repo, f"pulls/{number}")
        if (pr["state"] != "open" or pr["draft"] or
                pr["head"]["repo"]["full_name"].lower() != repo.lower() or
                pr["base"]["repo"]["full_name"].lower() != repo.lower() or
                pr["head"]["sha"] != head or pr["base"]["sha"] != immediate_base or
                pr["base"]["ref"] != base_ref or
                not pr["head"]["ref"].startswith(HELPER_BRANCH)):
            raise ValueError(f"Helper PR #{number} no longer matches its reviewed head/base")
        if index and not re.search(
            rf"(?m)^Depends-On: #{members[index - 1]}[ \t\r]*$", pr["body"] or ""
        ):
            raise ValueError(f"Helper PR #{number} is missing its predecessor")
        run_git("merge-base", "--is-ancestor", immediate_base, head)
        paths = changed_paths(immediate_base, head, run_git)
        if not paths or not paths <= HELPER_PATHS:
            raise ValueError(f"Helper PR #{number} touches a path outside the pilot")
        previous, immediate_base, base_ref = merge, head, pr["head"]["ref"]
    print(f"Verified helper batch: {', '.join('#' + n for n in approved_stack)}")


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
        paths = changed_paths(base, candidate)
        if paths and paths <= HELPER_PATHS:
            verify_helper_batch(base, candidate, env["GITHUB_REPOSITORY"])
        elif not docs_paths(paths):
            raise ValueError("Combined candidate is empty or outside the canary path allowlist")
        tree = git("rev-parse", f"{candidate}^{{tree}}").decode().strip()
        print(f"Queue candidate: {candidate}; main: {base}; tested tree: {tree}")
    git("diff", "--check", base, candidate)
    if mode == "fast" and changed_paths(base, candidate) & HELPER_PATHS:
        subprocess.run(["bash", HELPER_TEST], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("fast", "heavy"))
    try:
        verify(parser.parse_args().mode, os.environ)
    except (KeyError, TypeError, ValueError, subprocess.SubprocessError) as exc:
        sys.exit(f"stack-ci: {exc}")

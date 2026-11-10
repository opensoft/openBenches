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
PROJECT_TEST = "devcontainer.test/test-project-command.py"
PROJECT_PATHS = {b"scripts/project", PROJECT_TEST.encode()}
WAVE_SCRIPT = "scripts/sync-wave-widgets.sh"
WAVE_RECONCILER = "scripts/sync-wave-widgets.py"
WAVE_TEST = "devcontainer.test/test-wave-widget-sync.py"
WAVE_PATHS = {path.encode() for path in (WAVE_SCRIPT, WAVE_RECONCILER, WAVE_TEST)}
STACK_SCOPES = {
    "helper": (HELPER_PATHS, "ci/stack-helpers/", "openbenches-helper-reviewed"),
    "project": (PROJECT_PATHS, "ci/stack-project/", "openbenches-project-reviewed"),
    "wave-widget-sync": (
        WAVE_PATHS, "ci/stack-wave-widget-sync/", "openbenches-wave-widget-sync-reviewed",
    ),
}


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


def wave_pr_qualified(event, main, repo, request=github, run_git=git):
    """Select the cheap path only from a current, explicitly opted-in chain."""
    try:
        sha(main)
        number = event["number"]
        seen = set()
        expected = event["pull_request"]
        for _ in range(3):
            if type(number) is not int or number < 1 or number in seen:
                return False
            seen.add(number)
            pr = request(repo, f"pulls/{number}")
            if (pr["number"] != number or pr["state"] != "open" or pr["draft"]
                    or any(pr[ref]["repo"]["full_name"].lower() != repo.lower()
                           for ref in ("head", "base"))
                    or any(pr[ref]["sha"] != expected[ref]["sha"]
                           or pr[ref]["ref"] != expected[ref]["ref"]
                           for ref in ("head", "base"))
                    or not re.fullmatch(r"ci/stack-wave-widget-sync/.+", pr["head"]["ref"])
                    or not re.search(r"(?m)^Stack-CI: wave-widget-sync[ \t\r]*$", pr["body"] or "")):
                return False
            head, base = sha(pr["head"]["sha"]), sha(pr["base"]["sha"])
            run_git("fetch", "--no-tags", "origin", head)
            run_git("merge-base", "--is-ancestor", main, head)
            run_git("merge-base", "--is-ancestor", base, head)
            for start in (main, base):
                raw = run_git("diff", "--raw", "--no-abbrev", "--no-renames", "-z", start, head)
                fields = raw.split(b"\0")
                if fields[-1] != b"" or len(fields) < 3 or len(fields) % 2 != 1:
                    return False
                for header, path in zip(fields[0:-1:2], fields[1:-1:2]):
                    old_mode, new_mode, _old, _new, status = header.lstrip(b":").split()
                    if (path not in WAVE_PATHS or status != b"M"
                            or old_mode not in (b"100644", b"100755") or old_mode != new_mode):
                        return False
            dependencies = re.findall(r"(?m)^Depends-On:[^\n]*", pr["body"] or "")
            if pr["base"]["ref"] == "main":
                return (base == main and not dependencies
                        and request(repo, "branches/main")["commit"]["sha"] == main)
            if len(dependencies) != 1:
                return False
            dependency = re.fullmatch(r"Depends-On: #([1-9]\d*)[ \t\r]*", dependencies[0])
            if not dependency:
                return False
            number = int(dependency[1])
            parent = request(repo, f"pulls/{number}")
            if parent["head"]["sha"] != base or parent["head"]["ref"] != pr["base"]["ref"]:
                return False
            expected = parent
        return False
    except (KeyError, TypeError, ValueError, AttributeError, OSError, subprocess.SubprocessError):
        return False


def merged_wave_metadata(event, repo, request=github):
    """Ignore only delayed edits to an already-merged, opted-in Wave PR."""
    try:
        number = event["number"]
        if event["action"] != "edited" or type(number) is not int or number < 1:
            return False
        expected = event["pull_request"]["head"]
        pr = request(repo, f"pulls/{number}")
        if (pr["number"] != number or pr["state"] != "closed" or pr["merged"] is not True
                or pr["head"]["sha"] != sha(expected["sha"])
                or pr["head"]["ref"] != expected["ref"]
                or expected["repo"]["full_name"].lower() != repo.lower()
                or any(pr[ref]["repo"]["full_name"].lower() != repo.lower()
                       for ref in ("head", "base"))
                or pr["base"]["ref"] != "main"
                or not re.fullmatch(r"ci/stack-wave-widget-sync/.+", pr["head"]["ref"])
                or not re.search(r"(?m)^Stack-CI: wave-widget-sync[ \t\r]*$", pr["body"] or "")):
            return False
        sha(pr["merge_commit_sha"])
        files = request(repo, f"pulls/{number}/files?per_page=100")
        return (type(pr["changed_files"]) is int
                and 1 <= pr["changed_files"] == len(files) <= len(WAVE_PATHS)
                and all(file["filename"].encode() in WAVE_PATHS
                        and file["status"] == "modified" for file in files))
    except (KeyError, TypeError, ValueError, AttributeError, OSError, subprocess.SubprocessError):
        return False


def classify_wave(env):
    """Write only an explicit true result; every uncertainty retains full CI."""
    qualified = False
    merged_metadata = False
    try:
        if env["GITHUB_EVENT_NAME"] == "pull_request" and env["GITHUB_REPOSITORY"] == "opensoft/openBenches":
            with open(env["GITHUB_EVENT_PATH"], encoding="utf-8") as source:
                event = json.load(source)
            merged_metadata = merged_wave_metadata(event, env["GITHUB_REPOSITORY"])
            if not merged_metadata:
                main = git("rev-parse", "HEAD").decode().strip()
                qualified = wave_pr_qualified(event, main, env["GITHUB_REPOSITORY"])
    except (KeyError, TypeError, ValueError, OSError, subprocess.SubprocessError):
        pass
    value = "true" if qualified else "false"
    with open(env["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        print(f"wave_only={value}", file=output)
        print(f"merged_metadata={'true' if merged_metadata else 'false'}", file=output)
    print(f"Wave-only efficiency: {value}; full workstation checks: {not (qualified or merged_metadata)}")
    print(f"Merged Wave metadata: {merged_metadata}")


def candidate_scope(paths):
    for scope, (allowed, _, _) in STACK_SCOPES.items():
        if paths and paths <= allowed:
            return scope
    if docs_paths(paths):
        return "docs"
    raise ValueError("Combined candidate is empty or outside the canary path allowlist")


def verify_batch(base, candidate, repo, scope, request=github, run_git=git):
    """Match the candidate's ordered merge parents to one exact reviewed stack."""
    allowed, branch_prefix, approval_context = STACK_SCOPES[scope]
    label = scope.capitalize()
    commits = run_git("rev-list", "--first-parent", "--reverse", f"{base}..{candidate}")
    merges = commits.decode().splitlines()
    if not 2 <= len(merges) <= 3:
        raise ValueError(f"{label} batch must contain two or three merge commits")

    previous, immediate_base, base_ref = base, base, "main"
    approved_stack = None
    for index, merge in enumerate(merges):
        parents = run_git("show", "-s", "--format=%P", merge).decode().split()
        if len(parents) != 2 or parents[0] != previous:
            raise ValueError(f"{label} batch does not have the expected merge chain")
        head = sha(parents[1])
        statuses = request(repo, f"commits/{head}/status")["statuses"]
        receipts = [s for s in statuses if s["context"] == approval_context]
        if len(receipts) != 1 or receipts[0]["state"] != "success":
            raise ValueError(f"Missing successful {scope} approval for {head}")
        receipt = re.fullmatch(
            r"base=([0-9a-f]{40}) stack=([1-9]\d*(?:,[1-9]\d*){1,2})",
            receipts[0]["description"] or "",
        )
        if not receipt or receipt[1] != immediate_base:
            raise ValueError(f"{label} approval does not match the immediate base for {head}")
        members = receipt[2].split(",")
        if (len(members) != len(merges) or len(set(members)) != len(members)
                or (approved_stack is not None and members != approved_stack)):
            raise ValueError(f"{label} approvals do not identify this exact batch")
        approved_stack = members

        number = members[index]
        pr = request(repo, f"pulls/{number}")
        if (pr["state"] != "open" or pr["draft"] or
                pr["head"]["repo"]["full_name"].lower() != repo.lower() or
                pr["base"]["repo"]["full_name"].lower() != repo.lower() or
                pr["head"]["sha"] != head or pr["base"]["sha"] != immediate_base or
                pr["base"]["ref"] != base_ref or
                not pr["head"]["ref"].startswith(branch_prefix)):
            raise ValueError(f"{label} PR #{number} no longer matches its reviewed head/base")
        if index and not re.search(
            rf"(?m)^Depends-On: #{members[index - 1]}[ \t\r]*$", pr["body"] or ""
        ):
            raise ValueError(f"{label} PR #{number} is missing its predecessor")
        run_git("merge-base", "--is-ancestor", immediate_base, head)
        paths = changed_paths(immediate_base, head, run_git)
        if not paths or not paths <= allowed:
            raise ValueError(f"{label} PR #{number} touches a path outside the pilot")
        previous, immediate_base, base_ref = merge, head, pr["head"]["ref"]
    print(f"Verified {scope} batch: {', '.join('#' + n for n in approved_stack)}")


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
        scope = candidate_scope(changed_paths(base, candidate))
        if scope in STACK_SCOPES:
            verify_batch(base, candidate, env["GITHUB_REPOSITORY"], scope)
        tree = git("rev-parse", f"{candidate}^{{tree}}").decode().strip()
        print(f"Queue candidate: {candidate}; main: {base}; tested tree: {tree}")
    git("diff", "--check", base, candidate)
    if mode == "heavy":
        if env.get("GITHUB_OUTPUT"):
            with open(env["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
                print(f"scope={scope}", file=output)
        return
    paths = changed_paths(base, candidate)
    if paths & HELPER_PATHS:
        subprocess.run(["bash", HELPER_TEST], check=True)
    if paths & PROJECT_PATHS:
        subprocess.run(["bash", "-n", "scripts/project"], check=True)
        subprocess.run([
            sys.executable, PROJECT_TEST,
            "InstallTests.test_forwarders_preserve_legacy_argv_and_exit_code",
            "InstallTests.test_forwarder_refuses_unowned_command_and_finds_owned_path_entry",
            "InstallTests.test_forwarder_expands_tilde_and_rejects_relative_configuration",
            "InstallTests.test_checkout_forwarder_isolates_ownership_probe_from_pythonpath",
        ], check=True)
    if paths & WAVE_PATHS:
        subprocess.run(["bash", "-n", WAVE_SCRIPT], check=True)
        subprocess.run([sys.executable, "-m", "py_compile", WAVE_RECONCILER, WAVE_TEST], check=True)
        subprocess.run([
            sys.executable, WAVE_TEST,
            "WaveWidgetSyncTests.test_reconciles_owned_widgets_and_is_idempotent",
            "WaveWidgetSyncTests.test_invalid_or_symlinked_settings_are_preserved",
        ], check=True)


def verify_results(env):
    """Require exactly the platform jobs intended for this event and scope."""
    event = env["GITHUB_EVENT_NAME"]
    scope = env["SCOPE"]
    actual = (env["PROJECT"], env["WAVE_WIDGET_SYNC"])
    if event == "pull_request":
        expected = ("success", "success")
    elif event == "push" and env["VERIFIED"] == "success":
        expected = {
            "docs": ("skipped", "skipped"),
            "helper": ("skipped", "skipped"),
            "project": ("success", "skipped"),
            "wave-widget-sync": ("skipped", "success"),
        }[scope]
    else:
        raise ValueError("Expected config PR or successfully verified queue candidate")
    if actual != expected:
        raise ValueError(f"Expected platform results {expected}, got {actual}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("fast", "heavy", "gate", "classify-wave"))
    mode = parser.parse_args().mode
    try:
        if mode == "classify-wave":
            classify_wave(os.environ)
        elif mode == "gate":
            verify_results(os.environ)
        else:
            verify(mode, os.environ)
    except (KeyError, TypeError, ValueError, subprocess.SubprocessError) as exc:
        sys.exit(f"stack-ci: {exc}")

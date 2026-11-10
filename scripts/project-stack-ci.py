"""Conservative project CI deduplication; execute only from trusted main."""

from datetime import datetime
import json
import os
from pathlib import Path
import re
import runpy
import subprocess


COMMON = runpy.run_path(str(Path(__file__).with_name("stack-ci.py")))
git, github, sha = (COMMON[name] for name in ("git", "github", "sha"))
regular_scope_diff = COMMON["regular_scope_diff"]
scoped_pr_qualified = COMMON["scoped_pr_qualified"]
merged_scoped_metadata = COMMON["merged_scoped_metadata"]
verify_batch = COMMON["verify_batch"]
ALLOWED, PREFIX, CONTEXT = COMMON["STACK_SCOPES"]["project"]
WORKFLOW = ".github/workflows/stack-candidate-heavy.yml"
RUNS_ENDPOINT = "actions/workflows/stack-candidate-heavy.yml/runs?event=push&status=success&per_page=20"
REQUIRED_JOBS = {
    "Verify queue candidate", "openbenches-stack-heavy",
    *(f"Project stack integration ({os_name})" for os_name in (
        "ubuntu-latest", "ubuntu-24.04", "macos-latest")),
}
POLICY_PATHS = ("scripts/stack-ci.py", "scripts/project-stack-ci.py", WORKFLOW,
                ".github/workflows/project-command.yml")
QUEUE = r"mergify/merge-queue/[0-9a-f]{10}"
ERRORS = (KeyError, TypeError, ValueError, AttributeError, OSError, subprocess.SubprocessError)


def opted_in(text):
    return bool(re.search(r"(?m)^Stack-CI: project[ \t\r]*$", text or ""))


def parents(commit, run_git):
    return run_git("show", "-s", "--format=%P", sha(commit)).decode().split()


def receipt(head, repo, request):
    statuses = request(repo, f"commits/{head}/status")["statuses"]
    matching = [status for status in statuses if status["context"] == CONTEXT]
    if len(matching) != 1 or matching[0]["state"] != "success":
        raise ValueError("Missing unique successful project receipt")
    match = re.fullmatch(r"base=([0-9a-f]{40}) stack=([1-9]\d*(?:,[1-9]\d*){1,2})",
                         matching[0]["description"] or "")
    if not match:
        raise ValueError("Invalid project receipt")
    members = match[2].split(",")
    if len(set(members)) != len(members):
        raise ValueError("Duplicate members")
    return match[1], members


def tested_chain(candidate, repo, request, run_git):
    """Read immutable Git/receipt evidence, not the admission verifier's state.

    PRs may now be merged/retargeted. Keep verify_batch strictly open-PR-only.
    """
    top_parents = parents(candidate, run_git)
    if len(top_parents) != 2:
        raise ValueError("Not a candidate merge")
    _base, members = receipt(top_parents[1], repo, request)
    merges, current = [], candidate
    for _member in members:
        pair = parents(current, run_git)
        if len(pair) != 2:
            raise ValueError("Incomplete candidate chain")
        merges.append((current, pair[1]))
        current = pair[0]
    merges.reverse()
    root, original_base = current, current
    prs = []
    for index, (_merge, head) in enumerate(merges):
        approved_base, approved_members = receipt(head, repo, request)
        if approved_base != original_base or approved_members != members:
            raise ValueError("Receipts do not identify this exact chain")
        pr = request(repo, f"pulls/{members[index]}")
        if (pr["number"] != int(members[index]) or pr["draft"]
                or pr["state"] not in ("open", "closed")
                or (pr["state"] == "closed" and pr["merged"] is not True)
                or any(pr[ref]["repo"]["full_name"].lower() != repo.lower() for ref in ("head", "base"))
                or pr["head"]["sha"] != head or not pr["head"]["ref"].startswith(PREFIX)
                or not opted_in(pr["body"])):
            raise ValueError("Original member no longer matches")
        dependencies = re.findall(r"(?m)^Depends-On:[^\n]*", pr["body"] or "")
        expected = [] if not index else [f"Depends-On: #{members[index - 1]}"]
        if [line.rstrip(" \t\r") for line in dependencies] != expected:
            raise ValueError("Wrong predecessor")
        run_git("merge-base", "--is-ancestor", original_base, head)
        if not regular_scope_diff(original_base, head, ALLOWED, run_git):
            raise ValueError("Non-project member")
        original_base = head
        prs.append(pr)
    if not regular_scope_diff(root, candidate, ALLOWED, run_git):
        raise ValueError("Non-project candidate")
    return root, merges, prs


def successful_jobs(run, candidate, repo, request):
    response = request(repo, f"actions/runs/{run['id']}/jobs?per_page=100")
    jobs = response["jobs"]
    if response["total_count"] != len(jobs):
        raise ValueError("Incomplete jobs response")
    completed = []
    for name in REQUIRED_JOBS:
        matches = [job for job in jobs if job["name"] == name]
        if (len(matches) != 1 or matches[0]["head_sha"] != candidate
                or matches[0]["status"] != "completed" or matches[0]["conclusion"] != "success"):
            raise ValueError("Missing successful exact-head integration job")
        completed.append(datetime.fromisoformat(matches[0]["completed_at"].replace("Z", "+00:00")))
    return max(completed)


def landed_prefix(event, main, candidate, completed, repo, request, run_git):
    root, merges, prs = tested_chain(candidate, repo, request, run_git)
    actual = sha(event["after"])
    pair = parents(actual, run_git)
    if len(pair) != 2 or pair[0] != sha(event["before"]):
        return False
    indexes = [index for index, (_merge, head) in enumerate(merges) if head == pair[1]]
    if len(indexes) != 1:
        return False
    run_git("merge-base", "--is-ancestor", actual, main)
    for index in range(indexes[0], -1, -1):
        merge, head = merges[index]
        pair = parents(actual, run_git)
        pr = prs[index]
        if (len(pair) != 2 or pair[1] != head or pr["merged"] is not True
                or pr["merge_commit_sha"] != actual
                or datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00")) < completed
                or run_git("rev-parse", actual + "^{tree}") != run_git("rev-parse", merge + "^{tree}")):
            return False
        actual = pair[0]
    return actual == root


def successful_run(run, repo):
    return (run["event"] == "push" and run["actor"]["login"] == "mergify[bot]"
            and run["head_repository"]["full_name"].lower() == repo.lower()
            and re.fullmatch(QUEUE, run["head_branch"]) and run["path"] == WORKFLOW
            and run["run_attempt"] == 1 and run["status"] == "completed"
            and run["conclusion"] == "success")


def tested_landing(event, main, repo, request, run_git):
    runs = request(repo, RUNS_ENDPOINT)["workflow_runs"]
    for run in runs[:20]:
        try:
            if not successful_run(run, repo):
                continue
            candidate = sha(run["head_sha"])
            run_git("fetch", "--no-tags", "origin", candidate)
            # Historical success must use the same trusted policy and commands.
            run_git("diff", "--quiet", candidate, main, "--", *POLICY_PATHS)
            completed = successful_jobs(run, candidate, repo, request)
            if landed_prefix(event, main, candidate, completed, repo, request, run_git):
                return True
        except ERRORS:
            continue
    return False


def candidate_pr(event, main, repo, actor, request, run_git):
    """Mergify's draft PR is another duplicate event, not an author PR."""
    if actor != "mergify[bot]" or type(event["number"]) is not int:
        return False
    expected = event["pull_request"]
    pr = request(repo, f"pulls/{event['number']}")
    if (pr["number"] != event["number"] or pr["state"] not in ("open", "closed")
            or pr["user"]["login"] != "mergify[bot]"
            or not re.fullmatch(QUEUE, pr["head"]["ref"]) or pr["base"]["ref"] != "main"
            or any(pr[ref]["repo"]["full_name"].lower() != repo.lower() for ref in ("head", "base"))
            or any(pr[ref][key] != expected[ref][key] for ref in ("head", "base") for key in ("sha", "ref"))):
        return False
    candidate = sha(pr["head"]["sha"])
    run_git("fetch", "--no-tags", "origin", candidate)
    if pr["state"] == "open" and pr["base"]["sha"] == main:
        try:
            verify_batch(main, candidate, repo, "project", request, run_git)
            root, _merges, _prs = tested_chain(candidate, repo, request, run_git)
            return root == main
        except ERRORS:
            pass  # A member might have just landed; try exact completed evidence.
    # A closed draft is not itself merged. Require its successful exact run,
    # not an unconditional prefix/actor exemption for late metadata.
    for run in request(repo, RUNS_ENDPOINT)["workflow_runs"][:20]:
        if (successful_run(run, repo) and run["head_sha"] == candidate
                and run["head_branch"] == pr["head"]["ref"]):
            run_git("diff", "--quiet", candidate, main, "--", *POLICY_PATHS)
            successful_jobs(run, candidate, repo, request)
            root, _merges, _prs = tested_chain(candidate, repo, request, run_git)
            run_git("merge-base", "--is-ancestor", root, main)
            return root == pr["base"]["sha"]
    return False


def merged_metadata(event, main, repo, request, run_git):
    if not merged_scoped_metadata(event, repo, "project", request):
        return False
    pr = request(repo, f"pulls/{event['number']}")
    merge = sha(pr["merge_commit_sha"])
    run_git("fetch", "--no-tags", "origin", merge)
    run_git("merge-base", "--is-ancestor", merge, main)
    pair = parents(merge, run_git)
    return (len(pair) == 2 and pair[1] == event["pull_request"]["head"]["sha"]
            and regular_scope_diff(pair[0], merge, ALLOWED, run_git))


def decision(kind, event, main, repo, actor, ref, event_sha, request=github, run_git=git):
    """A reason permits only duplicate component CI to skip, never admission."""
    try:
        if repo != "opensoft/openBenches":
            return None
        sha(main)
        if kind == "pull_request":
            if any(event["pull_request"][ref]["repo"]["full_name"].lower() != repo.lower()
                   for ref in ("head", "base")):
                return None
            if re.fullmatch(QUEUE, event["pull_request"]["head"]["ref"]):
                return "project-candidate-pr" if candidate_pr(event, main, repo, actor, request, run_git) else None
            if merged_metadata(event, main, repo, request, run_git):
                return "merged-project-metadata"
            if scoped_pr_qualified(event, main, repo, "project", request, run_git):
                return "project-pr"
        if (kind != "push" or event["deleted"] is not False
                or event["repository"]["full_name"].lower() != repo.lower()
                or event["ref"] != ref or sha(event["after"]) != sha(event_sha)):
            return None
        head = sha(event["after"])
        run_git("fetch", "--no-tags", "origin", head)
        if re.fullmatch("refs/heads/" + re.escape(PREFIX) + r".+", ref):
            if request(repo, "branches/main")["commit"]["sha"] != main:
                return None
            run_git("merge-base", "--is-ancestor", main, head)
            message = run_git("show", "-s", "--format=%B", head).decode()
            if opted_in(message) and regular_scope_diff(main, head, ALLOWED, run_git):
                return "project-source-push"
        elif actor == "mergify[bot]" and re.fullmatch("refs/heads/" + QUEUE, ref):
            verify_batch(main, head, repo, "project", request, run_git)
            _root, _merges, _prs = tested_chain(head, repo, request, run_git)
            if regular_scope_diff(main, head, ALLOWED, run_git):
                return "project-candidate-push"
        elif actor == "mergify[bot]" and ref == "refs/heads/main":
            if tested_landing(event, main, repo, request, run_git):
                return "tested-project-landing"
    except ERRORS:
        pass
    return None


def classify(env):
    reason = None
    try:
        with open(env["GITHUB_EVENT_PATH"], encoding="utf-8") as source:
            event = json.load(source)
        main = git("rev-parse", "HEAD").decode().strip()
        reason = decision(env["GITHUB_EVENT_NAME"], event, main, env["GITHUB_REPOSITORY"],
                          env.get("GITHUB_ACTOR", ""), env.get("GITHUB_REF", ""), env.get("GITHUB_SHA", ""))
    except ERRORS:
        pass
    with open(env["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        print(f"skip_project={'true' if reason else 'false'}", file=output)
    print(f"Project CI: {reason or 'full-fallback'}")


if __name__ == "__main__":
    classify(os.environ)

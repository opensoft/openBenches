"""Offline Git/API fixtures for the project-only CI efficiency policy."""

from copy import deepcopy
import json
from pathlib import Path
import runpy
import subprocess
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
OLD = runpy.run_path(str(ROOT / "devcontainer.test/test-stack-ci.py"))
POLICY = runpy.run_path(str(ROOT / "scripts/project-stack-ci.py"))
REPO = "opensoft/openBenches"
QUEUE = "mergify/merge-queue/0123456789"
CONTEXT = "openbenches-project-reviewed"


class ProjectEfficiencyTests(unittest.TestCase):
    setUp = OLD["StackCiTest"].setUp
    git = OLD["StackCiTest"].git
    commit = OLD["StackCiTest"].commit

    def run_git(self, *args):
        if args[0] == "fetch":
            return b""  # All fixture objects are local; no network.
        return subprocess.check_output(["git", *args], cwd=self.repo)

    def request(self, repo, endpoint):
        self.assertEqual(repo, REPO)
        return self.responses[endpoint]

    def chain(self, count=3, mixed=False):
        for path in ("scripts/project", "devcontainer.test/test-project-command.py"):
            self.base = self.commit(path, "# original\n")
        self.responses = {"branches/main": {"commit": {"sha": self.base}}}
        self.heads, self.merges = [], []
        previous, branch = self.base, "main"
        members = ",".join(str(10 + n) for n in range(count))
        for index in range(count):
            number = 10 + index
            new_branch = f"ci/stack-project/{number}"
            self.git("switch", "-qc", new_branch)
            self.commit("README.md" if mixed and not index else "scripts/project", f"# member {index}\n")
            self.git("commit", "--amend", "-qm", "project\n\nStack-CI: project")
            head = self.git("rev-parse", "HEAD")
            self.heads.append(head)
            self.responses[f"pulls/{number}"] = {
                "number": number, "state": "open", "draft": False,
                "body": "Stack-CI: project" + (f"\nDepends-On: #{number - 1}" if index else ""),
                "head": {"sha": head, "ref": new_branch, "repo": {"full_name": REPO}},
                "base": {"sha": previous, "ref": branch, "repo": {"full_name": REPO}},
            }
            self.responses[f"commits/{head}/status"] = {"statuses": [{
                "context": CONTEXT, "state": "success", "description": f"base={previous} stack={members}",
            }]}
            previous, branch = head, new_branch
        return self.event(count - 1)

    def event(self, index=0, action="synchronize"):
        pr = deepcopy(self.responses[f"pulls/{index + 10}"])
        return {"action": action, "number": index + 10, "pull_request": pr}

    def decide(self, event, kind="pull_request", main=None, actor="author", ref="", event_sha=""):
        return POLICY["decision"](
            kind, event, main or self.base, REPO, actor, ref, event_sha,
            request=self.request, run_git=self.run_git)

    def push(self, head, ref, before=None):
        return {
            "after": head, "before": before or self.base, "deleted": False,
            "repository": {"full_name": REPO}, "ref": ref,
        }

    def candidate(self):
        self.git("switch", "-qc", QUEUE, self.base)
        for head in self.heads:
            self.git("merge", "-q", "--no-ff", head, "-m", "candidate")
            self.merges.append(self.git("rev-parse", "HEAD"))
        self.candidate_sha = self.merges[-1]
        return self.candidate_sha

    def evidence(self):
        self.candidate()
        run = {
            "id": 123, "head_sha": self.candidate_sha, "head_branch": QUEUE,
            "event": "push", "actor": {"login": "mergify[bot]"},
            "head_repository": {"full_name": REPO}, "run_attempt": 1,
            "path": ".github/workflows/stack-candidate-heavy.yml", "status": "completed",
            "conclusion": "success",
        }
        self.responses[POLICY["RUNS_ENDPOINT"]] = {"workflow_runs": [run]}
        jobs = [{"name": name, "status": "completed", "conclusion": "success",
                 "head_sha": self.candidate_sha, "completed_at": "2026-11-10T12:00:00Z"}
                for name in POLICY["REQUIRED_JOBS"]]
        self.responses["actions/runs/123/jobs?per_page=100"] = {"total_count": len(jobs), "jobs": jobs}

    def landed(self, count):
        previous = self.base
        self.actual = []
        for index in range(count):
            tree = self.git("rev-parse", self.merges[index] + "^{tree}")
            actual = self.git("commit-tree", tree, "-p", previous, "-p", self.heads[index], "-m", "landed")
            self.actual.append(actual)
            self.responses[f"pulls/{10 + index}"].update(
                state="closed", merged=True, merge_commit_sha=actual, merged_at="2026-11-10T12:01:00Z")
            previous = actual
        return self.push(previous, "refs/heads/main", self.base if count == 1 else self.actual[-2])

    def landing_decision(self, event):
        return self.decide(event, "push", main=event["after"], actor="mergify[bot]",
                           ref="refs/heads/main", event_sha=event["after"])

    def test_current_bottom_two_and_three_member_project_chains(self):
        self.chain()
        for index in range(3):
            with self.subTest(index=index):
                self.assertEqual(self.decide(self.event(index)), "project-pr")

    def test_mixed_ancestor_retains_full_checks(self):
        event = self.chain(mixed=True)
        self.assertIsNone(self.decide(event))

    def test_optin_scope_prefix_current_head_base_and_dependency_required(self):
        event = self.chain()
        for field, value in (("body", ""), ("body", "Stack-CI: wave-widget-sync"),
                             ("draft", True), ("state", "closed")):
            original = deepcopy(self.responses)
            self.responses["pulls/12"][field] = value
            self.assertIsNone(self.decide(event))
            self.responses = original
        for ref, field, value in (("head", "sha", "f" * 40), ("base", "sha", self.base),
                                  ("head", "ref", "ci/stack-wave-widget-sync/12"),
                                  ("base", "repo", {"full_name": "other/fork"})):
            original = deepcopy(self.responses)
            self.responses["pulls/12"][ref][field] = value
            self.assertIsNone(self.decide(event))
            self.responses = original
        self.responses["branches/main"]["commit"]["sha"] = "f" * 40
        self.assertIsNone(self.decide(event))

    def test_only_delayed_same_head_merged_project_metadata_is_exempt(self):
        event = self.chain(1)
        event["action"] = "edited"
        merge = self.candidate()
        self.responses["pulls/10"].update(state="closed", merged=True,
                                        merge_commit_sha=merge, changed_files=1)
        files = "pulls/10/files?per_page=100"
        self.responses[files] = [{"filename": "scripts/project", "status": "modified"}]
        self.assertEqual(self.decide(event, main=merge), "merged-project-metadata")
        for field, value in (("merged", False), ("changed_files", 2)):
            original = deepcopy(self.responses)
            self.responses["pulls/10"][field] = value
            self.assertIsNone(self.decide(event, main=merge))
            self.responses = original
        for action in ("synchronize", "opened", "reopened", "ready_for_review"):
            self.assertIsNone(self.decide({**event, "action": action}, main=merge))
        for file in ({"filename": "bootstrap.sh", "status": "modified"},
                     {"filename": "scripts/project", "status": "renamed"}):
            self.responses[files] = [file]
            self.assertIsNone(self.decide(event, main=merge))

    def test_metadata_with_changed_head_missing_git_or_unlanded_merge_stays_full(self):
        event = self.chain(1)
        merge = self.candidate()
        self.responses["pulls/10"].update(state="closed", merged=True,
                                        merge_commit_sha=merge, changed_files=1)
        self.responses["pulls/10/files?per_page=100"] = [{"filename": "scripts/project", "status": "modified"}]
        event["action"] = "edited"
        self.assertIsNone(self.decide(event))  # Trusted main predates landing.
        event["pull_request"]["head"]["sha"] = "f" * 40
        self.assertIsNone(self.decide(event, main=merge))

    def test_too_long_chains_and_open_mixed_edits_stay_full(self):
        event = self.chain(4)
        self.assertIsNone(self.decide(event))
        head = self.commit("README.md", "# real open edit\n")
        self.responses["pulls/13"]["head"]["sha"] = head
        self.assertIsNone(self.decide(self.event(3, "edited")))

    def test_author_push_requires_exact_sha_namespace_marker_and_regular_diff(self):
        self.chain(1)
        head = self.heads[0]
        ref = "refs/heads/ci/stack-project/10"
        event = self.push(head, ref)
        self.assertEqual(self.decide(event, "push", ref=ref, event_sha=head), "project-source-push")
        for changed in ({**event, "after": "f" * 40}, {**event, "deleted": True},
                        {**event, "ref": "refs/tags/v1"},
                        {**event, "repository": {"full_name": "other/fork"}}):
            self.assertIsNone(self.decide(changed, "push", ref=ref, event_sha=head))
        for wrong in ("refs/tags/v1", "refs/heads/main", "refs/heads/ordinary"):
            self.assertIsNone(self.decide(self.push(head, wrong), "push", ref=wrong, event_sha=head))
        self.git("commit", "--amend", "-qm", "no opt-in")
        head = self.git("rev-parse", "HEAD")
        self.assertIsNone(self.decide(self.push(head, ref), "push", ref=ref, event_sha=head))

    def test_source_push_empty_stale_or_diverged_main_stays_full(self):
        self.chain(1)
        ref = "refs/heads/ci/stack-project/10"
        head = self.heads[0]
        self.responses["branches/main"]["commit"]["sha"] = "f" * 40
        self.assertIsNone(self.decide(self.push(head, ref), "push", ref=ref, event_sha=head))
        self.responses["branches/main"]["commit"]["sha"] = self.base
        self.assertIsNone(self.decide(self.push(self.base, ref), "push", ref=ref, event_sha=self.base))
        self.git("switch", "-q", "--detach", self.base)
        new_main = self.commit("README.md", "main advanced\n")
        self.responses["branches/main"]["commit"]["sha"] = new_main
        self.assertIsNone(self.decide(self.push(head, ref), "push", main=new_main, ref=ref, event_sha=head))

    def test_mixed_deleted_renamed_mode_and_symlink_source_pushes_fall_back(self):
        self.chain(1)
        ref = "refs/heads/ci/stack-project/10"
        for operation in ("mixed", "delete", "rename", "mode", "symlink"):
            with self.subTest(operation=operation):
                self.git("switch", "-q", "--detach", self.base)
                if operation == "mixed":
                    self.commit("README.md", "mixed\n")
                elif operation == "delete":
                    self.git("rm", "scripts/project")
                elif operation == "rename":
                    self.git("mv", "scripts/project", "scripts/other")
                elif operation == "mode":
                    (self.repo / "scripts/project").chmod(0o755)
                    self.git("update-index", "--chmod=+x", "scripts/project")
                else:
                    path = self.repo / "scripts/project"
                    path.unlink()
                    path.symlink_to("elsewhere")
                    self.git("add", "scripts/project")
                self.git("commit", "--allow-empty", "-qm", "change\n\nStack-CI: project")
                head = self.git("rev-parse", "HEAD")
                self.assertIsNone(self.decide(self.push(head, ref), "push", ref=ref, event_sha=head))

    def test_queue_push_requires_strict_reviewed_batch_not_just_actor(self):
        self.chain()
        head = self.candidate()
        ref = "refs/heads/" + QUEUE
        event = self.push(head, ref)
        self.assertEqual(self.decide(event, "push", ref=ref, event_sha=head,
                                     actor="mergify[bot]"), "project-candidate-push")
        self.assertIsNone(self.decide(event, "push", ref=ref, event_sha=head))
        self.responses[f"commits/{self.heads[0]}/status"]["statuses"][0]["state"] = "failure"
        self.assertIsNone(self.decide(event, "push", ref=ref, event_sha=head, actor="mergify[bot]"))

    def candidate_event(self):
        pr = {"number": 99, "state": "open", "draft": True, "user": {"login": "mergify[bot]"},
              "head": {"sha": self.candidate_sha, "ref": QUEUE, "repo": {"full_name": REPO}},
              "base": {"sha": self.base, "ref": "main", "repo": {"full_name": REPO}}}
        self.responses["pulls/99"] = pr
        return {"action": "opened", "number": 99, "pull_request": deepcopy(pr)}

    def test_candidate_draft_pr_checks_exact_batch_instead_of_branch_only_skip(self):
        self.chain()
        self.candidate()
        event = self.candidate_event()
        self.assertEqual(self.decide(event, actor="mergify[bot]"), "project-candidate-pr")
        self.assertIsNone(self.decide(event))
        self.responses["pulls/10"]["body"] = "Stack-CI: wave-widget-sync"
        self.assertIsNone(self.decide(event, actor="mergify[bot]"))

    def test_closed_candidate_metadata_requires_successful_exact_heavy_run(self):
        self.chain()
        self.evidence()
        event = self.candidate_event()
        landing = self.landed(3)
        self.responses["pulls/99"]["state"] = "closed"
        event["action"] = "edited"
        self.assertEqual(self.decide(event, main=landing["after"], actor="mergify[bot]"), "project-candidate-pr")
        self.responses[POLICY["RUNS_ENDPOINT"]]["workflow_runs"][0]["conclusion"] = "failure"
        self.assertIsNone(self.decide(event, main=landing["after"], actor="mergify[bot]"))

    def test_successful_heavy_proof_matches_every_landed_prefix(self):
        self.chain()
        self.evidence()
        for count in range(1, 4):
            event = self.landed(count)
            with self.subTest(count=count):
                self.assertEqual(self.landing_decision(event), "tested-project-landing")

    def test_landing_requires_successful_exact_candidate_and_all_platforms(self):
        self.chain()
        self.evidence()
        event = self.landed(2)
        for field, value in (("conclusion", "failure"), ("head_sha", "f" * 40),
                             ("event", "pull_request"), ("run_attempt", 2),
                             ("actor", {"login": "author"}), ("head_branch", "ordinary"),
                             ("path", ".github/workflows/other.yml"),
                             ("head_repository", {"full_name": "other/fork"})):
            with self.subTest(field=field):
                original = deepcopy(self.responses)
                self.responses[POLICY["RUNS_ENDPOINT"]]["workflow_runs"][0][field] = value
                self.assertIsNone(self.landing_decision(event))
                self.responses = original
        for name in POLICY["REQUIRED_JOBS"]:
            original = deepcopy(self.responses)
            jobs = self.responses["actions/runs/123/jobs?per_page=100"]["jobs"]
            next(job for job in jobs if job["name"] == name)["conclusion"] = "skipped"
            self.assertIsNone(self.landing_decision(event))
            self.responses = original

    def test_landing_rejects_wrong_heads_trees_receipts_timing_and_extra_commits(self):
        self.chain()
        self.evidence()
        event = self.landed(2)
        for endpoint, field, value in (
            ("pulls/10", "merge_commit_sha", "f" * 40),
            ("pulls/11", "merged_at", "2026-11-10T11:59:00Z"),
            ("pulls/11", "merged", False),
            ("pulls/11", "body", "Stack-CI: wave-widget-sync"),
        ):
            original = deepcopy(self.responses)
            self.responses[endpoint][field] = value
            self.assertIsNone(self.landing_decision(event))
            self.responses = original
        original = deepcopy(self.responses)
        self.responses[f"commits/{self.heads[1]}/status"]["statuses"][0]["description"] = (
            f"base={self.base} stack=10,11,12")
        self.assertIsNone(self.landing_decision(event))
        self.responses = original
        for parents, tree in (([self.actual[0], self.heads[2]], self.merges[1]),
                              ([self.actual[0], self.heads[1]], self.merges[0]),
                              ([self.base, self.heads[1]], self.merges[1])):
            wrong = self.git("commit-tree", self.git("rev-parse", tree + "^{tree}"),
                             "-p", parents[0], "-p", parents[1], "-m", "wrong landing")
            bad_event = self.push(wrong, "refs/heads/main", parents[0])
            self.assertIsNone(self.landing_decision(bad_event))

    def test_missing_duplicate_truncated_jobs_and_api_errors_retain_full_landing(self):
        self.chain()
        self.evidence()
        event = self.landed(1)
        endpoint = "actions/runs/123/jobs?per_page=100"
        for change in ("missing", "duplicate", "truncated", "sha", "timestamp", "missing-run"):
            with self.subTest(change=change):
                original = deepcopy(self.responses)
                response = self.responses[endpoint]
                if change == "missing":
                    response["jobs"].pop()
                    response["total_count"] -= 1
                elif change == "duplicate":
                    response["jobs"].append(deepcopy(response["jobs"][0]))
                    response["total_count"] += 1
                elif change == "truncated":
                    response["total_count"] = 101
                elif change == "sha":
                    response["jobs"][0]["head_sha"] = "f" * 40
                elif change == "timestamp":
                    response["jobs"][0]["completed_at"] = None
                else:
                    self.responses.pop(POLICY["RUNS_ENDPOINT"])
                self.assertIsNone(self.landing_decision(event))
                self.responses = original

    def test_policy_change_or_mixed_candidate_cannot_reuse_old_success(self):
        self.chain()
        self.evidence()
        event = self.landed(1)
        self.git("switch", "-q", "--detach", event["after"])
        main = self.commit("scripts/project-stack-ci.py", "# changed policy\n")
        self.assertIsNone(self.decide(event, "push", main=main, actor="mergify[bot]",
                                     ref="refs/heads/main", event_sha=event["after"]))

    def test_all_incomplete_project_aggregate_results_fail(self):
        gate = POLICY["COMMON"]["verify_results"]
        for result in ("failure", "cancelled", "skipped", ""):
            with self.subTest(result=result), self.assertRaises(ValueError):
                gate({"GITHUB_EVENT_NAME": "push", "SCOPE": "project", "VERIFIED": "success",
                      "PROJECT": result, "WAVE_WIDGET_SYNC": "skipped"})

    def test_missing_api_git_and_unknown_events_keep_full_checks(self):
        event = self.chain()
        self.responses = {}
        self.assertIsNone(self.decide(event))
        for kind in ("workflow_dispatch", "pull_request_target", "schedule"):
            self.assertIsNone(self.decide(event, kind))
        with patch.dict(POLICY["decision"].__globals__, scoped_pr_qualified=lambda *_a, **_k: (_ for _ in ()).throw(OSError("unavailable"))):
            self.assertIsNone(self.decide(event))

    def test_output_errors_and_nonboolean_values_never_select_skip(self):
        function = POLICY["classify"]
        event_file, output = self.repo / "event.json", self.repo / "output"
        event_file.write_text("not JSON")
        env = {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_REPOSITORY": REPO,
               "GITHUB_EVENT_PATH": str(event_file), "GITHUB_OUTPUT": str(output)}
        function(env)
        self.assertIn("skip_project=false\n", output.read_text())
        event_file.write_text(json.dumps({}))
        for reason in (None, "project-pr"):
            output.write_text("")
            with patch.dict(function.__globals__, git=lambda *_a: b"a" * 40,
                            decision=lambda *_a, **_k: reason):
                function(env)
            self.assertIn(f"skip_project={'true' if reason else 'false'}\n", output.read_text())

    def test_workflow_wiring_preserves_fail_safe_platforms_and_scope_isolation(self):
        workflow = (ROOT / ".github/workflows/project-command.yml").read_text()
        self.assertIn("ref: main", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("python3 -I scripts/project-stack-ci.py", workflow)
        self.assertIn("actions: read", workflow)
        self.assertIn("needs: classify", workflow)
        self.assertIn("needs.classify.result != 'success' || needs.classify.outputs.skip_project != 'true'", workflow)
        self.assertIn("os: [ubuntu-latest, macos-latest]", workflow)
        self.assertIn("types: [opened, reopened, synchronize, edited, ready_for_review]", workflow)
        heavy = (ROOT / ".github/workflows/stack-candidate-heavy.yml").read_text()
        self.assertIn("os: [ubuntu-latest, ubuntu-24.04, macos-latest]", heavy)
        self.assertIn("bash -n scripts/project scripts/onp scripts/new-project.sh scripts/install-workbench-commands.sh scripts/setup-workbenches.sh setup.sh", heavy)
        fast = (ROOT / ".github/workflows/stack-pr-fast.yml").read_text()
        self.assertIn("python3 devcontainer.test/test-project-stack-ci.py", fast)
        wave = (ROOT / ".github/workflows/credential-recovery.yml").read_text()
        self.assertNotIn("skip_project", wave)
        for result in ("success", "failure", "cancelled", "skipped", ""):
            for value in ("true", "false", "", "True", "unknown"):
                self.assertEqual(result != "success" or value != "true",
                                 not (result == "success" and value == "true"))


if __name__ == "__main__":
    unittest.main()

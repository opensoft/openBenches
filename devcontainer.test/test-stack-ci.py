"""Exercise stack CI against real commits in a disposable Git repository."""

import os
from copy import deepcopy
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


GATE = Path(__file__).resolve().parents[1] / "scripts" / "stack-ci.py"
POLICY = runpy.run_path(str(GATE))
HELPER_TEST = POLICY["HELPER_TEST"]
HELPER = next(p.decode() for p in POLICY["HELPER_PATHS"] if p.decode() != HELPER_TEST)
PROJECT_TEST = POLICY["PROJECT_TEST"]
WAVE_TEST = "devcontainer.test/test-wave-widget-sync.py"
WAVE_SCRIPT = "scripts/sync-wave-widgets.sh"
WAVE_RECONCILER = "scripts/sync-wave-widgets.py"
WAVE_SCOPE = "wave-widget-sync"
REPO = "example/openbenches"


class StackCiTest(unittest.TestCase):
    def setUp(self):
        fixture = tempfile.TemporaryDirectory()
        self.addCleanup(fixture.cleanup)
        self.repo = Path(fixture.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Stack CI fixture")
        self.git("config", "user.email", "stack-ci@example.invalid")
        self.git("config", "commit.gpgSign", "false")
        self.base = self.commit("README.md", "base\n")
        self.git("update-ref", "refs/remotes/origin/main", self.base)

    def git(self, *args):
        return subprocess.check_output(
            ["git", *args], cwd=self.repo, text=True
        ).strip()

    def commit(self, path, text):
        file = self.repo / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding="utf-8")
        self.git("add", path)
        self.git("commit", "-qm", path)
        return self.git("rev-parse", "HEAD")

    def gate(self, mode, expected=None, **env):
        return subprocess.run(
            [sys.executable, str(GATE), mode],
            cwd=self.repo,
            env={
                **os.environ,
                "GITHUB_EVENT_NAME": "pull_request",
                "GITHUB_SHA": expected or self.git("rev-parse", "HEAD"),
                **env,
            },
            text=True,
            capture_output=True,
            check=False,
        )

    def test_fast_matches_immediate_base_and_head(self):
        parent = self.commit("docs/task-set-delivery.md", "parent\n")
        self.git("switch", "-qc", "top")
        head = self.commit(".specify/templates/tasks-template.md", "upper\n")
        self.git("switch", "-q", "main")
        self.git("merge", "-q", "--no-ff", "top", "-m", "test merge")
        passed = self.gate("fast", PR_HEAD=head, PR_BASE=parent)
        self.assertEqual(passed.returncode, 0, passed.stderr)
        self.assertIn(parent, passed.stdout)
        for base in (self.base, head):
            result = self.gate("fast", PR_HEAD=head, PR_BASE=base)
            self.assertIn("Candidate parents do not match", result.stderr)
            self.assertNotEqual(result.returncode, 0)

    def test_heavy_records_exact_tree(self):
        candidate = self.commit("docs/task-set-delivery.md", "stack\n")
        result = self.gate("heavy")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(candidate, result.stdout)
        self.assertIn(self.git("rev-parse", "HEAD^{tree}"), result.stdout)
        self.assertNotEqual(self.gate("heavy", expected=self.base).returncode, 0)

    def test_heavy_rejects_out_of_scope_and_empty_candidates(self):
        self.assertNotEqual(self.gate("heavy").returncode, 0)
        self.commit(".github/workflows/release-validation.yml", "out of scope\n")
        result = self.gate("heavy")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the canary path allowlist", result.stderr)

    def test_heavy_rejects_rename_into_allowed_path(self):
        (self.repo / "docs").mkdir()
        self.git("mv", "README.md", "docs/task-set-delivery.md")
        self.git("commit", "-qm", "rename an out-of-scope path")
        result = self.gate("heavy")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the canary path allowlist", result.stderr)

    def test_heavy_rejects_old_base(self):
        self.git("switch", "-qc", "candidate")
        self.commit("docs/task-set-delivery.md", "stack\n")
        self.git("switch", "-q", "main")
        current = self.commit("README.md", "new main\n")
        self.git("update-ref", "refs/remotes/origin/main", current)
        self.git("switch", "-q", "candidate")
        self.assertNotEqual(self.gate("heavy").returncode, 0)

    def test_fast_runs_focused_helper_tests(self):
        base = self.commit(HELPER_TEST, "echo focused-helper-test; exit 23\n")
        self.git("switch", "-qc", "helper")
        head = self.commit(HELPER, "# helper update\n")
        self.git("switch", "-q", "main")
        self.git("merge", "-q", "--no-ff", "helper", "-m", "test merge")
        result = self.gate("fast", PR_HEAD=head, PR_BASE=base)
        self.assertIn("focused-helper-test", result.stdout)
        self.assertNotEqual(result.returncode, 0)

    def scoped_batch(self, scope="helper", upper_path=None):
        _, prefix, approval = POLICY["STACK_SCOPES"][scope]
        source, tests = {
            "helper": (HELPER, HELPER_TEST),
            "project": ("scripts/project", PROJECT_TEST),
            WAVE_SCOPE: (WAVE_SCRIPT, WAVE_TEST),
        }[scope]
        self.git("switch", "-qc", prefix + "lower")
        lower = self.commit(source, "# source update\n")
        self.git("switch", "-qc", prefix + "upper")
        upper = self.commit(upper_path or tests, "# regression test\n")
        self.git("switch", "-qc", "candidate", self.base)
        self.git("merge", "-q", "--no-ff", lower, "-m", "Merge lower")
        self.git("merge", "-q", "--no-ff", upper, "-m", "Merge upper")
        candidate = self.git("rev-parse", "HEAD")

        def ref(commit, branch):
            return {"sha": commit, "ref": branch, "repo": {"full_name": REPO}}

        def status(base):
            return {"statuses": [{
                "context": approval, "state": "success",
                "description": f"base={base} stack=10,11",
            }]}

        responses = {
            f"commits/{lower}/status": status(self.base),
            f"commits/{upper}/status": status(lower),
            "pulls/10": {
                "head": ref(lower, prefix + "lower"),
                "base": ref(self.base, "main"),
                "state": "open", "draft": False, "body": "",
            },
            "pulls/11": {
                "head": ref(upper, prefix + "upper"),
                "base": ref(lower, prefix + "lower"),
                "state": "open", "draft": False, "body": "Depends-On: #10",
            },
        }
        return candidate, upper, responses

    def check_batch(self, candidate, responses, scope="helper"):
        return POLICY["verify_batch"](
            self.base, candidate, REPO, scope,
            request=lambda _repo, endpoint: responses[endpoint],
            run_git=lambda *args: subprocess.check_output(["git", *args], cwd=self.repo),
        )

    def test_helper_batch_accepts_exact_reviewed_chain(self):
        candidate, _, responses = self.scoped_batch()
        self.check_batch(candidate, responses)

    def test_helper_batch_rejects_changed_head_or_base(self):
        candidate, upper, responses = self.scoped_batch()
        for ref in ("head", "base"):
            with self.subTest(ref=ref):
                current = responses["pulls/11"][ref]["sha"]
                responses["pulls/11"][ref]["sha"] = self.base
                with self.assertRaisesRegex(ValueError, "reviewed head/base"):
                    self.check_batch(candidate, responses)
                responses["pulls/11"][ref]["sha"] = current

        receipt = responses[f"commits/{upper}/status"]["statuses"][0]
        receipt["description"] = f"base={self.base} stack=10,11"
        with self.assertRaisesRegex(ValueError, "immediate base"):
            self.check_batch(candidate, responses)

    def test_helper_batch_rejects_missing_approval_or_other_members(self):
        candidate, upper, responses = self.scoped_batch()
        statuses = responses[f"commits/{upper}/status"]["statuses"]
        receipt = statuses.pop()
        with self.assertRaisesRegex(ValueError, "Missing successful helper approval"):
            self.check_batch(candidate, responses)
        statuses.append(receipt)
        receipt["description"] = receipt["description"].replace("10,11", "10,12")
        with self.assertRaisesRegex(ValueError, "exact batch"):
            self.check_batch(candidate, responses)

    def test_project_batch_requires_its_own_current_approval(self):
        candidate, upper, responses = self.scoped_batch("project")
        self.check_batch(candidate, responses, "project")
        receipt = responses[f"commits/{upper}/status"]["statuses"][0]
        receipt["context"] = "openbenches-helper-reviewed"
        with self.assertRaisesRegex(ValueError, "Missing successful project approval"):
            self.check_batch(candidate, responses, "project")
        receipt["context"] = "openbenches-project-reviewed"
        receipt["description"] = f"base={self.base} stack=10,11"
        with self.assertRaisesRegex(ValueError, "immediate base"):
            self.check_batch(candidate, responses, "project")

    def test_heavy_rejects_mixed_project_and_helper_paths(self):
        self.commit("scripts/project", "# project update\n")
        self.commit(HELPER, "# helper update\n")
        result = self.gate("heavy")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the canary path allowlist", result.stderr)

    def test_wave_batch_requires_current_approval_and_exact_order(self):
        candidate, upper, responses = self.scoped_batch(WAVE_SCOPE)
        self.check_batch(candidate, responses, WAVE_SCOPE)
        receipt = responses[f"commits/{upper}/status"]["statuses"][0]
        current = receipt.copy()
        receipt["context"] = "openbenches-project-reviewed"
        with self.assertRaisesRegex(ValueError, "Missing successful wave-widget-sync approval"):
            self.check_batch(candidate, responses, WAVE_SCOPE)
        receipt.update(current)
        receipt["description"] = f"base={self.base} stack=10,11"
        with self.assertRaisesRegex(ValueError, "immediate base"):
            self.check_batch(candidate, responses, WAVE_SCOPE)
        receipt.update(current)
        receipt["description"] = receipt["description"].replace("10,11", "11,10")
        with self.assertRaisesRegex(ValueError, "exact batch"):
            self.check_batch(candidate, responses, WAVE_SCOPE)

    def test_wave_scope_rejects_the_launcher_even_in_a_reviewed_batch(self):
        launcher = "scripts/wave-container-shell.sh"
        candidate, _, responses = self.scoped_batch(WAVE_SCOPE, upper_path=launcher)
        with self.assertRaisesRegex(ValueError, "path outside the pilot"):
            self.check_batch(candidate, responses, WAVE_SCOPE)
        self.assertEqual(
            POLICY["candidate_scope"]({p.encode() for p in (WAVE_SCRIPT, WAVE_RECONCILER, WAVE_TEST)}),
            WAVE_SCOPE,
        )
        result = self.gate("heavy")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the canary path allowlist", result.stderr)

    def test_wave_fast_propagates_focused_fixture_failure(self):
        self.commit(WAVE_SCRIPT, "# widget entrypoint\n")
        self.commit(WAVE_RECONCILER, "# reconciler\n")
        base = self.commit(WAVE_TEST, "import sys\nprint(*sys.argv[1:])\nsys.exit(23)\n")
        self.git("switch", "-qc", "wave")
        head = self.commit(WAVE_RECONCILER, "# reconciler update\n")
        self.git("switch", "-q", "main")
        self.git("merge", "-q", "--no-ff", "wave", "-m", "test merge")
        result = self.gate("fast", PR_HEAD=head, PR_BASE=base)
        self.assertIn("test_reconciles_owned_widgets_and_is_idempotent", result.stdout)
        self.assertIn("test_invalid_or_symlinked_settings_are_preserved", result.stdout)
        self.assertNotEqual(result.returncode, 0)

    def test_candidate_aggregate_fails_closed_for_incomplete_wave_matrix(self):
        def result(event="push", scope=WAVE_SCOPE, verified="success", project="skipped", wave="success"):
            return self.gate("gate", GITHUB_EVENT_NAME=event, SCOPE=scope,
                             VERIFIED=verified, PROJECT=project, WAVE_WIDGET_SYNC=wave)

        self.assertEqual(result().returncode, 0)
        for status in ("failure", "cancelled", "skipped", ""):
            with self.subTest(status=status):
                self.assertNotEqual(result(wave=status).returncode, 0)
                self.assertNotEqual(result(event="pull_request", project="success", wave=status).returncode, 0)
        self.assertNotEqual(result(verified="failure").returncode, 0)
        self.assertNotEqual(result(project="success").returncode, 0)
        self.assertEqual(result(event="pull_request", verified="skipped", project="success").returncode, 0)
        for scope, project in (("docs", "skipped"), ("helper", "skipped"), ("project", "success")):
            with self.subTest(scope=scope):
                self.assertEqual(result(scope=scope, project=project, wave="skipped").returncode, 0)
                self.assertNotEqual(result(scope=scope, project=project).returncode, 0)

    def test_fast_runs_focused_project_tests(self):
        base = self.commit(PROJECT_TEST, "import sys\nprint(*sys.argv[1:])\nsys.exit(23)\n")
        self.git("switch", "-qc", "project")
        head = self.commit("scripts/project", "# project update\n")
        self.git("switch", "-q", "main")
        self.git("merge", "-q", "--no-ff", "project", "-m", "test merge")
        result = self.gate("fast", PR_HEAD=head, PR_BASE=base)
        self.assertIn("test_forwarders_preserve_legacy_argv_and_exit_code", result.stdout)
        self.assertNotEqual(result.returncode, 0)

    def test_heavy_rejects_mixed_helper_and_docs_paths(self):
        self.commit(HELPER, "# helper update\n")
        self.commit("docs/task-set-delivery.md", "docs\n")
        result = self.gate("heavy")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the canary path allowlist", result.stderr)


class WaveEfficiencyTest(unittest.TestCase):
    setUp = StackCiTest.setUp
    git = StackCiTest.git
    commit = StackCiTest.commit

    def chain(self, count=2, mixed_lower=False):
        for path in (WAVE_SCRIPT, WAVE_RECONCILER, WAVE_TEST):
            self.base = self.commit(path, "# original\n")
        self.git("update-ref", "refs/remotes/origin/main", self.base)
        responses = {"branches/main": {"commit": {"sha": self.base}}}
        parent_sha, parent_ref = self.base, "main"
        for index in range(count):
            number = index + 10
            branch = f"ci/stack-wave-widget-sync/{number}"
            self.git("switch", "-qc", branch)
            head = self.commit(
                "bootstrap.sh" if mixed_lower and not index else WAVE_TEST,
                f"# update {index}\n")
            body = "Stack-CI: wave-widget-sync"
            if index:
                body += f"\nDepends-On: #{number - 1}"
            pr = {
                "number": number, "state": "open", "draft": False, "body": body,
                "head": {"sha": head, "ref": branch, "repo": {"full_name": REPO}},
                "base": {"sha": parent_sha, "ref": parent_ref, "repo": {"full_name": REPO}},
            }
            responses[f"pulls/{number}"] = pr
            parent_sha, parent_ref = head, branch
        event = {"number": number, "pull_request": deepcopy(pr)}
        return event, responses

    def qualified(self, event, responses):
        def run_git(*args):
            if args[0] == "fetch":
                # The fixture commits already exist locally; no network.
                return b""
            return subprocess.check_output(["git", *args], cwd=self.repo)

        return POLICY["wave_pr_qualified"](
            event, self.base, REPO,
            request=lambda _repo, endpoint: responses[endpoint],
            run_git=run_git)

    def test_qualified_bottom_two_and_three_member_chains(self):
        event, responses = self.chain(3)
        for number in (10, 11, 12):
            with self.subTest(number=number):
                member = {"number": number, "pull_request": deepcopy(responses[f"pulls/{number}"])}
                self.assertTrue(self.qualified(member, responses))

    def test_mixed_ancestor_retains_full_checks(self):
        event, responses = self.chain(mixed_lower=True)
        self.assertFalse(self.qualified(event, responses))

    def test_opt_in_prefix_repo_state_and_dependency_are_not_guessed(self):
        event, responses = self.chain()
        for field, value in (
            ("body", ""), ("body", "Stack-CI: wave-widget-sync\nDepends-On: #99"),
            ("body", "Stack-CI: wave-widget-sync\nDepends-On: #10\nDepends-On: #10"),
            ("draft", True), ("state", "closed"),
        ):
            with self.subTest(field=field, value=value):
                changed = deepcopy(responses)
                changed["pulls/11"][field] = value
                self.assertFalse(self.qualified(event, changed))
        for ref, field, value in (
            ("head", "repo", {"full_name": "someone/fork"}),
            ("base", "repo", {"full_name": "someone/fork"}),
            ("head", "ref", "ordinary/wave"),
            ("base", "ref", "ci/stack-wave-widget-sync/not-the-parent"),
            ("base", "sha", self.base),
        ):
            with self.subTest(ref=ref, field=field):
                changed = deepcopy(responses)
                changed["pulls/11"][ref][field] = value
                self.assertFalse(self.qualified(event, changed))
        changed = deepcopy(responses)
        changed["pulls/10"]["body"] = ""
        self.assertFalse(self.qualified(event, changed))

    def test_stale_event_or_main_retains_full_checks(self):
        event, responses = self.chain()
        for ref in ("head", "base"):
            changed = deepcopy(event)
            changed["pull_request"][ref]["sha"] = "f" * 40
            self.assertFalse(self.qualified(changed, responses))
        changed = deepcopy(responses)
        changed["branches/main"]["commit"]["sha"] = "f" * 40
        self.assertFalse(self.qualified(event, changed))
        self.base = self.commit("README.md", "new main\n")
        self.assertFalse(self.qualified(event, responses))

    def test_rename_delete_and_type_or_mode_change_retain_full_checks(self):
        event, responses = self.chain(1)
        for operation in ("rename", "delete", "symlink", "mode"):
            with self.subTest(operation=operation):
                self.git("switch", "-q", "--detach", self.base)
                path = self.repo / WAVE_TEST
                if operation == "rename":
                    self.git("mv", WAVE_TEST, "different.py")
                elif operation == "delete":
                    self.git("rm", WAVE_TEST)
                elif operation == "symlink":
                    path.unlink()
                    path.symlink_to("elsewhere")
                    self.git("add", WAVE_TEST)
                else:
                    self.git("update-index", "--chmod=+x", WAVE_TEST)
                self.git("commit", "-qm", operation)
                changed = deepcopy(responses)
                changed["pulls/10"]["head"]["sha"] = self.git("rev-parse", "HEAD")
                current = {"number": 10, "pull_request": deepcopy(changed["pulls/10"])}
                self.assertFalse(self.qualified(current, changed))

    def test_missing_api_or_git_data_and_too_long_chains_retain_full_checks(self):
        event, responses = self.chain(4)
        self.assertFalse(self.qualified(event, responses))
        self.assertFalse(self.qualified(event, {}))
        self.assertFalse(POLICY["wave_pr_qualified"](
            event, self.base, REPO,
            request=lambda *_args: responses["pulls/13"],
            run_git=lambda *_args: (_ for _ in ()).throw(OSError("unavailable"))))

    def test_workflow_keeps_full_fallback_and_fast_ci(self):
        workflow = (GATE.parents[1] / ".github/workflows/credential-recovery.yml").read_text()
        for job in ("regression", "tools-runtime", "credential-images", "component-lifecycle"):
            # Include the whole job header before its first step.
            header = workflow.split(f"  {job}:\n", 1)[1].split("    steps:", 1)[0]
            self.assertIn("needs: classify", header)
            self.assertIn("always() && !cancelled()", header)
            self.assertIn("needs.classify.result != 'success' || needs.classify.outputs.wave_only != 'true'", header)
        self.assertIn("ref: main", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("classify-wave", workflow)
        fast = (GATE.parents[1] / ".github/workflows/stack-pr-fast.yml").read_text()
        self.assertIn("python3 scripts/stack-ci.py fast", fast)
        self.assertNotIn("needs: classify", fast)

    def test_classifier_output_defaults_full_for_non_pr_and_errors(self):
        function = POLICY["classify_wave"]
        output = self.repo / "outputs"
        event_file = self.repo / "event.json"
        event_file.write_text("not JSON")
        environment = {
            "GITHUB_EVENT_NAME": "pull_request", "GITHUB_REPOSITORY": "opensoft/openBenches",
            "GITHUB_OUTPUT": str(output), "GITHUB_EVENT_PATH": str(event_file),
        }
        for event in ("push", "workflow_dispatch", "pull_request"):
            with self.subTest(event=event):
                output.write_text("")
                function({**environment, "GITHUB_EVENT_NAME": event})
                self.assertEqual(output.read_text(), "wave_only=false\n")
        event_file.write_text("{}")
        with patch.dict(function.__globals__, git=lambda *_: b"f" * 40,
                        wave_pr_qualified=lambda *_: True):
            output.write_text("")
            function(environment)
            self.assertEqual(output.read_text(), "wave_only=true\n")
        for value in (False, None):
            with patch.dict(function.__globals__, git=lambda *_: b"f" * 40,
                            wave_pr_qualified=lambda *_: value):
                output.write_text("")
                function(environment)
                self.assertEqual(output.read_text(), "wave_only=false\n")
        with patch.dict(function.__globals__,
                        git=lambda *_: (_ for _ in ()).throw(OSError("unavailable"))):
            output.write_text("")
            function(environment)
            self.assertEqual(output.read_text(), "wave_only=false\n")

    def test_only_explicit_successful_classification_can_skip_jobs(self):
        # Matches the expression pinned in the workflow wiring test.
        for result in ("success", "failure", "cancelled", "skipped", ""):
            for output in ("true", "false", "", "True", "unknown"):
                run_full = result != "success" or output != "true"
                self.assertEqual(run_full, (result, output) != ("success", "true"))


if __name__ == "__main__":
    unittest.main()

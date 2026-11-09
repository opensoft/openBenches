"""Exercise stack CI against real commits in a disposable Git repository."""

import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest


GATE = Path(__file__).resolve().parents[1] / "scripts" / "stack-ci.py"
POLICY = runpy.run_path(str(GATE))
HELPER_TEST = POLICY["HELPER_TEST"]
HELPER = next(p.decode() for p in POLICY["HELPER_PATHS"] if p.decode() != HELPER_TEST)
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

    def helper_batch(self):
        self.git("switch", "-qc", "ci/stack-helpers/lower")
        lower = self.commit(HELPER, "# helper update\n")
        self.git("switch", "-qc", "ci/stack-helpers/upper")
        upper = self.commit(HELPER_TEST, "# regression test\n")
        self.git("switch", "-qc", "candidate", self.base)
        self.git("merge", "-q", "--no-ff", lower, "-m", "Merge lower")
        self.git("merge", "-q", "--no-ff", upper, "-m", "Merge upper")
        candidate = self.git("rev-parse", "HEAD")

        def ref(commit, branch):
            return {"sha": commit, "ref": branch, "repo": {"full_name": REPO}}

        def status(base):
            return {"statuses": [{
                "context": POLICY["HELPER_APPROVAL"], "state": "success",
                "description": f"base={base} stack=10,11",
            }]}

        responses = {
            f"commits/{lower}/status": status(self.base),
            f"commits/{upper}/status": status(lower),
            "pulls/10": {
                "head": ref(lower, "ci/stack-helpers/lower"),
                "base": ref(self.base, "main"),
                "state": "open", "draft": False, "body": "",
            },
            "pulls/11": {
                "head": ref(upper, "ci/stack-helpers/upper"),
                "base": ref(lower, "ci/stack-helpers/lower"),
                "state": "open", "draft": False, "body": "Depends-On: #10",
            },
        }
        return candidate, upper, responses

    def check_helper_batch(self, candidate, responses):
        return POLICY["verify_helper_batch"](
            self.base, candidate, REPO,
            request=lambda _repo, endpoint: responses[endpoint],
            run_git=lambda *args: subprocess.check_output(["git", *args], cwd=self.repo),
        )

    def test_helper_batch_accepts_exact_reviewed_chain(self):
        candidate, _, responses = self.helper_batch()
        self.check_helper_batch(candidate, responses)

    def test_helper_batch_rejects_changed_head_or_base(self):
        candidate, upper, responses = self.helper_batch()
        for ref in ("head", "base"):
            with self.subTest(ref=ref):
                current = responses["pulls/11"][ref]["sha"]
                responses["pulls/11"][ref]["sha"] = self.base
                with self.assertRaisesRegex(ValueError, "reviewed head/base"):
                    self.check_helper_batch(candidate, responses)
                responses["pulls/11"][ref]["sha"] = current

        receipt = responses[f"commits/{upper}/status"]["statuses"][0]
        receipt["description"] = f"base={self.base} stack=10,11"
        with self.assertRaisesRegex(ValueError, "immediate base"):
            self.check_helper_batch(candidate, responses)

    def test_helper_batch_rejects_missing_approval_or_other_members(self):
        candidate, upper, responses = self.helper_batch()
        statuses = responses[f"commits/{upper}/status"]["statuses"]
        receipt = statuses.pop()
        with self.assertRaisesRegex(ValueError, "Missing successful helper approval"):
            self.check_helper_batch(candidate, responses)
        statuses.append(receipt)
        receipt["description"] = receipt["description"].replace("10,11", "10,12")
        with self.assertRaisesRegex(ValueError, "exact batch"):
            self.check_helper_batch(candidate, responses)

    def test_heavy_rejects_mixed_helper_and_docs_paths(self):
        self.commit(HELPER, "# helper update\n")
        self.commit("docs/task-set-delivery.md", "docs\n")
        result = self.gate("heavy")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the canary path allowlist", result.stderr)


if __name__ == "__main__":
    unittest.main()

"""Exercise stack CI against real commits in a disposable Git repository."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


GATE = Path(__file__).resolve().parents[1] / "scripts" / "stack-ci.py"


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


if __name__ == "__main__":
    unittest.main()

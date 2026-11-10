"""Run the complete shared event-proof fixture suite for the helper policy."""

from pathlib import Path
import runpy
import unittest


ROOT = Path(__file__).resolve().parents[1]
SHARED = runpy.run_path(str(ROOT / "devcontainer.test/test-project-stack-ci.py"),
                       init_globals={"SCOPE": "helper"})


class HelperEfficiencyTests(SHARED["ProjectEfficiencyTests"]):
    def test_exact_five_jobs_and_command_policy_are_required(self):
        policy = SHARED["POLICY"]
        parity = runpy.run_path(str(ROOT / "devcontainer.test/test-helper-coverage-parity.py"))
        expected = {
            "Verify queue candidate", "openbenches-stack-heavy",
            "Helper full Bash regression", "Helper Git 2.34.1 compatibility",
            "Helper Bash 3.2 compatibility", "Helper PowerShell Linux", "Helper PowerShell Windows",
        }
        self.assertEqual(policy["REQUIRED_JOBS"], expected)
        for kind in ("bash", "compat", "powershell"):
            self.assertIn(f".github/actions/openspeckit-{kind}", policy["POLICY_PATHS"])
        self.assertEqual(len(parity["JOBS"]), 5)

    def test_each_missing_duplicate_or_non_success_job_keeps_full_checks(self):
        from copy import deepcopy

        policy = SHARED["POLICY"]
        event = self.closed_candidate()
        endpoint = "actions/runs/123/jobs?per_page=100"
        original = deepcopy(self.responses)
        for name in policy["REQUIRED_JOBS"]:
            for outcome in ("missing", "duplicate", "failure", "cancelled", "skipped", "", "unknown"):
                with self.subTest(job=name, outcome=outcome):
                    self.responses = deepcopy(original)
                    response = self.responses[endpoint]
                    job = next(job for job in response["jobs"] if job["name"] == name)
                    if outcome == "missing":
                        response["jobs"].remove(job)
                        response["total_count"] -= 1
                    elif outcome == "duplicate":
                        response["jobs"].append(deepcopy(job))
                        response["total_count"] += 1
                    else:
                        job["conclusion"] = outcome
                    self.assertIsNone(self.decide(event, actor="maintainer"))

    def test_every_command_and_policy_change_invalidates_old_candidate_proof(self):
        from unittest.mock import patch

        policy = SHARED["POLICY"]
        event = self.closed_candidate()
        original_git = self.run_git
        for path in policy["POLICY_PATHS"]:
            def changed(*args):
                if args[:2] == ("diff", "--quiet") and path in args:
                    raise policy["subprocess"].CalledProcessError(1, args)
                return original_git(*args)

            with self.subTest(path=path), patch.object(self, "run_git", side_effect=changed):
                self.assertIsNone(self.decide(event, actor="maintainer"))


if __name__ == "__main__":
    unittest.main()

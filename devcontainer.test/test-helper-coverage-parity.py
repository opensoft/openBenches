"""Audit the shared CI commands against the pre-extraction five-job baseline.

These readers deliberately handle only the checked-in block/inline run style;
actionlint validates YAML and hosted jobs validate the real runner environments.
No third-party YAML parser or network is required for these policy fixtures.
"""

import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASELINE = json.loads((ROOT / "devcontainer.test/helper-integration-baseline.json").read_text())
POLICY = runpy.run_path(str(ROOT / "scripts/stack-ci.py"))
CHECKOUT = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
JOBS = {
    "helper-regression": ("ubuntu-24.04", "bash", "HELPER_REGRESSION"),
    "helper-git-2-34-1": ("ubuntu-22.04", "compat", "HELPER_GIT_2_34_1"),
    "helper-bash-3-2": ("ubuntu-24.04", "compat", "HELPER_BASH_3_2"),
    "helper-powershell-linux": ("ubuntu-24.04", "powershell", "HELPER_POWERSHELL_LINUX"),
    "helper-powershell-windows": ("windows-latest", "powershell", "HELPER_POWERSHELL_WINDOWS"),
}


def text(path):
    return (ROOT / path).read_text()


def job_block(source, name):
    match = re.search(rf"(?ms)^  {re.escape(name)}:\n.*?(?=^  [\w-]+:\n|\Z)", source)
    if not match:
        raise AssertionError(f"Missing job {name}")
    return match[0]


def commands(source):
    lines, result, index = source.splitlines(), [], 0
    while index < len(lines):
        match = re.match(r"^(\s+)run: (.*)$", lines[index])
        index += 1
        if not match:
            continue
        if match[2] != "|":
            result.append(match[2])
            continue
        indent, body = len(match[1]), []
        while index < len(lines) and (not lines[index].strip()
                or len(lines[index]) - len(lines[index].lstrip()) > indent):
            body.append(lines[index][indent + 2:])
            index += 1
        result.append("\n".join(body).rstrip())
    return result


def action(kind):
    return text(f".github/actions/openspeckit-{kind}/action.yml")


def gate_env(event="push", scope="helper"):
    helper_result = "success" if event == "pull_request" or scope == "helper" else "skipped"
    return {
        "GITHUB_EVENT_NAME": event, "SCOPE": scope, "VERIFIED": "success",
        "PROJECT": "success" if event == "pull_request" or scope == "project" else "skipped",
        "WAVE_WIDGET_SYNC": "success" if event == "pull_request" or scope == "wave-widget-sync" else "skipped",
        **{value[2]: helper_result for value in JOBS.values()},
    }


class HelperCoverageParityTests(unittest.TestCase):
    def test_full_bash_commands_and_special_environments_are_preserved(self):
        source = action("bash")
        self.assertEqual(commands(source), BASELINE["bash_runs"])
        self.assertEqual(len(commands(source)), 18)
        binary = source.split("    - name: Run the claude-profile binary-selection regression test\n")[1]
        environment = binary.split("      env:\n")[1].split("      run:")[0]
        actual = [line.strip() for line in environment.splitlines()
                  if line.strip() and not line.lstrip().startswith("#")]
        self.assertEqual(actual, BASELINE["bash_binary_environment"])
        heavy = job_block(text(".github/workflows/stack-candidate-heavy.yml"), "helper-regression")
        ordinary = text(".github/workflows/speckit-git-bash.yml")
        for line in BASELINE["bash_environment"].splitlines():
            self.assertIn(line.strip(), ordinary)
            self.assertIn(line.strip(), heavy)

    def test_legacy_container_commands_and_pins_are_preserved(self):
        run = commands(action("compat"))
        self.assertEqual(run[1:], BASELINE["git_2_34_runs"] + BASELINE["bash_3_2_runs"])
        source = action("compat")
        for runtime in ("git-2-34-1", "bash-3-2"):
            self.assertIn(f"if: inputs.runtime == '{runtime}'", source)

    def test_powershell_commands_keep_their_original_platform_shells(self):
        source = action("powershell")
        run = commands(source)
        self.assertEqual(run[1:3], [BASELINE["powershell_runs"][0]] * 2)
        self.assertEqual(run[3:], BASELINE["powershell_runs"][1:])
        for os_name, shell, marker in (("Linux", "bash", "Linux"), ("Windows", "pwsh", "Windows")):
            block = source.split(f"    - name: Verify Git and PowerShell ({marker})\n")[1].split("    - name:")[0]
            self.assertIn(f"if: runner.os == '{os_name}'", block)
            self.assertIn(f"shell: {shell}", block)
        self.assertIn("-WindowsStateOnly", source)

    def test_invalid_action_modes_cannot_succeed_without_running_a_suite(self):
        for kind, variable, valid in (
            ("compat", "OPENSPECKIT_COMPAT_RUNTIME", ("git-2-34-1", "bash-3-2")),
            ("powershell", "OPENSPECKIT_RUNNER_OS", ("Linux", "Windows")),
        ):
            guard = commands(action(kind))[0]
            for value in (*valid, "unknown", ""):
                with self.subTest(kind=kind, value=value):
                    result = subprocess.run(["bash", "-euo", "pipefail", "-c", guard],
                                            env={**os.environ, variable: value}, capture_output=True)
                    self.assertEqual(result.returncode == 0, value in valid)

    def test_ordinary_jobs_names_runners_timeouts_and_full_triggers_remain(self):
        for kind, file in (("bash", "speckit-git-bash.yml"), ("powershell", "speckit-git-powershell.yml")):
            source = text(f".github/workflows/{file}")
            headers = BASELINE["ordinary_headers"][kind]
            if kind == "powershell":
                headers = {"regression": headers}
            for name, header in headers.items():
                self.assertEqual(job_block(source, name).split("    steps:\n")[0], header)
            triggers = source.split("\npermissions:")[0]
            for line in BASELINE["trigger_sections"][kind].splitlines():
                if line.strip().startswith("- ") or line.strip() in ("push:", "pull_request:", "workflow_dispatch:"):
                    self.assertIn(line, triggers)
            self.assertNotIn("types:", triggers)
            self.assertNotIn("branches:", triggers)
            self.assertNotIn("classify", source)
            self.assertNotIn("skip_", source)
            self.assertEqual(source.count(CHECKOUT), 3 if kind == "bash" else 1)
            self.assertIn("permissions:\n  contents: read\n", source)
        bash = text(".github/workflows/speckit-git-bash.yml")
        self.assertIn("uses: ./.github/actions/openspeckit-bash", job_block(bash, "regression"))
        for name in ("git-2-34-1", "bash-3-2"):
            block = job_block(bash, name)
            self.assertIn("uses: ./.github/actions/openspeckit-compat", block)
            self.assertIn(f"runtime: {name}", block)
        self.assertIn("uses: ./.github/actions/openspeckit-powershell",
                      job_block(text(".github/workflows/speckit-git-powershell.yml"), "regression"))

    def test_five_exact_candidate_jobs_are_mandatory_for_helper_and_config(self):
        source = text(".github/workflows/stack-candidate-heavy.yml")
        for name, (runner, kind, variable) in JOBS.items():
            block = job_block(source, name)
            self.assertIn(f"runs-on: {runner}", block)
            self.assertIn("needs: verify", block)
            self.assertIn("github.event_name == 'pull_request'", block)
            self.assertIn("needs.verify.result == 'success' && needs.verify.outputs.scope == 'helper'", block)
            self.assertIn("!cancelled()", block)
            self.assertIn(CHECKOUT, block)
            self.assertIn("ref: ${{ github.sha }}", block)
            self.assertIn("persist-credentials: false", block)
            self.assertIn('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"', block)
            self.assertIn(f"uses: ./.github/actions/openspeckit-{kind}", block)
            self.assertIn(f"{variable}: ${{{{ needs.{name}.result }}}}", source)
        gate = job_block(source, "gate")
        for name in JOBS:
            self.assertIn(name, gate.split("    steps:")[0])
        verify = job_block(source, "verify")
        self.assertIn("if: steps.candidate.outputs.scope == 'docs'\n", verify)
        self.assertNotIn("scope == 'helper'", verify)
        self.assertIn("bash devBenches/devcontainer.test/test-speckit-git-feature.sh", verify)
        self.assertIn("'openbenches-stack-heavy'", gate)
        for kind in ("bash", "compat", "powershell"):
            self.assertNotIn("continue-on-error:", action(kind))
        self.assertNotIn("continue-on-error:", source)

    def test_required_helper_results_cannot_be_missing_failed_or_skipped(self):
        for event in ("push", "pull_request"):
            env = gate_env(event)
            POLICY["verify_results"](env)
            for _runner, _kind, variable in JOBS.values():
                for value in (None, "failure", "cancelled", "skipped", "", "unknown"):
                    with self.subTest(event=event, variable=variable, value=value):
                        changed = dict(env)
                        if value is None:
                            changed.pop(variable)
                        else:
                            changed[variable] = value
                        with self.assertRaises((KeyError, ValueError)):
                            POLICY["verify_results"](changed)

    def test_other_scope_results_and_admission_verification_remain_required(self):
        for scope in ("docs", "project", "wave-widget-sync"):
            env = gate_env(scope=scope)
            POLICY["verify_results"](env)
            env["HELPER_REGRESSION"] = "success"
            with self.assertRaises(ValueError):
                POLICY["verify_results"](env)
        for verified in ("failure", "cancelled", "skipped", ""):
            with self.assertRaises(ValueError):
                POLICY["verify_results"]({**gate_env(), "VERIFIED": verified})

    def test_new_actions_and_parity_changes_are_covered_by_ci(self):
        heavy = text(".github/workflows/stack-candidate-heavy.yml")
        for path in (".github/actions/openspeckit-*/**", "devcontainer.test/test-helper-coverage-parity.py",
                     "devcontainer.test/helper-integration-baseline.json",
                     ".github/workflows/speckit-git-bash.yml", ".github/workflows/speckit-git-powershell.yml"):
            self.assertIn(path, heavy)
        self.assertIn("python3 devcontainer.test/test-helper-coverage-parity.py",
                      text(".github/workflows/stack-pr-fast.yml"))


if __name__ == "__main__":
    unittest.main()

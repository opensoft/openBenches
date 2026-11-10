"""Offline source qualification of the opt-in Claude/Codex delivery bootstrap."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


def resolve_assets(test_file):
    """Support checkout, declared /test fixture mount and packaged Tools paths."""
    candidates = [parent / "devBenches/base-image/files/openspeckit/setup-openspeckit"
                  for parent in test_file.resolve().parents]
    candidates.extend((Path("/test-fixtures/base-image/files/openspeckit/setup-openspeckit"),
                       Path("/usr/local/bin/setup-openspeckit")))
    setup = next((path for path in candidates if path.is_file()), None)
    if setup is not None:
        sources = (setup.resolve().parent / "task-set-delivery/SKILL.md",
                   Path("/usr/local/share/openspeckit/task-set-delivery/SKILL.md"))
        source = next((path for path in sources if path.is_file()), None)
        if source is not None:
            return setup, source
    raise FileNotFoundError("Matching task-set delivery bootstrap/assets not found in checkout, /test-fixtures or installed Tools")


SETUP, SOURCE = resolve_assets(Path(__file__))
MARKER = "<!-- OPENSPEC-SPECKIT-TASK-SETS:START -->"


class AssetResolutionTest(unittest.TestCase):
    def test_shallow_test_path_uses_declared_fixture_before_installed_command(self):
        setup = Path("/test-fixtures/base-image/files/openspeckit/setup-openspeckit")
        source = setup.parent / "task-set-delivery/SKILL.md"
        present = {setup, source, Path("/usr/local/bin/setup-openspeckit")}
        with patch.object(Path, "is_file", lambda path: path in present):
            self.assertEqual(resolve_assets(Path("/test/test-task-set-delivery.py")), (setup, source))

    def test_installed_command_uses_packaged_skill_when_checkout_is_absent(self):
        setup = Path("/usr/local/bin/setup-openspeckit")
        source = Path("/usr/local/share/openspeckit/task-set-delivery/SKILL.md")
        with patch.object(Path, "is_file", lambda path: path in (setup, source)):
            self.assertEqual(resolve_assets(Path("/test/test-task-set-delivery.py")), (setup, source))

    def test_missing_assets_fail_with_actionable_location_instead_of_index_error(self):
        with patch.object(Path, "is_file", lambda _path: False):
            with self.assertRaisesRegex(FileNotFoundError, "/test-fixtures or installed Tools"):
                resolve_assets(Path("/test/test-task-set-delivery.py"))


class TaskSetDeliveryTest(unittest.TestCase):
    def setUp(self):
        fixture = tempfile.TemporaryDirectory()
        self.addCleanup(fixture.cleanup)
        self.root = Path(fixture.name)
        self.repo, self.home = self.root / "repo", self.root / "home"
        self.repo.mkdir()
        self.home.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.repo)], check=True)
        templates = self.repo / ".specify/templates"
        templates.mkdir(parents=True)
        for name in ("tasks-template.md", "plan-template.md"):
            (templates / name).write_text("# Handwritten template\n\nKeep this content.\n")
        for name in ("AGENTS.md", "CLAUDE.md"):
            (self.repo / name).write_text("AGENTS-shape.md\n\n# Handwritten instructions\nKeep this rule.\n")
        self.env = {
            **os.environ, "HOME": str(self.home),
            "AGENT_PROTOCOL_ROOT": str(self.root / "protocols"),
            "CLAUDE_CONFIG_DIR": str(self.home / "custom-claude-profile"),
            "CODEX_HOME": str(self.home / "custom-codex-profile"),
        }
        self.flags = [
            "--repo", str(self.repo), "--skip-init", "--no-worktrees",
            "--no-skill-links", "--no-global-agent-pointers", "--no-skill-shape-blocks",
            "--no-skill-routing-blocks", "--no-speckit-registration", "--preserve-readmes",
        ]

    def bootstrap(self, *flags, expected=0):
        result = subprocess.run(
            [sys.executable, str(SETUP), *self.flags, *flags], env=self.env,
            cwd=self.repo, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def snapshot(self):
        return {p.relative_to(self.repo).as_posix(): p.read_bytes()
                for p in self.repo.rglob("*") if p.is_file() and ".git" not in p.parts}

    def test_adoption_installs_same_skill_for_both_agents_and_preserves_context(self):
        self.bootstrap("--task-set-delivery")
        for home in (".agents", ".claude", ".codex"):
            target = self.repo / home / "skills/task-set-delivery/SKILL.md"
            self.assertEqual(target.read_text(), SOURCE.read_text())
            self.assertFalse(target.is_symlink())
        for name in ("AGENTS.md", "CLAUDE.md"):
            text = (self.repo / name).read_text()
            self.assertTrue(text.startswith("AGENTS-shape.md\n"))
            self.assertIn("Keep this rule.", text)
            self.assertEqual(text.count(MARKER), 1)
            self.assertIn(".agents/skills/task-set-delivery/SKILL.md", text)
        for name in ("tasks-template.md", "plan-template.md"):
            text = (self.repo / ".specify/templates" / name).read_text()
            self.assertIn("Keep this content.", text)
            self.assertIn("exactly one set and one PR", text)
        self.assertFalse(Path(self.env["CLAUDE_CONFIG_DIR"]).exists())
        self.assertFalse(Path(self.env["CODEX_HOME"]).exists())
        self.assertFalse((self.home / ".codex/AGENTS.md").exists())

    def test_rerun_is_idempotent_and_preserves_custom_skill_without_force(self):
        self.bootstrap("--task-set-delivery")
        before = self.snapshot()
        self.bootstrap("--task-set-delivery")
        self.assertEqual(self.snapshot(), before)
        skill = self.repo / ".claude/skills/task-set-delivery/SKILL.md"
        skill.write_text("# Custom delivery process\n")
        self.bootstrap("--task-set-delivery")
        self.assertEqual(skill.read_text(), "# Custom delivery process\n")
        self.bootstrap("--task-set-delivery", "--force")
        self.assertEqual(skill.read_text(), SOURCE.read_text())

    def test_non_adoption_and_dry_run_do_not_install_delivery(self):
        self.bootstrap()
        before = self.snapshot()
        for name in ("AGENTS.md", "CLAUDE.md"):
            self.assertNotIn(MARKER, (self.repo / name).read_text())
        self.bootstrap("--task-set-delivery", "--dry-run")
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.repo / ".agents/skills/task-set-delivery").exists())

    def test_symlinked_instruction_destination_never_changes_outside_target(self):
        outside = self.root / "outside.md"
        outside.write_text("do not change\n")
        path = self.repo / "CLAUDE.md"
        path.unlink()
        path.symlink_to(outside)
        result = subprocess.run(
            [sys.executable, str(SETUP), *self.flags, "--task-set-delivery"],
            env=self.env, cwd=self.repo, capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(path.is_symlink())
        self.assertEqual(outside.read_text(), "do not change\n")

    def test_incomplete_managed_block_stops_without_replacing_handwritten_text(self):
        self.bootstrap()
        path = self.repo / "AGENTS.md"
        text = path.read_text() + "\n" + MARKER + "\nHandwritten incomplete block\n"
        path.write_text(text)
        result = self.bootstrap("--task-set-delivery", expected=1)
        self.assertIn("Ambiguous task-set instruction markers", result.stderr)
        self.assertEqual(path.read_text(), text)

    def test_pointer_opt_out_is_respected_during_adoption(self):
        before = {name: (self.repo / name).read_bytes() for name in ("AGENTS.md", "CLAUDE.md")}
        self.bootstrap("--task-set-delivery", "--no-repo-agent-pointers")
        for name, text in before.items():
            self.assertEqual((self.repo / name).read_bytes(), text)
        self.assertTrue((self.repo / ".agents/skills/task-set-delivery/SKILL.md").is_file())

    def tool_fixture(self, version="missing", install_version="0.3.0"):
        binary = self.root / "bin"
        binary.mkdir()
        self.version_file = self.root / "version"
        self.calls = self.root / "calls"
        self.version_file.write_text(version)
        gh = binary / "gh"
        gh.write_text("""#!/usr/bin/env python3
import os, sys
from pathlib import Path
version = Path(os.environ['TEST_STACK_VERSION'])
with open(os.environ['TEST_STACK_CALLS'], 'a') as stream:
    print(' '.join(sys.argv[1:]), file=stream)
if sys.argv[1:] == ['stack', '--version']:
    value = version.read_text()
    if value == 'missing':
        sys.exit(1)
    print('gh stack version ' + value)
elif sys.argv[1:] == ['extension', 'install', 'github/gh-stack', '--pin', 'v0.3.0']:
    version.write_text(os.environ['TEST_INSTALL_VERSION'])
else:
    sys.exit('Unexpected GitHub operation')
""")
        gh.chmod(0o755)
        self.env.update(
            PATH=str(binary) + os.pathsep + self.env["PATH"],
            TEST_STACK_VERSION=str(self.version_file), TEST_STACK_CALLS=str(self.calls),
            TEST_INSTALL_VERSION=install_version,
        )

    def test_tool_install_is_explicit_and_pinned_and_reruns_without_reinstall(self):
        self.tool_fixture()
        self.bootstrap("--task-set-delivery")
        self.assertFalse(self.calls.exists())
        self.bootstrap("--task-set-delivery", "--install-stack-tools")
        self.bootstrap("--task-set-delivery", "--install-stack-tools")
        calls = self.calls.read_text().splitlines()
        self.assertEqual(calls.count("extension install github/gh-stack --pin v0.3.0"), 1)
        self.assertEqual(self.version_file.read_text(), "0.3.0")

    def test_other_installed_version_is_not_replaced(self):
        self.tool_fixture(version="0.4.0")
        before = self.snapshot()
        result = self.bootstrap("--task-set-delivery", "--install-stack-tools", expected=1)
        self.assertIn("leaving it unchanged", result.stderr)
        self.assertEqual(self.version_file.read_text(), "0.4.0")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.calls.read_text().splitlines(), ["stack --version"])

    def test_tool_dry_run_does_not_install_and_bad_install_fails(self):
        self.tool_fixture(install_version="0.4.0")
        self.bootstrap("--task-set-delivery", "--install-stack-tools", "--dry-run")
        self.assertEqual(self.version_file.read_text(), "missing")
        before = self.snapshot()
        result = self.bootstrap("--task-set-delivery", "--install-stack-tools", expected=1)
        self.assertIn("did not report 0.3.0", result.stderr)
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()

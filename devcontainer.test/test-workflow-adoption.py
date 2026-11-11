"""Audit durable delivery discovery from a complete source checkout/export."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import re
import runpy
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACKAGED = Path("devBenches/base-image/files/openspeckit/task-set-delivery/SKILL.md")
ASSETS = (
    Path(".agents/skills/task-set-delivery/SKILL.md"),
    Path(".claude/skills/task-set-delivery/SKILL.md"),
)
SETUP = ROOT / "devBenches/base-image/files/openspeckit/setup-openspeckit"


def audit_adoption(root):
    canonical = (root / PACKAGED).read_bytes()
    for relative in ASSETS:
        path = root / relative
        if path.is_symlink() or not path.is_file() or path.read_bytes() != canonical:
            raise ValueError(f"Missing, linked or divergent skill asset: {relative}")
    agents = (root / "AGENTS.md").read_text()
    if (ASSETS[0].as_posix() not in agents
            or agents.count("<!-- OPENSPEC-SPECKIT-TASK-SETS:START -->") != 1
            or agents.count("<!-- OPENSPEC-SPECKIT-TASK-SETS:END -->") != 1):
        raise ValueError("AGENTS.md must point to the tracked delivery skill in one managed block")
    if not re.search(r"(?m)^@AGENTS\.md\s*$", (root / "CLAUDE.md").read_text()):
        raise ValueError("CLAUDE.md must import the repository AGENTS.md")


class WorkflowAdoptionTest(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for relative in (*ASSETS, PACKAGED, Path("AGENTS.md"), Path("CLAUDE.md")):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        return root

    def test_complete_source_contains_matching_discoverable_assets(self):
        audit_adoption(ROOT)

    def test_independent_copy_drift_is_rejected(self):
        root = self.fixture()
        path = root / ASSETS[1]
        path.write_bytes(path.read_bytes() + b"\n# drift\n")
        with self.assertRaisesRegex(ValueError, "divergent skill asset"):
            audit_adoption(root)

    def test_missing_copy_is_rejected(self):
        root = self.fixture()
        (root / ASSETS[0]).unlink()
        with self.assertRaisesRegex(ValueError, "Missing"):
            audit_adoption(root)

    def test_broken_instruction_import_is_rejected(self):
        root = self.fixture()
        (root / "CLAUDE.md").write_text("# No repository import\n")
        with self.assertRaisesRegex(ValueError, "must import"):
            audit_adoption(root)

    def test_missing_repository_pointer_is_rejected(self):
        root = self.fixture()
        path = root / "AGENTS.md"
        path.write_text(path.read_text().replace(ASSETS[0].as_posix(), "missing/SKILL.md"))
        with self.assertRaisesRegex(ValueError, "must point"):
            audit_adoption(root)

    def test_delivery_refresh_preserves_active_plan_and_is_repeatable(self):
        root = self.fixture()
        path = root / "AGENTS.md"
        before = path.read_text() + "\nHandwritten acceptance sentinel.\n"
        path.write_text(before)
        active = re.search(r"(?s)<!-- SPECKIT START -->.*?<!-- SPECKIT END -->", before)
        self.assertIsNotNone(active)
        namespace = runpy.run_path(str(SETUP))
        refresh = namespace["ensure_task_set_delivery"]
        source = ROOT / PACKAGED.parent
        with redirect_stdout(io.StringIO()):
            refresh(root, source, False, False, True)
        after = path.read_text()
        self.assertIn(active[0], after)
        self.assertEqual(before.splitlines()[0], after.splitlines()[0])
        self.assertIn("Handwritten acceptance sentinel.", after)
        audit_adoption(root)
        snapshot = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        with redirect_stdout(io.StringIO()):
            refresh(root, source, False, False, True)
        self.assertEqual(snapshot, {p.relative_to(root): p.read_bytes()
                                    for p in root.rglob("*") if p.is_file()})


if __name__ == "__main__":
    unittest.main()

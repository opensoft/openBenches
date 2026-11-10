"""Offline park handoff regression fixtures, reusable by downstream tool copies."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

CANONICAL=Path(__file__).resolve().parents[1]/"base-image/files/speckit-worktree/templates/specify"
DEFAULT=CANONICAL if CANONICAL.is_dir() else Path(__file__).resolve().parents[2]/".specify"
TEMPLATES=Path(os.environ.get("SPECKIT_PARK_TEMPLATE_ROOT",DEFAULT)).resolve()
SCRIPTS=Path("extensions/git/scripts/bash")


class ParkHandoffTests(unittest.TestCase):
    def setUp(self):
        self.scratch=tempfile.TemporaryDirectory(prefix="park-handoff-")
        self.addCleanup(self.scratch.cleanup)
        self.base=Path(self.scratch.name)
        self.env={k:v for k,v in os.environ.items()
                  if not k.startswith(("SPECIFY_","SPECKIT_","AGENT_PROTOCOL_ROOT"))}
        self.env.update(GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_NOSYSTEM="1",
                        GIT_TERMINAL_PROMPT="0",AGENT_PROTOCOL_ROOT=str(self.base/"protocol"))
        self.root=self.init(self.base/"project")
        self.origins={}
        for role in ("spec","code"):
            seed=self.init(self.base/(role+"-seed"))
            origin=self.base/(role+"-origin.git")
            self.git(self.base,"clone","-q","--bare",str(seed),str(origin))
            self.origins[role]=origin
            self.git(self.root,"-c","protocol.file.allow=always","submodule","add","-q",str(origin),role)
            self.identity(self.root/role)
        (self.root/"project.yaml").write_text(
            "kind: project-manifest\nschema: project-repo-schema\nid: fixture-project\nlegs:\n"
            "  - role: assembly\n    repository: dummy/fixture-project\n"
            "  - role: spec\n    path: spec\n  - role: code\n    path: code\n")
        destination=self.root/".specify"/SCRIPTS
        destination.mkdir(parents=True)
        for name in ("park.sh","git-common.sh","workspace-common.sh"):
            shutil.copyfile(TEMPLATES/SCRIPTS/name,destination/name)
        (self.root/".specify/extensions/git/git-config.yml").write_text(
            "checkout_mode: worktree\nbase_branch: main\nworktree_root: worktrees\n")
        (self.root/".gitignore").write_text("/worktrees/\n/.specify/feature.json\n")
        self.git(self.root,"add","-A")
        self.git(self.root,"commit","-qm","fixture project")
        self.workspace=self.init(self.base/"workspace")
        self.workspace_origin=self.base/"workspace-origin.git"
        self.git(self.base,"init","--bare","-q",str(self.workspace_origin))
        self.git(self.workspace,"remote","add","origin",str(self.workspace_origin))
        self.git(self.workspace,"push","-q","-u","origin","main")
        self.manifest=self.workspace/"workspaces/dummy/fixture-project.yaml"

    def run_command(self,cwd,*args,check=True):
        result=subprocess.run(args,cwd=cwd,env=self.env,text=True,capture_output=True,timeout=90)
        if check:
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return result

    def git(self,cwd,*args):
        return self.run_command(cwd,"git","-c","commit.gpgsign=false",*args).stdout.strip()

    def identity(self,path):
        self.git(path,"config","user.name","Handoff fixture")
        self.git(path,"config","user.email","handoff@example.invalid")

    def init(self,path):
        path.mkdir(parents=True)
        self.git(path,"init","-q","-b","main")
        self.identity(path)
        (path/"README.md").write_text("fixture\n")
        self.git(path,"add","README.md")
        self.git(path,"commit","-qm","fixture")
        return path

    def feature(self,branch):
        trees={}
        for role in ("spec","code"):
            tree=self.root/"worktrees"/branch/role
            self.git(self.root/role,"worktree","add","-q","-b",branch,str(tree),"main")
            trees[role]=tree
        directory=trees["spec"]/"specs"/branch
        directory.mkdir(parents=True)
        (directory/"spec.md").write_text("fixture spec\n")
        self.git(trees["spec"],"add","specs")
        self.git(trees["spec"],"commit","-qm","feature fixture")
        return trees

    def park(self,*args):
        return self.run_command(self.root,"bash",str(Path(".specify")/SCRIPTS/"park.sh"),
                                "--json","--workspace",str(self.workspace),*args,check=False)

    def assert_refusal_preserves_work(self,trees,branch,expected):
        (trees["spec"]/"pending.txt").write_text("spec work")
        (trees["code"]/"pending.txt").write_text("code work")
        heads={role:self.git(tree,"rev-parse","HEAD") for role,tree in trees.items()}
        statuses={role:self.git(tree,"status","--porcelain") for role,tree in trees.items()}
        remotes={role:self.git(origin,"rev-parse","refs/heads/"+branch)
                 for role,origin in self.origins.items()}
        before=self.manifest.read_bytes()
        for mode in (("--dry-run",),()):
            result=self.park(*mode)
            self.assertEqual(result.returncode,2,result.stdout+result.stderr)
            self.assertIn(expected,result.stderr)
            for role,tree in trees.items():
                self.assertEqual(self.git(tree,"rev-parse","HEAD"),heads[role])
                self.assertEqual(self.git(tree,"status","--porcelain"),statuses[role])
                self.assertEqual((tree/"pending.txt").read_text(),role+" work")
                self.assertEqual(self.git(self.origins[role],"rev-parse","refs/heads/"+branch),remotes[role])
            self.assertEqual(self.manifest.read_bytes(),before)

    def test_wrong_code_branch_refuses_before_either_commit(self):
        branch="001-one"
        trees=self.feature(branch)
        result=self.park()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.git(trees["code"],"switch","-q","-c","099-other")
        self.assert_refusal_preserves_work(trees,branch,"checked-out branch")

    def test_foreign_code_repository_refuses_before_either_commit(self):
        branch="001-one"
        trees=self.feature(branch)
        result=self.park()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.git(self.root/"code","worktree","move",str(trees["code"]),str(self.base/"saved-code"))
        foreign=self.init(trees["code"])
        self.git(foreign,"switch","-q","-c",branch)
        self.git(foreign,"remote","add","origin",str(self.origins["code"]))
        self.assert_refusal_preserves_work(trees,branch,"expected code repository")

    def test_matching_legs_record_the_actual_pushed_heads(self):
        branch="001-one"
        trees=self.feature(branch)
        for tree in trees.values():
            (tree/"pending.txt").write_text("work")
        result=self.park()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        body=self.manifest.read_text()
        for role,tree in trees.items():
            head=self.git(tree,"rev-parse","HEAD")
            self.assertEqual(self.git(self.origins[role],"rev-parse","refs/heads/"+branch),head)
            self.assertIn("parked_commit: "+head,body)


if __name__=="__main__":
    unittest.main()

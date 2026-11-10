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
        for name in ("park.sh","resume.sh","git-common.sh","workspace-common.sh"):
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



    def feature_record(self,body,branch):
        start=body.index("      - branch: "+branch+"\n")
        end=body.find("\n      - branch:",start)
        return body[start:] if end<0 else body[start:end+1]

    def test_subset_preserves_unselected_open_feature(self):
        one=self.feature("001-one")
        two=self.feature("002-two")
        first=self.park()
        self.assertEqual(first.returncode,0,first.stdout+first.stderr)
        before=self.feature_record(self.manifest.read_text(),"002-two")
        head=self.git(two["code"],"rev-parse","HEAD")
        (one["code"]/"selected.txt").write_text("selected work")
        (two["code"]/"unselected.txt").write_text("unselected work")
        result=self.park("--feature","001-one","--feature","001-one")
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(self.feature_record(self.manifest.read_text(),"002-two"),before)
        self.assertEqual(self.git(two["code"],"rev-parse","HEAD"),head)
        self.assertEqual(self.git(self.origins["code"],"rev-parse","refs/heads/002-two"),head)
        self.assertIn("?? unselected.txt",self.git(two["code"],"status","--porcelain"))
        self.assertEqual(self.git(one["code"],"rev-parse","HEAD"),
                         self.git(self.origins["code"],"rev-parse","refs/heads/001-one"))

    def test_subset_retains_gone_record_but_full_park_reconciles_it(self):
        self.feature("001-one")
        two=self.feature("002-two")
        first=self.park()
        self.assertEqual(first.returncode,0,first.stdout+first.stderr)
        before=self.feature_record(self.manifest.read_text(),"002-two")
        for role,tree in two.items():
            self.git(self.root/role,"worktree","remove",str(tree))
        (self.root/"worktrees/002-two").rmdir()
        subset=self.park("--feature","001-one")
        self.assertEqual(subset.returncode,0,subset.stdout+subset.stderr)
        self.assertEqual(self.feature_record(self.manifest.read_text(),"002-two"),before)
        full=self.park()
        self.assertEqual(full.returncode,0,full.stdout+full.stderr)
        self.assertNotIn("      - branch: 002-two",self.manifest.read_text())

    def test_partial_writer_replay_keeps_refreshed_unselected_values(self):
        one=self.feature("001-one")
        two=self.feature("002-two")
        first=self.park()
        self.assertEqual(first.returncode,0,first.stdout+first.stderr)
        old=self.feature_record(self.manifest.read_text(),"002-two")
        old_head=self.git(two["code"],"rev-parse","HEAD")
        self.git(two["code"],"commit","--allow-empty","-qm","peer update")
        new_head=self.git(two["code"],"rev-parse","HEAD")
        refreshed=old.replace(old_head,new_head)
        refreshed+="        fixture_note: preserve-newer-unselected\n"
        current=self.manifest.read_text().replace(old,refreshed)
        self.manifest.write_text(current)
        record=self.base/"partial-record.txt"
        lines=["project_id\tfixture-project","_shape\tthree-leg","_root\t.",
               "_tracking_branch\tmain","_worktree_root\tworktrees",
               "_selected_branches\t"+json.dumps(["001-one"]),
               "[feature]","branch\t001-one",
               "_feature_directory\tworktrees/001-one/spec/specs/001-one"]
        for role,tree in one.items():
            lines+=["[leg]","role\t"+role,"_remote\torigin",
                    "parked_commit\t"+self.git(tree,"rev-parse","HEAD"),
                    "wip\tfalse","wip_depth\t0","pushed\ttrue"]
        record.write_text("\n".join(lines)+"\n")
        scripts=self.root/".specify"/SCRIPTS
        command='source "$1/git-common.sh"; source "$1/workspace-common.sh"; workspace_write_manifest "$2" "$3"'
        self.run_command(self.root,"bash","-c",command,"fixture",str(scripts),str(self.manifest),str(record))
        self.assertEqual(self.feature_record(self.manifest.read_text(),"002-two"),refreshed)



    def test_subset_push_retry_keeps_peer_update(self):
        one=self.feature("001-one")
        two=self.feature("002-two")
        first=self.park()
        self.assertEqual(first.returncode,0,first.stdout+first.stderr)
        before=self.manifest.read_text()
        old=self.feature_record(before,"002-two")
        old_head=self.git(two["code"],"rev-parse","HEAD")
        self.git(two["code"],"commit","--allow-empty","-qm","peer feature update")
        new_head=self.git(two["code"],"rev-parse","HEAD")
        self.git(two["code"],"push","-q","origin","002-two")
        refreshed=old.replace(old_head,new_head)
        peer=self.base/"peer-workspace"
        self.git(self.base,"clone","-q","-b","main",str(self.workspace_origin),str(peer))
        self.identity(peer)
        peer_manifest=peer/"workspaces/dummy/fixture-project.yaml"
        peer_manifest.write_text(before.replace(old,refreshed))
        self.git(peer,"add",str(peer_manifest.relative_to(peer)))
        self.git(peer,"commit","-qm","peer unselected record update")
        peer_head=self.git(peer,"rev-parse","HEAD")
        shim=self.base/"shim"
        shim.mkdir()
        real_git=shutil.which("git",path=self.env.get("PATH"))
        (shim/"git").write_text(
            '#!/bin/sh\n'
            'if [ "$1" = -C ] && [ "$2" = "$HANDOFF_WORKSPACE" ] && '
            '[ "$3" = push ] && [ ! -f "$HANDOFF_RACED" ]; then\n'
            '  "$HANDOFF_REAL_GIT" -C "$HANDOFF_PEER" push -q origin main || exit 1\n'
            '  : > "$HANDOFF_RACED"\n'
            'fi\nexec "$HANDOFF_REAL_GIT" "$@"\n')
        (shim/"git").chmod(0o755)
        raced=self.base/"race-triggered"
        self.env.update(PATH=str(shim)+os.pathsep+self.env.get("PATH",os.defpath),
                        HANDOFF_REAL_GIT=real_git,HANDOFF_WORKSPACE=str(self.workspace),
                        HANDOFF_PEER=str(peer),HANDOFF_RACED=str(raced))
        (one["code"]/"selected.txt").write_text("selected work")
        result=self.park("--feature","001-one")
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertTrue(raced.is_file())
        self.assertEqual(self.feature_record(self.manifest.read_text(),"002-two"),refreshed)
        self.git(self.workspace,"merge-base","--is-ancestor",peer_head,"HEAD")
        remote=self.git(self.workspace_origin,"show","refs/heads/main:workspaces/dummy/fixture-project.yaml")
        self.assertIn(new_head,remote)
        self.assertIn(self.git(one["code"],"rev-parse","HEAD"),remote)



    def test_pending_manifest_publication_retries_unchanged_content(self):
        self.feature("001-one")
        remote_before=self.git(self.workspace_origin,"rev-parse","refs/heads/main")
        self.git(self.workspace,"remote","set-url","origin",str(self.base/"missing-workspace.git"))
        first=self.park()
        self.assertEqual(first.returncode,3,first.stdout+first.stderr)
        pending=self.git(self.workspace,"rev-parse","HEAD")
        manifest=self.manifest.read_bytes()
        self.assertNotEqual(pending,remote_before)
        again=self.park()
        self.assertEqual(again.returncode,3,again.stdout+again.stderr)
        self.assertEqual(self.git(self.workspace,"rev-parse","HEAD"),pending)
        self.assertEqual(self.manifest.read_bytes(),manifest)
        self.assertEqual(self.git(self.workspace_origin,"rev-parse","refs/heads/main"),remote_before)
        self.git(self.workspace,"remote","set-url","origin",str(self.workspace_origin))
        restored=self.park()
        self.assertEqual(restored.returncode,0,restored.stdout+restored.stderr)
        self.assertEqual(self.git(self.workspace,"rev-parse","HEAD"),pending)
        self.assertEqual(self.git(self.workspace_origin,"rev-parse","refs/heads/main"),pending)
        self.assertEqual(self.git(self.workspace_origin,"show","main:workspaces/dummy/fixture-project.yaml"),
                         manifest.decode().strip())

    def test_pending_manifest_publication_refuses_exhausted_retries(self):
        self.feature("001-one")
        remote_before=self.git(self.workspace_origin,"rev-parse","refs/heads/main")
        hook=self.workspace_origin/"hooks/pre-receive"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        result=self.park()
        self.assertEqual(result.returncode,3,result.stdout+result.stderr)
        self.assertNotEqual(self.git(self.workspace,"rev-parse","HEAD"),remote_before)
        self.assertEqual(self.git(self.workspace_origin,"rev-parse","refs/heads/main"),remote_before)
        self.assertIn("branch: 001-one",self.manifest.read_text())

    def existing_manifest_temporary_is_preserved(self,kind):
        trees=self.feature("001-one")
        first=self.park()
        self.assertEqual(first.returncode,0,first.stdout+first.stderr)
        before=self.manifest.read_bytes()
        temporary=self.manifest.with_name("."+self.manifest.name+".tmp")
        outside=self.base/"unrelated.txt"
        outside.write_text("unrelated work\n")
        if kind=="symlink":
            temporary.symlink_to(outside)
        else:
            temporary.write_text("existing temporary\n")
        previous=temporary.read_bytes()
        (trees["code"]/"new-work.txt").write_text("new feature work")
        result=self.park()
        self.assertEqual(result.returncode,3,result.stdout+result.stderr)
        self.assertEqual(outside.read_text(),"unrelated work\n")
        self.assertEqual(temporary.read_bytes(),previous)
        self.assertEqual(temporary.is_symlink(),kind=="symlink")
        self.assertFalse(self.manifest.is_symlink())
        self.assertEqual(self.manifest.read_bytes(),before)

    def test_manifest_temporary_symlink_does_not_overwrite_unrelated_file(self):
        self.existing_manifest_temporary_is_preserved("symlink")

    def test_manifest_temporary_existing_file_is_not_truncated(self):
        self.existing_manifest_temporary_is_preserved("file")

    def manifest_directory_symlink_is_refused(self,level):
        trees=self.feature("001-one")
        first=self.park()
        self.assertEqual(first.returncode,0,first.stdout+first.stderr)
        directory=self.workspace/"workspaces" if level=="workspaces" else self.manifest.parent
        outside=self.base/"outside-manifest-directory"
        directory.rename(outside)
        directory.symlink_to(outside,target_is_directory=True)
        self.git(self.workspace,"add","-A")
        self.git(self.workspace,"commit","-qm","fixture existing directory symlink")
        self.git(self.workspace,"push","-q","origin","main")
        target=outside/"dummy"/self.manifest.name if level=="workspaces" else outside/self.manifest.name
        before=target.read_bytes()
        (trees["code"]/"new-work.txt").write_text("new feature work")
        result=self.park()
        self.assertEqual(result.returncode,3,result.stdout+result.stderr)
        self.assertEqual(target.read_bytes(),before)
        self.assertTrue(directory.is_symlink())

    def test_manifest_workspace_directory_symlink_preserves_outside_target(self):
        self.manifest_directory_symlink_is_refused("workspaces")

    def test_manifest_org_directory_symlink_preserves_outside_target(self):
        self.manifest_directory_symlink_is_refused("org")

    def test_resume_selector_symlink_preserves_unrelated_target(self):
        _,trees=self.parked_wip()
        heads={role:self.git(tree,"rev-parse","HEAD") for role,tree in trees.items()}
        outside=self.base/"outside-selector.txt"
        outside.write_text("unrelated selector target\n")
        selector=self.root/".specify/feature.json"
        selector.symlink_to(outside)
        result=self.resume()
        self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(outside.read_text(),"unrelated selector target\n")
        self.assertTrue(selector.is_symlink())
        for role,tree in trees.items():
            self.assertEqual(self.git(tree,"rev-parse","HEAD"),heads[role])

    def test_resume_selector_hardlink_preserves_unrelated_target(self):
        self.parked_wip()
        outside=self.base/"outside-selector.txt"
        outside.write_text("unrelated selector target\n")
        selector=self.root/".specify/feature.json"
        os.link(outside,selector)
        result=self.resume()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(outside.read_text(),"unrelated selector target\n")
        self.assertEqual(json.loads(selector.read_text())["feature_directory"],
                         "worktrees/001-one/spec/specs/001-one")
        self.assertNotEqual(selector.stat().st_ino,outside.stat().st_ino)

    def selector_publication_refuses_before_reset(self,kind):
        _,trees=self.parked_wip()
        heads={role:self.git(tree,"rev-parse","HEAD") for role,tree in trees.items()}
        statuses={role:self.git(tree,"status","--porcelain") for role,tree in trees.items()}
        if kind=="directory":
            directory=self.root/".specify"
            outside=self.base/"external-specify"
            directory.rename(outside)
            directory.symlink_to(outside,target_is_directory=True)
        else:
            (self.root/".specify/.feature.json.tmp").write_text("existing temporary\n")
        result=self.resume()
        self.assertEqual(result.returncode,2,result.stdout+result.stderr)
        for role,tree in trees.items():
            self.assertEqual(self.git(tree,"rev-parse","HEAD"),heads[role])
            self.assertEqual(self.git(tree,"status","--porcelain"),statuses[role])
            self.assertEqual((tree/"pending.txt").read_text(),role+" work")
        if kind=="directory":
            self.assertTrue((self.root/".specify").is_symlink())
            self.assertFalse((outside/"feature.json").exists())
        else:
            self.assertEqual((self.root/".specify/.feature.json.tmp").read_text(),
                             "existing temporary\n")

    def test_resume_selector_directory_symlink_refuses_before_reset(self):
        self.selector_publication_refuses_before_reset("directory")

    def test_resume_selector_occupied_temporary_refuses_before_reset(self):
        self.selector_publication_refuses_before_reset("temporary")

    def test_manifest_workspace_root_alias_remains_supported(self):
        self.feature("001-one")
        alias=self.base/"workspace-alias"
        alias.symlink_to(self.workspace,target_is_directory=True)
        self.use_receiver(alias)
        result=self.park()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn("branch: 001-one",self.manifest.read_text())

    def receiver_workspace(self):
        receiver=self.base/"receiver-workspace"
        self.git(self.base,"clone","-q","-b","main",str(self.workspace_origin),str(receiver))
        self.identity(receiver)
        return receiver

    def use_receiver(self,receiver):
        self.workspace=receiver
        self.manifest=receiver/"workspaces/dummy/fixture-project.yaml"

    def test_receiving_workspace_refreshes_before_reading_manifest(self):
        receiver=self.receiver_workspace()
        branch,trees=self.parked_wip()
        for role,tree in trees.items():
            self.git(self.root/role,"worktree","remove",str(tree))
        self.use_receiver(receiver)
        self.assertFalse(self.manifest.exists())
        result=self.resume()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(self.git(receiver,"rev-parse","HEAD"),
                         self.git(self.workspace_origin,"rev-parse","refs/heads/main"))
        for role,tree in trees.items():
            self.assertEqual((tree/"pending.txt").read_text(),role+" work")
        self.assertFalse((receiver/".workspaces.lock").exists())

    def test_receiving_workspace_preserves_dirty_content_on_refresh_refusal(self):
        receiver=self.receiver_workspace()
        _,trees=self.parked_wip()
        self.use_receiver(receiver)
        before=self.git(receiver,"rev-parse","HEAD")
        heads={role:self.git(tree,"rev-parse","HEAD") for role,tree in trees.items()}
        (receiver/"README.md").write_text("unfinished receiver work")
        result=self.resume()
        self.assertEqual(result.returncode,2,result.stdout+result.stderr)
        self.assertIn("workspace-dirty",result.stderr)
        self.assertEqual((receiver/"README.md").read_text(),"unfinished receiver work")
        self.assertEqual(self.git(receiver,"rev-parse","HEAD"),before)
        for role,tree in trees.items():
            self.assertEqual(self.git(tree,"rev-parse","HEAD"),heads[role])
        self.assertFalse((receiver/".workspaces.lock").exists())

    def test_receiving_workspace_aborts_conflicting_refresh(self):
        receiver=self.receiver_workspace()
        _,trees=self.parked_wip()
        self.use_receiver(receiver)
        self.manifest.parent.mkdir(parents=True)
        self.manifest.write_text("receiver conflicting record\n")
        self.git(receiver,"add","workspaces")
        self.git(receiver,"commit","-qm","receiver record")
        before=self.git(receiver,"rev-parse","HEAD")
        heads={role:self.git(tree,"rev-parse","HEAD") for role,tree in trees.items()}
        result=self.resume()
        self.assertEqual(result.returncode,2,result.stdout+result.stderr)
        self.assertIn("rebase was aborted",result.stderr)
        self.assertEqual(self.git(receiver,"rev-parse","HEAD"),before)
        self.assertEqual(self.manifest.read_text(),"receiver conflicting record\n")
        self.assertEqual(self.git(receiver,"status","--porcelain"),"")
        for role,tree in trees.items():
            self.assertEqual(self.git(tree,"rev-parse","HEAD"),heads[role])
        self.assertFalse((receiver/".git/rebase-merge").exists())
        self.assertFalse((receiver/".workspaces.lock").exists())

    def test_receiving_workspace_refuses_unavailable_origin(self):
        _,trees=self.parked_wip()
        before={role:self.git(tree,"rev-parse","HEAD") for role,tree in trees.items()}
        self.git(self.workspace,"remote","set-url","origin",str(self.base/"missing-workspace.git"))
        result=self.resume()
        self.assertEqual(result.returncode,2,result.stdout+result.stderr)
        self.assertIn("could not refresh",result.stderr)
        for role,tree in trees.items():
            self.assertEqual(self.git(tree,"rev-parse","HEAD"),before[role])
        self.assertFalse((self.workspace/".workspaces.lock").exists())

    def test_receiving_workspace_dry_run_leaves_stale_clone_unchanged(self):
        receiver=self.receiver_workspace()
        self.parked_wip()
        self.use_receiver(receiver)
        before=self.git(receiver,"rev-parse","HEAD")
        result=self.resume("--dry-run")
        self.assertEqual(result.returncode,2,result.stdout+result.stderr)
        self.assertEqual(self.git(receiver,"rev-parse","HEAD"),before)
        self.assertFalse(self.manifest.exists())
        self.assertFalse((receiver/".git/FETCH_HEAD").exists())
        self.assertFalse((receiver/".workspaces.lock").exists())

    def resume(self,*args):
        return self.run_command(self.root,"bash",str(Path(".specify")/SCRIPTS/"resume.sh"),
                                "--json","--workspace",str(self.workspace),*args,check=False)

    def parked_wip(self):
        branch="001-one"
        trees=self.feature(branch)
        for role,tree in trees.items():
            (tree/"pending.txt").write_text(role+" work")
        result=self.park()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return branch,trees

    def existing_resume_refuses_changed_origin(self,state):
        branch,trees=self.parked_wip()
        before={role:(self.git(tree,"rev-parse","HEAD"),self.git(tree,"status","--porcelain"))
                for role,tree in trees.items()}
        manifest=self.manifest.read_bytes()
        if state=="advanced":
            peer=self.base/"peer-code"
            self.git(self.base,"clone","-q","-b",branch,str(self.origins["code"]),str(peer))
            self.identity(peer)
            self.git(peer,"commit","--allow-empty","-qm","remote advanced")
            self.git(peer,"push","-q","origin",branch)
        elif state=="deleted":
            self.git(self.origins["code"],"update-ref","-d","refs/heads/"+branch)
        else:
            self.git(self.root/"code","remote","set-url","origin",str(self.base/"missing-origin.git"))
        result=self.resume()
        self.assertEqual(result.returncode,2,result.stdout+result.stderr)
        self.assertIn("has moved since it was parked" if state=="advanced" else "could not be verified",
                      result.stderr)
        for role,tree in trees.items():
            self.assertEqual((self.git(tree,"rev-parse","HEAD"),self.git(tree,"status","--porcelain")),before[role])
        self.assertEqual(self.manifest.read_bytes(),manifest)

    def test_existing_resume_refuses_advanced_origin_before_any_reset(self):
        self.existing_resume_refuses_changed_origin("advanced")

    def test_existing_resume_refuses_deleted_origin_before_any_reset(self):
        self.existing_resume_refuses_changed_origin("deleted")

    def test_existing_resume_refuses_unavailable_origin_before_any_reset(self):
        self.existing_resume_refuses_changed_origin("unavailable")

    def test_existing_resume_is_idempotent_against_unchanged_origin(self):
        _,trees=self.parked_wip()
        first=self.resume()
        self.assertEqual(first.returncode,0,first.stdout+first.stderr)
        before={role:(self.git(tree,"rev-parse","HEAD"),self.git(tree,"status","--porcelain"))
                for role,tree in trees.items()}
        second=self.resume()
        self.assertEqual(second.returncode,0,second.stdout+second.stderr)
        for role,tree in trees.items():
            self.assertEqual((self.git(tree,"rev-parse","HEAD"),self.git(tree,"status","--porcelain")),before[role])
            self.assertEqual((tree/"pending.txt").read_text(),role+" work")


if __name__=="__main__":
    unittest.main()

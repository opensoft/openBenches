#!/usr/bin/env python3
"""Account rotation fixtures; no real credentials, desktop, or databases."""

from copy import deepcopy
import importlib.util
import base64
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("project_state", ROOT / "scripts/codex-project-state.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
A = module.owner_id("alice", "company")
B = module.owner_id("bob", "company")
OTHER = module.owner_id("personal", "personal")


def project(key="p", name="Example"):
    return {"id": key, "name": name, "rootPaths": ["example"], "createdAt": 1, "updatedAt": 2}


def fixture():
    donor = {"local-projects": {"p": project()}, "thread-project-assignments": {"t": {"projectKind": "local", "projectId": "p"}}, "project-order": ["p"], "projectless-thread-ids": ["unassigned"]}
    return {
        module.SCOPE: {"owner": B, "inactive": {
            A: {"atoms": {"local-document-identity": {"userId": "alice", "accountId": "company"}, "model": "keep-a"}, "globals": donor},
            OTHER: {"atoms": {}, "globals": {"local-projects": {"private": project("private")}}},
        }},
        module.ATOMS: {"model": "keep-b"}, "unrelated": {"retain": True},
        "local-projects": {}, "projectless-thread-ids": ["current-chat"],
    }


class ProjectStateTests(unittest.TestCase):
    def seed(self):
        return module.synchronize(fixture(), {}, "windows", "native-home", B, [A], A)

    def test_restore_retains_ids_memberships_and_unrelated_accounts(self):
        original = fixture()
        result, catalog = self.seed()
        self.assertEqual(original, fixture())
        self.assertEqual(result["local-projects"]["p"]["id"], "p")
        self.assertEqual(result["thread-project-assignments"]["t"]["projectId"], "p")
        self.assertEqual(result[module.ATOMS]["model"], original[module.ATOMS]["model"])
        self.assertEqual(result[module.ATOMS]["flat-project-sidebar-preferences-v1"]["mode"], "project")
        self.assertEqual(result[module.SCOPE]["inactive"][OTHER], original[module.SCOPE]["inactive"][OTHER])
        self.assertIn("current-chat", result["projectless-thread-ids"])
        self.assertNotIn("model", module.encode(catalog))

    def test_noop_is_idempotent(self):
        state, catalog = self.seed()
        self.assertEqual((state, catalog), module.synchronize(state, catalog, "windows", "native-home", B))

    def test_rename_addition_and_grouping_propagate(self):
        state, catalog = self.seed()
        state["local-projects"]["p"]["name"] = "Renamed"
        state["local-projects"]["new"] = project("new")
        state["thread-project-assignments"]["t"]["projectId"] = "new"
        state, _ = module.synchronize(state, catalog, "windows", "native-home", B)
        donor = state[module.SCOPE]["inactive"][A]["globals"]
        self.assertEqual(donor["local-projects"]["p"]["name"], "Renamed")
        self.assertEqual(donor["thread-project-assignments"]["t"]["projectId"], "new")

    def test_deletion_and_ungrouping_do_not_resurrect_stale_snapshot(self):
        state, catalog = self.seed()
        state["local-projects"].pop("p")
        state["thread-project-assignments"].pop("t")
        state["projectless-thread-ids"].append("t")
        state, catalog = module.synchronize(state, catalog, "windows", "native-home", B)
        self.assertEqual(catalog["shared"]["local-projects"], {})
        self.assertEqual(state[module.SCOPE]["inactive"][A]["globals"]["local-projects"], {})
        self.assertNotIn("t", state["thread-project-assignments"])
        self.assertIn("t", state["projectless-thread-ids"])

    def test_deleted_project_cleans_stale_order_and_membership(self):
        state, catalog = self.seed()
        state["local-projects"].pop("p")
        result, _ = module.synchronize(state, catalog, "windows", "native-home", B)
        self.assertNotIn("p", result["project-order"])
        self.assertNotIn("t", result["thread-project-assignments"])

    def test_explicit_projectless_state_wins_over_stale_assignment(self):
        state, catalog = self.seed()
        state["projectless-thread-ids"].append("t")
        result, catalog = module.synchronize(state, catalog, "windows", "native-home", B)
        self.assertNotIn("t", catalog["shared"]["thread-project-assignments"])
        self.assertNotIn("t", result["thread-project-assignments"])

    def test_unregistered_account_is_hydrated_without_clearing_catalog(self):
        state, catalog = self.seed()
        state[module.SCOPE]["owner"] = "c" * 64
        state["local-projects"] = {}
        state["thread-project-assignments"] = {}
        state, catalog = module.synchronize(state, catalog, "windows", "native-home", "c" * 64)
        self.assertIn("p", state["local-projects"])

    def test_explicit_profile_bindings_prepare_never_opened_accounts(self):
        identity = {"owner": module.owner_id("new-user", "company"), "userId": "new-user", "accountId": "company", "family": "opensoft", "email": "new@example.test"}
        state, catalog = module.synchronize(fixture(), {}, "windows", "native-home", B, [A], A, [identity])
        saved = state[module.SCOPE]["inactive"][identity["owner"]]
        self.assertEqual(saved["globals"]["local-projects"]["p"], project())
        self.assertEqual(saved["atoms"]["local-document-identity"]["userId"], "new-user")
        self.assertIn(identity["owner"], catalog["owners"])
        identity["family"] = "personal"
        with self.assertRaises(ValueError):
            module.synchronize(fixture(), {}, "windows", "native-home", B, [A], A, [identity])

    def test_cloud_ownership_and_preferences_are_not_copied(self):
        state = fixture()
        donor = state[module.SCOPE]["inactive"][A]["globals"]
        donor["local-projects"]["p"]["chatGptBacking"] = {"accountId": "alice-cloud"}
        donor["local-projects"]["g-p-cloud"] = {"id": "g-p-cloud", "name": "Cloud"}
        state["local-projects"]["p"] = {**project(), "chatGptBacking": {"accountId": "bob-cloud"}}
        result, catalog = module.synchronize(state, {}, "windows", "native-home", B, [A], A)
        self.assertEqual(result["local-projects"]["p"]["chatGptBacking"]["accountId"], "bob-cloud")
        self.assertNotIn("g-p-cloud", result["local-projects"])
        self.assertNotIn("chatGptBacking", module.encode(catalog))

    def test_runtime_and_home_mismatch_are_refused(self):
        state, catalog = self.seed()
        for runtime, home in (("beta-wsl", "native-home"), ("windows", "other-home")):
            with self.assertRaisesRegex(ValueError, "mismatch"):
                module.synchronize(state, catalog, runtime, home, B)

    def test_unknown_or_mismatched_seed_is_refused(self):
        with self.assertRaises(ValueError):
            module.synchronize(fixture(), {}, "windows", "native-home", B, [], A)
        state = fixture()
        state[module.SCOPE]["inactive"][A]["atoms"]["local-document-identity"]["userId"] = "wrong"
        with self.assertRaises(ValueError):
            module.synchronize(state, {}, "windows", "native-home", B, [A], A)

    def test_account_rotation_retains_changes(self):
        state, catalog = self.seed()
        saved_a = state[module.SCOPE]["inactive"].pop(A)
        saved_b = {"atoms": {"local-document-identity": {"userId": "bob", "accountId": "company"}}, "globals": {k: v for k, v in state.items() if k not in (module.SCOPE, module.ATOMS)}}
        rotated = {**saved_a["globals"], module.ATOMS: saved_a["atoms"], module.SCOPE: {"owner": A, "inactive": {B: saved_b}}}
        rotated["local-projects"]["p"]["name"] = "From Alice"
        result, _ = module.synchronize(rotated, catalog, "windows", "native-home", A)
        self.assertEqual(result[module.SCOPE]["inactive"][B]["globals"]["local-projects"]["p"]["name"], "From Alice")

    def test_edits_before_in_app_rotation_are_captured_from_inactive_account(self):
        state, catalog = self.seed()
        inactive = state[module.SCOPE]["inactive"][A]["globals"]
        inactive["local-projects"]["new"] = project("new", "Added before switching")
        inactive["thread-project-assignments"]["t"]["projectId"] = "new"
        result, catalog = module.synchronize(state, catalog, "windows", "native-home", B)
        self.assertEqual(result["local-projects"]["new"]["name"], "Added before switching")
        self.assertEqual(result["thread-project-assignments"]["t"]["projectId"], "new")

    def test_stale_snapshot_does_not_restore_another_accounts_deletion(self):
        state, catalog = self.seed()
        state["local-projects"].pop("p")
        inactive = state[module.SCOPE]["inactive"][A]["globals"]
        inactive["local-projects"]["new"] = project("new")
        result, _ = module.synchronize(state, catalog, "windows", "native-home", B)
        self.assertNotIn("p", result["local-projects"])
        self.assertIn("new", result["local-projects"])

    def test_destination_cloud_chat_membership_is_preserved(self):
        state = fixture()
        cloud = {"projectKind": "local", "projectId": "g-p-cloud", "projectOrigin": "chatgpt"}
        state["thread-project-assignments"] = {"t": cloud}
        result, catalog = module.synchronize(state, {}, "windows", "native-home", B, [A], A)
        self.assertEqual(result["thread-project-assignments"]["t"], cloud)
        result, catalog = module.synchronize(result, catalog, "windows", "native-home", B)
        self.assertIn("t", catalog["shared"]["thread-project-assignments"])

    def test_offline_restore_backups_and_live_process_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            state = home / ".codex-global-state.json"
            original = json.dumps(fixture()).encode()
            state.write_bytes(original)
            catalog = home / "catalog.json"
            with patch.object(module, "validate_runtime"):
                with self.assertRaisesRegex(ValueError, "running"):
                    module.prepare(home, catalog, "windows", B, [A], A, True, lambda _: True)
                self.assertEqual(state.read_bytes(), original)
                self.assertFalse(catalog.exists())
                report = module.prepare(home, catalog, "windows", B, [A], A, True, lambda _: False)
                self.assertTrue(report["applied"])
                self.assertEqual((Path(report["backup"]) / state.name).read_bytes(), original)
                self.assertFalse(module.prepare(home, catalog, "windows", B, apply=True, running=lambda _: False)["changed"])

    def test_changed_state_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = home / ".codex-global-state.json"
            path.write_text(json.dumps(fixture()))
            def concurrent(_):
                path.write_text('{"external":"change"}')
                return False
            with patch.object(module, "validate_runtime"), self.assertRaisesRegex(ValueError, "changed"):
                module.prepare(home, home / "catalog.json", "windows", B, [A], A, True, concurrent)
            self.assertEqual(json.loads(path.read_text()), {"external": "change"})

    def test_native_windows_and_linux_home_guards(self):
        with patch.object(module.os, "name", "nt"):
            with self.assertRaises(ValueError):
                module.validate_runtime("windows", "\\\\wsl.localhost\\distro\\home")
            with self.assertRaises(ValueError):
                module.validate_runtime("beta-wsl", "/home/example/.codex")
        with patch.object(module.os, "name", "posix"):
            with self.assertRaises(ValueError):
                module.validate_runtime("windows", "/home/example/.codex")
            with self.assertRaises(ValueError):
                module.validate_runtime("beta-wsl", "/mnt/c/Users/example/.codex")

    def test_process_guard_uses_only_selected_package(self):
        for runtime, package in (("windows", "OpenAI.Codex_"), ("beta-wsl", "OpenAI.CodexBeta_")):
            with patch.object(module.Path, "is_file", return_value=True), patch.object(module.subprocess, "run", return_value=SimpleNamespace(stdout="1")) as run:
                self.assertTrue(module.desktop_running(runtime))
                command = run.call_args.args[0][-1]
                self.assertIn(package, command)
                self.assertNotIn("wsl --shutdown", command)

    def test_active_identity_requires_matching_company_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            claims = {"email": "work@example.test", "https://api.openai.com/auth": {"chatgpt_user_id": "alice", "chatgpt_account_id": "company"}}
            body = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
            (home / "auth.json").write_text(json.dumps({"tokens": {"id_token": f"fixture.{body}.fixture"}}))
            root = home / "profiles"
            root.mkdir()
            metadata = root / ".profile.json"
            metadata.write_text(json.dumps({"family": "personal", "email": "work@example.test"}))
            with self.assertRaises(ValueError):
                module.authenticated_owner(home, root)
            metadata.write_text(json.dumps({"family": "opensoft", "email": "work@example.test"}))
            self.assertEqual(module.authenticated_owner(home, root), A)


if __name__ == "__main__":
    unittest.main()

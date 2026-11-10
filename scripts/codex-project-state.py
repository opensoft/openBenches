#!/usr/bin/env python3
"""Prepare shared Opensoft local projects while the selected desktop is stopped."""

from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

SCOPE = "electron-account-renderer-state-v1"
ATOMS = "electron-persisted-atom-state"
PROJECT_FIELDS = ("id", "name", "rootPaths", "createdAt", "updatedAt")
PROJECT_MAPS = ("project-appearances", "sidebar-project-thread-orders")
HOST_MAPS = (
    "app-server-project-id-by-legacy-project-id-by-host",
    "app-server-projects-migration-by-host",
)
OWNER = re.compile(r"^[0-9a-f]{64}$")


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def owner_id(user_id, account_id):
    raw = json.dumps([user_id, account_id], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def read_json(path):
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def native_projects(globals_):
    result = {}
    for key, project in globals_.get("local-projects", {}).items():
        if key.startswith("g-p-"):
            continue
        if not isinstance(project, dict) or project.get("id") != key:
            raise ValueError("unsupported local project record")
        if not isinstance(project.get("name"), str) or not isinstance(project.get("rootPaths"), list):
            raise ValueError("unsupported local project fields")
        result[key] = {k: deepcopy(project[k]) for k in PROJECT_FIELDS if k in project}
    return result


def project_state(globals_, host_key):
    projects = native_projects(globals_)
    projectless = set(globals_.get("projectless-thread-ids", []))
    assignments = {
        thread: {"projectKind": "local", "projectId": item["projectId"]}
        for thread, item in globals_.get("thread-project-assignments", {}).items()
        if item.get("projectKind") == "local" and item.get("projectId") in projects
        and item.get("projectOrigin") != "chatgpt" and thread not in projectless
    }
    result = {
        "local-projects": projects,
        "thread-project-assignments": assignments,
        "projectless-thread-ids": sorted(projectless),
        "project-order": [p for p in globals_.get("project-order", []) if p in projects],
    }
    for key in PROJECT_MAPS:
        result[key] = {p: deepcopy(v) for p, v in globals_.get(key, {}).items() if p in projects}
    for key in HOST_MAPS:
        value = globals_.get(key, {}).get(host_key)
        result[key] = {} if value is None else {host_key: deepcopy(value)}
    mappings = result[HOST_MAPS[0]].get(host_key, {})
    result[HOST_MAPS[0]] = {host_key: {p: v for p, v in mappings.items() if p in projects}}
    return result


def merge_initial(base, incoming):
    """Adopt a previously unsynchronized account without interpreting omissions as deletions."""
    merged = deepcopy(base)
    for key in ("local-projects", "thread-project-assignments", *PROJECT_MAPS):
        merged[key].update(incoming[key])
    merged["projectless-thread-ids"] = sorted((set(base["projectless-thread-ids"]) | set(incoming["projectless-thread-ids"])) - set(incoming["thread-project-assignments"]))
    merged["project-order"] = list(dict.fromkeys(base["project-order"] + incoming["project-order"]))
    for key in HOST_MAPS:
        for host, value in incoming[key].items():
            merged[key].setdefault(host, {}).update(value)
    for thread in merged["projectless-thread-ids"]:
        merged["thread-project-assignments"].pop(thread, None)
    return merged


def normalize(shared):
    projects = shared["local-projects"]
    unassigned = set(shared["projectless-thread-ids"])
    shared["thread-project-assignments"] = {
        t: value for t, value in shared["thread-project-assignments"].items()
        if value["projectId"] in projects and t not in unassigned
    }
    shared["project-order"] = list(dict.fromkeys([p for p in shared["project-order"] if p in projects] + list(projects)))
    shared["projectless-thread-ids"] = sorted(unassigned)
    for key in PROJECT_MAPS:
        shared[key] = {p: value for p, value in shared[key].items() if p in projects}
    for host, mapping in shared[HOST_MAPS[0]].items():
        shared[HOST_MAPS[0]][host] = {p: value for p, value in mapping.items() if p in projects}
    return shared


def merge_changes(shared, before, after):
    """Apply only actual edits since this account's last preparation."""
    shared = deepcopy(shared)
    reassigned = set()
    for key in ("local-projects", "thread-project-assignments", *PROJECT_MAPS, HOST_MAPS[1]):
        for item in before[key].keys() - after[key].keys():
            shared[key].pop(item, None)
        for item, value in after[key].items():
            if item not in before[key] or before[key][item] != value:
                shared[key][item] = deepcopy(value)
                if key == "thread-project-assignments":
                    reassigned.add(item)
    for host in before[HOST_MAPS[0]].keys() | after[HOST_MAPS[0]].keys():
        previous = before[HOST_MAPS[0]].get(host, {})
        current = after[HOST_MAPS[0]].get(host, {})
        merged = shared[HOST_MAPS[0]].setdefault(host, {})
        for project in previous.keys() - current.keys():
            merged.pop(project, None)
        for project, value in current.items():
            if project not in previous or previous[project] != value:
                merged[project] = value
    unassigned = set(shared["projectless-thread-ids"])
    unassigned -= set(before["projectless-thread-ids"]) - set(after["projectless-thread-ids"])
    unassigned |= set(after["projectless-thread-ids"]) - set(before["projectless-thread-ids"])
    unassigned -= reassigned
    shared["projectless-thread-ids"] = sorted(unassigned)
    if before["project-order"] != after["project-order"]:
        shared["project-order"] = after["project-order"]
    return normalize(shared)


def apply_project_state(globals_, shared, known_project_ids=()):
    previous = native_projects(globals_)
    local = globals_.setdefault("local-projects", {})
    # Retain only each destination's cloud ownership fields, never a donor's.
    owned = {p: {k: v for k, v in local[p].items() if k not in PROJECT_FIELDS} for p in previous}
    for project in previous:
        local.pop(project)
    for project, value in shared["local-projects"].items():
        local[project] = {**deepcopy(owned.get(project, {})), **deepcopy(value)}
    native_ids = set(previous) | set(shared["local-projects"]) | set(known_project_ids)
    assignments = globals_.setdefault("thread-project-assignments", {})
    for thread, value in list(assignments.items()):
        if value.get("projectKind") == "local" and value.get("projectId") in native_ids and value.get("projectOrigin") != "chatgpt":
            del assignments[thread]
    assignments.update({thread: deepcopy(value) for thread, value in shared["thread-project-assignments"].items() if assignments.get(thread, {}).get("projectOrigin") != "chatgpt"})
    globals_["projectless-thread-ids"] = [thread for thread in shared["projectless-thread-ids"] if assignments.get(thread, {}).get("projectOrigin") != "chatgpt"]
    for thread in globals_["projectless-thread-ids"]:
        if assignments.get(thread, {}).get("projectOrigin") != "chatgpt":
            assignments.pop(thread, None)
    order = [p for p in globals_.get("project-order", []) if p not in native_ids]
    globals_["project-order"] = shared["project-order"] + [p for p in shared["local-projects"] if p not in shared["project-order"]] + order
    for key in PROJECT_MAPS:
        globals_[key] = {**{p: v for p, v in globals_.get(key, {}).items() if p not in native_ids}, **deepcopy(shared[key])}
    for key in HOST_MAPS:
        globals_.setdefault(key, {}).update(deepcopy(shared[key]))
    hosts = globals_.setdefault("thread-project-membership-host-ids", {})
    for thread in shared["thread-project-assignments"]:
        hosts[thread] = "local"


def synchronize(state, catalog, runtime, home, active_owner, enrolled=(), seed_owner=None, identities=()):
    """Pure transformation; all input objects remain untouched."""
    state, catalog = deepcopy(state), deepcopy(catalog)
    home = str(home)
    host_key = f"local:{home}"
    if catalog and (catalog.get("version") != 1 or catalog.get("runtime") != runtime or catalog.get("codexHome") != home or catalog.get("family") != "opensoft"):
        raise ValueError("catalog runtime, home, family, or version mismatch")
    scope = state.get(SCOPE)
    if not isinstance(scope, dict) or scope.get("owner") != active_owner or not isinstance(scope.get("inactive"), dict):
        raise ValueError("desktop account scope does not match the authenticated account")
    bindings = {item["owner"]: item for item in catalog.get("identities", [])}
    for item in identities:
        if item.get("family") != "opensoft" or owner_id(item.get("userId"), item.get("accountId")) != item.get("owner"):
            raise ValueError("invalid Opensoft identity enrollment")
        bindings[item["owner"]] = {key: deepcopy(item[key]) for key in ("owner", "userId", "accountId", "family", "email") if key in item}
    owners = set(catalog.get("owners", [])) | set(enrolled) | set(bindings) | {active_owner}
    if any(not OWNER.fullmatch(owner) for owner in owners):
        raise ValueError("invalid account owner binding")
    for owner, identity in bindings.items():
        if owner != active_owner and owner not in scope["inactive"]:
            scope["inactive"][owner] = {
                "atoms": {"local-document-identity": {
                    "userId": identity["userId"], "accountId": identity["accountId"],
                    "accountUserId": f"{identity['userId']}__{identity['accountId']}",
                    "requestUserId": identity["userId"],
                }},
                "globals": {},
            }
    snapshots = {active_owner: state}
    for owner, snapshot in scope["inactive"].items():
        identity = snapshot.get("atoms", {}).get("local-document-identity", {})
        if owner in owners:
            if owner_id(identity.get("userId"), identity.get("accountId")) != owner:
                raise ValueError("inactive account identity does not match its owner binding")
            snapshots[owner] = snapshot["globals"]
    if seed_owner:
        if catalog:
            raise ValueError("a catalog already exists; seeding again is refused")
        if seed_owner not in owners or seed_owner not in snapshots:
            raise ValueError("seed account must be explicitly enrolled and present")
        if not project_state(snapshots[seed_owner], host_key)["local-projects"]:
            raise ValueError("refusing an empty seed project set")
    if catalog:
        shared = catalog["shared"]
        # In-app rotation can leave real edits in an inactive account. Compare
        # every prepared snapshot to its own baseline; unchanged stale copies
        # contribute nothing. The active account wins simultaneous conflicts.
        for owner in sorted(snapshots, key=lambda value: (value == active_owner, value)):
            current = project_state(snapshots[owner], host_key)
            baseline = catalog.get("baselines", {}).get(owner)
            if baseline is None:
                shared = merge_initial(shared, current)
            elif digest(current) != baseline["digest"]:
                shared = merge_changes(shared, baseline["state"], current)
    else:
        shared = project_state({}, host_key)
        # Import every enrolled account before replacing any snapshot. The
        # selected seed and active account take precedence on initial conflicts.
        order = sorted(snapshots, key=lambda value: (value == active_owner, value == seed_owner, value))
        for owner in order:
            shared = merge_initial(shared, project_state(snapshots[owner], host_key))
    shared = normalize(shared)
    baselines = dict(catalog.get("baselines", {}))
    known_project_ids = set(catalog.get("shared", {}).get("local-projects", {}))
    for owner, globals_ in snapshots.items():
        apply_project_state(globals_, shared, known_project_ids)
        projected = project_state(globals_, host_key)
        baselines[owner] = {"digest": digest(projected), "state": projected}
        atoms = state.setdefault(ATOMS, {}) if owner == active_owner else scope["inactive"][owner].setdefault("atoms", {})
        preferences = atoms.setdefault("flat-project-sidebar-preferences-v1", {})
        preferences.update(mode="project", initialized=True)
    catalog = {
        "version": 1, "runtime": runtime, "codexHome": home, "family": "opensoft",
        "owners": sorted(owners), "shared": shared, "baselines": baselines,
        "identities": [bindings[owner] for owner in sorted(bindings)],
    }
    return state, catalog


def authenticated_owner(home, profile_root):
    auth = read_json(home / "auth.json")
    token = auth.get("tokens", {}).get("id_token", "")
    claims = json.loads(base64.urlsafe_b64decode(token.split(".")[1] + "=="))
    email = claims.get("email", "").casefold()
    profiles = [read_json(p) for p in profile_root.rglob(".profile.json")]
    if not any(p.get("family") == "opensoft" and p.get("email", "").casefold() == email for p in profiles):
        raise ValueError("active login is not an enrolled Opensoft profile")
    identity = claims["https://api.openai.com/auth"]
    return owner_id(identity.get("chatgpt_user_id") or identity["user_id"], identity["chatgpt_account_id"])


def validate_runtime(runtime, home):
    if runtime == "windows":
        if os.name != "nt" or str(home).startswith("\\\\"):
            raise ValueError("Windows projects require a native local Windows home")
    elif os.name == "nt" or str(home).startswith(("/mnt/", "/media/")):
        raise ValueError("Beta/WSL projects require a separate Linux home")


def desktop_running(runtime):
    package = "OpenAI.Codex_" if runtime == "windows" else "OpenAI.CodexBeta_"
    windows_root = Path(os.environ.get("SystemRoot", "C:/Windows")) if os.name == "nt" else Path("/mnt/c/Windows")
    powershell = windows_root / "System32/WindowsPowerShell/v1.0/powershell.exe"
    if powershell.is_file():
        command = "$ErrorActionPreference='Stop'; @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -like '*WindowsApps\\" + package + "*' }).Count"
        result = subprocess.run([str(powershell), "-NoProfile", "-Command", command], capture_output=True, text=True, check=True)
        return int(result.stdout.strip()) > 0
    if runtime == "windows" or os.environ.get("WSL_DISTRO_NAME"):
        raise ValueError("cannot inspect the selected Windows desktop package")
    result = subprocess.run(["pgrep", "-f", "[Cc]odex[Bb]eta|[Cc]hatGPT [Bb]eta"], capture_output=True)
    if result.returncode not in (0, 1):
        raise ValueError("cannot inspect the Beta desktop process")
    return result.returncode == 0


@contextmanager
def locked(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        path.unlink()


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def prepare(home, catalog_path, runtime, owner, enrolled=(), seed_owner=None, apply=False, running=desktop_running, identities=()):
    validate_runtime(runtime, home)
    state_path = home / ".codex-global-state.json"
    original = state_path.read_bytes()
    state = json.loads(original.decode("utf-8-sig"))
    catalog_bytes = catalog_path.read_bytes() if catalog_path.exists() else None
    catalog = json.loads(catalog_bytes) if catalog_bytes else {}
    updated, catalog = synchronize(state, catalog, runtime, home, owner, enrolled, seed_owner, identities)
    changes = updated != state or catalog_bytes is None or json.loads(catalog_bytes) != catalog
    report = {"runtime": runtime, "projects": len(catalog["shared"]["local-projects"]), "assignments": len(catalog["shared"]["thread-project-assignments"]), "enrolledAccounts": len(catalog["owners"]), "changed": changes, "applied": False}
    if not apply or not changes:
        return report
    with locked(catalog_path.with_suffix(".lock")):
        if running(runtime):
            raise ValueError("selected desktop is running; exit it normally before preparing state")
        if state_path.read_bytes() != original or (catalog_path.read_bytes() if catalog_path.exists() else None) != catalog_bytes:
            raise ValueError("state changed during preparation; retry from fresh input")
        backup = catalog_path.parent / "backups" / f"{time.time_ns()}"
        backup.mkdir(parents=True)
        for path in (state_path, state_path.with_name(state_path.name + ".bak"), catalog_path):
            if path.exists():
                shutil.copy2(path, backup / path.name)
        if running(runtime) or state_path.read_bytes() != original or (catalog_path.read_bytes() if catalog_path.exists() else None) != catalog_bytes:
            raise ValueError("desktop or state changed before commit; original files were preserved")
        if updated != state:
            rendered = (encode(updated) + "\n").encode()
            atomic_write(state_path, rendered)
            atomic_write(state_path.with_name(state_path.name + ".bak"), rendered)
        atomic_write(catalog_path, (encode(catalog) + "\n").encode())
        report.update(applied=True, backup=str(backup))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True, choices=("windows", "beta-wsl"))
    parser.add_argument("--home", required=True, type=Path)
    parser.add_argument("--profiles", required=True, type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--enroll-owner", action="append", default=[])
    parser.add_argument("--seed-owner")
    parser.add_argument("--enroll-identities", type=Path, help="Explicit credential-free Opensoft owner bindings")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        home = args.home.expanduser().resolve()
        validate_runtime(args.runtime, home)
        owner = authenticated_owner(home, args.profiles)
        catalog = args.catalog or home / "workbenches-projects" / args.runtime / "opensoft.json"
        identities = read_json(args.enroll_identities)["identities"] if args.enroll_identities else []
        print(json.dumps(prepare(home, catalog, args.runtime, owner, args.enroll_owner, args.seed_owner, args.apply, identities=identities)))
        return 0
    except (ValueError, KeyError, IndexError, OSError, subprocess.SubprocessError) as error:
        print(f"Codex project preparation refused: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

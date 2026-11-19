#!/usr/bin/env python3
"""Launch and inspect the per-user workBenches OpenCode Desktop servers."""

import argparse
import base64
import copy
import fcntl
import http.client
import json
import os
from pathlib import Path
import re
import secrets
import signal
import shutil
import subprocess
import sys
import time
from urllib.parse import parse_qs, urlencode

from model_session_gate import RetrySession, SessionGate


PROFILES = {
    "claude": (4096, "claude-agent", "opus", "opus", "sonnet", "haiku"),
    "openai": (4097, "openai", "sol", "astra", "terra", "luna"),
}
OPENAI_MODELS = {
    "sol": "gpt-6.2-sol",
    "astra": "gpt-6.2-astra",
    "terra": "gpt-6.1-terra",
    "luna": "gpt-6-luna",
}
OPENAI_RELEASE = re.compile(r"gpt-(\d+)(?:\.(\d+))?(?:\.(\d+))?-(sol|astra|terra|luna)")
JSONC_STRING = r'"(?:[^"\\]|\\.)*"'
JSONC_COMMENTS = re.compile(JSONC_STRING + r"|//[^\r\n]*|/\*[\s\S]*?\*/")
JSONC_TRAILING_COMMAS = re.compile(JSONC_STRING + r"|,(?=\s*[}\]])")
OMO_PLUGIN = "oh-my-openagent@5.1.77"
OPENAI_BACKEND = 4197
PLANNERS = {"oracle", "prometheus", "metis", "momus"}
LOOKUP_AGENTS = {"explore", "librarian"}


def read_settings(root):
    path = root / "workstation.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def source_roster(home):
    path = home / ".omo/omo.jsonc"
    source = {}
    if path.is_file():
        contents = path.read_text(encoding="utf-8-sig")
        contents = JSONC_COMMENTS.sub(lambda token: token[0] if token[0].startswith('"') else " ", contents)
        contents = JSONC_TRAILING_COMMAS.sub(lambda token: token[0] if token[0].startswith('"') else "", contents)
        source = json.loads(contents)
    agents = {"sisyphus", "hephaestus", "atlas", "sisyphus-junior", "multimodal-looker"} | PLANNERS | LOOKUP_AGENTS
    categories = ("quick", "deep", "ultrabrain", "artistry", "visual-engineering", "writing",
                  "unspecified-high", "unspecified-low")
    harness = source.setdefault("[opencode]", {})
    harness.setdefault("agents", {name: {} for name in sorted(agents)})
    harness.setdefault("categories", {name: {} for name in categories})
    return source


def openai_account(home, settings):
    account = settings.get("openai_account")
    last_used = home / ".local/state/workbenches/opencode-last-profile"
    registry = home / ".config/workbenches/opencode-profiles.json"
    if not account and last_used.is_file() and registry.is_file():
        account = last_used.read_text().strip()
    if account:
        if not registry.is_file():
            raise RuntimeError("The chosen popencode account requires the workBenches OpenCode profile registry")
        manifest = json.loads(registry.read_text(encoding="utf-8-sig"))
        if not any(profile.get("name") == account for profile in manifest["profiles"]):
            raise RuntimeError(f"No registered popencode account matches {account}")
    return account


def profile_config(source, name, openai_models):
    _, provider, primary, planning, implementation, lookup = PROFILES[name]
    config = copy.deepcopy(source)
    harness = config["[opencode]"]

    def bind(settings, model):
        resolved_model = openai_models[model] if name == "openai" else model
        settings["model"] = f"{provider}/{resolved_model}"
        for key in ("fallback", "fallbacks", "fallback_models", "variant", "reasoning_effort"):
            settings.pop(key, None)
        if name == "claude":
            settings.pop("reasoning", None)
        if isinstance(settings.get("ultrawork"), dict):
            bind(settings["ultrawork"], model)

    for agent, settings in harness["agents"].items():
        model = implementation
        if agent == "sisyphus":
            model = primary
        elif agent in PLANNERS:
            model = planning
        elif agent in LOOKUP_AGENTS:
            model = lookup
        bind(settings, model)
    for category, settings in harness["categories"].items():
        bind(settings, lookup if category == "quick" else implementation)
    harness["model_fallback"] = False
    harness["disabled_providers"] = []
    config["profiles"] = {name: {"[opencode]": harness}}
    return config


def instance_environment(home, root, name, password, claude_config_dir):
    folder = root / name
    # Do not inherit provider keys or the legacy popencode credential overlay.
    prefixes = ("OPENCODE_", "OMO_", "OCX_", "OPENAI_", "ANTHROPIC_", "CLAUDE_", "AWS_", "GOOGLE_", "VERTEX_")
    env = {key: value for key, value in os.environ.items() if not key.startswith(prefixes)}
    env.update(
        HOME=str(folder),
        XDG_CONFIG_HOME=str(folder / "config"),
        XDG_DATA_HOME=str(folder / "data"),
        XDG_CACHE_HOME=str(folder / "cache"),
        XDG_STATE_HOME=str(folder / "state"),
        OPENCODE_DB=str(folder / "opencode.db"),
        OPENCODE_PASSWORD=password,
        OMO_PROFILE=name,
        PATH=f"{home / '.local/bin'}:{home / '.opencode/bin'}:{env.get('PATH', os.defpath)}",
    )
    if name == "claude":
        env["CLAUDE_CONFIG_DIR"] = str(claude_config_dir)
        claude_binary = read_settings(root).get("claude_binary")
        if claude_binary:
            env["OPENCODE_CLAUDE_PATH"] = claude_binary
    return env


def api(port, password, path, *, method="GET", gate=False):
    upstream = http.client.HTTPConnection("127.0.0.1", port, timeout=20 if method == "POST" else 5)
    try:
        headers = {"Accept": "application/json"}
        if password:
            auth = base64.b64encode(f"opencode:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {auth}"
        upstream.request(method, path, headers=headers)
        response = upstream.getresponse()
        if gate and response.status == 200 and response.getheader("X-OpenCode-Profile-Gate") != "openai":
            raise RuntimeError("OpenAI port already has a server without the freshness gate; leave it running until it is idle and stopped")
        return response.status, json.load(response) if response.status == 200 else None
    finally:
        upstream.close()


def provider_models(response, provider):
    catalog = response.get("data", response) if isinstance(response, dict) else response
    if not isinstance(catalog, list):
        raise RuntimeError(f"{provider}: unexpected model catalog format")
    return {item["id"] for item in catalog if isinstance(item, dict)
            and item.get("providerID") == provider and isinstance(item.get("id"), str)}


def openai_release(model):
    match = OPENAI_RELEASE.fullmatch(model)
    if match is None:
        return None
    return match[4], tuple(int(part or 0) for part in match.groups()[:3])


def latest_openai_models(models):
    latest = {}
    for model in sorted(models):
        release = openai_release(model)
        if release is None:
            continue
        family, version = release
        if family not in latest or version > openai_release(latest[family])[1]:
            latest[family] = model
    return latest


def configured_openai_models(folder):
    path = folder / "openai-models.json"
    saved = json.loads(path.read_text()) if path.is_file() else {}
    return latest_openai_models(set(OPENAI_MODELS.values()) | set(saved.values()))


def refresh_openai(folder):
    port = PROFILES["openai"][0]
    password = (folder / "server-password").read_text().strip()
    with (folder / "start.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        status, catalog = api(port, password, "/api/model")
        if status != 200:
            raise RuntimeError(f"OpenAI catalog returned HTTP {status}")
        latest = latest_openai_models(provider_models(catalog, "openai"))
        current = configured_openai_models(folder)
        unavailable = [family for family, model in current.items()
                       if family not in latest or openai_release(latest[family])[1] < openai_release(model)[1]]
        if unavailable:
            raise RuntimeError("OpenAI catalog has no current or newer release for: " + ", ".join(sorted(unavailable)))
        json_file(folder / "openai-models.json", latest)
    print(json.dumps(latest, indent=2))
    print("OpenAI model choices saved for the next server start.")


def json_file(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(".pending")
    pending.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    pending.replace(path)


def configured_records(response, key):
    if isinstance(response, dict):
        response = response.get("data", response)
    if isinstance(response, dict):
        response = response.get(key, response)
    if isinstance(response, dict):
        return {name: record for name, record in response.items() if isinstance(record, dict)}
    if isinstance(response, list):
        return {record.get("id", record.get("name")): record for record in response if isinstance(record, dict)}
    return {}


def model_reference(record):
    model = record.get("model")
    if isinstance(model, dict):
        model_id = model.get("modelID") or model.get("model") or model.get("id")
        if model.get("providerID") and model_id:
            return f"{model['providerID']}/{model_id}"
    return model if isinstance(model, str) else None


def agent_bindings(expected, response):
    agents = configured_records(response, "agents")
    actual = {agent: model_reference(agents.get(agent, {})) for agent in expected}
    mismatches = {agent: {"expected": settings["model"], "loaded": actual[agent]}
                  for agent, settings in expected.items()
                  if actual[agent] != settings["model"] and not settings.get("disable") and not settings.get("disabled")}
    return actual, mismatches


def audit(folder, name, project=None):
    port, provider, *_ = PROFILES[name]
    path_suffix = "?" + urlencode({"location[directory]": str(project)}) if project else ""
    password = (folder / "server-password").read_text().strip()
    denied, _ = api(port, None, "/api/info")
    info, _ = api(port, password, "/api/info", gate=name == "openai")
    if denied != 401 or info != 200:
        raise RuntimeError(f"{name}: expected unauthenticated 401 and authenticated 200, got {denied}/{info}")
    agent_status, agents_raw = api(port, password, "/api/agent" + path_suffix)
    provider_status, _ = api(port, password, f"/api/provider/{provider}" + path_suffix)
    model_status, models_raw = api(port, password, "/api/model" + path_suffix)
    if (agent_status, provider_status, model_status) != (200, 200, 200):
        raise RuntimeError(f"{name}: metadata returned agent {agent_status}, provider {provider_status}, models {model_status}")
    omo_path = folder / ".omo/omo.jsonc"
    expected = json.loads(omo_path.read_text())["profiles"][name]["[opencode]"]["agents"]
    actual, mismatches = agent_bindings(expected, agents_raw)
    models = provider_models(models_raw, provider)
    missing_models = sorted({settings["model"].split("/", 1)[1] for settings in expected.values()
                             if not settings.get("disable") and not settings.get("disabled")} - models)
    report = {"profile": name, "url": f"http://127.0.0.1:{port}", "project": str(project) if project else None,
              "provider": provider, "agents": actual, "mismatches": mismatches, "missing_models": missing_models}
    newer_models = {}
    if name == "openai":
        latest = latest_openai_models(models)
        for settings in expected.values():
            model = settings["model"].split("/", 1)[1]
            release = openai_release(model)
            if release and release[0] in latest and openai_release(latest[release[0]])[1] > release[1]:
                newer_models[model] = latest[release[0]]
        report["newer_openai_models"] = newer_models
    json_file(folder / "metadata-check.json", report)
    print(json.dumps(report, indent=2))
    return not mismatches and not missing_models and not newer_models


def write_profile(folder, name, source, openai_models):
    _, provider, primary, *_ = PROFILES[name]
    primary = openai_models[primary] if name == "openai" else primary
    roster = profile_config(source, name, openai_models)
    json_file(folder / ".omo/omo.jsonc", roster)
    settings = {
        "$schema": "https://opencode.ai/config.json",
        "plugins": [OMO_PLUGIN],
        "default_agent": "sisyphus",
        "agents": {"build": {"model": f"{provider}/{primary}"}},
        "policies": [
            {"action": "provider.use", "resource": "*", "effect": "deny"},
            {"action": "provider.use", "resource": provider, "effect": "allow"},
        ],
    }
    if name == "openai":
        settings["model"] = f"{provider}/{primary}"
    json_file(folder / "config/opencode/opencode.json", settings)
    return roster["profiles"][name]["[opencode]"]["agents"]


def location_query(directory):
    return "?" + urlencode({"location[directory]": directory}) if directory else ""


class OpenAIModelUpdater:
    def __init__(self, folder, source, password, current):
        self.folder = folder
        self.source = source
        self.password = password
        self.current = current
        self.needs_recovery = False

    def metadata(self, path, expected_type):
        status, response = api(OPENAI_BACKEND, self.password, path)
        data = response.get("data", response) if isinstance(response, dict) else response
        if status != 200 or not isinstance(data, expected_type):
            raise RuntimeError(f"Unexpected OpenCode metadata for {path.split('?')[0]} (HTTP {status})")
        return data

    def idle(self):
        if self.metadata("/api/session/active", dict):
            return False
        if self.metadata("/api/experimental/job?status=running", list):
            return False
        for location in self.metadata("/api/debug/location", list):
            directory = location.get("directory") if isinstance(location, dict) else None
            if not isinstance(directory, str) or not directory:
                raise RuntimeError("OpenCode returned an invalid loaded location")
            query = location_query(directory)
            if self.metadata("/api/shell" + query, list):
                return False
            terminals = self.metadata("/api/pty" + query, list)
            if any(not isinstance(terminal, dict) or terminal.get("status") != "exited" for terminal in terminals):
                return False
        return not self.metadata("/api/session/active", dict)

    def reload(self):
        status, _ = api(OPENAI_BACKEND, self.password, "/api/location/reload", method="POST")
        if status != 204:
            raise RuntimeError(f"OpenCode configuration reload returned HTTP {status}")

    def prepare(self, body, path, no_mutations):
        if self.needs_recovery:
            raise RetrySession("OpenAI could not restore its previous profile. Restart this profile before creating another session.")
        try:
            request = json.loads(body) if body else {}
        except (ValueError, UnicodeError):
            return  # Let OpenCode validate malformed session requests.
        if not isinstance(request, dict):
            return
        location = request.get("location") or {}
        directory = location.get("directory") if isinstance(location, dict) else None
        directory = directory or parse_qs(path.query).get("location[directory]", [None])[0]
        query = location_query(directory) if isinstance(directory, str) else ""

        try:
            base = provider_models(self.metadata("/api/model", list), "openai")
            if query:
                base &= provider_models(self.metadata("/api/model" + query, list), "openai")
            latest = latest_openai_models(base)
            if not latest:
                raise RetrySession("Connect OpenAI in Desktop's provider settings to load the model tiers, then retry.")
            if any(family not in latest or openai_release(latest[family])[1] < openai_release(model)[1]
                   for family, model in self.current.items()):
                raise RetrySession("The OpenAI catalog is missing a current model tier. Check the account and retry.")
            if latest == self.current:
                return
            if not no_mutations or not self.idle():
                raise RetrySession("New OpenAI models are available. Finish active work and retry opening the session.")
            with (self.folder / "start.lock").open("a") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                self.apply(latest, query)
        except (OSError, ValueError, RuntimeError, http.client.HTTPException) as error:
            print(f"OpenAI model check deferred ({type(error).__name__}): {error}", file=sys.stderr, flush=True)
            raise RetrySession("OpenAI could not verify or apply a model upgrade. Retry opening the session.") from error

    def apply(self, latest, query):
        try:
            expected = write_profile(self.folder, "openai", self.source, latest)
            self.reload()
            _, mismatches = agent_bindings(expected, self.metadata("/api/agent" + query, (list, dict)))
            if mismatches:
                raise RuntimeError("The reloaded OpenAI roster did not match the updated model bindings")
            json_file(self.folder / "openai-models.json", latest)
        except (OSError, ValueError, RuntimeError, http.client.HTTPException):
            try:
                previous = write_profile(self.folder, "openai", self.source, self.current)
                self.reload()
                _, mismatches = agent_bindings(previous, self.metadata("/api/agent" + query, (list, dict)))
                if mismatches:
                    raise RuntimeError("The restored OpenAI roster did not match the previous model bindings")
            except (OSError, ValueError, RuntimeError, http.client.HTTPException):
                self.needs_recovery = True
                raise
            raise
        self.current = latest
        print("OpenAI models updated while idle: " + ", ".join(latest.values()), flush=True)


def wait_for_server(process, port, password, *, gate=False):
    for _ in range(30):
        if process.poll() is not None:
            break
        try:
            if api(port, password, "/api/info", gate=gate)[0] == 200:
                return True
        except (OSError, http.client.HTTPException):
            pass
        time.sleep(1)
    return False


def serve_openai(home, root, binary):
    folder = root / "openai"
    port = PROFILES["openai"][0]
    password = (folder / "server-password").read_text().strip()
    source = source_roster(home)
    updater = OpenAIModelUpdater(folder, source, password, configured_openai_models(folder))
    env = instance_environment(home, root, "openai", password, None)
    with SessionGate(("127.0.0.1", port), OPENAI_BACKEND, updater.prepare) as gate:
        try:
            api(OPENAI_BACKEND, None, "/api/info")
        except ConnectionRefusedError:
            pass
        else:
            raise RuntimeError(f"OpenAI internal loopback port {OPENAI_BACKEND} is occupied")
        backend = subprocess.Popen([str(binary), "serve", "--hostname", "127.0.0.1", "--port", str(OPENAI_BACKEND)],
                                   cwd=folder, env=env, stdin=subprocess.DEVNULL)
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
        try:
            if not wait_for_server(backend, OPENAI_BACKEND, password) or api(OPENAI_BACKEND, None, "/api/info")[0] != 401:
                raise RuntimeError("The OpenAI backend did not start with loopback authentication")
            gate.timeout = 1
            while backend.poll() is None:
                gate.handle_request()
            raise RuntimeError("The OpenAI backend exited")
        finally:
            if backend.poll() is None:
                backend.terminate()
                try:
                    backend.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    backend.kill()
                    backend.wait()


def start(home, root, binary, name, source, claude_config_dir):
    folder = root / name
    port = PROFILES[name][0]
    openai = name == "openai"
    folder.mkdir(exist_ok=True)
    with (folder / "start.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        password_path = folder / "server-password"
        password = password_path.read_text().strip() if password_path.is_file() else secrets.token_urlsafe(32)
        try:
            status, _ = api(port, password, "/api/info", gate=openai)
        except ConnectionRefusedError:
            pass
        else:
            if status == 200 and password_path.is_file():
                print(f"{name}: already running at http://127.0.0.1:{port}")
                return
            raise RuntimeError(f"{name}: port {port} is in use; left the existing listener alone")

        env = instance_environment(home, root, name, password, claude_config_dir)
        claude_binary = env.get("OPENCODE_CLAUDE_PATH", "claude")
        if name == "claude" and not shutil.which(claude_binary, path=env["PATH"]):
            raise RuntimeError("Claude Code is missing from PATH; start from the shell for your Claude subscription")
        write_profile(folder, name, source, configured_openai_models(folder) if openai else {})
        password_path.write_text(password + "\n", encoding="utf-8")
        command = [str(binary), "serve", "--hostname", "127.0.0.1", "--port", str(port)]
        if openai:
            command = [sys.executable, str(Path(__file__).resolve()), "_serve-openai", str(binary)]
            env = None  # The supervisor reads the profile password from disk and isolates its backend.
        with (folder / "server.log").open("ab") as log:
            process = subprocess.Popen(command, cwd=folder, env=env, stdin=subprocess.DEVNULL, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
        try:
            if wait_for_server(process, port, password, gate=openai):
                print(f"{name}: listening at http://127.0.0.1:{port}")
                return process
            raise RuntimeError(f"{name}: server did not become ready; see {folder / 'server.log'}")
        except BaseException:
            if process.poll() is None:
                process.terminate()
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("start", "supervise", "health", "verify", "refresh"))
    parser.add_argument("--profile", choices=PROFILES)
    parser.add_argument("--project", type=Path, help="Optional absolute WSL project path for metadata verification")
    parser.add_argument("--claude-config-dir", type=Path, help="Existing subscription-backed Claude Code config directory")
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error("Run this in the Linux distribution that hosts your OpenCode profiles")
    if args.command == "supervise" and not args.profile:
        parser.error("supervise needs exactly one --profile")
    if args.project and not args.project.is_dir():
        parser.error("--project must name an existing WSL directory")
    os.umask(0o077)
    home = Path.home()
    root = home / ".local/state/opencode-desktop-profiles"
    root.mkdir(parents=True, exist_ok=True)
    if args.command == "refresh":
        if args.profile == "claude" or args.project:
            parser.error("refresh checks the OpenAI server's base catalog")
        try:
            refresh_openai(root / "openai")
        except (OSError, ValueError, RuntimeError, http.client.HTTPException) as error:
            print(f"openai: {error}", file=sys.stderr)
            return 1
        return 0
    names = [args.profile] if args.profile else list(PROFILES)
    launching = args.command in ("start", "supervise")
    if launching:
        settings = read_settings(root)
        binary = Path(os.environ.get("OPENCODE_BIN") or settings.get("opencode_binary") or home / ".opencode/bin/opencode")
        version = subprocess.check_output([str(binary), "--version"], text=True).strip()
        release = re.fullmatch(r"2\.(\d+)\.(\d+)(?:[-+].*)?", version)
        if not release or tuple(map(int, release.groups())) < (2, 3):
            raise RuntimeError(f"Expected OpenCode v2.2.3 or later in the v2 line; got {version!r}")
        if "openai" in names and tuple(map(int, release.groups())) < (3, 1):
            raise RuntimeError(f"The OpenAI profile requires OpenCode v2.3.1 or later for GPT-6.2 with ChatGPT sign-in; got {version!r}")
        source = source_roster(home)
        claude_config_dir = (args.claude_config_dir or Path(os.environ.get("CLAUDE_CONFIG_DIR")
                             or settings.get("claude_config_dir") or root / "claude/.claude")).expanduser().resolve()
        if "openai" in names:
            account = openai_account(home, settings)
            selection = f" as popencode account {account}" if account else " with your workstation account"
            print(f"OpenAI: connect with ChatGPT OAuth{selection} during first use.")
        if "claude" in names:
            print(f"Claude: use the subscription login in {claude_config_dir}.")
    success = True
    for name in names:
        try:
            if args.command == "health":
                password = (root / name / "server-password").read_text().strip()
                port = PROFILES[name][0]
                if api(port, None, "/api/info")[0] != 401 or api(port, password, "/api/info", gate=name == "openai")[0] != 200:
                    raise RuntimeError("The private listener did not answer its authenticated health check")
                print(f"{name}: listening at http://127.0.0.1:{port}")
            elif launching:
                process = start(home, root, binary, name, source, claude_config_dir)
                if args.command == "supervise":
                    if process is None:
                        print(f"{name}: retaining the existing listener; scheduled ownership requires a fresh start", file=sys.stderr)
                        return 1
                    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
                    try:
                        return process.wait() or 1  # Unexpected stops should be retried by Task Scheduler.
                    finally:
                        if process.poll() is None:
                            process.terminate()
                            process.wait(timeout=20)
            else:
                success = audit(root / name, name, args.project.resolve() if args.project else None) and success
        except (OSError, ValueError, RuntimeError, http.client.HTTPException) as error:
            print(f"{name}: {error}", file=sys.stderr)
            success = False
    return 0 if success else 1


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "_serve-openai" and sys.platform == "linux":
        os.umask(0o077)
        user_home = Path.home()
        serve_openai(user_home, user_home / ".local/state/opencode-desktop-profiles", Path(sys.argv[2]))
    else:
        sys.exit(main())

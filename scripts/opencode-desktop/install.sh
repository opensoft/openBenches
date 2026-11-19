#!/usr/bin/env bash
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
runtime="$HOME/.local/lib/workbenches/opencode-desktop"
state="$HOME/.local/state/opencode-desktop-profiles"
launcher="$runtime/setup_profiles.py"
host_python=/usr/bin/python3
release=v2.3.2
release_url="https://github.com/anomalyco/opencode/releases/download/$release"

# The asynchronous Tools inventory runs in a container. Check Windows and
# Linux loopback from the WSL host through the existing workstation broker.
if [[ "${1:-}" == --status && -n "${WORKBENCHES_HOST_RPC:-}" ]]; then
    exec python3 -c 'import sys, workbenches_host; sys.exit(workbenches_host.run(["bash", sys.argv[1], "--status"], env={"WORKBENCHES_HOST_RPC": ""}).returncode)' "$here/install.sh"
fi

if [[ -z "${WSL_DISTRO_NAME:-}" || $(id -u) -eq 0 ]]; then
    echo 'Run the OpenCode Desktop installer as your workstation user in WSL.' >&2
    exit 2
fi

run_windows() {
    local mode="$1" windows_script powershell
    shift
    if ! powershell="$(command -v powershell.exe)"; then
        # WSL can leave Windows executables off PATH while interop still works.
        powershell="$(wslpath -u "${SystemRoot:-C:\Windows}\System32\WindowsPowerShell\v1.0\powershell.exe")" || return 1
        if [[ ! -x "$powershell" ]]; then
            echo 'Windows PowerShell is unavailable to the OpenCode Desktop installer.' >&2
            return 1
        fi
    fi
    windows_script="$(wslpath -w "$here/install-windows.ps1")"
    "$powershell" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$windows_script" \
        -Action "$mode" -Distribution "$WSL_DISTRO_NAME" "$@" | tr -d '\r'
}

case "${1:-install}" in
    --status)
        status="$(run_windows Status)"
        if [[ "$status" == installed ]] && ! "$host_python" -B "$launcher" health >/dev/null 2>&1; then
            status='needs check'
        fi
        printf '%s\n' "$status"
        exit 0
        ;;
    --disable)
        run_windows Disable
        exit 0
        ;;
    install) ;;
    *) echo 'Usage: install.sh [install|--status|--disable]' >&2; exit 2 ;;
esac

[[ -x "$host_python" ]] || { echo 'Install the Ubuntu python3 package for the OpenCode logon tasks.' >&2; exit 1; }
umask 077
install -d -m 0700 "$runtime" "$state"
temp="$(mktemp -d "$runtime/install.XXXXXXXX")"
trap 'rm -f -- "$temp/opencode.tar.gz" "$temp/opencode" "$temp/claude-install.sh" "$temp/setup_profiles.py" "$temp/model_session_gate.py"; rmdir -- "$temp"' EXIT

supports_profiles() {
    local current
    [[ -x "$1" ]] && current="$("$1" --version 2>/dev/null)" || return 1
    [[ "$current" =~ ^2\.([0-9]+)\.([0-9]+)([-+].*)?$ ]] || return 1
    (( BASH_REMATCH[1] > 3 || (BASH_REMATCH[1] == 3 && BASH_REMATCH[2] >= 1) ))
}

opencode="${WORKBENCH_OPENCODE_BINARY:-$HOME/.opencode/bin/opencode}"
if ! supports_profiles "$opencode"; then
    opencode="$runtime/opencode"
    if ! supports_profiles "$opencode"; then
        case "$(uname -m)" in
            x86_64) arch=x64; checksum=563b5d663637226b6e3bb4bb6803281bc39b0d2cd88db06d674b6420aab009b0 ;;
            aarch64) arch=arm64; checksum=9d10185acdb72336e086e699ca363a6065f410fd3c1caed0dc8046e95ac06ccb ;;
            *) echo 'No OpenCode workstation binary for this WSL architecture.' >&2; exit 2 ;;
        esac
        curl --fail --location --silent --show-error --retry 2 \
            "$release_url/opencode-linux-$arch.tar.gz" --output "$temp/opencode.tar.gz"
        printf '%s  %s\n' "$checksum" "$temp/opencode.tar.gz" | sha256sum --check --status
        tar -xOzf "$temp/opencode.tar.gz" opencode > "$temp/opencode"
        chmod 0700 "$temp/opencode"
        supports_profiles "$temp/opencode"
        mv -f -- "$temp/opencode" "$opencode"
    fi
fi

claude="${WORKBENCH_CLAUDE_BINARY:-$(command -v claude || true)}"
if [[ ! -x "$claude" ]]; then
    curl --fail --location --silent --show-error --retry 2 \
        https://claude.ai/install.sh --output "$temp/claude-install.sh"
    bash "$temp/claude-install.sh"
    claude="$HOME/.local/bin/claude"
    [[ -x "$claude" ]] || { echo 'Claude Code did not install for this user.' >&2; exit 1; }
fi

for file in setup_profiles.py model_session_gate.py; do
    install -m 0600 "$here/$file" "$temp/$file"
    mv -f -- "$temp/$file" "$runtime/$file"
done

"$host_python" -B - "$runtime" "$state" "$opencode" "$claude" <<'PY'
import os
from pathlib import Path
import sys

runtime, state, opencode, claude = map(Path, sys.argv[1:])
sys.path.insert(0, str(runtime))
from setup_profiles import json_file, openai_account, read_settings, source_roster

settings = read_settings(state)
settings.update(opencode_binary=str(opencode.absolute()), claude_binary=str(claude.absolute()))
if directory := os.environ.get('CLAUDE_CONFIG_DIR'):
    settings['claude_config_dir'] = str(Path(directory).expanduser().resolve())
if account := os.environ.get('WORKBENCH_OPENCODE_ACCOUNT'):
    settings['openai_account'] = account
if account := openai_account(Path.home(), settings):
    settings['openai_account'] = account
    print(f'OpenAI Desktop account: sign in to the subscription used by popencode {account}.')
source_roster(Path.home())['[opencode]']
json_file(state / 'workstation.json', settings)
PY

run_windows Install -LinuxUser "$(id -un)" -Launcher "$launcher"
for _ in {1..30}; do
    if "$host_python" -B "$launcher" health 2>/dev/null; then exit 0; fi
    sleep 1
done
echo "Autostart was registered, but both listeners could not be verified. See $state/{claude,openai}/server.log." >&2
exit 1

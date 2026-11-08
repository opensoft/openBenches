#!/usr/bin/env bash
# Reconcile Wave launch shortcuts after setup. Host I/O also works on Windows paths from WSL.
set -o pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1
source "$root/bootstrap.sh"

if [[ "${WORKBENCHES_SKIP_WAVE_WIDGETS:-}" == 1 ]]; then
    echo 'Wave Terminal widget setup skipped by WORKBENCHES_SKIP_WAVE_WIDGETS=1.'
    exit 0
fi
command -v python3 >/dev/null 2>&1 || exit 1

config_dir="${WAVETERM_CONFIG_DIR:-}"
distro="${WSL_DISTRO_NAME:-}"
if [[ -z "$config_dir" ]]; then
    if [[ -n "$distro" ]] || grep -qi microsoft /proc/version 2>/dev/null; then
        windows_profile="$(powershell.exe -NoProfile -Command '
            $paths = @(
                "$env:ProgramFiles\Wave\Wave.exe"
                "$env:LOCALAPPDATA\Programs\waveterm\Wave.exe"
                "$env:LOCALAPPDATA\Programs\Wave\Wave.exe"
            )
            if ($paths | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf }) {
                [Environment]::GetFolderPath("UserProfile")
            }
        ' </dev/null | tr -d '\r')" || exit 1
        [[ -n "$windows_profile" ]] || exit 0
        wsl_profile="$(wslpath -u "$windows_profile")" || exit 1
        config_dir="$wsl_profile/.config/waveterm"
    else
        if [[ ! -d /Applications/Wave.app && ! -d "$HOME/Applications/Wave.app" ]]; then
            wave_status="$(python3 "$root/scripts/setup-components.py" tool-status wave)" || exit 1
            [[ "$wave_status" == installed ]] || exit 0
        fi
        config_dir="$HOME/.config/waveterm"
    fi
fi

inventory="$(python3 "$root/scripts/setup-components.py" bench-statuses --include-legacy-rust)" || exit 1
for bench in pyBench flutterBench cppBench rustBench cloudBench; do
    if ! grep -Eq "^$bench"$'\t''(installed|image only|needs setup)$' <<< "$inventory"; then
        echo 'Wave widget sync skipped because the bench inventory could not be verified.' >&2
        exit 0
    fi
done

projects_root="${WAVE_PROJECTS_ROOT:-${PROJECTS_ROOT:-$HOME/projects}}"
connection="${WAVE_WSL_CONNECTION:-}"
if [[ -z "$connection" ]] && { [[ -n "$distro" ]] || grep -qi microsoft /proc/version 2>/dev/null; }; then
    connection="wsl://${distro:-Ubuntu-24.04}"
fi
umask 077
staged="$(mktemp -d)" || exit 1
snapshot="$staged/snapshot"
updated="$staged/updated"
templates="$staged/templates"
lock=''
connection_temp=''
widget_temp=''
recovery=''
cleanup() {
    # A signal or failed publication must not leave a claimed setting absent.
    if [[ -n "$recovery" ]]; then
        for file in connections.json widgets.json; do
            if [[ -e "$recovery/$file" && ! -e "$config_dir/$file" && ! -L "$config_dir/$file" ]]; then
                link_without_replacing "$recovery/$file" "$config_dir/$file" || :
            fi
        done
        printf 'Original Wave settings retained in %s.\n' "$recovery" >&2
    fi
    [[ -z "$connection_temp" ]] || rm -f -- "$connection_temp"
    [[ -z "$widget_temp" ]] || rm -f -- "$widget_temp"
    [[ -z "$lock" ]] || rmdir -- "$lock"
    rm -rf -- "$staged"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
mkdir -- "$snapshot" "$updated" "$templates" || exit 1

for file in connections.json widgets.json; do
    live="$config_dir/$file"
    if [[ -L "$live" || ( -e "$live" && ! -f "$live" ) ]]; then
        printf 'Refusing to replace Wave settings at %s.\n' "$live" >&2
        exit 1
    fi
    if [[ -f "$live" ]]; then cp -p -- "$live" "$snapshot/$file" || exit 1; fi
done

prepare() {
    python3 "$root/scripts/sync-wave-widgets.py" "$snapshot" "$updated" "$templates" \
        "$root" "$projects_root" "$connection" "$inventory"
}

if prepare; then
    :
else
    status=$?
    [[ "$status" == 3 ]] || exit "$status"
    sibling="$(dirname "$root")/Install-Wave-Terminal"
    installer_dir="${WAVE_TERMINAL_INSTALLER_DIR:-$HOME/.cache/workbenches/Install-Wave-Terminal}"
    if [[ -z "${WAVE_TERMINAL_INSTALLER_DIR:-}" && -x "$sibling/scripts/install-workbenches-widgets.sh" ]]; then
        installer_dir="$sibling"
    fi
    installer="$installer_dir/scripts/install-workbenches-widgets.sh"
    if [[ ! -x "$installer" ]]; then
        [[ ! -e "$installer_dir" ]] || exit 1
        mkdir -p -- "$(dirname "$installer_dir")" || exit 1
        workbenches_clone "${WAVE_TERMINAL_INSTALLER_REPO:-https://github.com/opensoft/Install-Wave-Terminal.git}" \
            "$installer_dir" --depth 1 || exit "$?"
    fi
    "$installer" --skip-launcher --waveterm-config "$templates" --workbenches-root "$root" \
        --projects-root "$projects_root" --font-size "${WAVE_WIDGET_FONT_SIZE:-16}" \
        --wsl-connection "$connection" || exit "$?"
    prepare || exit "$?"
fi

if [[ ! -f "$updated/connections.json" && ! -f "$updated/widgets.json" ]]; then
    echo 'Wave Terminal widgets are configured.'
    exit 0
fi

mkdir -p -- "$config_dir" || exit 1
if ! mkdir -- "$config_dir/.openbenches-widget-sync.lock" 2>/dev/null; then
    echo 'Wave settings are locked by another sync. Rerun setup to retry.' >&2
    exit 1
fi
lock="$config_dir/.openbenches-widget-sync.lock"

matches_snapshot() {
    local file="$1" live="$config_dir/$1"
    [[ ! -L "$live" ]] || return 1
    if [[ -f "$snapshot/$file" ]]; then
        [[ -f "$live" ]] && cmp -s -- "$snapshot/$file" "$live"
    else
        [[ ! -e "$live" ]]
    fi
}

check_snapshot() {
    if ! matches_snapshot connections.json || ! matches_snapshot widgets.json; then
        echo 'Wave settings changed during setup. Rerun setup to sync the latest settings.' >&2
        exit 1
    fi
}

stage_for_replace() {
    local file="$1" temp="$2"
    # Retain permissions on existing settings files before changing the contents.
    if [[ -f "$snapshot/$file" ]]; then cp -p -- "$snapshot/$file" "$temp" || return 1; fi
    cat -- "$updated/$file" > "$temp"
}

link_without_replacing() {
    if [[ "$(uname -s)" == Darwin ]]; then
        ln -h -- "$1" "$2"
    else
        ln -T -- "$1" "$2"
    fi
}

publish() {
    local file="$1" temp="$2" live="$config_dir/$1"
    if [[ -f "$snapshot/$file" ]]; then
        if [[ -z "$recovery" ]]; then
            recovery="$(mktemp -d "$config_dir/.openbenches-settings-backup.XXXXXX")" || return 1
        fi
        # Capture the actual displaced version, not just the earlier snapshot.
        # Wave does not share our lock: never overwrite a save it makes here.
        if [[ "$(uname -s)" == Darwin ]]; then
            mv -fh -- "$live" "$recovery/$file" || return 1
        else
            mv -fT -- "$live" "$recovery/$file" || return 1
        fi
        if [[ -L "$recovery/$file" || ! -f "$recovery/$file" ]] ||
            ! cmp -s -- "$snapshot/$file" "$recovery/$file"; then
            echo 'Wave settings changed during publication; the displaced version was preserved. Rerun setup.' >&2
            return 1
        fi
    fi
    link_without_replacing "$temp" "$live" || return 1
}

if [[ -f "$updated/connections.json" ]]; then
    connection_temp="$(mktemp "$config_dir/.openbenches-connections.XXXXXX")" || exit 1
    stage_for_replace connections.json "$connection_temp" || exit 1
fi
if [[ -f "$updated/widgets.json" ]]; then
    widget_temp="$(mktemp "$config_dir/.openbenches-widgets.XXXXXX")" || exit 1
    stage_for_replace widgets.json "$widget_temp" || exit 1
fi
check_snapshot
# Enable the connection before any widget references it.
if [[ -n "$connection_temp" ]]; then
    publish connections.json "$connection_temp" || exit 1
    cp -- "$updated/connections.json" "$snapshot/connections.json" || exit 1
fi
if [[ -n "$widget_temp" ]]; then
    check_snapshot
    publish widgets.json "$widget_temp" || exit 1
fi
printf 'Wave Terminal widgets configured in %s.\n' "$config_dir"

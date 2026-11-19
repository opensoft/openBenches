#!/usr/bin/env bash

windows_powershell_path() {
    local executable
    if executable="$(command -v powershell.exe)"; then
        printf '%s\n' "$executable"
        return
    fi
    # WSL can leave Windows executables off PATH while interop still works.
    if executable="$(wslpath -u "${SystemRoot:-C:\Windows}\System32\WindowsPowerShell\v1.0\powershell.exe")" && [[ -x "$executable" ]]; then
        printf '%s\n' "$executable"
        return
    fi
    echo 'Windows PowerShell is unavailable to setup.' >&2
    return 1
}

#!/usr/bin/env python3
"""Prepare shared bench bind sources as the host user before Docker creates them.

The settings file .claude.json is distinct from .claude/.credentials.json.
Existing settings and credential files are never opened or replaced.
"""
import os
from pathlib import Path
import subprocess
import sys

try:
    import workbenches_host as host
except ImportError:
    host = None

DIRECTORIES = (
    'projects', '.ssh', '.azure', '.aws', '.kube', '.config/gh', '.claude',
    '.claude-profiles', '.codex', '.chatgpt-profiles', '.opencode-profiles',
    '.gemini-profiles', '.grok-profiles', '.glm-profiles', '.omnigent', '.agents',
    '.pi', '.pi-profiles', '.config/workbenches', '.local/lib/workbenches',
    '.local/state/workbenches', '.config/sonarqube', '.gemini', '.grok',
    '.copilot-cli', '.notebooklm', '.notebooklm-mcp-cli',
    '.local/state/opensoft/agenttower/logs',
)
SETTINGS = {'.zshrc': b'', '.p10k.zsh': b'', '.bashrc': b'', '.gitconfig': b'', '.claude.json': b'{}\n'}


def valid_type(path, directory):
    if path.is_symlink() and host is not None and host.active():
        flag = '-d' if directory else '-f'
        return host.run(['test', flag, path], capture_output=True).returncode == 0
    return path.is_dir() if directory else path.is_file()


def prepare(home):
    os.umask(0o077)
    # Validate everything before creating anything. Links into host-only mounts
    # must be checked on the workstation and must never be written through.
    existing = set()
    for names, directory in ((DIRECTORIES, True), (SETTINGS, False)):
        for name in names:
            path = home / name
            if path.is_symlink() or path.exists():
                if not valid_type(path, directory):
                    expected = 'directory' if directory else 'settings file'
                    raise ValueError(f'Expected a {expected} at {path}; restore the bind source before installing a bench.')
                existing.add(name)
    for name in DIRECTORIES:
        if name not in existing:
            (home / name).mkdir(mode=0o700, parents=True, exist_ok=True)
    for name, initial in SETTINGS.items():
        if name in existing:
            continue
        path = home / name
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            continue
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(initial)
    print('Bench folders and settings are ready.')


if __name__ == '__main__':
    try:
        prepare(Path.home())
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f'Bench home preparation failed: {error}', file=sys.stderr)
        sys.exit(1)

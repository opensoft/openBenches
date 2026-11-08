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


def host_linked(path):
    return (host is not None and host.active()
            and any(candidate.is_symlink() for candidate in (path, *path.parents)))


def valid_type(path, directory):
    if host_linked(path):
        flag = '-d' if directory else '-f'
        return host.run(['test', flag, path], capture_output=True).returncode == 0
    return path.is_dir() if directory else path.is_file()


def existing_source(path, directory):
    if host_linked(path):
        present = (host.run(['test', '-e', path], capture_output=True).returncode == 0
                   or host.run(['test', '-L', path], capture_output=True).returncode == 0)
    else:
        present = path.is_symlink() or path.exists()
    if not present:
        return False
    if not valid_type(path, directory):
        expected = 'directory' if directory else 'settings file'
        raise ValueError(f'Expected a {expected} at {path}; restore the bind source before installing a bench.')
    return True


def prepare(home):
    os.umask(0o077)
    # Validate everything before creating anything. Links into host-only mounts
    # must be checked on the workstation and must never be written through.
    for names, directory in ((DIRECTORIES, True), (SETTINGS, False)):
        for name in names:
            existing_source(home / name, directory)
    for name in DIRECTORIES:
        if not existing_source(home / name, True):
            path = home / name
            if host_linked(path):
                # Missing children of user-selected host links are created by
                # the host; no existing settings file or link is replaced.
                result = host.run(['bash', '-c', 'umask 077; mkdir -p -- "$1"',
                                   'bench-home', path], capture_output=True)
                if result.returncode:
                    raise ValueError(f'Could not create directory on the host: {path}')
            else:
                path.mkdir(mode=0o700, parents=True, exist_ok=True)
    for name, initial in SETTINGS.items():
        if existing_source(home / name, False):
            continue
        path = home / name
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            continue
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(initial)
    for names, directory in ((DIRECTORIES, True), (SETTINGS, False)):
        for name in names:
            if not existing_source(home / name, directory):
                raise ValueError(f'Required bind source disappeared during preparation: {home / name}')
    print('Bench folders and settings are ready.')


if __name__ == '__main__':
    try:
        prepare(Path.home())
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f'Bench home preparation failed: {error}', file=sys.stderr)
        sys.exit(1)

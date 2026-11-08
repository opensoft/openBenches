#!/usr/bin/env python3
"""Service readiness and ownership checks without touching a Docker engine."""
import os
import socket
import json
import re
import importlib.util
import sys
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / 'scripts/lib/tools-container.sh'


class ServiceTests(unittest.TestCase):
    def test_agent_freshness_is_checked_by_healthy_command_shims(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            repo = home / 'repo'
            (repo / 'scripts/lib').mkdir(parents=True)
            shutil.copy(ROOT / 'scripts/tools-command.sh', repo / 'scripts/tools-command.sh')
            shutil.copytree(ROOT / 'tools-container', repo / 'tools-container')
            library = LIB.read_text() + r"""
workbenches_tools_state() { echo up; }
workbenches_tools_start() {
    echo refresh >> "$HOME/refreshes"
    workbenches_tools_fingerprint > "$HOME/mounted"
}
workbenches_runtime_docker() {
    if [[ "$1 $2" == 'container inspect' ]]; then cat "$HOME/mounted"; return; fi
    [[ "$1" == exec ]] || return 90
    for argument in "$@"; do
        [[ "$argument" != SSH_AUTH_SOCK && "$argument" != SSH_AUTH_SOCK=* ]] || return 91
    done
    echo exec
}
"""
            (repo / 'scripts/lib/tools-container.sh').write_text(library)
            (repo / 'scripts/lib/tools-host-broker.sh').write_text(
                'touch "$1/alive"\ntrap "exit 0" TERM\nwhile test -f "$1/alive"; do sleep .02; done\n')
            env = dict(os.environ, HOME=str(home), XDG_CACHE_HOME=str(home / '.cache'),
                       WORKBENCHES_TOOLS_ROOT=str(repo), WORKBENCHES_TOOLS_CONTAINER='fixture')

            def fingerprint(current):
                return subprocess.check_output(
                    ['bash', '-c', 'source "$1"; workbenches_tools_fingerprint',
                     'fixture', str(repo / 'scripts/lib/tools-container.sh')],
                    env=current, text=True).strip()

            def invoke(before, after, changed):
                (home / 'mounted').write_text(before + '\n')
                (home / 'refreshes').unlink(missing_ok=True)
                for _ in range(2):
                    result = subprocess.run(
                        ['bash', str(repo / 'scripts/tools-command.sh'), 'git', '--version'],
                        env=after, text=True, capture_output=True, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout.strip(), 'exec')
                refreshes = home / 'refreshes'
                self.assertEqual(refreshes.read_text().splitlines() if refreshes.exists() else [],
                                 ['refresh'] if changed else [])

            first_path, second_path = home / 'first.sock', home / 'second.sock'
            with socket.socket(socket.AF_UNIX) as first, socket.socket(socket.AF_UNIX) as second:
                first.bind(str(first_path)); second.bind(str(second_path))
                first_env = dict(env, SSH_AUTH_SOCK=str(first_path))
                second_env = dict(env, SSH_AUTH_SOCK=str(second_path))
                invoke(fingerprint(first_env), first_env, False)
                invoke(fingerprint(first_env), second_env, True)
                absent_env = dict(env); absent_env.pop('SSH_AUTH_SOCK', None)
                invoke(fingerprint(second_env), absent_env, True)
                missing_env = dict(env, SSH_AUTH_SOCK=str(home / 'late.sock'))
                before = fingerprint(missing_env)
                with socket.socket(socket.AF_UNIX) as late:
                    late.bind(missing_env['SSH_AUTH_SOCK'])
                    invoke(before, missing_env, True)
                before = fingerprint(first_env)
                first_path.unlink()
                with socket.socket(socket.AF_UNIX) as replacement:
                    replacement.bind(str(first_path))
                    invoke(before, first_env, True)
                fallback = self.shell(f'''SSH_AUTH_SOCK={str(first_path)!r}
stat() {{ [[ "$1" == -Lf ]] || return 1; echo bsd-identity; }}
workbenches_ssh_agent_identity''')
                self.assertEqual(fallback, 'socket:bsd-identity')

    def test_home_sources_removed_after_preflight_are_recreated(self):
        spec = importlib.util.spec_from_file_location('bench_home', ROOT / 'scripts/setup-bench-home.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        for name, directory in (('.azure', True), ('.claude.json', False)):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                home = Path(temporary); target = home / name
                target.mkdir() if directory else target.write_text('fixture')
                original = module.valid_type
                removed = False

                def remove_after_validation(path, kind):
                    nonlocal removed
                    result = original(path, kind)
                    if path == target and not removed:
                        path.rmdir() if directory else path.unlink()
                        removed = True
                    return result

                with mock.patch.object(module, 'valid_type', side_effect=remove_after_validation):
                    module.prepare(home)
                self.assertTrue(removed)
                self.assertTrue(target.is_dir() if directory else target.is_file())

    def test_host_only_ancestor_links_are_validated_without_writes(self):
        spec = importlib.util.spec_from_file_location('bench_home', ROOT / 'scripts/setup-bench-home.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / 'home'; home.mkdir()
            module.prepare(home)
            target = Path(temporary) / 'host-config'
            (home / '.config').rename(target)
            (home / '.config').symlink_to(target, target_is_directory=True)
            # One genuinely missing host child must be created on the host,
            # not mistaken for an invalid existing target.
            (target / 'sonarqube').rmdir()
            existing = Path.exists
            mkdir = Path.mkdir
            calls = []

            def tools_exists(path):
                if str(path).startswith(str(home / '.config') + os.sep):
                    return False
                return existing(path)

            def no_link_writes(path, *args, **kwargs):
                self.assertFalse(str(path).startswith(str(home / '.config')))
                return mkdir(path, *args, **kwargs)

            def host_test(argv, **kwargs):
                calls.append(argv)
                return subprocess.run([str(value) for value in argv], **kwargs)

            bridge = mock.Mock()
            bridge.active.return_value = True
            bridge.run.side_effect = host_test
            with (mock.patch.object(module, 'host', bridge),
                  mock.patch.object(Path, 'exists', tools_exists),
                  mock.patch.object(Path, 'mkdir', no_link_writes)):
                module.prepare(home)
            self.assertTrue((home / '.config').is_symlink())
            self.assertEqual((target / 'sonarqube').stat().st_mode & 0o777, 0o700)
            for child in ('gh', 'workbenches', 'sonarqube'):
                self.assertIn(['test', '-d', home / '.config' / child], calls)

    def test_numeric_leading_bench_keys_work_in_legacy_entrypoints(self):
        def function(file, name):
            match = re.search(r'^' + re.escape(name) + r'\(\) \{\n.*?^\}', file.read_text(),
                              re.MULTILINE | re.DOTALL)
            self.assertIsNotNone(match, name)
            return match.group(0)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); (root / 'scripts').mkdir()
            path = root / 'sysBenches/365Bench'; path.mkdir(parents=True)
            config = root / 'catalog.json'
            config.write_text(json.dumps({'benches': {'365Bench': {
                'path': 'sysBenches/365Bench', 'url': 'https://example.test/365.git',
                'description': 'M365 fixture'}}, 'infrastructure': {}}))
            setup = ROOT / 'scripts/setup-workbenches.sh'
            update = ROOT / 'scripts/update-project.sh'
            body = '\n'.join((function(setup, 'is_installed'),
                              function(setup, 'install_all_benches'),
                              function(update, 'is_bench_installed'),
                              function(update, 'get_available_benches_for_ai')))
            body += r"""
is_installed 365Bench || exit 41
is_bench_installed 365Bench || exit 42
get_available_benches_for_ai
is_installed() { return 1; }
clone_repo() { printf '%s|%s|%s|%s\n' "$1" "$2" "$3" "$4"; }
install_all_benches 365Bench
"""
            result = subprocess.run(['bash', '-c', body],
                                    env=dict(os.environ, CONFIG_FILE=str(config),
                                             SCRIPT_DIR=str(root / 'scripts')),
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('365Bench: M365 fixture', result.stdout)
            self.assertIn('365Bench|https://example.test/365.git|sysBenches/365Bench|M365 fixture',
                          result.stdout)

    def test_acceptance_opens_ai_accounts_in_profiles_and_cancels_without_vault(self):
        # Use the production renderer/input/profile action; isolate discovery and
        # the external credential helper so this regression needs no Docker/login.
        sys.path.insert(0, str(ROOT / 'devcontainer.test'))
        spec = importlib.util.spec_from_file_location('acceptance', ROOT / 'devcontainer.test/test-workstation-acceptance.py')
        acceptance = importlib.util.module_from_spec(spec); spec.loader.exec_module(acceptance)
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            acceptance.REPO = home
            acceptance.REPORT = home
            script = r'''source "$WB_TEST_SETUP"
init_components --loading
for key in "${!component_description[@]}"; do component_status[$key]=installed; done
component_status[docker]=up; component_status[setup_tools]=up
component_status[wsl]=up
setup_os_label=Linux
refresh_component_statuses() { :; }
activate_requirement() { echo UNEXPECTED_VAULT_ACTION; exit 99; }
configure_selected_accounts() {
    local choice
    setup_read 'AI assistant (codex/claude) [codex]' choice || return "$?"
    printf 'Authentication route [1]: '
    IFS= read -r choice || return 130
    [[ "$choice" != Q ]] || return 130
    return 99
}
draw_ui
while true; do
    handle_input; result=$?
    [[ "$result" != 2 ]] || exit 130
    [[ "$result" != 1 ]] || exit 99
    draw_ui
done
'''
            (home / 'setup.sh').write_text(script)
            env = dict(os.environ, HOME=temporary, XDG_CONFIG_HOME=str(home / '.config'),
                       WB_TEST_SETUP=str(ROOT / 'scripts/interactive-setup.sh'), TERM='xterm-256color')
            try:
                output = acceptance.terminal('profiles-cancel', acceptance.account_setup_replies(
                    [(r'Authentication route \[1\]: ', 'Q\n')], cancel=True), expected=130, env=env, timeout=10)
            except subprocess.TimeoutExpired:
                self.fail((home / 'profiles-cancel.txt').read_text()[-5000:])
            self.assertIn('Profile action cancelled; saved profiles kept.', output)
            self.assertNotIn('UNEXPECTED_VAULT_ACTION', output)
            self.assertFalse((home / '.config/workbenches/openai-profiles.json').exists())

    def shell(self, body):
        result = subprocess.run(['bash', '-c', f'source "$1"\n{body}', 'test', str(LIB)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def test_docker_unreachable_and_windows_engine_are_down(self):
        for answer in ('return 1', 'echo windows'):
            with self.subTest(answer=answer):
                self.assertEqual(self.shell(f'docker() {{ {answer}; }}; workbenches_docker_state'), 'down')

    def test_managed_container_requires_owner_home_and_health(self):
        for role in ('tools', 'vault'):
            for owner, uid, home, running, health, expected in (
                (role, str(os.getuid()), os.environ['HOME'], 'true', 'healthy', 'up'),
                (role, str(os.getuid()), os.environ['HOME'], 'false', 'healthy', 'down'),
                (role, str(os.getuid()), os.environ['HOME'], 'true', 'unhealthy', 'down'),
                ('foreign', str(os.getuid()), os.environ['HOME'], 'true', 'healthy', 'down'),
                (role, '987654', os.environ['HOME'], 'true', 'healthy', 'down'),
                (role, str(os.getuid()), '/other-home', 'true', 'healthy', 'down'),
            ):
                with self.subTest(role=role, expected=expected, health=health, owner=owner, uid=uid, home=home):
                    record = '|'.join((owner, uid, running, health, home))
                    self.assertEqual(self.shell(f'''workbenches_docker_state() {{ echo up; }}
workbenches_runtime_docker() {{ printf '%s' "$RECORD"; }}
RECORD={record!r}
workbenches_managed_state sample {role}'''), expected)

    def test_missing_is_distinct_from_inspect_failure(self):
        for error, expected in (('Error: No such container: sample', 'missing'), ('permission denied', 'down')):
            with self.subTest(error=error):
                self.assertEqual(self.shell(f'''workbenches_docker_state() {{ echo up; }}
workbenches_runtime_docker() {{ echo {error!r} >&2; return 1; }}
workbenches_managed_state sample tools'''), expected)

    def test_foreign_name_never_causes_build_stop_or_delete(self):
        for role in ('tools', 'vault'):
            output = self.shell(f'''workbenches_docker_state() {{ echo up; }}
workbenches_pin_docker() {{ :; }}
workbenches_runtime_docker() {{
    if [[ "$1 $2" == 'container inspect' ]]; then echo 'foreign|0|fingerprint|/somewhere'; return; fi
    echo "UNEXPECTED:$*"; return 99
}}
workbenches_{role}_start && exit 20
:''')
            self.assertNotIn('UNEXPECTED', output)

    def test_remote_engine_is_rejected(self):
        self.assertEqual(self.shell('DOCKER_HOST=tcp://remote:2376; unset DOCKER_CONTEXT; workbenches_pin_docker && exit 20; echo rejected'), 'rejected')

    def test_desktop_tools_use_platform_socket_group_and_agent_mount(self):
        for system, distro, expected_group, has_agent in (
            ('Linux', 'Ubuntu', '1001', True),
            ('Darwin', '', '0', True),
            ('Linux', 'Ubuntu', '1001', False),
        ):
            with (self.subTest(system=system, has_agent=has_agent),
                  tempfile.TemporaryDirectory() as home,
                  socket.socket(socket.AF_UNIX) as agent):
                agent_path = Path(home) / 'agent.sock'
                if has_agent:
                    agent.bind(str(agent_path))
                else:
                    agent_path.mkdir()
                output = self.shell(f'''
HOME={home!r}; XDG_CACHE_HOME="$HOME/.cache"
WSL_DISTRO_NAME={distro!r}; SSH_AUTH_SOCK={str(agent_path)!r}
workbenches_docker_state() {{ echo up; }}
workbenches_pin_docker() {{ WORKBENCHES_DOCKER_ENDPOINT=unix:///var/run/docker.sock; }}
workbenches_tools_fingerprint() {{ echo runtime; }}
workbenches_tools_image_fingerprint() {{ echo image; }}
workbenches_services_network() {{ :; }}
workbenches_tools_state() {{ echo up; }}
uname() {{ echo {system}; }}
stat() {{ echo 1001; }}
workbenches_runtime_docker() {{
    case "$1 $2" in
        'container inspect') return 1 ;;
        'image inspect') echo image ;;
        'info --format')
            if [[ "$3" == *OperatingSystem* ]]; then echo 'Docker Desktop'; else echo engine; fi ;;
        'create --name')
            while [[ $# -gt 0 ]]; do
                case "$1:$2" in
                    --group-add:*) echo "socket-group:$2" >&2 ;;
                    --mount:*agent.sock*|--mount:*ssh-auth.sock*|--env:SSH_AUTH_SOCK=*)
                        echo "$2" >&2 ;;
                esac
                shift
            done ;;
        'container start') : ;;
        'exec '*) echo engine ;;
        *) echo "UNEXPECTED:$*" >&2; return 99 ;;
    esac
}}
workbenches_tools_start 2>&1
''')
                expected = [f'socket-group:{expected_group}']
                if has_agent:
                    source = agent_path if distro else '/run/host-services/ssh-auth.sock'
                    target = '/run/workbenches-ssh-agent.sock'
                    expected.extend([f'type=bind,src={source},dst={target}',
                                     f'SSH_AUTH_SOCK={target}'])
                self.assertEqual(output.splitlines(), expected)

    def test_launcher_finishes_when_broker_ignores_term(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            scripts = home / 'repo/scripts'
            (scripts / 'lib').mkdir(parents=True)
            shutil.copy(ROOT / 'scripts/tools-command.sh', scripts / 'tools-command.sh')
            (scripts / 'lib/tools-container.sh').write_text('''workbenches_tools_state() { echo up; }
workbenches_tools_configuration_matches() { return 0; }
workbenches_runtime_docker() { :; }
''')
            (scripts / 'lib/tools-host-broker.sh').write_text('''trap '' TERM
touch "$1/alive"
printf '%s' "$$" > "$HOME/broker-pid"
while :; do sleep 0.05; done
''')
            env = dict(os.environ, HOME=str(home), XDG_CACHE_HOME=str(home / '.cache'),
                       WORKBENCHES_TOOLS_ROOT=str(scripts.parent), WORKBENCHES_TOOLS_CONTAINER='fixture')
            result = subprocess.run(['bash', str(scripts / 'tools-command.sh'), 'python3', '--version'],
                                    env=env, capture_output=True, text=True, timeout=6)
            self.assertEqual(result.returncode, 0, result.stderr)
            with self.assertRaises(ProcessLookupError):
                os.kill(int((home / 'broker-pid').read_text()), 0)
            self.assertFalse(list((home / '.cache/workbenches/tools/sessions').iterdir()))


if __name__ == '__main__':
    unittest.main()

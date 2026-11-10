#!/usr/bin/env python3
"""Wave reconciliation against disposable settings and a fake Docker inventory."""

import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONNECTION = 'wsl://Ubuntu'
INVENTORY = (
    'pyBench\tinstalled\nflutterBench\tneeds setup\ncppBench\tneeds setup\n'
    'rustBench\tneeds setup\ncloudBench\tneeds setup'
)


def widget(meta, **fields):
    return {'blockdef': {'meta': meta}, **fields}


class WaveWidgetSyncTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.config = self.home / 'Wave config'
        self.config.mkdir()
        self.widgets = self.config / 'widgets.json'
        self.connections = self.config / 'connections.json'
        self.projects = self.home / 'Projects with spaces'
        self.projects.mkdir()
        binaries = self.home / 'bin'
        binaries.mkdir()
        self.wrapper(binaries / 'python3', f'''
if [[ "$1" == */setup-components.py ]]; then
    printf '%s\\n' "$TEST_INVENTORY"
else
    exec {shlex.quote(sys.executable)} "$@"
fi
''')
        installer = self.home / 'installer/scripts/install-workbenches-widgets.sh'
        installer.parent.mkdir(parents=True)
        self.wrapper(installer, '''
while [[ "$1" != --waveterm-config ]]; do shift; done
if [[ -n "$TEST_CONCURRENT_WRITE" ]]; then
    printf '%s\\n' '{"saved-by-wave": true}' > "$WAVETERM_CONFIG_DIR/widgets.json"
fi
printf '%s\\n' "$TEST_TEMPLATES" > "$2/widgets.json"
''')
        self.wrapper(binaries / 'mv', f'''
if [[ "$*" == *'/widgets.json' ]]; then
    if [[ -n "$TEST_FAIL_WIDGET_WRITE" ]]; then exit 1; fi
    if [[ -n "$TEST_PUBLICATION_WRITE" ]]; then
        printf '%s\\n' '{{"saved-by-wave": true}}' > "$WAVETERM_CONFIG_DIR/widgets.json"
    fi
fi
exec {shlex.quote(shutil.which('mv'))} "$@"
''')
        self.wrapper(binaries / 'ln', f'''
if [[ -n "$TEST_RECREATE_WIDGET" && "$*" == *'/widgets.json' ]]; then
    printf '%s\\n' '{{"saved-by-wave": "after-claim"}}' > "$WAVETERM_CONFIG_DIR/widgets.json"
fi
exec {shlex.quote(shutil.which('ln'))} "$@"
''')
        self.wrapper(binaries / 'grep', f'''
if [[ -n "$TEST_NATIVE" && "$*" == '-qi microsoft /proc/version' ]]; then exit 1; fi
exec {shlex.quote(shutil.which('grep'))} "$@"
''')
        self.env = dict(os.environ, PATH=f'{binaries}:{os.environ["PATH"]}',
                        HOME=str(self.home), WAVETERM_CONFIG_DIR=str(self.config),
                        WAVE_PROJECTS_ROOT=str(self.projects), WAVE_WSL_CONNECTION=CONNECTION,
                        WAVE_TERMINAL_INSTALLER_DIR=str(installer.parents[1]),
                        WORKBENCHES_SKIP_WAVE_WIDGETS='0', TEST_INVENTORY=INVENTORY,
                        TEST_CONCURRENT_WRITE='', TEST_FAIL_WIDGET_WRITE='',
                        TEST_PUBLICATION_WRITE='', TEST_RECREATE_WIDGET='',
                        TEST_NATIVE='',
                        TEST_TEMPLATES=json.dumps({
                            'defwidget@terminal': widget({'term:fontsize': 16}),
                            'projects': widget({}, description='Open the WSL projects directory'),
                            'pyBench': widget({'term:fontsize': 16}),
                        }))

    @staticmethod
    def wrapper(path, body):
        path.write_text('#!/usr/bin/env bash\n' + body)
        path.chmod(0o700)

    def sync(self, **overrides):
        return subprocess.run(['bash', str(ROOT / 'scripts/sync-wave-widgets.sh')],
                              env=dict(self.env, **overrides), stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=10)

    def test_reconciles_owned_widgets_and_is_idempotent(self):
        old_cloud = widget({'cmd:initscript': 'exec /old/scripts/wave-container-shell.sh '
                            '--workbenches-root /old --title cloudBench cloudBench'})
        custom = widget({'cmd:initscript': 'echo hello'})
        self.widgets.write_text(json.dumps({
            'defwidget@terminal': widget({'term:fontsize': 20}),
            'projects': widget({}, description='Open the WSL projects directory'),
            'cloudBench': old_cloud,
            'rustBench': custom,
            'custom': {'label': 'Keep me'},
        }))
        self.connections.write_text(json.dumps({CONNECTION: {'custom-setting': 1},
                                                'ssh://elsewhere': {'setting': 2}}))
        result = self.sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        widgets = json.loads(self.widgets.read_text())
        self.assertNotIn('cloudBench', widgets)
        self.assertEqual(widgets['rustBench'], custom)
        self.assertEqual(widgets['custom'], {'label': 'Keep me'})
        self.assertEqual(widgets['defwidget@terminal']['blockdef']['meta']['term:fontsize'], 20)
        # The reconciler publishes the canonical path; macOS temp paths may
        # start with the /var symlink rather than /private/var.
        self.assertEqual(widgets['projects']['blockdef']['meta']['file'], str(self.projects.resolve()))
        self.assertEqual(widgets['pyBench']['blockdef']['meta']['cmd:cwd'], str(ROOT))
        self.assertEqual(json.loads(self.connections.read_text()), {
            CONNECTION: {'custom-setting': 1, 'conn:wshenabled': True},
            'ssh://elsewhere': {'setting': 2},
        })
        inodes = (self.widgets.stat().st_ino, self.connections.stat().st_ino)
        self.assertEqual(self.sync().returncode, 0)
        self.assertEqual((self.widgets.stat().st_ino, self.connections.stat().st_ino), inodes)

    def test_preserves_a_custom_projects_widget(self):
        custom_projects = widget({'file': str(self.home / 'Personal projects')},
                                 description='My own projects')
        self.widgets.write_text(json.dumps({'projects': custom_projects}))
        result = self.sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        widgets = json.loads(self.widgets.read_text())
        self.assertEqual(widgets['projects'], custom_projects)
        self.assertIn('pyBench', widgets)

    def test_concurrent_edit_aborts_before_either_file_is_published(self):
        self.widgets.write_text('{}')
        self.connections.write_text('{}')
        result = self.sync(TEST_CONCURRENT_WRITE='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('changed during setup', result.stderr)
        self.assertEqual(json.loads(self.widgets.read_text()), {'saved-by-wave': True})
        self.assertEqual(self.connections.read_text(), '{}')

    def test_legacy_installer_commands_are_updated_or_removed(self):
        self.widgets.write_text(json.dumps({
            'pyBench': widget({'cmd:initscript':
                               'exec /old/scripts/wave-container-shell.sh --title pyBench py-bench'}),
            'cloudBench': widget({'cmd:initscript':
                                  'exec /old/scripts/wave-container-shell.sh --title cloudBench cloudBench'}),
        }))
        result = self.sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        widgets = json.loads(self.widgets.read_text())
        self.assertNotIn('cloudBench', widgets)
        args = shlex.split(widgets['pyBench']['blockdef']['meta']['cmd:initscript'])
        self.assertEqual(args[1:4], [str(ROOT / 'scripts/wave-container-shell.sh'),
                                    '--workbenches-root', str(ROOT)])

    def test_native_default_uses_local_connection(self):
        self.connections.write_text('{"ssh://custom": {"keep": true}}')
        result = self.sync(WAVE_WSL_CONNECTION='', WSL_DISTRO_NAME='', TEST_NATIVE='1')
        self.assertEqual(result.returncode, 0, result.stderr)
        widgets = json.loads(self.widgets.read_text())
        for key in ('defwidget@terminal', 'projects', 'pyBench'):
            self.assertEqual(widgets[key]['blockdef']['meta']['connection'], '')
        self.assertEqual(self.connections.read_text(), '{"ssh://custom": {"keep": true}}')

    def test_native_gui_bundle_without_path_launcher_is_discovered(self):
        (self.home / 'Applications/Wave.app').mkdir(parents=True)
        result = self.sync(WAVETERM_CONFIG_DIR='', WAVE_WSL_CONNECTION='',
                           WSL_DISTRO_NAME='', TEST_NATIVE='1')
        self.assertEqual(result.returncode, 0, result.stderr)
        widgets = json.loads((self.home / '.config/waveterm/widgets.json').read_text())
        self.assertEqual(widgets['defwidget@terminal']['blockdef']['meta']['connection'], '')

    def test_widget_write_failure_preserves_old_widgets_and_can_retry(self):
        self.widgets.write_text('{"custom": true}')
        result = self.sync(TEST_FAIL_WIDGET_WRITE='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.widgets.read_text(), '{"custom": true}')
        self.assertIs(json.loads(self.connections.read_text())[CONNECTION]['conn:wshenabled'], True)
        self.assertEqual(self.sync().returncode, 0)
        self.assertIn('pyBench', json.loads(self.widgets.read_text()))

    def test_save_between_comparison_and_claim_is_restored_and_reported(self):
        self.widgets.write_text('{"custom": true}')
        result = self.sync(TEST_PUBLICATION_WRITE='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('changed during publication', result.stderr)
        self.assertEqual(json.loads(self.widgets.read_text()), {'saved-by-wave': True})
        backup = list(self.config.glob('.openbenches-settings-backup.*/widgets.json'))
        self.assertEqual(len(backup), 1)
        self.assertEqual(backup[0].read_bytes(), self.widgets.read_bytes())

    def test_save_after_claim_is_not_overwritten(self):
        original = '{"custom": true}'
        self.widgets.write_text(original)
        result = self.sync(TEST_RECREATE_WIDGET='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(self.widgets.read_text()), {'saved-by-wave': 'after-claim'})
        backup = list(self.config.glob('.openbenches-settings-backup.*/widgets.json'))
        self.assertEqual(len(backup), 1)
        self.assertEqual(backup[0].read_text(), original)

    def test_unknown_inventory_and_held_lock_leave_settings_alone(self):
        self.widgets.write_text('{}')
        self.assertEqual(self.sync(TEST_INVENTORY='pyBench\tneeds docker').returncode, 0)
        lock = self.config / '.openbenches-widget-sync.lock'
        lock.mkdir()
        self.assertNotEqual(self.sync().returncode, 0)
        self.assertTrue(lock.is_dir())
        self.assertEqual(self.widgets.read_text(), '{}')
        self.assertFalse(self.connections.exists())

    def test_refuses_an_invalid_selected_connection_without_writes(self):
        widgets = '{"custom": {"label": "Keep me"}}\n'
        connections = json.dumps({CONNECTION: "not a settings object", 'ssh://custom': {}})
        self.widgets.write_text(widgets)
        self.connections.write_text(connections)
        result = self.sync()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f'Wave connection {CONNECTION} must contain a JSON object', result.stderr)
        self.assertEqual(self.widgets.read_text(), widgets)
        self.assertEqual(self.connections.read_text(), connections)

    def test_refuses_non_object_settings_without_writes(self):
        for name in ('widgets.json', 'connections.json'):
            for content in ('[]\n', 'null\n', '"not an object"\n'):
                with self.subTest(name=name, content=content):
                    self.widgets.write_text('{}\n')
                    self.connections.write_text('{}\n')
                    path = self.config / name
                    path.write_text(content)
                    before = (self.widgets.read_bytes(), self.connections.read_bytes())
                    result = self.sync()
                    self.assertNotEqual(result.returncode, 0, result.stderr)
                    self.assertIn('must contain a JSON object', result.stderr)
                    self.assertEqual((self.widgets.read_bytes(), self.connections.read_bytes()), before)

    def test_refuses_symlinked_connections_without_touching_the_target(self):
        original = json.dumps({CONNECTION: {'custom-setting': True}}) + '\n'
        target = self.home / 'external-connections.json'
        target.write_text(original)
        self.connections.symlink_to(target)
        self.widgets.write_text('{"custom": true}\n')
        result = self.sync()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Refusing to replace Wave settings', result.stderr)
        self.assertTrue(self.connections.is_symlink())
        self.assertEqual(target.read_text(), original)
        self.assertEqual(self.widgets.read_text(), '{"custom": true}\n')

    def test_explicit_skip_preserves_settings_without_creating_a_lock(self):
        self.widgets.write_text('{"custom": true}\n')
        self.connections.write_text('{"ssh://custom": {}}\n')
        before = (self.widgets.read_bytes(), self.connections.read_bytes())
        result = self.sync(WORKBENCHES_SKIP_WAVE_WIDGETS='1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('skipped by WORKBENCHES_SKIP_WAVE_WIDGETS=1', result.stdout)
        self.assertEqual((self.widgets.read_bytes(), self.connections.read_bytes()), before)
        self.assertFalse((self.config / '.openbenches-widget-sync.lock').exists())

    def test_refuses_a_directory_at_either_settings_path(self):
        for name in ('widgets.json', 'connections.json'):
            with self.subTest(name=name):
                self.widgets.write_text('{}\n')
                self.connections.write_text('{}\n')
                path = self.config / name
                other = self.connections if name == 'widgets.json' else self.widgets
                path.unlink()
                path.mkdir()
                marker = path / 'keep.txt'
                marker.write_text('keep this directory')
                result = self.sync()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Refusing to replace Wave settings', result.stderr)
                self.assertEqual(marker.read_text(), 'keep this directory')
                self.assertEqual(other.read_text(), '{}\n')
                marker.unlink()
                path.rmdir()

    def test_preserves_existing_settings_permissions_when_publishing(self):
        self.widgets.write_text('{}\n')
        self.connections.write_text('{}\n')
        self.widgets.chmod(0o640)
        self.connections.chmod(0o600)
        result = self.sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('pyBench', json.loads(self.widgets.read_text()))
        self.assertTrue(json.loads(self.connections.read_text())[CONNECTION]['conn:wshenabled'])
        self.assertEqual(self.widgets.stat().st_mode & 0o777, 0o640)
        self.assertEqual(self.connections.stat().st_mode & 0o777, 0o600)

    def test_initializes_empty_settings_files(self):
        self.widgets.write_text('')
        self.connections.write_text('')
        result = self.sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        widgets = json.loads(self.widgets.read_text())
        self.assertIn('pyBench', widgets)
        self.assertEqual(widgets['projects']['blockdef']['meta']['file'], str(self.projects.resolve()))
        self.assertTrue(json.loads(self.connections.read_text())[CONNECTION]['conn:wshenabled'])

    def test_incomplete_installer_template_preserves_both_settings(self):
        self.widgets.write_text('{"custom": {"label": "Keep me"}}\n')
        self.connections.write_text('{"ssh://custom": {}}\n')
        before = (self.widgets.read_bytes(), self.connections.read_bytes())
        templates = json.loads(self.env['TEST_TEMPLATES'])
        del templates['pyBench']
        result = self.sync(TEST_TEMPLATES=json.dumps(templates))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Wave installer did not supply widget pyBench', result.stderr)
        self.assertEqual((self.widgets.read_bytes(), self.connections.read_bytes()), before)

    def test_duplicate_connection_keys_preserve_both_settings(self):
        self.widgets.write_text('{"custom": true}\n')
        self.connections.write_text('{"ssh://custom": {}, "ssh://custom": {"keep": true}}\n')
        before = (self.widgets.read_bytes(), self.connections.read_bytes())
        result = self.sync()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('duplicate JSON key: ssh://custom', result.stderr)
        self.assertEqual((self.widgets.read_bytes(), self.connections.read_bytes()), before)

    def test_invalid_or_symlinked_settings_are_preserved(self):
        self.widgets.write_text('{"custom": 1, "custom": 2}')
        self.assertNotEqual(self.sync().returncode, 0)
        self.assertEqual(self.widgets.read_text(), '{"custom": 1, "custom": 2}')
        target = self.home / 'other.json'
        self.widgets.rename(target)
        self.widgets.symlink_to(target)
        self.assertNotEqual(self.sync().returncode, 0)
        self.assertTrue(self.widgets.is_symlink())
        self.assertFalse(self.connections.exists())


if __name__ == '__main__':
    unittest.main()

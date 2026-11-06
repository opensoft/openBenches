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
if [[ -n "$TEST_FAIL_WIDGET_WRITE" && "$*" == *'/widgets.json' ]]; then exit 1; fi
exec {shlex.quote(shutil.which('mv'))} "$@"
''')
        self.env = dict(os.environ, PATH=f'{binaries}:{os.environ["PATH"]}',
                        HOME=str(self.home), WAVETERM_CONFIG_DIR=str(self.config),
                        WAVE_PROJECTS_ROOT=str(self.projects), WAVE_WSL_CONNECTION=CONNECTION,
                        WAVE_TERMINAL_INSTALLER_DIR=str(installer.parents[1]),
                        WORKBENCHES_SKIP_WAVE_WIDGETS='0', TEST_INVENTORY=INVENTORY,
                        TEST_CONCURRENT_WRITE='', TEST_FAIL_WIDGET_WRITE='',
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
        self.assertEqual(widgets['projects']['blockdef']['meta']['file'], str(self.projects))
        self.assertEqual(widgets['pyBench']['blockdef']['meta']['cmd:cwd'], str(ROOT))
        self.assertEqual(json.loads(self.connections.read_text()), {
            CONNECTION: {'custom-setting': 1, 'conn:wshenabled': True},
            'ssh://elsewhere': {'setting': 2},
        })
        inodes = (self.widgets.stat().st_ino, self.connections.stat().st_ino)
        self.assertEqual(self.sync().returncode, 0)
        self.assertEqual((self.widgets.stat().st_ino, self.connections.stat().st_ino), inodes)

    def test_concurrent_edit_aborts_before_either_file_is_published(self):
        self.widgets.write_text('{}')
        self.connections.write_text('{}')
        result = self.sync(TEST_CONCURRENT_WRITE='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('changed during setup', result.stderr)
        self.assertEqual(json.loads(self.widgets.read_text()), {'saved-by-wave': True})
        self.assertEqual(self.connections.read_text(), '{}')

    def test_widget_write_failure_preserves_old_widgets_and_can_retry(self):
        self.widgets.write_text('{"custom": true}')
        result = self.sync(TEST_FAIL_WIDGET_WRITE='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.widgets.read_text(), '{"custom": true}')
        self.assertIs(json.loads(self.connections.read_text())[CONNECTION]['conn:wshenabled'], True)
        self.assertEqual(self.sync().returncode, 0)
        self.assertIn('pyBench', json.loads(self.widgets.read_text()))

    def test_unknown_inventory_and_held_lock_leave_settings_alone(self):
        self.widgets.write_text('{}')
        self.assertEqual(self.sync(TEST_INVENTORY='pyBench\tneeds docker').returncode, 0)
        lock = self.config / '.openbenches-widget-sync.lock'
        lock.mkdir()
        self.assertNotEqual(self.sync().returncode, 0)
        self.assertTrue(lock.is_dir())
        self.assertEqual(self.widgets.read_text(), '{}')
        self.assertFalse(self.connections.exists())

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

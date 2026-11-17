import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

def jwt(email):
    body = base64.urlsafe_b64encode(json.dumps({'email': email}).encode()).decode().rstrip('=')
    return 'fixture.' + body + '.fixture'

class AccountBinding(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.home = self.base / 'home'
        self.home.mkdir()
        self.profiles = self.base / 'profiles'
        self.selected = self.profiles / 'profiles/test/team-002'
        self.selected.mkdir(parents=True)
        self.manifest = self.base / 'profiles.json'
        self.manifest.write_text(json.dumps({'profiles': [
            {'name': 'team-002', 'email': 'team-002@example.invalid', 'family': 'test',
             'aliases': ['team002'], 'profilePath': 'test/team-002'},
            {'name': 'max-001', 'email': 'max-001@example.invalid', 'family': 'test',
             'aliases': ['max001'], 'profilePath': 'test/max-001'}]}))
        self.auth('team-002@example.invalid')
        self.log = self.base / 'provider.json'
        self.fake = self.base / 'codex'
        self.fake.write_text('''#!/usr/bin/env python3
import json, os, subprocess, sys
child = subprocess.check_output([sys.executable, '-c', 'import os;print(os.environ.get("CODEX_HOME", ""))'], text=True).strip()
with open(os.environ['PROVIDER_LOG'], 'w') as out:
 json.dump({'home':os.environ.get('CODEX_HOME'), 'profile':os.environ.get('CODEX_PROFILE_NAME'), 'api_key':bool(os.environ.get('OPENAI_API_KEY')), 'access_override':bool(os.environ.get('CODEX_ACCESS_TOKEN')), 'child_home':child, 'args':sys.argv[1:]}, out)
sys.exit(int(os.environ.get('PROVIDER_EXIT', '0')))
''')
        self.fake.chmod(0o755)
        self.env = dict(os.environ)
        for key in list(self.env):
            if key.startswith(('CODEX_', 'CHATGPT_', 'CLAUDE_', 'WORKBENCHES_CLAUDE_', 'LANES_')):
                self.env.pop(key)
        self.env.update(HOME=str(self.home), CODEX_BIN=str(self.fake), CODEX_PROFILES_HOME=str(self.profiles),
                        CODEX_PROFILES_MANIFEST=str(self.manifest), PROVIDER_LOG=str(self.log),
                        WORKBENCHES_SHARED_MCP_FAMILIES='none', WORKBENCHES_DISABLE_DEFAULT_VIBE_MCP='1',
                        CODEX_HOME=str(self.home / '.codex'))

    def auth(self, email):
        (self.selected / 'auth.json').write_text(json.dumps({'auth_mode': 'chatgpt',
            'tokens': {'id_token': jwt(email), 'access_token': jwt(email)}}))

    def run_exec(self, args=('task with spaces',), **env):
        return subprocess.run([str(ROOT / 'base-image/files/codex-exec'), *args],
                              env=dict(self.env, **env), text=True, capture_output=True)

    def refused(self, **env):
        result = self.run_exec(**env)
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.log.exists(), result.stderr)

    def test_missing_selection_refuses_default_home(self):
        self.refused()

    def test_unknown_profile_refuses(self):
        self.refused(CLAUDE_PROFILE_NAME='unconfigured')

    def test_missing_credentials_refuse(self):
        (self.selected / 'auth.json').unlink()
        self.refused(CLAUDE_PROFILE_NAME='team-002')

    def test_mismatched_credentials_refuse(self):
        self.auth('max-001@example.invalid')
        self.refused(CLAUDE_PROFILE_NAME='team-002')

    def test_malformed_credentials_refuse(self):
        (self.selected / 'auth.json').write_text('{}')
        self.refused(CLAUDE_PROFILE_NAME='team-002')

    def test_selected_lane_overrides_stale_home_and_children_inherit(self):
        result = self.run_exec(CLAUDE_PROFILE_NAME='team-002')
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(self.log.read_text())
        self.assertEqual(record['home'], str(self.selected))
        self.assertEqual(record['child_home'], str(self.selected))
        self.assertEqual(record['profile'], 'team-002')

    def test_alias_arguments_exit_and_api_environment(self):
        result = self.run_exec(('exec', '--json', 'task with "quotes" and spaces'),
                               CODEX_PROFILE_NAME='team002', PROVIDER_EXIT='23',
                               OPENAI_API_KEY='fixture-key', CODEX_ACCESS_TOKEN='fixture-token')
        self.assertEqual(result.returncode, 23, result.stderr)
        record = json.loads(self.log.read_text())
        self.assertEqual(record['args'][-3:], ['exec', '--json', 'task with "quotes" and spaces'])
        self.assertFalse(record['api_key'])
        self.assertFalse(record['access_override'])
        self.assertIn('forced_login_method="chatgpt"', record['args'])
        self.assertIn('cli_auth_credentials_store="file"', record['args'])

    def test_explicit_max001_is_supported(self):
        selected = self.profiles / 'profiles/test/max-001'
        selected.mkdir()
        (selected / 'auth.json').write_text(json.dumps({'tokens': {
            'id_token': jwt('max-001@example.invalid'), 'access_token': jwt('max-001@example.invalid')}}))
        result = self.run_exec(CODEX_PROFILE_NAME='max001')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.log.read_text())['home'], str(selected))

    def test_offline_home_resolution_does_not_start_provider(self):
        result = subprocess.run([str(ROOT / 'base-image/files/codex-profile'), 'home', 'team002'],
                                env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(self.selected))
        self.assertFalse(self.log.exists())

    def test_claude_launch_resets_stale_selected_codex_account(self):
        claude_base = self.base / 'claude-profiles'
        (claude_base / 'profiles/test/team-002').mkdir(parents=True)
        fake_claude = self.base / 'claude'
        fake_claude.write_text('''#!/usr/bin/env python3
import json,os,sys
if '--version' in sys.argv:
 print('2.1.326 (Claude Code)')
else:
 with open(os.environ['PROVIDER_LOG'],'w') as out:
  json.dump({key:os.environ.get(key) for key in ['CODEX_HOME','CODEX_PROFILE_NAME','CLAUDE_PROFILE_NAME']},out)
''')
        fake_claude.chmod(0o755)
        # Provider registries can choose different directory layouts.
        custom_home = self.profiles / 'profiles/custom/team-002'
        custom_home.mkdir(parents=True)
        manifest = json.loads(self.manifest.read_text())
        claude_manifest = self.base / 'claude.json'
        claude_manifest.write_text(json.dumps(manifest))
        manifest['profiles'][0]['profilePath'] = 'custom/team-002'
        self.manifest.write_text(json.dumps(manifest))
        fake_bin = self.base / 'bin'
        fake_bin.mkdir()
        (fake_bin / 'codex-profile').symlink_to(ROOT / 'base-image/files/codex-profile')
        env = dict(self.env, CLAUDE_BIN=str(fake_claude), CLAUDE_PROFILES_HOME=str(claude_base),
                   CLAUDE_PROFILES_MANIFEST=str(claude_manifest), CODEX_PROFILE_NAME='max-001',
                   PATH=str(fake_bin) + os.pathsep + self.env['PATH'],
                   WORKBENCHES_CLAUDE_CURRENT_BIN=str(self.base / 'not-installed'), TMUX='fixture')
        result = subprocess.run([str(ROOT / 'base-image/files/claude-profile'), '--no-lane',
                                 'run', 'team002', '-p', 'fixture'], env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(self.log.read_text())
        self.assertEqual(record['CODEX_PROFILE_NAME'], 'team-002')
        self.assertEqual(record['CODEX_HOME'], str(custom_home))

if __name__ == '__main__':
    unittest.main()

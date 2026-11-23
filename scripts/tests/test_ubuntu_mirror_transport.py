"""Offline tests of the exact shared-image Ubuntu mirror normalization block."""
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
START = '# BEGIN official Ubuntu HTTPS mirrors'
END = '# END official Ubuntu HTTPS mirrors'


class UbuntuMirrorTransportTests(unittest.TestCase):
    def script(self, root):
        dockerfile = (ROOT / 'base-image' / 'Dockerfile').read_text()
        self.assertIn(START, dockerfile)
        block = dockerfile.split(START, 1)[1].split(END, 1)[0].strip()
        self.assertTrue(block.startswith('RUN '))
        script = block[4:].replace('\\\n', '\n')
        return script.replace('/etc/apt', str(root))

    def normalize(self, files, twice=False):
        with tempfile.TemporaryDirectory(prefix='ubuntu-mirrors-') as tmp:
            root = Path(tmp)
            (root / 'sources.list.d').mkdir()
            for name, content in files.items():
                (root / name).write_text(content)
            command = self.script(root)
            subprocess.run(['sh', '-c', command], check=True, capture_output=True, text=True)
            if twice:
                subprocess.run(['sh', '-c', command], check=True, capture_output=True, text=True)
            return {str(p.relative_to(root)): p.read_text() for p in root.rglob('*') if p.is_file()}

    def test_deb822_preserves_suite_components_and_keys(self):
        before = 'Types: deb\nURIs: http://archive.ubuntu.com/ubuntu/ http://security.ubuntu.com/ubuntu/\nSuites: noble noble-updates\nComponents: main universe\nSigned-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg\n'
        result = self.normalize({'sources.list.d/ubuntu.sources': before})
        self.assertEqual(result['sources.list.d/ubuntu.sources'], before.replace('http://', 'https://'))

    def test_legacy_and_ports_sources(self):
        before = 'deb http://ports.ubuntu.com/ubuntu-ports noble main\ndeb-src http://archive.ubuntu.com/ubuntu noble universe\n'
        self.assertEqual(self.normalize({'sources.list': before})['sources.list'], before.replace('http://', 'https://'))

    def test_custom_repositories_and_comments_are_unchanged(self):
        before = '# old http://archive.ubuntu.com/ubuntu\ndeb http://example.invalid/ubuntu noble main\ndeb http://archive.ubuntu.com.example.invalid/ubuntu noble main\ndeb https://archive.ubuntu.com/ubuntu noble main\n'
        self.assertEqual(self.normalize({'sources.list.d/custom.list': before})['sources.list.d/custom.list'], before)

    def test_missing_optional_sources_are_ignored(self):
        self.assertEqual(self.normalize({}), {})

    def test_repeated_normalization_is_idempotent(self):
        before = 'deb http://security.ubuntu.com/ubuntu noble-security main\n'
        self.assertEqual(self.normalize({'sources.list': before}, twice=True)['sources.list'], before.replace('http://', 'https://'))

    def test_trusted_bootstrap_precedes_transport_change(self):
        text = (ROOT / 'base-image' / 'Dockerfile').read_text()
        start = text.index(START)
        end = text.index(END, start)
        self.assertLess(text.index('    ca-certificates \\'), start)
        self.assertIn('test -s /etc/ssl/certs/ca-certificates.crt', text[start:end])
        self.assertLess(end, text.index('# DOCKER CLI & COMPOSE'))
        self.assertNotIn('Verify-Peer "false"', text[start:end])
        self.assertNotIn('--insecure', text[start:end])


if __name__ == '__main__':
    unittest.main()

"""Exercise real loopback HTTP admission against a synthetic OpenCode backend."""

import base64
from contextlib import contextmanager
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import sys
from tempfile import TemporaryDirectory
from threading import Event, Thread
import types
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

if sys.platform == "win32":
    sys.modules["fcntl"] = types.SimpleNamespace(LOCK_EX=1, flock=lambda *_: None)

from model_session_gate import SessionGate
import setup_profiles as profiles


AUTH = "Basic " + base64.b64encode(b"opencode:fixture-password").decode()
SOURCE = {"[opencode]": {"agents": {"sisyphus": {"ultrawork": {}}, "oracle": {}, "atlas": {}, "explore": {}},
                         "categories": {"quick": {}}}}
UPGRADE = {**profiles.OPENAI_MODELS, "sol": "gpt-6.10-sol"}


@contextmanager
def listening(server):
    with server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield server.server_port
        finally:
            server.shutdown()
            thread.join()


class Backend(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def route(self):
        fixture = self.server.fixture
        if self.headers.get("Authorization") != AUTH and self.headers.get("Cookie") != "session=fixture":
            self.send_error(401)
            return
        path = urlsplit(self.path).path
        fixture.calls.append((self.command, path))
        if path == "/api/location/reload":
            fixture.reloads += 1
            self.send_response(204)
            self.end_headers()
            return
        if path == "/api/event":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(b"data: fixture\n\n")
            fixture.release_stream.wait(5)
            return
        if path == "/api/pty/fixture/connect":
            self.send_response_only(101)
            self.send_header("Connection", "Upgrade")
            self.send_header("Upgrade", "websocket")
            self.end_headers()
            self.connection.sendall(self.rfile.read(4))
            return
        options = {
            "/api/info": {},
            "/api/model": {"data": [{"providerID": "openai", "id": model} for model in UPGRADE.values()]},
            "/api/session/active": {"data": fixture.active},
            "/api/experimental/job": {"data": fixture.jobs},
            "/api/debug/location": [{"directory": "/home/brett/project"}],
            "/api/shell": {"data": []},
            "/api/pty": {"data": [{"status": "exited"}]},
        }
        if path == "/api/agent":
            roster = json.loads((fixture.folder / ".omo/omo.jsonc").read_text())["[opencode]"]["agents"]
            data = [{"id": name, "model": item["model"]} for name, item in roster.items()]
            if fixture.failed_upgrade and fixture.reloads == 1:
                data[0]["model"] = "openai/gpt-6.2-sol"
            value = {"data": data}
        elif path == "/api/session":
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            value = {"created": body["location"]["directory"]}
        elif path == "/api/session/ses_fixture/prompt":
            fixture.prompt_entered.set()
            fixture.release_prompt.wait(5)
            value = {}
        else:
            value = options[path]
        response = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    do_GET = do_POST = route


class SessionGateTests(unittest.TestCase):
    @contextmanager
    def fixture(self):
        with TemporaryDirectory() as temp:
            self.folder = Path(temp)
            self.calls = []
            self.reloads = 0
            self.active = {}
            self.jobs = []
            self.failed_upgrade = False
            self.prompt_entered = Event()
            self.release_prompt = Event()
            self.release_stream = Event()
            profiles.write_profile(self.folder, "openai", SOURCE, profiles.OPENAI_MODELS)
            backend = ThreadingHTTPServer(("127.0.0.1", 0), Backend)
            backend.fixture = self
            with listening(backend) as port, patch.object(profiles, "OPENAI_BACKEND", port):
                updater = profiles.OpenAIModelUpdater(self.folder, SOURCE, "fixture-password", profiles.OPENAI_MODELS)
                with listening(SessionGate(("127.0.0.1", 0), port, updater.prepare)) as self.port:
                    yield updater

    def request(self, method, path, body=None, headers=None):
        client = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            client.request(method, path, body, {"Authorization": AUTH} if headers is None else headers)
            response = client.getresponse()
            return response.status, response.headers, response.read()
        finally:
            client.close()

    def create(self, headers=None):
        return self.request("POST", "/api/session", b'{"location":{"directory":"/home/brett/project"}}', headers)

    def test_updates_and_verifies_before_forwarding_first_new_session(self):
        with self.fixture() as updater:
            self.assertEqual(self.request("GET", "/api/info")[1]["X-OpenCode-Profile-Gate"], "openai")
            self.assertEqual(self.create({"Cookie": "session=fixture"})[0], 200)
            self.assertLess(self.calls.index(("POST", "/api/location/reload")), self.calls.index(("GET", "/api/agent")))
            self.assertLess(self.calls.index(("GET", "/api/agent")), self.calls.index(("POST", "/api/session")))
            self.assertEqual(updater.current, UPGRADE)
            self.assertEqual(self.create()[0], 200)
            self.assertEqual(self.reloads, 1)

    def test_active_work_defers_upgrade_and_later_session_can_retry(self):
        with self.fixture():
            self.active = {"ses_fixture": {"type": "running"}}
            self.assertEqual(self.create()[0], 503)
            self.active = {}
            self.jobs = [{"status": "running"}]
            self.assertEqual(self.create()[0], 503)
            self.jobs = []
            request = Thread(target=self.request, args=("POST", "/api/session/ses_fixture/prompt", b"{}"), daemon=True)
            request.start()
            try:
                self.assertTrue(self.prompt_entered.wait(2))
                self.assertEqual(self.create()[0], 503)
                self.assertEqual(self.reloads, 0)
            finally:
                self.release_prompt.set()
                request.join()
            self.assertEqual(self.create()[0], 200)

    def test_failed_readback_restores_profile_and_refuses_session(self):
        with self.fixture() as updater:
            self.failed_upgrade = True
            self.assertEqual(self.create()[0], 503)
            self.assertEqual(self.reloads, 2)
            self.assertEqual(updater.current, profiles.OPENAI_MODELS)
            self.assertFalse((self.folder / "openai-models.json").exists())
            self.assertNotIn(("POST", "/api/session"), self.calls)

    def test_unauthenticated_request_does_not_trigger_catalog_checks(self):
        with self.fixture():
            self.assertEqual(self.create({})[0], 401)
            self.assertEqual(self.calls, [])

    def test_event_stream_stays_open_during_an_idle_upgrade(self):
        with self.fixture():
            client = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
            try:
                client.request("GET", "/api/event", headers={"Authorization": AUTH})
                response = client.getresponse()
                self.assertEqual(response.readline(), b"data: fixture\n")
                self.assertEqual(self.create()[0], 200)
            finally:
                self.release_stream.set()
                client.close()

    def test_websocket_upgrade_reaches_backend(self):
        with self.fixture():
            with socket.create_connection(("127.0.0.1", self.port), timeout=5) as client:
                headers = (f"GET /api/pty/fixture/connect HTTP/1.1\r\nHost: 127.0.0.1:{self.port}\r\n"
                           f"Authorization: {AUTH}\r\nConnection: Upgrade\r\nUpgrade: websocket\r\n\r\n")
                client.sendall(headers.encode() + b"echo")
                with client.makefile("rb") as response:
                    self.assertIn(b"101", response.readline())
                    for line in response:
                        if line == b"\r\n":
                            break
                    self.assertEqual(response.read(4), b"echo")


if __name__ == "__main__":
    unittest.main()

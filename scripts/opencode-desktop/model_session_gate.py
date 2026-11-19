"""Loopback HTTP gate for the dedicated OpenAI Desktop server."""

from contextlib import closing, contextmanager
from http.client import HTTPConnection, HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from posixpath import normpath
import re
import select
import socket
from threading import Lock
from urllib.parse import unquote, urlsplit


HOP_HEADERS = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
               "proxy-connection", "te", "trailer", "transfer-encoding", "upgrade"}
FORK = re.compile(r"/api/session/[^/]+/fork")
READ_METHODS = {"GET", "HEAD", "OPTIONS"}


class SessionGate(ThreadingHTTPServer):
    def __init__(self, frontend, backend_port, prepare_session):
        super().__init__(frontend, DesktopRequest)
        self.backend_port = backend_port
        self.prepare_session = prepare_session
        self.admission = Lock()
        self.active_requests = 0

    @contextmanager
    def admit(self, create, payload, path):
        with self.admission:
            if create:
                self.prepare_session(payload, path, self.active_requests == 0)
            self.active_requests += 1
        try:
            yield
        finally:
            with self.admission:
                self.active_requests -= 1


class RetrySession(Exception):
    """Tell Desktop to retry creation while preserving its current session state."""


class DesktopRequest(BaseHTTPRequestHandler):
    # Keep the request stream unbuffered so WebSocket bytes remain on the socket.
    rbufsize = 0
    protocol_version = "HTTP/1.1"

    def log_message(self, *_):
        # Never log a Desktop URL, pairing ticket, session body or credential.
        pass

    def reply(self, status, message, retry=False):
        body = json.dumps({"message": message}).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        if retry:
            self.send_header("Retry-After", "3")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def filtered_headers(self, headers):
        connection = {entry.strip().lower() for value in headers.get_all("Connection", [])
                      for entry in value.split(",")}
        excluded = HOP_HEADERS | connection | {"expect"}
        return [(name, value) for name, value in headers.items() if name.lower() not in excluded]

    def authenticated(self):
        with closing(HTTPConnection("127.0.0.1", self.server.backend_port, timeout=5)) as upstream:
            headers = {name: self.headers[name] for name in ("Authorization", "Cookie", "Host")
                       if name in self.headers}
            headers["Accept"] = "application/json"
            upstream.request("GET", "/api/info", headers=headers)
            return upstream.getresponse().status == 200

    def proxy_http(self, body, gate_info=False):
        upstream = HTTPConnection("127.0.0.1", self.server.backend_port, timeout=15)
        try:
            upstream.putrequest(self.command, self.path, skip_host="Host" in self.headers, skip_accept_encoding=True)
            for name, value in self.filtered_headers(self.headers):
                if name.lower() != "content-length":
                    upstream.putheader(name, value)
            if body is not None or self.command not in READ_METHODS:
                upstream.putheader("Content-Length", str(len(body or b"")))
            upstream.putheader("Connection", "close")
            upstream.endheaders(body)
            # Long-running requests and idle SSE may wait indefinitely.
            upstream.sock.settimeout(None)
            response = upstream.getresponse()
            self.send_response_only(response.status, response.reason)
            for name, value in self.filtered_headers(response.headers):
                if name.lower() != "x-opencode-profile-gate":
                    self.send_header(name, value)
            if gate_info and response.status == 200:
                self.send_header("X-OpenCode-Profile-Gate", "openai")
            self.send_header("Connection", "close")
            self.end_headers()
            if self.command == "HEAD":
                return
            while chunk := response.read1(65536):
                self.wfile.write(chunk)
        finally:
            upstream.close()

    def proxy_websocket(self):
        with socket.create_connection(("127.0.0.1", self.server.backend_port), timeout=5) as upstream:
            upstream.settimeout(None)
            head = [self.requestline, *(f"{name}: {value}" for name, value in self.headers.items()), "", ""]
            upstream.sendall("\r\n".join(head).encode("iso-8859-1"))
            peers = {self.connection: upstream, upstream: self.connection}
            while True:
                ready, _, _ = select.select(peers, [], [])
                for source in ready:
                    chunk = source.recv(65536)
                    if not chunk:
                        return
                    peers[source].sendall(chunk)

    def forward(self):
        self.close_connection = True
        try:
            path = urlsplit(self.path)
            port = self.server.server_port
            if (path.netloc or path.scheme or not path.path.startswith("/") or
                    self.headers.get("Host", "") not in (f"127.0.0.1:{port}", f"localhost:{port}")):
                self.reply(400, "The profile accepts only its loopback address.")
                return
            if "Transfer-Encoding" in self.headers or len(self.headers.get_all("Content-Length", [])) > 1:
                self.reply(400, "Use one Content-Length for this local request.")
                return
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 64 * 1024 * 1024:
                self.reply(413, "The local request exceeds the profile limit.")
                return
            body = bytearray()
            while len(body) < length:
                chunk = self.rfile.read(min(length - len(body), 65536))
                if not chunk:
                    return
                body.extend(chunk)
            route = "/" + normpath(unquote(path.path)).lstrip("/")
            upgrade = self.command == "GET" and self.headers.get("Upgrade", "").lower() == "websocket"
            create = self.command == "POST" and (route == "/api/session" or FORK.fullmatch(route))
            if upgrade:
                with self.server.admit(False, None, path):
                    self.proxy_websocket()
            elif self.command in READ_METHODS:
                self.proxy_http(body, path.path == "/api/info")
            else:
                # Let OpenCode handle unauthenticated requests, without refreshing or applying models.
                create = bool(create and self.authenticated())
                with self.server.admit(create, body, path):
                    self.proxy_http(body)
        except RetrySession as error:
            self.reply(503, str(error), retry=True)
        except ValueError:
            self.reply(400, "Invalid local OpenCode request.")
        except (OSError, HTTPException):
            # Closing an interrupted stream is sufficient; appending an error body would corrupt it.
            pass

    do_GET = do_HEAD = do_OPTIONS = do_POST = do_PUT = do_PATCH = do_DELETE = forward

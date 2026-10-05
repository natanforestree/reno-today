import gzip
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import helpers  # noqa: F401  (puts collector/ on the path)
import net


class Handler(BaseHTTPRequestHandler):
    hits = {}
    posted = None
    posted_type = None

    def log_message(self, *args):
        pass

    def _send(self, status, body=b"", headers=()):
        self.send_response(status)
        for k, v in headers:
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        Handler.hits[path] = Handler.hits.get(path, 0) + 1
        if path == "/gzip":
            self._send(200, gzip.compress(b'{"ok": true}'), [("Content-Encoding", "gzip")])
        elif path == "/ua":
            self._send(200, self.headers.get("User-Agent", "").encode())
        elif path == "/flaky":
            self._send(503, b"oops") if Handler.hits[path] == 1 else self._send(200, b"fine")
        elif path.startswith("/missing"):
            self._send(404, b"nope")
        elif path == "/bad-json":
            self._send(200, b"{not json")
        else:
            self._send(500)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        Handler.posted = json.loads(self.rfile.read(length))
        Handler.posted_type = self.headers.get("Content-Type")
        self._send(204)


class NetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        net.RETRY_PAUSE = 0

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        Handler.hits = {}

    def test_decodes_gzip_json(self):
        self.assertEqual(net.get_json(self.base + "/gzip"), {"ok": True})

    def test_sends_our_user_agent(self):
        self.assertIn("github.com/natanforestree/reno-today", net.get_text(self.base + "/ua"))

    def test_retries_a_server_error_once(self):
        self.assertEqual(net.get_text(self.base + "/flaky"), "fine")
        self.assertEqual(Handler.hits["/flaky"], 2)

    def test_does_not_retry_a_client_error(self):
        with self.assertRaises(net.FetchError) as cm:
            net.get_text(self.base + "/missing")
        self.assertEqual(cm.exception.status, 404)
        self.assertEqual(Handler.hits["/missing"], 1)

    def test_bad_json_is_a_fetch_error(self):
        with self.assertRaises(net.FetchError):
            net.get_json(self.base + "/bad-json")

    def test_errors_never_include_the_query_string(self):
        with self.assertRaises(net.FetchError) as cm:
            net.get_text(self.base + "/missing?apikey=SECRET123")
        self.assertNotIn("SECRET123", str(cm.exception))
        self.assertIn("HTTP 404", str(cm.exception))

    def test_label_replaces_the_url_in_errors(self):
        with self.assertRaises(net.FetchError) as cm:
            net.get_text(self.base + "/missing/token-in-path", label="discord webhook")
        self.assertNotIn("token-in-path", str(cm.exception))
        self.assertIn("discord webhook", str(cm.exception))

    def test_unreachable_host_is_a_fetch_error(self):
        with self.assertRaises(net.FetchError) as cm:
            net.get_text("http://127.0.0.1:9/", timeout=2)
        self.assertIsNone(cm.exception.status)

    def test_post_json(self):
        self.assertEqual(net.post_json(self.base + "/hook", {"content": "hi"}), 204)
        self.assertEqual(Handler.posted, {"content": "hi"})
        self.assertEqual(Handler.posted_type, "application/json")


if __name__ == "__main__":
    unittest.main()

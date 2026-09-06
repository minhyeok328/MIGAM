from contextlib import closing
import io
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[2]


class LocalDeliveryTests(unittest.TestCase):
    def test_idle_browser_preconnection_does_not_block_next_request(self):
        import socket
        import threading
        from urllib.request import urlopen
        from wsgiref.simple_server import make_server
        from scripts.run_local_demo import DemoApplication, QuietRequestHandler, ThreadingDemoServer

        accepted = threading.Event()
        class ObservedHandler(QuietRequestHandler):
            def handle(self):
                accepted.set()
                super().handle()

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "index.html").write_text("demo page", encoding="utf-8")
            server = make_server("127.0.0.1", 0, DemoApplication(root, None),
                                 server_class=ThreadingDemoServer, handler_class=ObservedHandler)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                with socket.create_connection(server.server_address, timeout=2):
                    self.assertTrue(accepted.wait(2))
                    with urlopen(f"http://127.0.0.1:{server.server_port}/artworks", timeout=2) as response:
                        self.assertEqual(response.read(), b"demo page")
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=3)

    def test_keyless_web_api_smoke_preserves_existing_database_and_cleans_temporary_files(self):
        with TemporaryDirectory() as temporary:
            folder = Path(temporary)
            dist = folder / "dist"
            dist.mkdir()
            (dist / "index.html").write_text("<!doctype html><title>demo</title>", encoding="utf-8")
            database = folder / "existing.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("CREATE TABLE marker (value TEXT)")
                connection.execute("INSERT INTO marker VALUES ('preserved')")
                connection.commit()
            before = database.read_bytes()
            environment = {
                **os.environ,
                "MIGAM_DB_PATH": str(database),
                "TEMP": str(folder), "TMP": str(folder), "TMPDIR": str(folder),
                "VITE_KAKAO_JAVASCRIPT_KEY": "must-not-use-or-print",
            }
            result = subprocess.run([
                sys.executable, "-X", "utf8", str(ROOT / "scripts" / "run_local_demo.py"),
                "--dist", str(dist), "--port", "0", "--smoke-test",
            ], cwd=ROOT, env=environment, capture_output=True, text=True, encoding="utf-8", timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("Web, health and API smoke checks passed", result.stdout)
            self.assertNotIn("must-not-use-or-print", result.stdout + result.stderr)
            self.assertNotIn("GET /", result.stdout + result.stderr)
            self.assertEqual(database.read_bytes(), before)
            self.assertEqual(list(folder.glob("migam-local-demo-*")), [])

    def test_static_routes_do_not_expose_files_outside_the_demo_assets(self):
        from scripts.run_local_demo import DemoApplication

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            dist = root / "dist"
            dist.mkdir()
            (dist / "index.html").write_text("demo page", encoding="utf-8")
            (root / ".env").write_text("private-marker", encoding="utf-8")
            application = DemoApplication(dist, None)
            for path, expected in [
                ("/discover", "200"), ("/exhibitions/1", "200"),
                ("/artworks", "200"), ("/artworks/1", "200"),
                ("/../.env", "404"), ("/assets/missing.js", "404"),
                ("/admin/", "404"), ("/.env", "404"),
            ]:
                with self.subTest(path=path):
                    status = []
                    body = b"".join(application({
                        "PATH_INFO": path, "REQUEST_METHOD": "GET", "wsgi.input": io.BytesIO(),
                    }, lambda value, headers: status.append(value)))
                    self.assertTrue(status[0].startswith(expected), status)
                    self.assertNotIn(b"private-marker", body)

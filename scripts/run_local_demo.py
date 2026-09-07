"""Serve a keyless web build and real API against disposable fictional data."""

import argparse
import json
import mimetypes
import os
from pathlib import Path
import re
import shutil
import signal
from socketserver import ThreadingMixIn
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
from urllib.request import urlopen
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server


ROOT = Path(__file__).resolve().parents[1]
PAGE = re.compile(r"/(?:discover|taste|saved|compare|settings|artworks|(?:exhibitions|institutions|artworks)/[1-9][0-9]*)/?$")


class QuietRequestHandler(WSGIRequestHandler):
    timeout = 10

    def log_message(self, format, *args):
        pass


class ThreadingDemoServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True
    block_on_close = False

    def close_request(self, request):
        # Django connections are thread-local, including the health check path.
        from django.conf import settings
        if settings.configured:
            from django.db import connections
            connections.close_all()
        super().close_request(request)


class DemoApplication:
    def __init__(self, dist, api, *, mode="fictional-demo"):
        self.dist = Path(dist).resolve()
        self.api = api
        self.mode = mode

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "/")
        method = environ.get("REQUEST_METHOD", "GET")
        if path.startswith("/api/internal/v1/") and self.api is not None:
            return self.api(environ, start_response)
        if path == "/healthz" and method in {"GET", "HEAD"}:
            from django.db import connection

            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                status, body = "200 OK", json.dumps({"status": "ok", "mode": self.mode}).encode()
            except Exception:
                status, body = "503 Service Unavailable", b'{"status":"unavailable"}'
            finally:
                connection.close()
            start_response(status, [("Content-Type", "application/json"), ("Cache-Control", "no-store")])
            return [] if method == "HEAD" else [body]
        if method not in {"GET", "HEAD"}:
            start_response("405 Method Not Allowed", [("Allow", "GET, HEAD")])
            return [b"Method not allowed"]
        file = (self.dist / path.lstrip("/")).resolve()
        safe = file.is_relative_to(self.dist) and not any(
            part.startswith(".") for part in Path(path.replace("\\", "/")).parts if part != "/"
        )
        if not safe or path.startswith("/admin"):
            file = None
        elif not file.is_file():
            file = self.dist / "index.html" if path == "/" or PAGE.fullmatch(path) else None
        if file is None or not file.is_file():
            start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
            return [b"Not found"]
        content_type = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        start_response("200 OK", [
            ("Content-Type", content_type), ("Content-Length", str(file.stat().st_size)),
            ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff"),
            ("Referrer-Policy", "no-referrer"),
        ])
        if method == "HEAD":
            return []

        def contents():
            with file.open("rb") as stream:
                while chunk := stream.read(65536):
                    yield chunk

        return contents()


def build_assets(destination, *, mode="demo"):
    node = shutil.which("node")
    frontend = ROOT / "frontend"
    if node is None or not (frontend / "node_modules" / "vite" / "bin" / "vite.js").is_file():
        raise RuntimeError("Install Node.js 24.15+ and run npm ci --prefix frontend first.")
    environment = {key: value for key, value in os.environ.items() if not key.startswith("VITE_")}
    for script, arguments in [
        ("typescript/bin/tsc", ["--noEmit"]),
        ("vite/bin/vite.js", ["build", "--mode", mode, "--outDir", str(destination), "--emptyOutDir"]),
    ]:
        subprocess.run([node, str(frontend / "node_modules" / script), *arguments],
                       cwd=frontend, env=environment, check=True)


def smoke_check(origin):
    with urlopen(origin + "/", timeout=10) as response:
        if response.status != 200 or b"html" not in response.read().lower():
            raise RuntimeError("Web smoke check failed")
    with urlopen(origin + "/healthz", timeout=10) as response:
        if json.load(response).get("status") != "ok":
            raise RuntimeError("Health smoke check failed")
    with urlopen(origin + "/api/internal/v1/search/?type=EXHIBITION", timeout=10) as response:
        payload = json.load(response)
        if response.status != 200 or payload.get("total", 0) < 1:
            raise RuntimeError("API smoke check found no fictional exhibitions")
    print("Web, health and API smoke checks passed.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5181)
    parser.add_argument("--dist", type=Path, help="Use an existing demo-mode build instead of building")
    parser.add_argument("--container", action="store_true", help="Bind all container interfaces; publish loopback only")
    parser.add_argument("--smoke-test", action="store_true", help="Verify web and API, then shut down")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    if args.dist is not None and not (args.dist / "index.html").is_file():
        parser.error("--dist must contain a demo-mode index.html")
    sys.path.insert(0, str(ROOT))
    # The launcher owns both the SQLite and asset directories. Inherited database
    # settings and API keys cannot select a real database or enable collection.
    for key in tuple(os.environ):
        if key.startswith(("VITE_", "KAKAO_", "CULTURE_API_")) or key == "DJANGO_SECRET_KEY":
            os.environ.pop(key)
    with TemporaryDirectory(prefix="migam-local-demo-") as temporary:
        directory = Path(temporary)
        dist = args.dist.resolve() if args.dist else directory / "dist"
        if args.dist is None:
            build_assets(dist)
        os.environ["MIGAM_DB_PATH"] = str(directory / "demo.sqlite3")
        os.environ["MIGAM_DEMO_MODE"] = "1"
        os.environ["DJANGO_SETTINGS_MODULE"] = "backend.config.local_settings"
        import django
        django.setup()
        from django.core.management import call_command
        from django.core.wsgi import get_wsgi_application
        from django.db import connections
        from backend.apps.discovery.demo import seed_demo

        server, worker = None, None
        previous_signal = signal.getsignal(signal.SIGTERM)
        stopping = threading.Event()
        signal.signal(signal.SIGTERM, lambda number, frame: stopping.set())
        try:
            call_command("migrate", verbosity=0, interactive=False)
            seed_demo()
            host = "0.0.0.0" if args.container else "127.0.0.1"
            server = make_server(host, args.port, DemoApplication(dist, get_wsgi_application()),
                                 server_class=ThreadingDemoServer,
                                 handler_class=QuietRequestHandler)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            origin = f"http://127.0.0.1:{server.server_port}"
            print(f"Fictional MIGAM web and API: {origin}", flush=True)
            print("Existing databases are not used. Access logging is disabled. Ctrl+C stops the demo.", flush=True)
            if args.smoke_test:
                smoke_check(origin)
            else:
                while worker.is_alive() and not stopping.wait(0.5):
                    pass
        except KeyboardInterrupt:
            pass
        finally:
            if server is not None:
                server.shutdown()
                server.server_close()
            if worker is not None:
                worker.join(timeout=5)
            connections.close_all()
            signal.signal(signal.SIGTERM, previous_signal)
    print("Demo stopped; temporary database and generated assets removed.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Local demo could not start: {error}", file=sys.stderr)
        raise SystemExit(1)

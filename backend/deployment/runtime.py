"""WSGI entry point with immutable per-generation visitor databases."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time

from .snapshots import PrivateBlobs, SnapshotStore

ROOT = Path(__file__).resolve().parents[2]
CACHE_SECONDS = 300
_lock = threading.Lock()
_manifest = None
_last_check = 0.0
_serving_key = None
_serving_path = None
_django_app = None
_directory = None
_store = None


def response(start_response, status, payload):
    body = json.dumps(payload).encode()
    start_response(status, [("Content-Type", "application/json"), ("Content-Length", str(len(body))),
                            ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff")])
    return [body]


def serving_database():
    global _manifest, _last_check, _serving_key, _serving_path, _directory, _store
    now = time.time()
    candidate = _manifest
    if _manifest is None or now - _last_check >= CACHE_SECONDS:
        try:
            if _store is None:
                _store = SnapshotStore(PrivateBlobs())
            candidate = _store.manifest() or _manifest
        except Exception:
            if _manifest is None:
                raise
        _last_check = now
    if candidate is None:
        raise RuntimeError("no published data")
    key = (candidate["sha256"], int(now // CACHE_SECONDS))
    if _serving_key == key:
        return _serving_path
    if _directory is None:
        _directory = tempfile.TemporaryDirectory(prefix="migam-serving-")
    try:
        target, original = prepare_manifest(candidate, key)
    except Exception:
        if _manifest is None or candidate["sha256"] == _manifest["sha256"]:
            raise
        # A bad new generation must not break the previous good generation.
        candidate = _manifest
        key = (candidate["sha256"], int(now // CACHE_SECONDS))
        if _serving_key == key:
            return _serving_path
        target, original = prepare_manifest(candidate, key)
    previous = _serving_path
    _manifest = candidate
    _serving_key, _serving_path = key, target
    if previous is not None:
        previous.unlink(missing_ok=True)
    # Keep the current original only; open request connections are closed before this call.
    for path in Path(_directory.name).glob("*.sqlite3"):
        if path not in (target, original):
            path.unlink(missing_ok=True)
    return target


def prepare_manifest(manifest, key):
    target = Path(_directory.name) / f"{key[0]}-{key[1]}.sqlite3"
    original = Path(_directory.name) / f"{key[0]}.sqlite3"
    if not original.exists():
        _store.restore(original, manifest)
    from .worker import backup
    backup(original, target)
    subprocess.run([sys.executable, "-m", "backend.deployment.worker", "prepare", "--database", str(target)],
                   cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30, check=True)
    return target, original


def app(environ, start_response):
    global _django_app
    if not environ.get("PATH_INFO", "").startswith("/api/internal/v1/"):
        return response(start_response, "404 Not Found", {"error": "not_found"})
    try:
        if int(environ.get("CONTENT_LENGTH") or 0) > 64 * 1024:
            return response(start_response, "413 Payload Too Large", {"error": "request_too_large"})
    except ValueError:
        return response(start_response, "400 Bad Request", {"error": "invalid_length"})
    with _lock:
        try:
            if _django_app is not None:
                from django.db import connections
                connections.close_all()
            path = serving_database()
            uri = path.resolve().as_uri() + "?mode=ro"
            if _django_app is None:
                os.environ["DJANGO_SETTINGS_MODULE"] = "backend.config.public_settings"
                os.environ["MIGAM_DB_PATH"] = uri
                from django.core.wsgi import get_wsgi_application
                _django_app = get_wsgi_application()
            from django.db import connections
            connections["default"].settings_dict["NAME"] = uri

            def no_cache(status, headers, exc_info=None):
                headers = [(name, value) for name, value in headers if name.lower() != "cache-control"]
                headers.append(("Cache-Control", "no-store"))
                return start_response(status, headers, exc_info)

            result = _django_app(environ, no_cache)
            try:
                return list(result)
            finally:
                result.close()
                connections.close_all()
        except Exception:
            return response(start_response, "503 Service Unavailable", {"error": "data_temporarily_unavailable"})

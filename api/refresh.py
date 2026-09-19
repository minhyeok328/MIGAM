"""Vercel Cron only. Never return internal exception text or storage details."""

import hmac
from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path
import subprocess
import sys


def authorized(value):
    secret = os.environ.get("CRON_SECRET", "")
    return len(secret) >= 32 and hmac.compare_digest(value, f"Bearer {secret}")


class handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if not authorized(self.headers.get("Authorization", "")):
            self.reply(401, {"error": "unauthorized"})
            return
        try:
            result = subprocess.run([sys.executable, "-m", "backend.deployment.worker", "refresh"],
                                    cwd=Path(__file__).resolve().parents[1], capture_output=True,
                                    text=True, timeout=270, check=True)
            payload = json.loads(result.stdout.strip().splitlines()[-1])
            failed = any(value == "FAILED" for value in payload.get("sources", {}).values())
            self.reply(500 if failed else 200, payload)
        except Exception:
            self.reply(500, {"status": "FAILED"})

    def reply(self, code, payload):
        content = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

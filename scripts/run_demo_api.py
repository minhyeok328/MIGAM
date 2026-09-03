"""Run the real API with fictional records in a disposable, isolated SQLite DB."""

import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory


def main() -> None:
    repository = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repository))
    with TemporaryDirectory(prefix="migam-tp006-demo-") as directory:
        os.environ["MIGAM_DB_PATH"] = str(Path(directory) / "demo.sqlite3")
        os.environ["MIGAM_DEMO_MODE"] = "1"
        os.environ["DJANGO_SETTINGS_MODULE"] = "backend.config.local_settings"
        import django
        django.setup()
        from django.core.management import call_command
        from django.db import connections
        from backend.apps.discovery.demo import seed_demo

        try:
            call_command("migrate", verbosity=0, interactive=False)
            seed_demo()
            print("Fictional MIGAM demo API: http://127.0.0.1:8001", flush=True)
            print("Existing project databases are not used. Access logging is disabled.", flush=True)
            call_command("runserver", "127.0.0.1:8001", use_reloader=False)
        finally:
            connections.close_all()


if __name__ == "__main__":
    main()

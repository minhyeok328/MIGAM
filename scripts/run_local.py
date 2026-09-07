"""Serve local web assets and the internal API using an existing read-only database."""

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
from urllib.request import urlopen
from wsgiref.simple_server import make_server


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_local_demo import DemoApplication, QuietRequestHandler, ThreadingDemoServer, build_assets


def preparation_guidance(database):
    invoke = "& " if os.name == "nt" else ""
    return (
        "Stop the local server, then back up and prepare this database explicitly:\n"
        f'{invoke}"{sys.executable}" "{ROOT / "scripts" / "prepare_local_data.py"}" --database "{database}"\n'
        "Preparation updates derived data; it does not reverify official sources. Restart afterward."
    )


def check_database_ready(database):
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    from django.utils import timezone
    from backend.apps.catalog.models import Exhibition
    from backend.apps.discovery.models import SearchDocument
    from backend.data_pipeline.freshness.schedule import refresh_schedule_for

    with connection.cursor() as cursor:
        cursor.execute("PRAGMA integrity_check")
        if cursor.fetchall() != [("ok",)]:
            raise RuntimeError("Database integrity check failed. Restore a verified backup to a separate file.")
    executor = MigrationExecutor(connection)
    executor.loader.check_consistent_history(connection)
    if executor.migration_plan(executor.loader.graph.leaf_nodes()):
        raise RuntimeError("Unapplied migrations were found.\n" + preparation_guidance(database))
    now = timezone.now()
    today = timezone.localdate(now)
    exhibitions = {exhibition.pk: exhibition for exhibition in Exhibition.objects.all()}
    for exhibition in exhibitions.values():
        expected = exhibition.lifecycle
        if expected not in {"CANCELED", "UNKNOWN"}:
            expected = "ENDED" if exhibition.end_date < today else "UPCOMING" if exhibition.start_date > today else "CURRENT"
        stale = (
            exhibition.freshness == "FRESH"
            and refresh_schedule_for(exhibition, now=now).freshness == "STALE"
        )
        if exhibition.lifecycle != expected or stale:
            raise RuntimeError("Time-based lifecycle or freshness data needs preparation.\n" + preparation_guidance(database))
    for document in SearchDocument.objects.filter(result_type="EXHIBITION"):
        exhibition = exhibitions.get(document.object_id)
        if exhibition is None or any(
            getattr(document, field) != getattr(exhibition, field)
            for field in ("lifecycle", "start_date", "end_date")
        ):
            raise RuntimeError("Search projection dates need preparation.\n" + preparation_guidance(database))


def smoke_check(origin):
    for path in ("/", "/discover"):
        with urlopen(origin + path, timeout=10) as response:
            if response.status != 200 or b"html" not in response.read().lower():
                raise RuntimeError("Web smoke check failed")
    with urlopen(origin + "/healthz", timeout=10) as response:
        if json.load(response) != {"status": "ok", "mode": "local-data"}:
            raise RuntimeError("Health smoke check failed")
    with urlopen(origin + "/api/internal/v1/search/?type=EXHIBITION", timeout=10) as response:
        payload = json.load(response)
        # An existing, prepared database may legitimately have no current exhibitions.
        if response.status != 200 or not isinstance(payload.get("total"), int) or not isinstance(payload.get("results"), list):
            raise RuntimeError("API smoke check failed")
    print("Web, health and API smoke checks passed (local-data).", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=ROOT / "backend" / "db.sqlite3")
    parser.add_argument("--port", type=int, default=5180)
    parser.add_argument("--dist", type=Path, help="Use an existing local-mode build instead of building")
    parser.add_argument("--smoke-test", action="store_true", help="Verify web and API, then shut down")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    database = args.database.resolve()
    if not database.is_file():
        parser.error("Select an existing SQLite database with --database; no database was created.\n" + preparation_guidance(database))
    if args.dist is not None and not (args.dist / "index.html").is_file():
        parser.error("--dist must contain a local-mode index.html")
    for key in tuple(os.environ):
        if key.startswith(("VITE_", "KAKAO_", "CULTURE_API_")) or key == "DJANGO_SECRET_KEY":
            os.environ.pop(key)
    # SQLite's URI protects the existing file against accidental request-side writes
    # and refuses to create a missing database even if the file disappears later.
    os.environ["MIGAM_DB_PATH"] = database.as_uri() + "?mode=ro"
    os.environ["MIGAM_DEMO_MODE"] = "0"
    os.environ["DJANGO_SETTINGS_MODULE"] = "backend.config.local_settings"
    import django
    django.setup()
    from django.core.wsgi import get_wsgi_application
    from django.db import DatabaseError, connections
    from django.db.migrations.exceptions import InconsistentMigrationHistory

    server, worker = None, None
    previous_signal = signal.getsignal(signal.SIGTERM)

    def stop(number, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    try:
        try:
            check_database_ready(database)
        except (DatabaseError, InconsistentMigrationHistory) as error:
            raise RuntimeError("Database schema, integrity or migration history is not ready.\n" + preparation_guidance(database)) from error
        finally:
            connections.close_all()
        with TemporaryDirectory(prefix="migam-local-data-") as temporary:
            dist = args.dist.resolve() if args.dist else Path(temporary) / "dist"
            if args.dist is None:
                build_assets(dist, mode="local-data")
            try:
                server = make_server("127.0.0.1", args.port, DemoApplication(dist, get_wsgi_application(), mode="local-data"),
                                     server_class=ThreadingDemoServer, handler_class=QuietRequestHandler)
                worker = threading.Thread(target=server.serve_forever, daemon=True)
                worker.start()
                origin = f"http://127.0.0.1:{server.server_port}"
                print(f"Local-data MIGAM web and API: {origin}", flush=True)
                print("Existing database is read-only. Access logging is disabled. Ctrl+C stops the server.", flush=True)
                if args.smoke_test:
                    smoke_check(origin)
                else:
                    while worker.is_alive():
                        worker.join(timeout=0.5)
            finally:
                if server is not None:
                    server.shutdown()
                    server.server_close()
                if worker is not None:
                    worker.join(timeout=5)
                connections.close_all()
    except KeyboardInterrupt:
        pass
    finally:
        connections.close_all()
        signal.signal(signal.SIGTERM, previous_signal)
    print("Local server stopped; temporary assets removed and existing database preserved.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Local server could not start: {error}", file=sys.stderr)
        raise SystemExit(1)

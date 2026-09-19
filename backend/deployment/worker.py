"""Isolated writable process for snapshot preparation and daily collection."""

import argparse
from contextlib import closing
from datetime import datetime
import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from zoneinfo import ZoneInfo

from .snapshots import PrivateBlobs, SnapshotStore


def setup(database):
    os.environ["DJANGO_SETTINGS_MODULE"] = "backend.config.settings"
    os.environ["MIGAM_DB_PATH"] = str(Path(database).resolve())
    import django
    django.setup()


def backup(source, destination):
    with closing(sqlite3.connect(Path(source).resolve().as_uri() + "?mode=ro", uri=True)) as original:
        with closing(sqlite3.connect(destination)) as copy:
            original.backup(copy)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "refresh", "bootstrap"))
    parser.add_argument("--database")
    parser.add_argument("--source")
    args = parser.parse_args()
    if args.mode == "prepare":
        setup(args.database)
        from .derived import update_derived_state
        from django.db import connections
        update_derived_state()
        connections.close_all()
        return

    blobs = PrivateBlobs()
    store = SnapshotStore(blobs)
    day = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    if not store.claim_daily_run(day):
        print(json.dumps({"status": "ALREADY_CLAIMED", "day": day}))
        return
    with TemporaryDirectory(prefix="migam-refresh-") as directory:
        database = Path(directory) / "canonical.sqlite3"
        if args.mode == "bootstrap":
            if store.manifest() is not None:
                raise RuntimeError("bootstrap cannot replace an existing published database")
            backup(args.source, database)
        else:
            store.restore(database)
        setup(database)
        from django.core.management import call_command
        from django.db import connection, connections
        from .collection import refresh_sources
        call_command("migrate", verbosity=0, interactive=False)
        # Operator accounts, sessions and Admin logs are never included in hosted data.
        with connection.cursor() as cursor:
            for table in ("django_admin_log", "django_session", "auth_user_groups", "auth_user_user_permissions", "auth_user"):
                cursor.execute(f'DELETE FROM "{table}"')
        statuses = refresh_sources(Path(directory), blobs)
        connections.close_all()
        manifest = store.publish(database, source_status=statuses)
        try:
            blobs.prune({manifest["path"], manifest["previous"]})
        except Exception:
            statuses["retention"] = "FAILED"
        print(json.dumps({"status": "PUBLISHED", "sources": statuses, "sha256": manifest["sha256"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never let credentials, full URLs, raw source data or DB paths enter logs.
        print('{"status":"FAILED"}')
        raise SystemExit(1)

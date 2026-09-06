"""Back up an existing SQLite database before upgrading local discovery data."""

import argparse
from contextlib import closing
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
import sys
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=ROOT / "backend" / "db.sqlite3")
    parser.add_argument("--backup-dir", type=Path, default=ROOT / "data" / "incoming" / "backups")
    args = parser.parse_args()
    database = args.database.resolve(strict=True)
    backup_dir = args.backup_dir.resolve()
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = backup_dir / f"{database.stem}-{stamp}-{uuid4().hex[:8]}.sqlite3"
    # SQLite's backup API also includes committed WAL contents.
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as source:
        with closing(sqlite3.connect(backup)) as destination:
            source.backup(destination)
            if destination.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise RuntimeError("Backup integrity check failed; original database was not changed")
    print(f"Verified backup: {backup}", flush=True)

    sys.path.insert(0, str(ROOT))
    os.environ["MIGAM_DB_PATH"] = str(database)
    os.environ["DJANGO_SETTINGS_MODULE"] = "backend.config.settings"
    import django
    django.setup()
    from django.core.management import call_command
    from django.db import connections
    try:
        call_command("migrate", interactive=False)
        call_command("rebuild_discovery_data")
    finally:
        connections.close_all()


if __name__ == "__main__":
    main()

"""Restore a verified SQLite backup into a separate, new database file only."""

import argparse
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import sys
from tempfile import NamedTemporaryFile


def check_integrity(connection, description):
    try:
        valid = connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
    except sqlite3.DatabaseError as error:
        raise RuntimeError(f"{description} integrity check failed; no database was replaced.") from error
    if not valid:
        raise RuntimeError(f"{description} integrity check failed; no database was replaced.")


def restore_database(backup, output):
    backup = Path(backup).resolve(strict=True)
    requested_output = Path(output).absolute()
    # lexists also refuses a dangling symlink instead of following it to a new target.
    if os.path.lexists(requested_output):
        raise RuntimeError("Refusing to overwrite an existing output path; choose a new database file.")
    output = requested_output.resolve()
    if output == backup:
        raise RuntimeError("Refusing to restore over the backup; choose a separate new database file.")
    if not output.parent.is_dir():
        raise RuntimeError("The output parent directory must already exist.")
    temporary = None
    try:
        with closing(sqlite3.connect(backup.as_uri() + "?mode=ro", uri=True)) as source:
            check_integrity(source, "Backup")
            with NamedTemporaryFile(prefix=".migam-restore-", suffix=".sqlite3", dir=output.parent, delete=False) as file:
                temporary = Path(file.name)
            with closing(sqlite3.connect(temporary)) as destination:
                # Copy committed WAL contents through SQLite, never by copying the main file.
                source.backup(destination)
                check_integrity(destination, "Restored database")
        with temporary.open("r+b") as file:
            os.fsync(file.fileno())
        # Publishing a hard link is atomic and fails if another process creates
        # output after validation. os.replace would overwrite that user's file.
        os.link(temporary, output)
        return output
    finally:
        if temporary is not None:
            for path in (temporary, *(Path(str(temporary) + suffix) for suffix in ("-wal", "-shm", "-journal"))):
                path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = restore_database(args.backup, args.output)
    print(f"Verified database restored to: {output}", flush=True)
    print("The original database was not replaced. Use run_local.py --database with this new path.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, sqlite3.DatabaseError) as error:
        print(f"Local restore failed: {error}", file=sys.stderr)
        raise SystemExit(1)

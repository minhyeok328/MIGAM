from contextlib import closing
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[2]


class LocalPreparationTests(unittest.TestCase):
    def test_preparation_backs_up_original_and_preserves_existing_user_data(self):
        with TemporaryDirectory() as temp:
            folder = Path(temp)
            database = folder / "existing.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("CREATE TABLE preserved_marker (value TEXT)")
                connection.execute("INSERT INTO preserved_marker VALUES ('original-data')")
                connection.commit()
                before = list(connection.iterdump())
            result = subprocess.run([
                sys.executable, str(ROOT / "scripts" / "prepare_local_data.py"),
                "--database", str(database), "--backup-dir", str(folder / "backups"),
            ], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            backup, = (folder / "backups").glob("*.sqlite3")
            with closing(sqlite3.connect(backup)) as connection:
                self.assertEqual(list(connection.iterdump()), before)
                self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone(), ("ok",))
            with closing(sqlite3.connect(database)) as connection:
                self.assertEqual(connection.execute("SELECT value FROM preserved_marker").fetchone(), ("original-data",))
                self.assertIn("discovery_searchdocument", {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")})

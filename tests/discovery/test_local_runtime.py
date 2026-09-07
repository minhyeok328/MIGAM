from contextlib import closing
import json
import os
from pathlib import Path
import queue
import shutil
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]


def run_script(name, *arguments, environment=None):
    return subprocess.run(
        [sys.executable, "-X", "utf8", str(ROOT / "scripts" / name), *map(str, arguments)],
        cwd=ROOT, env=environment, capture_output=True, text=True, encoding="utf-8", timeout=60,
    )


class LocalRestoreTests(unittest.TestCase):
    def test_restore_refuses_corrupt_source_and_leaves_no_partial_output(self):
        with TemporaryDirectory() as temporary:
            folder = Path(temporary)
            backup = folder / "corrupt.sqlite3"
            backup.write_bytes(b"This is not a SQLite database")
            output = folder / "restored.sqlite3"
            result = run_script("restore_local_data.py", "--backup", backup, "--output", output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("integrity", result.stderr.lower())
            self.assertEqual(list(folder.iterdir()), [backup])
            self.assertEqual(backup.read_bytes(), b"This is not a SQLite database")

    def test_restore_refuses_existing_output_and_source_itself(self):
        with TemporaryDirectory() as temporary:
            folder = Path(temporary)
            backup = folder / "backup.sqlite3"
            with closing(sqlite3.connect(backup)) as connection:
                connection.execute("CREATE TABLE marker (value TEXT)")
                connection.execute("INSERT INTO marker VALUES ('source')")
                connection.commit()
            existing = folder / "existing.sqlite3"
            existing.write_bytes(b"Existing user data")
            before = backup.read_bytes()
            for output in (existing, backup):
                with self.subTest(output=output.name):
                    result = run_script("restore_local_data.py", "--backup", backup, "--output", output)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("refus", result.stderr.lower())
                    self.assertEqual(backup.read_bytes(), before)
                    self.assertEqual(existing.read_bytes(), b"Existing user data")

    def test_restore_includes_committed_wal_and_preserves_source(self):
        with TemporaryDirectory() as temporary:
            folder = Path(temporary)
            backup = folder / "backup.sqlite3"
            output = folder / "restored.sqlite3"
            with closing(sqlite3.connect(backup)) as source:
                source.execute("PRAGMA journal_mode=WAL")
                source.execute("PRAGMA wal_autocheckpoint=0")
                source.execute("CREATE TABLE marker (value TEXT)")
                source.execute("INSERT INTO marker VALUES ('committed-wal')")
                source.commit()
                self.assertGreater(Path(str(backup) + "-wal").stat().st_size, 0)
                before = backup.read_bytes()
                result = run_script("restore_local_data.py", "--backup", backup, "--output", output)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(backup.read_bytes(), before)
                self.assertEqual(source.execute("SELECT value FROM marker").fetchone(), ("committed-wal",))
                with closing(sqlite3.connect(output)) as restored:
                    self.assertEqual(restored.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
                    self.assertEqual(restored.execute("SELECT value FROM marker").fetchone(), ("committed-wal",))
            self.assertEqual(set(folder.iterdir()), {backup, output})


class LocalRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_directory = TemporaryDirectory()
        cls.addClassCleanup(cls.fixture_directory.cleanup)
        cls.fixture = Path(cls.fixture_directory.name) / "prepared.sqlite3"
        result = subprocess.run([
            sys.executable, "-X", "utf8", "-c", """
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.config.local_settings'
os.environ['MIGAM_DEMO_MODE'] = '0'
import django
django.setup()
from datetime import timedelta
from django.core.management import call_command
from django.db import connection, connections
from django.utils import timezone
from backend.apps.catalog.models import Exhibition, ExhibitionSourceLink, Institution
from backend.apps.discovery.projection import rebuild_search_documents
from backend.apps.sources.models import SourceRecord
call_command('migrate', interactive=False, verbosity=0)
institution = Institution.objects.create(registry_id='local-fixture', name='Local Fixture')
source = SourceRecord.objects.create(source_id='fixture', institution_id='local-fixture',
    source_record_id='fixture-1', source_owner='Local Fixture', payload={}, content_hash='a' * 64)
today = timezone.localdate()
exhibition = Exhibition.objects.create(institution=institution, title='Existing local exhibition',
    start_date=today-timedelta(days=5), end_date=today+timedelta(days=5), venue='Fixture',
    region_area='Seoul', region_district='Fixture', lifecycle='CURRENT', freshness='STALE',
    official_url='https://example.com/local-fixture', last_verified_at=timezone.now()-timedelta(days=4))
ExhibitionSourceLink.objects.create(exhibition=exhibition, source_id='fixture',
    source_record_id='fixture-1', latest_source_record=source)
rebuild_search_documents()
with connection.cursor() as cursor:
    cursor.execute('CREATE TABLE user_marker (value TEXT)')
    cursor.execute("INSERT INTO user_marker VALUES ('must-preserve')")
connections.close_all()
""",
        ], cwd=ROOT, env={**os.environ, "MIGAM_DB_PATH": str(cls.fixture)},
            capture_output=True, text=True, encoding="utf-8", timeout=60)
        if result.returncode:
            raise RuntimeError(result.stderr + result.stdout)

    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name)
        self.database = self.folder / "selected.sqlite3"
        shutil.copyfile(self.fixture, self.database)
        self.dist = self.folder / "dist"
        self.dist.mkdir()
        (self.dist / "index.html").write_text("<!doctype html><title>Local assets</title>", encoding="utf-8")
        (self.folder / ".env").write_text("private-file-marker", encoding="utf-8")
        self.environment = {
            **os.environ, "TEMP": str(self.folder), "TMP": str(self.folder), "TMPDIR": str(self.folder),
            "MIGAM_DB_PATH": str(self.folder / "inherited-must-not-open.sqlite3"),
            "MIGAM_DEMO_MODE": "1", "VITE_DEMO_MODE": "1",
            "VITE_KAKAO_JAVASCRIPT_KEY": "must-not-use-or-print",
            "DJANGO_SETTINGS_MODULE": "not.a.real.settings.module",
        }

    def launch(self, database=None):
        return run_script("run_local.py", "--database", database or self.database,
                          "--dist", self.dist, "--port", "0", "--smoke-test", environment=self.environment)

    def test_missing_database_is_not_created_and_explains_preparation(self):
        missing = self.folder / "missing.sqlite3"
        result = self.launch(missing)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("prepare_local_data.py", result.stderr)
        self.assertFalse(missing.exists())
        self.assertEqual(list(self.folder.glob("migam-local-data-*")), [])

    def test_unapplied_migrations_are_refused_without_changing_database(self):
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("DELETE FROM django_migrations WHERE app = 'discovery'")
            connection.commit()
        before = self.database.read_bytes()
        result = self.launch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("migration", result.stderr.lower())
        self.assertIn("prepare_local_data.py", result.stderr)
        self.assertEqual(self.database.read_bytes(), before)

    def test_outdated_lifecycle_or_freshness_requires_explicit_preparation(self):
        for update in (
            "UPDATE catalog_exhibition SET lifecycle='ENDED'",
            "UPDATE catalog_exhibition SET freshness='FRESH'",
            "UPDATE discovery_searchdocument SET lifecycle='ENDED' WHERE result_type='EXHIBITION'",
        ):
            with self.subTest(update=update):
                shutil.copyfile(self.fixture, self.database)
                with closing(sqlite3.connect(self.database)) as connection:
                    connection.execute(update)
                    connection.commit()
                before = self.database.read_bytes()
                result = self.launch()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("prepare_local_data.py", result.stderr)
                self.assertEqual(self.database.read_bytes(), before)

    def test_smoke_uses_selected_database_without_seed_or_timestamp_writes(self):
        before = self.database.read_bytes()
        result = self.launch()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Web, health and API smoke checks passed", result.stdout)
        self.assertIn("local-data", result.stdout)
        self.assertEqual(self.database.read_bytes(), before)
        self.assertFalse((self.folder / "inherited-must-not-open.sqlite3").exists())
        self.assertNotIn("must-not-use-or-print", result.stderr + result.stdout)
        self.assertNotIn("GET /", result.stderr + result.stdout)
        self.assertEqual(list(self.folder.glob("migam-local-data-*")), [])

    def test_database_connection_refuses_accidental_writes(self):
        wrapper = """
import runpy, sys
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
from django.db import connection, connections, OperationalError
try:
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO user_marker VALUES ('accidental-write')")
except OperationalError as error:
    if 'readonly' not in str(error).lower():
        raise
    print('Accidental database write was refused')
else:
    raise RuntimeError('Existing database accepted an accidental write')
finally:
    connections.close_all()
"""
        before = self.database.read_bytes()
        result = subprocess.run([
            sys.executable, "-X", "utf8", "-c", wrapper,
            str(ROOT / "scripts" / "run_local.py"), "--database", str(self.database),
            "--dist", str(self.dist), "--port", "0", "--smoke-test",
        ], cwd=ROOT, env=self.environment, capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Accidental database write was refused", result.stdout)
        self.assertEqual(self.database.read_bytes(), before)

    def test_restored_database_can_start_without_modifying_backup_or_restored_data(self):
        output = self.folder / "restored.sqlite3"
        before = self.database.read_bytes()
        result = run_script("restore_local_data.py", "--backup", self.database, "--output", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        restored_before = output.read_bytes()
        result = self.launch(output)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(output.read_bytes(), restored_before)
        self.assertEqual(self.database.read_bytes(), before)

    def test_process_serves_actual_api_and_safe_spa_then_cleans_up_on_sigterm(self):
        self.assert_process_serves_then_stops("SIGTERM")

    def test_process_preserves_database_and_cleans_up_on_ctrl_c(self):
        self.assert_process_serves_then_stops("SIGINT")

    def assert_process_serves_then_stops(self, stop_signal):
        # Deliver a real Python SIGTERM from stdin on Windows too, where
        # Popen.terminate() forcibly kills the process without a signal handler.
        wrapper = """
import _thread, runpy, signal, sys, threading
def stop_on_input():
    stop_signal = sys.stdin.readline().strip()
    _thread.interrupt_main(getattr(signal, stop_signal))
threading.Thread(target=stop_on_input, daemon=True).start()
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
"""
        before = self.database.read_bytes()
        process = subprocess.Popen([
            sys.executable, "-X", "utf8", "-u", "-c", wrapper,
            str(ROOT / "scripts" / "run_local.py"), "--database", str(self.database),
            "--dist", str(self.dist), "--port", "0",
        ], cwd=ROOT, env=self.environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding="utf-8")
        output, lines = [], queue.Queue()

        def read_output():
            for line in process.stdout:
                output.append(line)
                lines.put(line)
            lines.put(None)

        reader = threading.Thread(target=read_output, daemon=True)
        reader.start()
        try:
            origin = None
            while origin is None:
                line = lines.get(timeout=30)
                self.assertIsNotNone(line, "".join(output))
                if "http://127.0.0.1:" in line:
                    origin = line[line.index("http://127.0.0.1:"):].strip()
            for path in ("/", "/discover", "/exhibitions/1", "/settings", "/artworks"):
                with urlopen(origin + path, timeout=5) as response:
                    self.assertIn(b"Local assets", response.read())
            with urlopen(origin + "/healthz", timeout=5) as response:
                self.assertEqual(json.load(response), {"status": "ok", "mode": "local-data"})
            with urlopen(origin + "/api/internal/v1/search/?type=EXHIBITION&q=Existing", timeout=5) as response:
                payload = json.load(response)
                self.assertEqual(payload["total"], 1)
                self.assertEqual(payload["results"][0]["title"], "Existing local exhibition")
            with urlopen(origin + "/api/internal/v1/exhibitions/1/", timeout=5) as response:
                self.assertEqual(response.status, 200)
            request = Request(origin + "/api/internal/v1/recommendations/", data=b"{}",
                              headers={"Content-Type": "application/json"})
            with urlopen(request, timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertIsInstance(json.load(response)["recommendations"], list)
            for path in ("/admin/", "/../.env", "/assets/missing.js"):
                with self.assertRaises(HTTPError) as error:
                    urlopen(origin + path, timeout=5)
                self.assertEqual(error.exception.code, 404)
            process.stdin.write(stop_signal + "\n")
            process.stdin.flush()
            self.assertEqual(process.wait(timeout=15), 0, "".join(output))
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)
            reader.join(timeout=5)
            process.stdin.close()
            process.stdout.close()
        self.assertNotIn("GET /", "".join(output))
        self.assertNotIn("must-not-use-or-print", "".join(output))
        self.assertEqual(self.database.read_bytes(), before)
        self.assertEqual(list(self.folder.glob("migam-local-data-*")), [])

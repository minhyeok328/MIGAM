from contextlib import closing
import gzip
import hashlib
import json
import os
import re
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from backend.deployment.snapshots import SnapshotError, SnapshotStore
from backend.data_pipeline.collectors.seoul_download import (
    download_csv, observed_revision, DownloadError, OfficialRedirects,
)


class MemoryBlobs:
    def __init__(self):
        self.files = {}

    def get(self, path):
        return self.files.get(path)

    def put(self, path, data, *, overwrite=False):
        if path in self.files and not overwrite:
            raise FileExistsError(path)
        self.files[path] = data

    def delete(self, path):
        self.files.pop(path, None)


class PublicSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / "original.sqlite3"
        with closing(sqlite3.connect(self.db)) as connection:
            connection.execute("CREATE TABLE example (id INTEGER PRIMARY KEY, value TEXT)")
            connection.execute("INSERT INTO example VALUES (1, 'preserved')")
            connection.commit()
        self.blobs = MemoryBlobs()
        self.store = SnapshotStore(self.blobs)

    def test_roundtrip_preserves_original_and_restores_database(self):
        before = self.db.read_bytes()
        manifest = self.store.publish(self.db, source_status={"sema": "SUCCESS"})
        target = self.root / "serving.sqlite3"
        self.store.restore(target, manifest)
        self.assertEqual(before, target.read_bytes())
        self.assertEqual(before, self.db.read_bytes())
        self.assertEqual(manifest["sha256"], hashlib.sha256(before).hexdigest())

    def test_corrupt_download_never_replaces_last_good_database(self):
        manifest = self.store.publish(self.db, source_status={})
        target = self.root / "serving.sqlite3"
        target.write_bytes(b"last good")
        self.blobs.files[manifest["path"]] = gzip.compress(b"not sqlite")
        with self.assertRaises(SnapshotError):
            self.store.restore(target, manifest)
        self.assertEqual(target.read_bytes(), b"last good")

    def test_invalid_manifest_path_and_oversized_database_rejected(self):
        manifest = self.store.publish(self.db, source_status={})
        for changes in ({"path": "https://attacker.invalid/db"}, {"size": 100_000_000}):
            with self.subTest(changes=changes), self.assertRaises(SnapshotError):
                self.store.restore(self.root / "db", {**manifest, **changes})

    def test_daily_claim_is_immutable_and_previous_snapshot_retained(self):
        self.assertTrue(self.store.claim_daily_run("2026-09-19"))
        self.assertFalse(self.store.claim_daily_run("2026-09-19"))
        first = self.store.publish(self.db, source_status={})
        with closing(sqlite3.connect(self.db)) as connection:
            connection.execute("INSERT INTO example VALUES (2, 'new')")
            connection.commit()
        second = self.store.publish(self.db, source_status={})
        self.assertEqual(second["previous"], first["path"])
        self.assertIn(first["path"], self.blobs.files)

    def test_non_sqlite_publish_does_not_replace_manifest(self):
        self.store.publish(self.db, source_status={})
        before = self.blobs.files["state/current.json"]
        self.db.write_bytes(b"broken")
        with self.assertRaises(SnapshotError):
            self.store.publish(self.db, source_status={})
        self.assertEqual(before, self.blobs.files["state/current.json"])

    def test_runtime_uses_last_good_generation_when_new_snapshot_is_corrupt(self):
        from backend.deployment import runtime
        first = self.store.publish(self.db, source_status={})
        with TemporaryDirectory() as cache:
            directory = type("Directory", (), {"name": cache})()
            with patch.multiple(runtime, _manifest=None, _last_check=0, _serving_key=None,
                                _serving_path=None, _directory=directory, _store=self.store), \
                    patch.object(runtime.subprocess, "run"), patch.object(runtime.time, "time", return_value=600):
                initial = runtime.serving_database()
                original = initial.read_bytes()
                with closing(sqlite3.connect(self.db)) as connection:
                    connection.execute("INSERT INTO example VALUES (2, 'changed')")
                    connection.commit()
                second = self.store.publish(self.db, source_status={})
                self.blobs.files[second["path"]] = b"corrupt"
                with patch.object(runtime.time, "time", return_value=901):
                    fallback = runtime.serving_database()
                self.assertEqual(fallback.read_bytes(), original)
                self.assertEqual(runtime._manifest["sha256"], first["sha256"])

    def test_cron_auth_fails_closed(self):
        from api.refresh import authorized
        with patch.dict("os.environ", {"CRON_SECRET": ""}):
            self.assertFalse(authorized("Bearer "))
        with patch.dict("os.environ", {"CRON_SECRET": "x" * 48}):
            self.assertFalse(authorized("Bearer wrong"))
            self.assertTrue(authorized("Bearer " + "x" * 48))

    def test_public_entry_rejects_operator_and_file_routes_before_storage(self):
        from backend.deployment.runtime import app
        for path in ("/admin/", "/admin/data-status/", "/backend/db.sqlite3"):
            statuses = []
            with patch("backend.deployment.runtime.serving_database", side_effect=AssertionError):
                app({"PATH_INFO": path}, lambda status, headers: statuses.append(status))
            self.assertEqual(statuses, ["404 Not Found"])

    def test_incomplete_csv_transfer_is_retryable_on_next_run(self):
        from backend.deployment.collection import csv_records
        from backend.data_pipeline.collectors.seoul_download import RetryableDownloadError
        with patch("backend.deployment.collection.observed_revision", return_value="2026-09-19"), \
                patch("backend.deployment.collection.download_csv", side_effect=RetryableDownloadError) as download:
            for _ in range(2):
                with self.assertRaises(RetryableDownloadError):
                    csv_records("seoul-oa-15323-sema", None, self.root, self.blobs)
        self.assertEqual(download.call_count, 2)

    def test_access_block_cannot_be_retried_for_same_revision(self):
        from backend.deployment.collection import csv_records
        with patch("backend.deployment.collection.observed_revision", return_value="2026-09-19"), \
                patch("backend.deployment.collection.download_csv", side_effect=DownloadError) as download:
            for _ in range(2):
                with self.assertRaises(DownloadError):
                    csv_records("seoul-oa-15323-sema", None, self.root, self.blobs)
        self.assertEqual(download.call_count, 1)


class Response:
    def __init__(self, data, status=200):
        self.data = data
        self.status = status
        self.headers = {}

    def read(self, size=-1):
        result, self.data = self.data[:size], self.data[size:]
        return result

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class OfficialDownloadTests(unittest.TestCase):
    def test_period_scan_only_fetches_approved_places_but_rechecks_detail(self):
        from backend.data_pipeline.collectors.culture_info import CultureInfoApiCollector
        from backend.data_pipeline.registry import SourceRegistry
        from tests.data_pipeline.test_culture_info import StaticXmlTransport
        transport = StaticXmlTransport()
        original_get = transport.get
        def get(url, params):
            if url.endswith("/period2"):
                return '''<response><body><items>
                    <item><seq>999999</seq><place>다른 공연장</place></item>
                    <item><seq>394181</seq><place>수원시립미술관</place></item>
                    </items><totalCount>2</totalCount></body></response>'''.encode()
            return original_get(url, params)
        transport.get = get
        registry = SourceRegistry.load(Path(__file__).resolve().parents[2] / "sources.yaml")
        records = CultureInfoApiCollector(registry, "test-only", transport=transport).collect(
            {"from": "20260101", "to": "20261231"}, summary_places=frozenset({"수원시립미술관"}),
        )
        self.assertEqual([row.source_record_id for row in records], ["394181"])
        self.assertEqual([params["seq"] for _, params in transport.calls], ["394181"])

    def test_existing_file_is_not_removed_or_downloaded(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "OA-15323.csv"
            path.write_bytes(b"keep")
            with self.assertRaises(DownloadError):
                download_csv("seoul-oa-15323-sema", directory,
                             opener=lambda *args, **kwargs: self.fail("network reached"))
            self.assertEqual(path.read_bytes(), b"keep")

    def test_revision_comes_from_data_update_not_metadata_update(self):
        page = '<th>메타정보 수정일</th><td>2025.01.01.</td><th>데이터 갱신일</th><td><span>2026.09.19.</span></td>'
        revision = observed_revision("seoul-oa-15323-sema",
                                     opener=lambda *a, **kw: Response(page.encode()))
        self.assertEqual(revision, "2026-09-19")
        with self.assertRaises(DownloadError):
            observed_revision("seoul-oa-15323-sema", opener=lambda *a, **kw: Response(b"login"))

    def test_redirect_cannot_send_form_to_other_hosts(self):
        with self.assertRaises(DownloadError):
            OfficialRedirects().redirect_request(None, None, 302, "", {}, "https://other.invalid/")

    def test_only_approved_ids_and_https_form_are_used(self):
        requests = []

        def open_request(request, timeout):
            requests.append(request)
            return Response(b"title,date\nexample,2026-09-19\n")

        with TemporaryDirectory() as directory:
            path, metadata = download_csv("seoul-oa-15323-sema", Path(directory), opener=open_request)
            self.assertEqual(path.read_bytes(), b"title,date\nexample,2026-09-19\n")
            self.assertEqual(metadata["source_id"], "seoul-oa-15323-sema")
        self.assertEqual(requests[0].full_url, "https://datafile.seoul.go.kr/bigfile/iot/sheet/csv/download.do")
        self.assertIn(b"infId=OA-15323", requests[0].data)
        with self.assertRaises(DownloadError):
            download_csv("unapproved", Path("."), opener=open_request)
        self.assertEqual(len(requests), 1)

    def test_access_block_is_not_retried_or_saved(self):
        from urllib.error import HTTPError
        calls = []

        def blocked(request, timeout):
            calls.append(request)
            raise HTTPError(request.full_url, 429, "stop", {}, None)

        with TemporaryDirectory() as directory:
            with self.assertRaises(DownloadError):
                download_csv("seoul-oa-15323-sema", Path(directory), opener=blocked)
            self.assertEqual(list(Path(directory).iterdir()), [])
        self.assertEqual(len(calls), 1)


class PublicWSGITests(unittest.TestCase):
    def test_deployment_rewrite_accepts_every_openapi_route_with_trailing_slash(self):
        import yaml
        root = Path(__file__).resolve().parents[2]
        config = json.loads((root / "vercel.json").read_text())
        contract = yaml.safe_load((root / "openapi/internal-v1.yaml").read_text(encoding="utf-8"))
        api_rule = next(rule for rule in config["rewrites"] if rule["destination"] == "/api")
        for path in contract["paths"]:
            with self.subTest(path=path):
                self.assertIsNotNone(re.fullmatch(api_rule["source"], path))

    def test_real_wsgi_uses_readonly_data_and_checks_host(self):
        root = Path(__file__).resolve().parents[2]
        with TemporaryDirectory() as directory:
            database = Path(directory) / "fictional.sqlite3"
            environment = {**os.environ, "MIGAM_DB_PATH": str(database), "MIGAM_DEMO_MODE": "1",
                           "DJANGO_SETTINGS_MODULE": "backend.config.local_settings"}
            seed = subprocess.run([sys.executable, "-X", "utf8", "-c", """
import django
django.setup()
from django.core.management import call_command
from backend.apps.discovery.demo import seed_demo
from django.db import connections
call_command('migrate', interactive=False, verbosity=0)
seed_demo()
connections.close_all()
"""], cwd=root, env=environment, capture_output=True, text=True, timeout=30)
            self.assertEqual(seed.returncode, 0, seed.stderr)
            original = database.read_bytes()
            smoke = subprocess.run([sys.executable, "-X", "utf8", "-c", """
import io, json, os, sys
from pathlib import Path
from wsgiref.util import setup_testing_defaults
from backend.deployment.snapshots import SnapshotStore
from backend.deployment import runtime
from tests.discovery.test_public_deployment import MemoryBlobs
store = SnapshotStore(MemoryBlobs())
store.publish(Path(sys.argv[1]), source_status={})
runtime._store = store
os.environ['DJANGO_SECRET_KEY'] = 'fictional-test-secret-never-used-outside-tests-12345'
def request(host, path, method='GET', body=b''):
    env = {}
    setup_testing_defaults(env)
    env.update(HTTP_HOST=host, PATH_INFO=path, REQUEST_METHOD=method, CONTENT_TYPE='application/json',
               CONTENT_LENGTH=str(len(body)), **{'wsgi.input': io.BytesIO(body)})
    result = {}
    def start(status, headers, exc_info=None):
        result['status'] = status
        result['headers'] = dict(headers)
    result['body'] = b''.join(runtime.app(env, start))
    return result
good = request('migam-home-preview.vercel.app', '/api/internal/v1/search/')
assert good['status'].startswith('200'), good
assert good['headers']['Cache-Control'] == 'no-store'
assert request('other.invalid', '/api/internal/v1/search/')['status'].startswith('400')
assert request('migam-home-preview.vercel.app', '/admin/')['status'].startswith('404')
from django.db import connection, connections, OperationalError
try:
    connection.cursor().execute("UPDATE catalog_exhibition SET title='should not write'")
except OperationalError as error:
    assert 'readonly' in str(error).lower()
else:
    raise AssertionError('visitor DB allowed write')
connections.close_all()
print('public WSGI search, host, routes and readonly checks passed')
""", str(database)], cwd=root, env=environment, capture_output=True, text=True, timeout=60)
            self.assertEqual(smoke.returncode, 0, smoke.stderr + smoke.stdout)
            self.assertEqual(database.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()

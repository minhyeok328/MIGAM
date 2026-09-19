"""Private, bounded SQLite snapshots. Never expose storage URLs to visitors."""

from contextlib import closing
from datetime import date, datetime, timezone
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
from tempfile import NamedTemporaryFile


MAX_DATABASE_BYTES = 64 * 1024 * 1024
MANIFEST_PATH = "state/current.json"


class SnapshotError(RuntimeError):
    pass


def verify_database(path):
    try:
        with closing(sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)) as db:
            if db.execute("PRAGMA quick_check").fetchone() != ("ok",):
                raise SnapshotError("database integrity check failed")
    except sqlite3.Error as error:
        raise SnapshotError("invalid snapshot database") from error


class PrivateBlobs:
    def __init__(self):
        # The SDK is an optional deployment dependency, never required by local tests.
        os.environ["VERCEL_TELEMETRY_DISABLED"] = "1"
        from vercel.blob import BlobClient
        token = os.environ.get("BLOB_READ_WRITE_TOKEN", "")
        if not token:
            raise SnapshotError("private storage is not configured")
        self.client = BlobClient(token=token)

    def get(self, path):
        from vercel.blob.errors import BlobNotFoundError
        try:
            result = self.client.get(path, access="private", use_cache=False, timeout=25)
        except BlobNotFoundError:
            return None
        if result is None:
            return None
        if len(result.content) > MAX_DATABASE_BYTES:
            raise SnapshotError("snapshot download exceeds size limit")
        return result.content

    def prune(self, keep):
        # This is a dedicated MIGAM store. Only remove our versioned objects.
        for prefix in ("snapshots/", "runs/"):
            for blob in self.client.iter_objects(prefix=prefix):
                if blob.pathname in keep:
                    continue
                age = datetime.now(timezone.utc) - blob.uploaded_at
                if age.days >= (2 if prefix == "snapshots/" else 30):
                    self.client.delete(blob.url)

    def delete(self, path):
        self.client.delete(path)

    def put(self, path, data, *, overwrite=False):
        from vercel.blob.errors import BlobError
        try:
            self.client.put(path, data, access="private", overwrite=overwrite,
                            content_type="application/octet-stream", cache_control_max_age=60)
        except BlobError as error:
            # Only an observed existing object means a duplicate, never a network failure.
            if not overwrite and self.get(path) is not None:
                raise FileExistsError(path) from error
            raise SnapshotError("private storage upload failed") from error


class SnapshotStore:
    def __init__(self, blobs):
        self.blobs = blobs

    def manifest(self):
        payload = self.blobs.get(MANIFEST_PATH)
        if payload is None:
            return None
        try:
            if len(payload) > 16384:
                raise ValueError("oversized manifest")
            result = json.loads(payload)
            self.validate(result)
            return result
        except (ValueError, TypeError, KeyError) as error:
            raise SnapshotError("invalid snapshot manifest") from error

    @staticmethod
    def validate(manifest):
        if not isinstance(manifest, dict):
            raise SnapshotError("invalid snapshot manifest")
        digest = manifest.get("sha256", "")
        if (manifest.get("version") != 1 or not re.fullmatch(r"[0-9a-f]{64}", digest)
                or manifest.get("path") != f"snapshots/{digest}.sqlite3.gz"
                or type(manifest.get("size")) is not int
                or not 0 < manifest["size"] <= MAX_DATABASE_BYTES):
            raise SnapshotError("invalid snapshot manifest")

    def restore(self, target, manifest=None):
        manifest = manifest or self.manifest()
        if manifest is None:
            raise SnapshotError("no published data")
        self.validate(manifest)
        compressed = self.blobs.get(manifest["path"])
        if compressed is None:
            raise SnapshotError("snapshot is unavailable")
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
                content = stream.read(MAX_DATABASE_BYTES + 1)
            if (len(content) != manifest["size"]
                    or hashlib.sha256(content).hexdigest() != manifest["sha256"]):
                raise SnapshotError("snapshot checksum mismatch")
        except (OSError, EOFError) as error:
            raise SnapshotError("invalid snapshot archive") from error
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=target.parent, suffix=".sqlite3", delete=False) as temp:
            temp.write(content)
            temporary = Path(temp.name)
        try:
            verify_database(temporary)
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        return manifest

    def claim_daily_run(self, day):
        if date.fromisoformat(day).isoformat() != day:
            raise SnapshotError("invalid run date")
        try:
            self.blobs.put(f"runs/{day}.json", b'{"claimed":true}')
            return True
        except FileExistsError:
            return False

    def publish(self, database, *, source_status):
        database = Path(database)
        if not 0 < database.stat().st_size <= MAX_DATABASE_BYTES:
            raise SnapshotError("database size exceeds limit")
        verify_database(database)
        content = database.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        path = f"snapshots/{digest}.sqlite3.gz"
        previous = self.manifest()
        try:
            self.blobs.put(path, gzip.compress(content, mtime=0))
        except FileExistsError:
            pass
        manifest = {
            "version": 1, "sha256": digest, "path": path, "size": len(content),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "previous": previous["path"] if previous else None,
            "sources": source_status,
        }
        self.blobs.put(MANIFEST_PATH, json.dumps(manifest).encode(), overwrite=True)
        return manifest

from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from backend.apps.catalog.models import Exhibition, ExhibitionSourceLink, VerificationRecord
from backend.apps.sources.models import IngestionRun, InstitutionRunResult, Source
from backend.data_pipeline.persistence import persist_records
from backend.data_pipeline.registry import SourceRegistry
from backend.deployment.collection import refresh_sources
from tests.persistence.test_refresh_execution import valid_record

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 9, 19, 3, tzinfo=timezone.utc)
SOURCE = "seoul-oa-2708-sejong"


class PublicRefreshTests(TestCase):
    def setUp(self):
        self.registry = SourceRegistry.load(ROOT / "sources.yaml")
        persist_records([valid_record()], self.registry, as_of=date(2026, 9, 19), command_name="test")
        self.exhibition = Exhibition.objects.get()
        Exhibition.objects.update(last_verified_at=datetime(2026, 9, 1, tzinfo=timezone.utc))

    def run_daily(self, collector):
        with patch("backend.deployment.collection.collect_source", side_effect=collector), \
                patch("django.utils.timezone.now", return_value=NOW):
            return refresh_sources(ROOT, None)

    def test_failed_collection_keeps_verified_time_and_records_failure(self):
        original = Exhibition.objects.get().last_verified_at
        def fail(*args):
            raise RuntimeError("unavailable")
        result = self.run_daily(fail)
        self.exhibition.refresh_from_db()
        self.assertEqual(result[SOURCE], "FAILED")
        self.assertEqual(self.exhibition.last_verified_at, original)
        self.assertEqual(self.exhibition.freshness, "STALE")
        self.assertTrue(VerificationRecord.objects.filter(exhibition=self.exhibition, outcome="FAILED").exists())

    def test_ended_record_with_changed_official_payload_is_processed(self):
        Exhibition.objects.update(lifecycle="ENDED", end_date=date(2026, 9, 1))
        before = ExhibitionSourceLink.objects.get().latest_source_record_id
        def collect(source, *args):
            return [valid_record(title="공식 제목 변경")] if source == SOURCE else []
        result = self.run_daily(collect)
        self.assertTrue(result[SOURCE].startswith("SUCCESS"))
        self.assertNotEqual(ExhibitionSourceLink.objects.get().latest_source_record_id, before)

    def test_discovery_persistence_failure_records_institution_failure(self):
        Exhibition.objects.update(lifecycle="ENDED", end_date=date(2026, 9, 1))
        with patch("backend.data_pipeline.persistence.persist_records", side_effect=RuntimeError("write failed")):
            self.run_daily(lambda *args: [valid_record()])
        run = IngestionRun.objects.filter(command="daily_public_discovery", source_id=SOURCE).latest("id")
        self.assertEqual(run.status, "FAILED")
        self.assertTrue(InstitutionRunResult.objects.filter(ingestion_run=run, status="FAILED").exists())

    def test_blocked_source_does_not_reach_collector(self):
        from backend.data_pipeline.registry_state import sync_registry_state
        sync_registry_state(self.registry)
        Source.objects.filter(registry_id=SOURCE).update(operation_status="SUSPENDED")
        called = []
        self.run_daily(lambda source, *args: called.append(source) or [])
        self.assertNotIn(SOURCE, called)

from datetime import date
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from backend.apps.catalog.models import Exhibition, VerificationRecord
from backend.apps.sources.models import IngestionRun
from backend.data_pipeline.fixture_loader import load_qualification_fixture
from backend.data_pipeline.persistence import persist_records
from backend.data_pipeline.registry import SourceRegistry
from tests.data_pipeline.test_culture_info import StaticXmlTransport


ROOT = Path(__file__).resolve().parents[2]


class LiveRefreshTests(TestCase):
    def seed(self, source_id):
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        raw = next(row for row in load_qualification_fixture(ROOT / "fixtures/source-qualification.json", registry) if row.source_record_id == source_id)
        persist_records([raw], registry, as_of=date(2026, 9, 6), command_name="test")
        return Exhibition.objects.get()

    def test_real_refresh_fetches_only_selected_official_detail(self):
        exhibition = self.seed("394181")
        class UpdatedOfficialResponse(StaticXmlTransport):
            def get(self, url, params):
                return super().get(url, params).replace(b"</title>", b" refreshed</title>")
        with patch("backend.data_pipeline.collectors.culture_info.UrllibXmlTransport", return_value=UpdatedOfficialResponse()), patch.dict("os.environ", {"CULTURE_PORTAL_SERVICE_KEY": "test-key"}):
            call_command("refresh_exhibition", id=exhibition.pk, stdout=StringIO())
        exhibition.refresh_from_db()
        self.assertTrue(exhibition.title.endswith(" refreshed"))
        verification = VerificationRecord.objects.get(exhibition=exhibition)
        self.assertEqual(verification.outcome, "SUCCESS")
        self.assertEqual(verification.source_record_id, "394181")

    def test_missing_official_csv_never_silently_uses_qualification_fixture(self):
        exhibition = self.seed("37607")
        before = exhibition.last_verified_at
        with self.assertRaisesRegex(CommandError, "CSV"):
            call_command("refresh_exhibition", id=exhibition.pk, stdout=StringIO())
        exhibition.refresh_from_db()
        self.assertEqual(exhibition.last_verified_at, before)
        self.assertFalse(VerificationRecord.objects.filter(outcome="SUCCESS").exists())

    def test_due_source_filter_does_not_refresh_other_institutions(self):
        self.seed("37607")
        output = StringIO()
        call_command("refresh_due_exhibitions", source="kcisa-cultureinfo", stdout=output)
        self.assertIn("target=0", output.getvalue())
        self.assertEqual(IngestionRun.objects.count(), 1)

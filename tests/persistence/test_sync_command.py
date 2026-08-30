from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from backend.apps.data_quality.models import ExhibitionCandidate
from backend.apps.sources.models import IngestionRun, SourceRecord


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures" / "source-qualification.json"


class SyncExhibitionsCommandTests(TestCase):
    def test_imports_approved_fixture_through_the_quality_pipeline(self) -> None:
        output = StringIO()

        call_command(
            "sync_exhibitions",
            fixture=str(FIXTURE),
            as_of="2026-08-30",
            stdout=output,
        )

        run = IngestionRun.objects.get()
        self.assertEqual(run.status, IngestionRun.Status.SUCCESS)
        self.assertEqual(run.received_count, 25)
        self.assertEqual(run.verified_count, 24)
        self.assertEqual(run.excluded_count, 1)
        self.assertEqual(run.quarantined_count, 1)
        self.assertEqual(SourceRecord.objects.count(), 25)
        self.assertEqual(ExhibitionCandidate.objects.count(), 25)
        self.assertIn(
            "received=25 verified=24 excluded=1 quarantined=1",
            output.getvalue(),
        )

    def test_filters_fixture_by_registered_source(self) -> None:
        call_command(
            "sync_exhibitions",
            fixture=str(FIXTURE),
            as_of="2026-08-30",
            source="seoul-oa-2708-sejong",
            stdout=StringIO(),
        )

        run = IngestionRun.objects.get()
        self.assertEqual(run.source_id, "seoul-oa-2708-sejong")
        self.assertEqual(run.received_count, 5)
        self.assertEqual(SourceRecord.objects.count(), 5)

    def test_rejects_unknown_source_before_creating_a_run(self) -> None:
        with self.assertRaisesRegex(CommandError, "unknown source"):
            call_command(
                "sync_exhibitions",
                fixture=str(FIXTURE),
                as_of="2026-08-30",
                source="not-registered",
                stdout=StringIO(),
            )

        self.assertFalse(IngestionRun.objects.exists())

from datetime import date, datetime, timezone as datetime_timezone
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


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures" / "source-qualification.json"
UTC = datetime_timezone.utc
NOW = datetime(2026, 8, 31, 3, 0, tzinfo=UTC)


class RefreshCommandTests(TestCase):
    def setUp(self) -> None:
        self.registry = SourceRegistry.load(ROOT / "sources.yaml")
        self.records = load_qualification_fixture(FIXTURE, self.registry)

    def seed(self, *source_record_ids: str) -> tuple[Exhibition, ...]:
        selected = [
            record
            for record in self.records
            if record.source_record_id in source_record_ids
        ]
        persist_records(
            selected,
            self.registry,
            as_of=date(2026, 8, 31),
            command_name="sync_exhibitions",
        )
        return tuple(
            Exhibition.objects.filter(
                source_links__source_record_id__in=source_record_ids
            ).order_by("source_links__source_record_id")
        )

    def test_show_refresh_schedule_is_read_only(self) -> None:
        exhibition = self.seed("37607")[0]
        exhibition.last_verified_at = datetime(2026, 8, 30, 3, 0, tzinfo=UTC)
        exhibition.save(update_fields=("last_verified_at", "updated_at"))
        run_count = IngestionRun.objects.count()
        output = StringIO()

        with patch(
            "backend.apps.sources.management.commands.show_refresh_schedule.timezone.now",
            return_value=NOW,
        ):
            call_command("show_refresh_schedule", stdout=output)

        exhibition.refresh_from_db()
        rendered = output.getvalue()
        self.assertIn(f"id={exhibition.pk}", rendered)
        self.assertIn("due=yes", rendered)
        self.assertIn("freshness=FRESH", rendered)
        self.assertIn("reason=UPCOMING_WITHIN_7_DAYS", rendered)
        self.assertEqual(IngestionRun.objects.count(), run_count)
        self.assertEqual(VerificationRecord.objects.count(), 0)
        self.assertEqual(exhibition.freshness, Exhibition.Freshness.FRESH)

    def test_refresh_due_exhibitions_refreshes_only_due_records(self) -> None:
        exhibitions = self.seed("37607", "1576627")
        due = next(
            exhibition
            for exhibition in exhibitions
            if exhibition.source_links.get().source_record_id == "37607"
        )
        not_due = next(exhibition for exhibition in exhibitions if exhibition != due)
        due.last_verified_at = datetime(2026, 8, 29, 3, 0, tzinfo=UTC)
        due.save(update_fields=("last_verified_at", "updated_at"))
        not_due_at = datetime(2026, 8, 31, 2, 30, tzinfo=UTC)
        not_due.last_verified_at = not_due_at
        not_due.save(update_fields=("last_verified_at", "updated_at"))
        output = StringIO()

        with patch(
            "backend.apps.sources.management.commands.refresh_due_exhibitions.timezone.now",
            return_value=NOW,
        ):
            call_command(
                "refresh_due_exhibitions",
                fixture=str(FIXTURE),
                stdout=output,
            )

        due.refresh_from_db()
        not_due.refresh_from_db()
        self.assertEqual(due.last_verified_at, NOW)
        self.assertEqual(not_due.last_verified_at, not_due_at)
        self.assertEqual(
            set(VerificationRecord.objects.values_list("exhibition_id", flat=True)),
            {due.pk},
        )
        self.assertIn("target=1 success=1 failure=0", output.getvalue())

    def test_refresh_exhibition_allows_explicit_ended_record(self) -> None:
        exhibition = self.seed("37023")[0]
        self.assertEqual(exhibition.lifecycle, Exhibition.Lifecycle.ENDED)

        with patch(
            "backend.apps.sources.management.commands.refresh_exhibition.timezone.now",
            return_value=NOW,
        ):
            call_command(
                "refresh_exhibition",
                id=exhibition.pk,
                fixture=str(FIXTURE),
                stdout=StringIO(),
            )

        verification = VerificationRecord.objects.get(exhibition=exhibition)
        self.assertEqual(verification.outcome, VerificationRecord.Outcome.SUCCESS)

    def test_refresh_exhibition_rejects_unknown_id_without_run(self) -> None:
        with self.assertRaisesRegex(CommandError, "unknown exhibition"):
            call_command(
                "refresh_exhibition",
                id=999999,
                fixture=str(FIXTURE),
                stdout=StringIO(),
            )

        self.assertEqual(IngestionRun.objects.count(), 0)

    def test_due_refresh_failure_keeps_canonical_and_records_failed_run(self) -> None:
        exhibition = self.seed("37607")[0]
        exhibition.last_verified_at = datetime(2026, 8, 28, 3, 0, tzinfo=UTC)
        exhibition.save(update_fields=("last_verified_at", "updated_at"))
        original_title = exhibition.title

        with (
            patch(
                "backend.apps.sources.management.commands.refresh_due_exhibitions.timezone.now",
                return_value=NOW,
            ),
            self.assertRaisesRegex(CommandError, "missing-fixture"),
        ):
            call_command(
                "refresh_due_exhibitions",
                fixture=str(ROOT / "fixtures" / "missing-fixture.json"),
                stdout=StringIO(),
            )

        exhibition.refresh_from_db()
        run = IngestionRun.objects.get(command="refresh_due_exhibitions")
        self.assertEqual(exhibition.title, original_title)
        self.assertEqual(run.status, IngestionRun.Status.FAILED)
        self.assertTrue(
            VerificationRecord.objects.filter(
                exhibition=exhibition,
                outcome=VerificationRecord.Outcome.FAILED,
            ).exists()
        )

from dataclasses import replace
from datetime import date, datetime, timezone as datetime_timezone
from pathlib import Path

from django.test import TestCase

from backend.apps.catalog.models import Exhibition, FieldEvidence, VerificationRecord
from backend.apps.sources.models import IngestionRun
from backend.data_pipeline.freshness.execution import (
    RefreshExecutionError,
    refresh_exhibitions,
)
from backend.data_pipeline.models import RawExhibitionRecord
from backend.data_pipeline.persistence import persist_records
from backend.data_pipeline.registry import SourceRegistry


ROOT = Path(__file__).resolve().parents[2]
UTC = datetime_timezone.utc


def valid_record(**changes: object) -> RawExhibitionRecord:
    record = RawExhibitionRecord(
        source_id="seoul-oa-2708-sejong",
        institution_id="sejong-center-main-exhibition",
        source_record_id="37607",
        source_owner="세종문화회관",
        title="제3회 호반미술상",
        start_date="2026-08-01",
        end_date="2026-09-30",
        venue="세종미술관 1·2관",
        region_area="서울",
        region_district="종로구",
        official_url=(
            "https://www.sejongpac.or.kr/portal/performance/performance/"
            "performTicket.do?performIdx=37607&menuNo=200558"
        ),
        raw={"PERFORM_IDX": "37607", "TITLE": "제3회 호반미술상"},
    )
    return replace(record, **changes)


class RefreshExecutionTests(TestCase):
    def setUp(self) -> None:
        self.registry = SourceRegistry.load(ROOT / "sources.yaml")
        persist_records(
            [valid_record()],
            self.registry,
            as_of=date(2026, 8, 30),
            command_name="sync_exhibitions",
        )
        self.exhibition = Exhibition.objects.get()
        self.exhibition.last_verified_at = datetime(
            2026, 8, 28, 3, 0, tzinfo=UTC
        )
        self.exhibition.save(update_fields=("last_verified_at", "updated_at"))

    def test_successful_refresh_records_success_and_updates_verification_time(
        self,
    ) -> None:
        summary = refresh_exhibitions(
            [self.exhibition],
            collect=lambda: [valid_record()],
            registry=self.registry,
            as_of=date(2026, 8, 31),
            now=datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
            command_name="refresh_due_exhibitions",
        )

        self.exhibition.refresh_from_db()
        run = IngestionRun.objects.get(pk=summary.run_id)
        verification = VerificationRecord.objects.get(ingestion_run=run)
        self.assertEqual(run.status, IngestionRun.Status.SUCCESS)
        self.assertEqual(summary.success_count, 1)
        self.assertEqual(summary.failure_count, 0)
        self.assertEqual(
            self.exhibition.last_verified_at,
            datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
        )
        self.assertEqual(self.exhibition.freshness, Exhibition.Freshness.FRESH)
        self.assertEqual(verification.outcome, VerificationRecord.Outcome.SUCCESS)

    def test_collection_failure_preserves_last_normal_canonical_and_evidence(
        self,
    ) -> None:
        original_verified_at = self.exhibition.last_verified_at
        original_values = (
            self.exhibition.title,
            self.exhibition.start_date,
            self.exhibition.end_date,
            self.exhibition.venue,
            self.exhibition.lifecycle,
            self.exhibition.official_url,
        )
        original_evidence = list(
            FieldEvidence.objects.order_by("id").values_list(
                "field_name", "canonical_value", "adopted"
            )
        )

        def unavailable_source() -> list[RawExhibitionRecord]:
            raise OSError("source unavailable")

        with self.assertRaisesRegex(RefreshExecutionError, "source unavailable"):
            refresh_exhibitions(
                [self.exhibition],
                collect=unavailable_source,
                registry=self.registry,
                as_of=date(2026, 8, 31),
                now=datetime(2026, 8, 31, 3, 0, 0, 1, tzinfo=UTC),
                command_name="refresh_due_exhibitions",
            )

        self.exhibition.refresh_from_db()
        run = IngestionRun.objects.get(command="refresh_due_exhibitions")
        self.assertEqual(run.status, IngestionRun.Status.FAILED)
        self.assertIn("source unavailable", run.error_message)
        self.assertEqual(self.exhibition.last_verified_at, original_verified_at)
        self.assertEqual(
            (
                self.exhibition.title,
                self.exhibition.start_date,
                self.exhibition.end_date,
                self.exhibition.venue,
                self.exhibition.lifecycle,
                self.exhibition.official_url,
            ),
            original_values,
        )
        self.assertEqual(
            list(
                FieldEvidence.objects.order_by("id").values_list(
                    "field_name", "canonical_value", "adopted"
                )
            ),
            original_evidence,
        )
        self.assertEqual(self.exhibition.freshness, Exhibition.Freshness.STALE)
        self.assertEqual(
            VerificationRecord.objects.get().outcome,
            VerificationRecord.Outcome.FAILED,
        )

    def test_refresh_scope_does_not_persist_records_outside_target(self) -> None:
        other_record = valid_record(
            source_record_id="37608",
            title="다른 전시",
            start_date="2026-10-01",
            end_date="2026-10-31",
            official_url=(
                "https://www.sejongpac.or.kr/portal/performance/performance/"
                "performTicket.do?performIdx=37608&menuNo=200558"
            ),
            raw={"PERFORM_IDX": "37608", "TITLE": "다른 전시"},
        )
        persist_records(
            [other_record],
            self.registry,
            as_of=date(2026, 8, 30),
            command_name="sync_exhibitions",
        )
        other_exhibition = Exhibition.objects.exclude(pk=self.exhibition.pk).get()
        other_verified_at = datetime(2026, 8, 27, 3, 0, tzinfo=UTC)
        other_exhibition.last_verified_at = other_verified_at
        other_exhibition.save(update_fields=("last_verified_at", "updated_at"))

        summary = refresh_exhibitions(
            [self.exhibition],
            collect=lambda: [valid_record(), other_record],
            registry=self.registry,
            as_of=date(2026, 8, 31),
            now=datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
            command_name="refresh_exhibition",
        )

        other_exhibition.refresh_from_db()
        run = IngestionRun.objects.get(pk=summary.run_id)
        self.assertEqual(other_exhibition.last_verified_at, other_verified_at)
        self.assertFalse(
            VerificationRecord.objects.filter(exhibition=other_exhibition).exists()
        )
        self.assertEqual(run.observations.count(), 1)
        self.assertEqual(
            run.observations.get().source_record.source_record_id,
            "37607",
        )

    def test_missing_target_record_is_failure_without_deleting_canonical(self) -> None:
        original_title = self.exhibition.title

        with self.assertRaisesRegex(RefreshExecutionError, "not returned"):
            refresh_exhibitions(
                [self.exhibition],
                collect=lambda: [],
                registry=self.registry,
                as_of=date(2026, 8, 31),
                now=datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
                command_name="refresh_exhibition",
            )

        self.exhibition.refresh_from_db()
        self.assertEqual(self.exhibition.title, original_title)
        self.assertTrue(Exhibition.objects.filter(pk=self.exhibition.pk).exists())
        self.assertEqual(
            IngestionRun.objects.get(command="refresh_exhibition").status,
            IngestionRun.Status.FAILED,
        )

    def test_quality_failure_preserves_canonical_evidence_and_verification_time(
        self,
    ) -> None:
        original_verified_at = self.exhibition.last_verified_at
        original_title = self.exhibition.title
        original_evidence = list(
            FieldEvidence.objects.order_by("id").values_list(
                "field_name", "canonical_value", "adopted"
            )
        )
        invalid_record = valid_record(official_url=None)

        with self.assertRaisesRegex(RefreshExecutionError, "failed quality"):
            refresh_exhibitions(
                [self.exhibition],
                collect=lambda: [invalid_record],
                registry=self.registry,
                as_of=date(2026, 8, 31),
                now=datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
                command_name="refresh_exhibition",
            )

        self.exhibition.refresh_from_db()
        self.assertEqual(self.exhibition.title, original_title)
        self.assertEqual(self.exhibition.last_verified_at, original_verified_at)
        self.assertEqual(
            list(
                FieldEvidence.objects.order_by("id").values_list(
                    "field_name", "canonical_value", "adopted"
                )
            ),
            original_evidence,
        )
        self.assertEqual(
            IngestionRun.objects.get(command="refresh_exhibition").status,
            IngestionRun.Status.FAILED,
        )
        self.assertEqual(
            VerificationRecord.objects.get().outcome,
            VerificationRecord.Outcome.FAILED,
        )

    def test_normalization_exception_preserves_canonical_and_records_failure(
        self,
    ) -> None:
        class InvalidText:
            def __str__(self) -> str:
                raise ValueError("normalization failed")

        original_verified_at = self.exhibition.last_verified_at
        original_title = self.exhibition.title
        malformed_record = valid_record(title=InvalidText())

        with self.assertRaisesRegex(RefreshExecutionError, "normalization failed"):
            refresh_exhibitions(
                [self.exhibition],
                collect=lambda: [malformed_record],
                registry=self.registry,
                as_of=date(2026, 8, 31),
                now=datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
                command_name="refresh_exhibition",
            )

        self.exhibition.refresh_from_db()
        run = IngestionRun.objects.get(command="refresh_exhibition")
        self.assertEqual(self.exhibition.title, original_title)
        self.assertEqual(self.exhibition.last_verified_at, original_verified_at)
        self.assertEqual(run.status, IngestionRun.Status.FAILED)
        self.assertIn("normalization failed", run.error_message)
        self.assertEqual(
            VerificationRecord.objects.get().outcome,
            VerificationRecord.Outcome.FAILED,
        )

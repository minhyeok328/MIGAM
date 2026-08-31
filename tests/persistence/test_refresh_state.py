from datetime import date, datetime, timezone as datetime_timezone

from django.test import TestCase

from backend.apps.catalog.models import Exhibition, Institution, VerificationRecord
from backend.apps.sources.models import IngestionRun
from backend.data_pipeline.freshness.state import (
    apply_time_based_freshness,
    record_refresh_failure,
    record_refresh_success,
)


UTC = datetime_timezone.utc


class RefreshStateTests(TestCase):
    def setUp(self) -> None:
        institution = Institution.objects.create(
            registry_id="refresh-state-institution",
            name="상태 테스트 기관",
            region_area="서울",
            region_district="종로구",
        )
        self.exhibition = Exhibition.objects.create(
            institution=institution,
            title="마지막 정상 정본",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 9, 30),
            venue="원래 전시장",
            region_area="서울",
            region_district="종로구",
            lifecycle=Exhibition.Lifecycle.CURRENT,
            official_url="https://example.com/exhibitions/original",
            last_verified_at=datetime(2026, 8, 28, 3, 0, tzinfo=UTC),
        )

    def ingestion_run(self, status: str) -> IngestionRun:
        return IngestionRun.objects.create(
            command="refresh_due_exhibitions",
            status=status,
            finished_at=datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
        )

    def test_time_based_refresh_marks_only_overdue_periodic_exhibitions_stale(
        self,
    ) -> None:
        ended = Exhibition.objects.create(
            institution=self.exhibition.institution,
            title="종료 전시",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 8, 1),
            venue="종료 전시장",
            region_area="서울",
            region_district="종로구",
            lifecycle=Exhibition.Lifecycle.ENDED,
            official_url="https://example.com/exhibitions/ended",
            last_verified_at=datetime(2026, 7, 30, 3, 0, tzinfo=UTC),
        )

        updated_ids = apply_time_based_freshness(
            Exhibition.objects.all(),
            now=datetime(2026, 8, 31, 3, 0, 0, 1, tzinfo=UTC),
        )

        self.exhibition.refresh_from_db()
        ended.refresh_from_db()
        self.assertEqual(
            updated_ids,
            (self.exhibition.pk,),
        )
        self.assertEqual(self.exhibition.freshness, Exhibition.Freshness.STALE)
        self.assertEqual(ended.freshness, Exhibition.Freshness.FRESH)

    def test_first_failed_run_preserves_last_verified_canonical(self) -> None:
        failed_run = self.ingestion_run(IngestionRun.Status.FAILED)
        original_verified_at = self.exhibition.last_verified_at

        record_refresh_failure(
            self.exhibition,
            ingestion_run=failed_run,
            checked_at=datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
            error_message="temporary timeout",
        )

        self.exhibition.refresh_from_db()
        record = VerificationRecord.objects.get()
        self.assertEqual(self.exhibition.title, "마지막 정상 정본")
        self.assertEqual(self.exhibition.venue, "원래 전시장")
        self.assertEqual(self.exhibition.last_verified_at, original_verified_at)
        self.assertEqual(self.exhibition.freshness, Exhibition.Freshness.FRESH)
        self.assertEqual(self.exhibition.eligibility, Exhibition.Eligibility.VERIFIED)
        self.assertEqual(record.outcome, VerificationRecord.Outcome.FAILED)
        self.assertEqual(record.error_message, "temporary timeout")

    def test_two_distinct_consecutive_failed_runs_make_record_unverified(self) -> None:
        first_run = self.ingestion_run(IngestionRun.Status.FAILED)
        second_run = self.ingestion_run(IngestionRun.Status.FAILED)

        record_refresh_failure(
            self.exhibition,
            ingestion_run=first_run,
            checked_at=datetime(2026, 8, 30, 3, 0, tzinfo=UTC),
            error_message="first failure",
        )
        record_refresh_failure(
            self.exhibition,
            ingestion_run=second_run,
            checked_at=datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
            error_message="second failure",
        )

        self.exhibition.refresh_from_db()
        self.assertEqual(
            self.exhibition.freshness,
            Exhibition.Freshness.UNVERIFIED,
        )
        self.assertEqual(
            self.exhibition.eligibility,
            Exhibition.Eligibility.DISCOVERY_ONLY,
        )

    def test_excluded_record_does_not_become_unverified_after_failures(self) -> None:
        self.exhibition.freshness = Exhibition.Freshness.STALE
        self.exhibition.eligibility = Exhibition.Eligibility.EXCLUDED
        self.exhibition.save(
            update_fields=("freshness", "eligibility", "updated_at")
        )
        first_run = self.ingestion_run(IngestionRun.Status.FAILED)
        second_run = self.ingestion_run(IngestionRun.Status.FAILED)

        record_refresh_failure(
            self.exhibition,
            ingestion_run=first_run,
            checked_at=datetime(2026, 8, 30, 3, 0, tzinfo=UTC),
            error_message="first failure",
        )
        record_refresh_failure(
            self.exhibition,
            ingestion_run=second_run,
            checked_at=datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
            error_message="second failure",
        )

        self.exhibition.refresh_from_db()
        self.assertEqual(self.exhibition.freshness, Exhibition.Freshness.STALE)
        self.assertEqual(
            self.exhibition.eligibility,
            Exhibition.Eligibility.EXCLUDED,
        )

    def test_failure_transition_uses_current_locked_exhibition_state(self) -> None:
        stale_instance = Exhibition.objects.get(pk=self.exhibition.pk)
        Exhibition.objects.filter(pk=self.exhibition.pk).update(
            freshness=Exhibition.Freshness.STALE,
            eligibility=Exhibition.Eligibility.EXCLUDED,
        )
        first_run = self.ingestion_run(IngestionRun.Status.FAILED)
        second_run = self.ingestion_run(IngestionRun.Status.FAILED)

        record_refresh_failure(
            stale_instance,
            ingestion_run=first_run,
            checked_at=datetime(2026, 8, 30, 3, 0, tzinfo=UTC),
            error_message="first failure",
        )
        record_refresh_failure(
            stale_instance,
            ingestion_run=second_run,
            checked_at=datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
            error_message="second failure",
        )

        self.exhibition.refresh_from_db()
        self.assertEqual(self.exhibition.freshness, Exhibition.Freshness.STALE)
        self.assertEqual(
            self.exhibition.eligibility,
            Exhibition.Eligibility.EXCLUDED,
        )

    def test_repeated_failure_recording_for_same_run_counts_once(self) -> None:
        failed_run = self.ingestion_run(IngestionRun.Status.FAILED)

        for error_message in ("request 1", "request retry"):
            record_refresh_failure(
                self.exhibition,
                ingestion_run=failed_run,
                checked_at=datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
                error_message=error_message,
            )

        self.exhibition.refresh_from_db()
        self.assertEqual(VerificationRecord.objects.count(), 1)
        self.assertEqual(self.exhibition.freshness, Exhibition.Freshness.FRESH)

    def test_success_after_failures_restores_fresh_verified_state(self) -> None:
        first_run = self.ingestion_run(IngestionRun.Status.FAILED)
        second_run = self.ingestion_run(IngestionRun.Status.FAILED)
        success_run = self.ingestion_run(IngestionRun.Status.SUCCESS)
        record_refresh_failure(
            self.exhibition,
            ingestion_run=first_run,
            checked_at=datetime(2026, 8, 29, 3, 0, tzinfo=UTC),
            error_message="first failure",
        )
        record_refresh_failure(
            self.exhibition,
            ingestion_run=second_run,
            checked_at=datetime(2026, 8, 30, 3, 0, tzinfo=UTC),
            error_message="second failure",
        )

        record_refresh_success(
            self.exhibition,
            ingestion_run=success_run,
            checked_at=datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
            source_id="official-source",
            source_record_id="record-1",
        )

        self.exhibition.refresh_from_db()
        self.assertEqual(self.exhibition.freshness, Exhibition.Freshness.FRESH)
        self.assertEqual(self.exhibition.eligibility, Exhibition.Eligibility.VERIFIED)
        self.assertEqual(
            self.exhibition.last_verified_at,
            datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
        )
        self.assertEqual(
            list(
                VerificationRecord.objects.order_by("checked_at").values_list(
                    "outcome", flat=True
                )
            ),
            [
                VerificationRecord.Outcome.FAILED,
                VerificationRecord.Outcome.FAILED,
                VerificationRecord.Outcome.SUCCESS,
            ],
        )

from dataclasses import replace
from datetime import date, datetime, timezone as datetime_timezone
from importlib import import_module, util
from pathlib import Path
from zoneinfo import ZoneInfo

from django.test import TestCase

from backend.apps.catalog.models import Exhibition, SourceConflict
from backend.apps.sources.models import (
    CollectionIssue,
    IngestionRun,
    InstitutionAllowlistEntry,
    InstitutionRunResult,
    SourceRecord,
)
from backend.data_pipeline.institution_runs import record_institution_result
from backend.data_pipeline.models import RawExhibitionRecord
from backend.data_pipeline.persistence import persist_records
from backend.data_pipeline.registry import SourceRegistry
from backend.data_pipeline.registry_state import sync_registry_state


ROOT = Path(__file__).resolve().parents[2]
SEOUL = ZoneInfo("Asia/Seoul")


def seoul_time(day: int, hour: int = 0) -> datetime:
    return datetime(2026, 9, day, hour, tzinfo=SEOUL)


def valid_record(**changes: object) -> RawExhibitionRecord:
    record = RawExhibitionRecord(
        source_id="seoul-oa-2708-sejong",
        institution_id="sejong-center-main-exhibition",
        source_record_id="37607",
        source_owner="세종문화회관",
        title="제3회 호반미술상",
        start_date="2026-09-02",
        end_date="2026-09-29",
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


class InstitutionQualificationTests(TestCase):
    def setUp(self) -> None:
        self.registry = SourceRegistry.load(ROOT / "sources.yaml")
        sync_registry_state(self.registry)
        self.entry = InstitutionAllowlistEntry.objects.get(
            registry_id="sejong-center-main-exhibition"
        )
        self.record_sequence = 0

    def feature(self) -> tuple[object, object]:
        source_models = import_module("backend.apps.sources.models")
        for model_name in (
            "InstitutionQualificationRun",
            "PromotionEvidence",
        ):
            self.assertTrue(
                hasattr(source_models, model_name),
                f"sources.{model_name} model is missing",
            )
        self.assertIsNotNone(
            util.find_spec("backend.data_pipeline.qualification"),
            "qualification service is missing",
        )
        return (
            source_models.InstitutionQualificationRun,
            source_models.PromotionEvidence,
        )

    def qualification_run(
        self,
        *,
        finished_at: datetime,
        status: str = InstitutionRunResult.Status.SUCCESS,
        meaningful: bool = False,
        received_count: int = 5,
    ) -> tuple[IngestionRun, InstitutionRunResult]:
        run = IngestionRun.objects.create(
            command="test-qualification",
            qualification_mode=True,
        )
        if meaningful:
            self.record_sequence += 1
            persist_records(
                [
                    valid_record(
                        title=f"승격 검증 전시 {self.record_sequence}",
                    )
                ],
                self.registry,
                as_of=date(2026, 9, 1),
                command_name="test-qualification",
                run=run,
            )
        run.status = (
            IngestionRun.Status.SUCCESS
            if status == InstitutionRunResult.Status.SUCCESS
            else IngestionRun.Status.FAILED
        )
        run.finished_at = finished_at
        run.save(update_fields=("status", "finished_at"))
        result = record_institution_result(
            run,
            self.entry,
            status=status,
            received_count=received_count,
            verified_count=received_count,
            error_message=("qualification failed" if status == "FAILED" else ""),
            finished_at=finished_at,
        )
        self.entry.refresh_from_db()
        return run, result

    def test_registry_target_and_qualification_creation_boundaries(self) -> None:
        InstitutionQualificationRun, _ = self.feature()
        self.assertEqual(self.entry.qualification_target_count, 5)

        normal_run = IngestionRun.objects.create(command="normal-sync")
        record_institution_result(
            normal_run,
            self.entry,
            status=InstitutionRunResult.Status.SUCCESS,
            finished_at=seoul_time(1),
        )
        self.assertFalse(InstitutionQualificationRun.objects.exists())

        self.entry.lifecycle = InstitutionAllowlistEntry.Lifecycle.ACTIVE
        self.entry.save(update_fields=("lifecycle", "updated_at"))
        self.qualification_run(finished_at=seoul_time(2))
        self.assertFalse(InstitutionQualificationRun.objects.exists())

    def test_failed_provisional_result_records_failed_qualification(self) -> None:
        InstitutionQualificationRun, _ = self.feature()

        _, result = self.qualification_run(
            finished_at=seoul_time(1),
            status=InstitutionRunResult.Status.FAILED,
            received_count=4,
        )

        qualification = InstitutionQualificationRun.objects.get(
            institution_result=result
        )
        self.assertEqual(qualification.status, "FAILED")
        self.assertEqual(qualification.service_date, date(2026, 9, 1))
        self.assertEqual(qualification.target_count, 5)
        self.assertEqual(qualification.final_missing_core_target_count, 1)
        self.assertIsNone(qualification.retry_count)
        self.assertIn("qualification failed", qualification.failure_reasons)

    def test_missing_target_cannot_be_recorded_as_success(self) -> None:
        InstitutionQualificationRun, _ = self.feature()
        run = IngestionRun.objects.create(
            command="test-qualification",
            qualification_mode=True,
        )

        result = record_institution_result(
            run,
            self.entry,
            status=InstitutionRunResult.Status.SUCCESS,
            received_count=4,
            verified_count=4,
            finished_at=seoul_time(1),
        )

        self.entry.refresh_from_db()
        qualification = InstitutionQualificationRun.objects.get(
            institution_result=result
        )
        self.assertEqual(result.status, InstitutionRunResult.Status.FAILED)
        self.assertEqual(qualification.status, InstitutionQualificationRun.Status.FAILED)
        self.assertEqual(self.entry.health, InstitutionAllowlistEntry.Health.DEGRADED)
        self.assertIn("QUALIFICATION_TARGET_MISSING", result.error_message)

    def test_exact_fourteen_days_and_three_dates_promote_with_evidence(self) -> None:
        InstitutionQualificationRun, PromotionEvidence = self.feature()

        first_run, _ = self.qualification_run(
            finished_at=seoul_time(1),
            meaningful=True,
        )
        self.qualification_run(finished_at=seoul_time(7))
        _, final_result = self.qualification_run(finished_at=seoul_time(13))

        self.entry.refresh_from_db()
        final_result.refresh_from_db()
        evidence = PromotionEvidence.objects.get(institution=self.entry)
        self.assertEqual(self.entry.lifecycle, "ACTIVE")
        self.assertEqual(self.entry.lifecycle_changed_at, seoul_time(13))
        self.assertEqual(self.entry.lifecycle_changed_by, "SYSTEM")
        self.assertEqual(
            self.entry.lifecycle_change_reason,
            "QUALIFICATION_PROMOTION",
        )
        self.assertEqual(final_result.lifecycle_after, "ACTIVE")
        self.assertEqual(
            set(evidence.qualification_runs.values_list("service_date", flat=True)),
            {date(2026, 9, 1), date(2026, 9, 7), date(2026, 9, 13)},
        )
        self.assertEqual(evidence.qualification_runs.count(), 3)
        self.assertEqual(evidence.last_qualification_run.service_date, date(2026, 9, 13))
        self.assertEqual(evidence.meaningful_change_history.ingestion_run, first_run)
        self.assertEqual(InstitutionQualificationRun.objects.count(), 3)

    def test_same_seoul_date_counts_once(self) -> None:
        _, PromotionEvidence = self.feature()

        self.qualification_run(finished_at=seoul_time(1, 1), meaningful=True)
        self.qualification_run(finished_at=seoul_time(1, 20))
        self.qualification_run(finished_at=seoul_time(13))

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.lifecycle, "PROVISIONAL")
        self.assertFalse(PromotionEvidence.objects.exists())

    def test_one_minute_before_fourteen_days_does_not_promote(self) -> None:
        _, PromotionEvidence = self.feature()

        self.qualification_run(finished_at=seoul_time(1), meaningful=True)
        self.qualification_run(finished_at=seoul_time(7))
        self.qualification_run(finished_at=seoul_time(12, 23))

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.lifecycle, "PROVISIONAL")
        self.assertFalse(PromotionEvidence.objects.exists())

    def test_service_date_uses_the_seoul_midnight_boundary(self) -> None:
        InstitutionQualificationRun, _ = self.feature()

        self.qualification_run(
            finished_at=datetime(
                2026,
                9,
                1,
                14,
                59,
                tzinfo=datetime_timezone.utc,
            )
        )
        self.qualification_run(
            finished_at=datetime(
                2026,
                9,
                1,
                15,
                0,
                tzinfo=datetime_timezone.utc,
            )
        )

        self.assertEqual(
            list(
                InstitutionQualificationRun.objects.order_by("finished_at").values_list(
                    "service_date",
                    flat=True,
                )
            ),
            [date(2026, 9, 1), date(2026, 9, 2)],
        )

    def test_failure_resets_the_success_sequence(self) -> None:
        _, PromotionEvidence = self.feature()

        self.qualification_run(finished_at=seoul_time(1), meaningful=True)
        self.qualification_run(
            finished_at=seoul_time(5),
            status=InstitutionRunResult.Status.FAILED,
            received_count=4,
        )
        self.qualification_run(finished_at=seoul_time(7))
        self.qualification_run(finished_at=seoul_time(13))

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.lifecycle, "PROVISIONAL")
        self.assertFalse(PromotionEvidence.objects.exists())

    def test_meaningful_change_is_required(self) -> None:
        _, PromotionEvidence = self.feature()

        self.qualification_run(finished_at=seoul_time(1))
        self.qualification_run(finished_at=seoul_time(7))
        self.qualification_run(finished_at=seoul_time(13))

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.lifecycle, "PROVISIONAL")
        self.assertFalse(PromotionEvidence.objects.exists())

    def test_non_normal_source_blocks_promotion(self) -> None:
        _, PromotionEvidence = self.feature()

        self.qualification_run(finished_at=seoul_time(1), meaningful=True)
        self.qualification_run(finished_at=seoul_time(7))
        self.entry.source.operation_status = "PAUSED"
        self.entry.source.save(update_fields=("operation_status", "updated_at"))
        self.qualification_run(finished_at=seoul_time(13))

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.lifecycle, "PROVISIONAL")
        self.assertFalse(PromotionEvidence.objects.exists())

    def test_open_source_conflict_blocks_promotion(self) -> None:
        _, PromotionEvidence = self.feature()

        self.qualification_run(finished_at=seoul_time(1), meaningful=True)
        self.qualification_run(finished_at=seoul_time(7))
        SourceConflict.objects.create(
            exhibition=Exhibition.objects.get(),
            field_name="venue",
            canonical_value="세종미술관 1·2관",
            candidate_value="세종미술관 2관",
            candidate_source_record=SourceRecord.objects.get(),
        )
        self.qualification_run(finished_at=seoul_time(13))

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.lifecycle, "PROVISIONAL")
        self.assertFalse(PromotionEvidence.objects.exists())

    def test_open_critical_is_preserved_on_failed_qualification(self) -> None:
        InstitutionQualificationRun, PromotionEvidence = self.feature()
        CollectionIssue.objects.create(
            registry_id="qualification-critical",
            classification=CollectionIssue.Classification.ACCESS_BLOCK,
            scope=CollectionIssue.Scope.ENTRY,
            source=self.entry.source,
            institution=self.entry,
            status=CollectionIssue.Status.OPEN,
        )

        _, result = self.qualification_run(
            finished_at=seoul_time(13),
            status=InstitutionRunResult.Status.FAILED,
        )

        qualification = InstitutionQualificationRun.objects.get(
            institution_result=result
        )
        self.assertEqual(qualification.status, "FAILED")
        self.assertEqual(qualification.policy_access_issue_count, 1)
        self.assertFalse(PromotionEvidence.objects.exists())

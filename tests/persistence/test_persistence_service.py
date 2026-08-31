from datetime import date
from pathlib import Path

from django.test import TestCase

from backend.apps.data_quality.models import ExhibitionCandidate
from backend.apps.sources.models import (
    IngestionObservation,
    IngestionRun,
    SourceRecord,
)
from backend.data_pipeline.models import RawExhibitionRecord
from backend.data_pipeline.persistence import persist_records
from backend.data_pipeline.registry import SourceRegistry


ROOT = Path(__file__).resolve().parents[2]


def valid_record() -> RawExhibitionRecord:
    return RawExhibitionRecord(
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
        official_url="https://www.sejongpac.or.kr/portal/performance/performance/performTicket.do?performIdx=37607&menuNo=200558",
        raw={"PERFORM_IDX": "37607", "TITLE": "제3회 호반미술상"},
    )


def quarantined_record() -> RawExhibitionRecord:
    return RawExhibitionRecord(
        source_id="kcisa-cultureinfo",
        institution_id="nfm-seoul-main",
        source_record_id="348222",
        source_owner="한국문화정보원",
        title="다시 만난 하늘",
        start_date="20250917",
        end_date="20251103",
        venue="국립민속박물관",
        region_area="서울",
        region_district="종로구",
        official_url=None,
        raw={"seq": "348222", "url": None},
    )


class PersistenceServiceTests(TestCase):
    def setUp(self) -> None:
        self.registry = SourceRegistry.load(ROOT / "sources.yaml")

    def test_persists_verified_and_quarantined_candidates_with_run_counts(self) -> None:
        summary = persist_records(
            [valid_record(), quarantined_record()],
            self.registry,
            as_of=date(2026, 8, 30),
            command_name="sync_exhibitions",
        )

        run = IngestionRun.objects.get(pk=summary.run_id)
        self.assertEqual(run.status, IngestionRun.Status.SUCCESS)
        self.assertEqual(run.received_count, 2)
        self.assertEqual(run.verified_count, 1)
        self.assertEqual(run.excluded_count, 1)
        self.assertEqual(run.quarantined_count, 1)
        self.assertEqual(SourceRecord.objects.count(), 2)
        self.assertEqual(IngestionObservation.objects.count(), 2)
        self.assertEqual(ExhibitionCandidate.objects.count(), 2)
        quarantined = ExhibitionCandidate.objects.get(quarantined=True)
        self.assertEqual(quarantined.core_result, "FAIL")
        self.assertIn(
            "RECORD_EXCEPTION",
            {issue["code"] for issue in quarantined.quality_issues},
        )

    def test_reprocessing_same_input_reuses_source_version_and_candidate(self) -> None:
        first = persist_records(
            [valid_record()],
            self.registry,
            as_of=date(2026, 8, 30),
            command_name="sync_exhibitions",
        )
        second = persist_records(
            [valid_record()],
            self.registry,
            as_of=date(2026, 8, 30),
            command_name="sync_exhibitions",
        )

        self.assertNotEqual(first.run_id, second.run_id)
        self.assertEqual(IngestionRun.objects.count(), 2)
        self.assertEqual(SourceRecord.objects.count(), 1)
        self.assertEqual(ExhibitionCandidate.objects.count(), 1)
        self.assertEqual(IngestionObservation.objects.count(), 2)

    def test_uses_precreated_run_for_collection_failure_traceability(self) -> None:
        run = IngestionRun.objects.create(command="refresh_due_exhibitions")

        summary = persist_records(
            [valid_record()],
            self.registry,
            as_of=date(2026, 8, 30),
            command_name="refresh_due_exhibitions",
            run=run,
        )

        self.assertEqual(summary.run_id, run.pk)
        self.assertEqual(IngestionRun.objects.count(), 1)
        run.refresh_from_db()
        self.assertEqual(run.status, IngestionRun.Status.SUCCESS)

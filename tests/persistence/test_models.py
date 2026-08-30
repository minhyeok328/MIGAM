from datetime import date

from django.db import IntegrityError, transaction
from django.test import TestCase

from backend.apps.data_quality.models import ExhibitionCandidate
from backend.apps.sources.models import (
    IngestionObservation,
    IngestionRun,
    SourceRecord,
)


class IngestionStorageModelTests(TestCase):
    def test_preserves_source_version_and_normalization_candidate_separately(self) -> None:
        run = IngestionRun.objects.create(command="sync_exhibitions")
        source_record = SourceRecord.objects.create(
            source_id="seoul-oa-2708-sejong",
            institution_id="sejong-center-main-exhibition",
            source_record_id="37607",
            source_owner="세종문화회관",
            payload={"TITLE": "제3회 호반미술상"},
            content_hash="a" * 64,
        )
        observation = IngestionObservation.objects.create(
            ingestion_run=run,
            source_record=source_record,
        )
        candidate = ExhibitionCandidate.objects.create(
            source_record=source_record,
            rule_version="1.0.0",
            title="제3회 호반미술상",
            start_date=date(2026, 9, 2),
            end_date=date(2026, 9, 29),
            venue="세종미술관 1·2관",
            region_area="서울",
            region_district="종로구",
            lifecycle="UPCOMING",
            official_url="https://www.sejongpac.or.kr/example/37607",
            core_result="PASS",
            eligibility="VERIFIED",
            quality_issues=[],
        )

        self.assertEqual(observation.source_record, source_record)
        self.assertEqual(candidate.source_record.payload["TITLE"], "제3회 호반미술상")
        self.assertEqual(candidate.core_result, "PASS")

    def test_rejects_duplicate_source_versions_and_rule_candidates(self) -> None:
        source_record = SourceRecord.objects.create(
            source_id="kcisa-cultureinfo",
            institution_id="suma-haenggung",
            source_record_id="394181",
            source_owner="한국문화정보원",
            payload={"seq": "394181"},
            content_hash="b" * 64,
        )
        duplicate_source = {
            "source_id": source_record.source_id,
            "institution_id": source_record.institution_id,
            "source_record_id": source_record.source_record_id,
            "source_owner": source_record.source_owner,
            "payload": source_record.payload,
            "content_hash": source_record.content_hash,
        }

        with self.assertRaises(IntegrityError), transaction.atomic():
            SourceRecord.objects.create(**duplicate_source)

        ExhibitionCandidate.objects.create(
            source_record=source_record,
            rule_version="1.0.0",
            lifecycle="CURRENT",
            core_result="PASS",
            eligibility="VERIFIED",
            quality_issues=[],
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            ExhibitionCandidate.objects.create(
                source_record=source_record,
                rule_version="1.0.0",
                lifecycle="CURRENT",
                core_result="PASS",
                eligibility="VERIFIED",
                quality_issues=[],
            )

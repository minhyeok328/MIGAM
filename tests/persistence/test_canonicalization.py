from dataclasses import replace
from datetime import date
from pathlib import Path

from django.test import TestCase

from backend.apps.catalog.models import (
    DuplicateCandidate,
    Exhibition,
    ExhibitionSourceLink,
    FieldEvidence,
    SourceConflict,
)
from backend.apps.data_quality.models import ExhibitionCandidate
from backend.apps.sources.models import SourceRecord
from backend.data_pipeline.canonicalization import canonicalize_candidates
from backend.data_pipeline.models import RawExhibitionRecord
from backend.data_pipeline.persistence import persist_records
from backend.data_pipeline.registry import SourceRegistry


ROOT = Path(__file__).resolve().parents[2]


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


def candidate(
    *,
    source_id: str,
    source_record_id: str,
    institution_id: str = "shared-institution",
    title: str = "빛의 전시",
    start_date: date = date(2026, 9, 1),
    end_date: date = date(2026, 10, 1),
    venue: str = "공간 1",
    official_url: str = "https://example.com/exhibitions/1",
) -> ExhibitionCandidate:
    source_record = SourceRecord.objects.create(
        source_id=source_id,
        institution_id=institution_id,
        source_record_id=source_record_id,
        source_owner="공식 기관",
        payload={
            "title": title,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "venue": venue,
            "region_area": "서울",
            "region_district": "종로구",
            "official_url": official_url,
        },
        content_hash=(source_id + source_record_id).ljust(64, "0")[:64],
    )
    return ExhibitionCandidate.objects.create(
        source_record=source_record,
        rule_version="1.0.0",
        title=title,
        start_date=start_date,
        end_date=end_date,
        venue=venue,
        region_area="서울",
        region_district="종로구",
        lifecycle="CURRENT",
        official_url=official_url,
        core_result="PASS",
        eligibility="VERIFIED",
        quality_issues=[],
    )


class CanonicalizationTests(TestCase):
    def setUp(self) -> None:
        self.registry = SourceRegistry.load(ROOT / "sources.yaml")

    def test_promotes_only_verified_candidates_and_records_field_evidence(self) -> None:
        persist_records(
            [valid_record(), quarantined_record()],
            self.registry,
            as_of=date(2026, 8, 30),
            command_name="sync_exhibitions",
        )

        exhibition = Exhibition.objects.get()
        self.assertEqual(exhibition.title, "제3회 호반미술상")
        self.assertEqual(exhibition.eligibility, Exhibition.Eligibility.VERIFIED)
        self.assertEqual(ExhibitionSourceLink.objects.count(), 1)
        self.assertEqual(
            set(
                FieldEvidence.objects.filter(adopted=True).values_list(
                    "field_name", flat=True
                )
            ),
            {
                "title",
                "start_date",
                "end_date",
                "venue",
                "region_area",
                "region_district",
                "lifecycle",
                "official_url",
            },
        )

    def test_reprocessing_same_source_record_does_not_duplicate_canonical_data(self) -> None:
        for _ in range(2):
            persist_records(
                [valid_record()],
                self.registry,
                as_of=date(2026, 8, 30),
                command_name="sync_exhibitions",
            )

        self.assertEqual(Exhibition.objects.count(), 1)
        self.assertEqual(ExhibitionSourceLink.objects.count(), 1)
        self.assertEqual(FieldEvidence.objects.count(), 8)

    def test_new_version_of_same_official_id_updates_existing_canonical(self) -> None:
        persist_records(
            [valid_record()],
            self.registry,
            as_of=date(2026, 8, 30),
            command_name="sync_exhibitions",
        )
        persist_records(
            [valid_record(title="제3회 호반미술상 연장", end_date="2026-10-05")],
            self.registry,
            as_of=date(2026, 9, 1),
            command_name="sync_exhibitions",
        )

        exhibition = Exhibition.objects.get()
        self.assertEqual(exhibition.title, "제3회 호반미술상 연장")
        self.assertEqual(exhibition.end_date, date(2026, 10, 5))
        self.assertEqual(SourceRecord.objects.count(), 2)
        self.assertEqual(ExhibitionSourceLink.objects.count(), 1)
        self.assertEqual(
            FieldEvidence.objects.filter(field_name="title", adopted=True).count(),
            1,
        )
        self.assertEqual(
            FieldEvidence.objects.filter(field_name="title", adopted=False).count(),
            1,
        )

    def test_strong_cross_source_match_merges_one_canonical(self) -> None:
        first = candidate(source_id="official-a", source_record_id="a-1")
        second = candidate(source_id="official-b", source_record_id="b-1")

        canonicalize_candidates([first])
        canonicalize_candidates([second])

        self.assertEqual(Exhibition.objects.count(), 1)
        self.assertEqual(ExhibitionSourceLink.objects.count(), 2)

    def test_similar_record_with_different_period_stays_separate_for_review(self) -> None:
        first = candidate(source_id="official-a", source_record_id="a-1")
        second = candidate(
            source_id="official-b",
            source_record_id="b-1",
            start_date=date(2026, 11, 1),
            end_date=date(2026, 12, 1),
            venue="공간 2",
            official_url="https://example.com/exhibitions/2",
        )

        canonicalize_candidates([first])
        canonicalize_candidates([second])

        self.assertEqual(Exhibition.objects.count(), 2)
        duplicate = DuplicateCandidate.objects.get()
        self.assertEqual(duplicate.status, DuplicateCandidate.Status.OPEN)
        self.assertEqual(
            {duplicate.primary_exhibition_id, duplicate.related_exhibition_id},
            set(Exhibition.objects.values_list("id", flat=True)),
        )

    def test_conflicting_field_preserves_current_value_and_excludes_canonical(self) -> None:
        first = candidate(source_id="official-a", source_record_id="a-1")
        second = candidate(
            source_id="official-b",
            source_record_id="b-1",
            official_url="https://example.com/exhibitions/other",
        )

        canonicalize_candidates([first])
        canonicalize_candidates([second])

        exhibition = Exhibition.objects.get()
        self.assertEqual(exhibition.official_url, "https://example.com/exhibitions/1")
        self.assertEqual(exhibition.eligibility, Exhibition.Eligibility.EXCLUDED)
        conflict = SourceConflict.objects.get()
        self.assertEqual(conflict.field_name, "official_url")
        self.assertEqual(conflict.status, SourceConflict.Status.OPEN)
        self.assertTrue(
            FieldEvidence.objects.filter(
                field_name="official_url",
                source_record=second.source_record,
                adopted=False,
            ).exists()
        )

from datetime import date
import json
from pathlib import Path
import unittest

from backend.data_pipeline.models import RawExhibitionRecord
from backend.data_pipeline.normalization import normalize_record
from backend.data_pipeline.pipeline import process_records
from backend.data_pipeline.quality import evaluate_core_quality
from backend.data_pipeline.registry import SourceRegistry


ROOT = Path(__file__).resolve().parents[2]


class NormalizationQualityTests(unittest.TestCase):
    def test_normalizes_dates_and_passes_a_complete_official_record(self) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        raw = RawExhibitionRecord(
            source_id="seoul-oa-2708-sejong",
            institution_id="sejong-center-main-exhibition",
            source_record_id="37607",
            source_owner="세종문화회관",
            title="  제3회 호반미술상  ",
            start_date="2026.09.02",
            end_date="2026.09.29",
            venue="세종미술관 1·2관",
            region_area="서울",
            region_district="종로구",
            official_url="https://www.sejongpac.or.kr/portal/performance/performance/performTicket.do?performIdx=37607&menuNo=200558",
        )

        normalized = normalize_record(raw, as_of=date(2026, 8, 30))
        result = evaluate_core_quality(normalized, registry)

        self.assertEqual(normalized.title, "제3회 호반미술상")
        self.assertEqual(normalized.start_date, date(2026, 9, 2))
        self.assertEqual(normalized.end_date, date(2026, 9, 29))
        self.assertEqual(normalized.lifecycle, "UPCOMING")
        self.assertEqual(result.core_result, "PASS")
        self.assertEqual(result.eligibility, "VERIFIED")
        self.assertEqual(result.issues, ())

    def test_quarantines_a_registered_record_exception(self) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        raw = RawExhibitionRecord(
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
        )

        normalized = normalize_record(raw, as_of=date(2026, 8, 30))
        result = evaluate_core_quality(normalized, registry)

        self.assertEqual(result.core_result, "FAIL")
        self.assertEqual(result.eligibility, "EXCLUDED")
        self.assertTrue(result.quarantine)
        self.assertIn("RECORD_EXCEPTION", {issue.code for issue in result.issues})

    def test_reproduces_the_approved_qualification_fixture(self) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        fixture = json.loads(
            (ROOT / "fixtures" / "source-qualification.json").read_text(
                encoding="utf-8"
            )
        )
        records = []
        for item in fixture["records"]:
            source = registry.source(item["source_id"])
            region = item["region"]
            records.append(
                RawExhibitionRecord(
                    source_id=item["source_id"],
                    institution_id=item["institution_id"],
                    source_record_id=item["source_record_id"],
                    source_owner=source["owner"],
                    title=item["title"],
                    start_date=item["start_date"],
                    end_date=item["end_date"],
                    venue=item["venue"],
                    region_area=region["area"],
                    region_district=region["district"],
                    official_url=item["official_url"],
                )
            )

        processed = process_records(records, registry, as_of=date(2026, 8, 30))

        self.assertEqual(
            sum(item.quality.core_result == "PASS" for item in processed),
            24,
        )
        self.assertEqual(
            [
                item.normalized.raw_record.source_record_id
                for item in processed
                if item.quality.quarantine
            ],
            ["348222"],
        )


if __name__ == "__main__":
    unittest.main()

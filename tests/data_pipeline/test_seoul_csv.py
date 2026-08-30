from pathlib import Path
import unittest

from backend.data_pipeline.collectors.seoul_csv import (
    SeoulCsvCollector,
    SourceContractError,
)
from backend.data_pipeline.registry import SourceRegistry


ROOT = Path(__file__).resolve().parents[2]


class SeoulCsvCollectorTests(unittest.TestCase):
    def test_collects_official_korean_sejong_sheet_headers(self) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        collector = SeoulCsvCollector(registry, "seoul-oa-2708-sejong")
        csv_text = """공연 고유번호,공연 장르명,공연명,공연 시작일자,공연 종료일자,공연 장소목록,공연상세 URL
37607,기획전시,제 3회 호반미술상,20260902,20260929,"세종미술관 1관,세종미술관 2관",https://www.sejongpac.or.kr/portal/performance/performance/performTicket.do?performIdx=37607&menuNo=200558
"""

        try:
            records = collector.collect(csv_text.encode("cp949"))
        except SourceContractError as error:
            self.fail(f"official Seoul Sheet headers must be accepted: {error}")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source_record_id, "37607")
        self.assertEqual(records[0].title, "제 3회 호반미술상")

    def test_collects_official_korean_sema_sheet_headers(self) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        collector = SeoulCsvCollector(registry, "seoul-oa-15323-sema")
        csv_text = """전시NO,전시회명,전시장소,전시시작기간,전시끝기간,바로가기링크
1576627,서울시립 서서울미술관 플레이 라운지,서울시립 서서울미술관,2026-09-01,2026-10-11,https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1576627
"""

        try:
            records = collector.collect(csv_text.encode("cp949"))
        except SourceContractError as error:
            self.fail(f"official Seoul Sheet headers must be accepted: {error}")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source_record_id, "1576627")
        self.assertEqual(records[0].institution_id, "sema-seoseoul")

    def test_collects_only_allowlisted_sejong_exhibitions(self) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        collector = SeoulCsvCollector(registry, "seoul-oa-2708-sejong")
        csv_text = """PERFORM_IDX,GENRE_NAME,TITLE,START_DATE,END_DATE,PLACE_LIST,INFO_URL
37607,전시기타,제3회 호반미술상,2026-09-02,2026-09-29,"세종미술관 1관,세종미술관 2관",https://www.sejongpac.or.kr/portal/performance/performance/performTicket.do?performIdx=37607&menuNo=200558
99999,뮤지컬,제외할 공연,2026-09-02,2026-09-29,세종미술관 1관,https://www.sejongpac.or.kr/portal/performance/performance/performTicket.do?performIdx=99999&menuNo=200558
"""

        records = collector.collect(csv_text)

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.source_record_id, "37607")
        self.assertEqual(record.institution_id, "sejong-center-main-exhibition")
        self.assertEqual(record.title, "제3회 호반미술상")
        self.assertEqual(record.region_area, "서울")
        self.assertEqual(record.region_district, "종로구")
        self.assertNotIn("MAIN_IMG", record.raw)

    def test_rejects_csv_when_a_required_source_column_is_missing(self) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        collector = SeoulCsvCollector(registry, "seoul-oa-2708-sejong")
        csv_text = """PERFORM_IDX,GENRE_NAME,TITLE,START_DATE,END_DATE,PLACE_LIST
37607,전시기타,제3회 호반미술상,2026-09-02,2026-09-29,세종미술관 1관
"""

        with self.assertRaisesRegex(ValueError, "INFO_URL"):
            collector.collect(csv_text)

    def test_routes_sema_rows_to_the_exact_allowlisted_institution(self) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        collector = SeoulCsvCollector(registry, "seoul-oa-15323-sema")
        csv_text = """DP_EX_NO,DP_NAME,DP_START,DP_END,DP_PLACE,DP_LNK
1576627,플레이 라운지,2026-09-01,2026-10-11,서울시립 서서울미술관,https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1576627
1553791,마틴 파,2026-07-16,2026-10-18,서울시립 사진미술관,https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1553791
1111111,다른 분관 전시,2026-07-16,2026-10-18,서울시립 북서울미술관,https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1111111
"""

        records = collector.collect(csv_text)

        self.assertEqual(
            [(record.source_record_id, record.institution_id) for record in records],
            [
                ("1576627", "sema-seoseoul"),
                ("1553791", "sema-photo"),
            ],
        )

    def test_accepts_cp949_encoded_csv_downloads(self) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        collector = SeoulCsvCollector(registry, "seoul-oa-2708-sejong")
        csv_text = """PERFORM_IDX,GENRE_NAME,TITLE,START_DATE,END_DATE,PLACE_LIST,INFO_URL
37607,전시기타,제3회 호반미술상,2026-09-02,2026-09-29,세종미술관 1관,https://www.sejongpac.or.kr/portal/performance/performance/performTicket.do?performIdx=37607&menuNo=200558
"""

        records = collector.collect(csv_text.encode("cp949"))

        self.assertEqual(records[0].title, "제3회 호반미술상")

    def test_tolerates_invalid_legacy_bytes_outside_collected_fields(self) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        collector = SeoulCsvCollector(registry, "seoul-oa-2708-sejong")
        csv_prefix = """PERFORM_IDX,GENRE_NAME,TITLE,START_DATE,END_DATE,PLACE_LIST,INFO_URL,IGNORED
37607,전시기타,제3회 호반미술상,2026-09-02,2026-09-29,세종미술관 1관,https://www.sejongpac.or.kr/portal/performance/performance/performTicket.do?performIdx=37607&menuNo=200558,""".encode(
            "cp949"
        )
        csv_content = csv_prefix + b"\x82" + b'"\n'

        try:
            records = collector.collect(csv_content)
        except SourceContractError as error:
            self.fail(f"invalid bytes in ignored fields must not block collection: {error}")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source_record_id, "37607")


if __name__ == "__main__":
    unittest.main()

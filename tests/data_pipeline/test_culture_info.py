from pathlib import Path
from typing import Mapping
import unittest

from backend.data_pipeline.collectors.culture_info import CultureInfoApiCollector
from backend.data_pipeline.registry import SourceRegistry


ROOT = Path(__file__).resolve().parents[2]


class StaticXmlTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str]]] = []

    def get(self, url: str, params: Mapping[str, str]) -> bytes:
        self.calls.append((url, dict(params)))
        if url.endswith("/period2"):
            return b"""<?xml version='1.0' encoding='UTF-8'?>
<response><header><resultCode>00</resultCode><resultMsg>OK</resultMsg></header>
<body><items><item><seq>394181</seq></item><item><seq>348222</seq></item></items>
<totalCount>2</totalCount><PageNo>1</PageNo><numOfrows>100</numOfrows></body></response>"""

        seq = params["seq"]
        details = {
            "394181": """<response><header><resultCode>00</resultCode></header><body><item>
<seq>394181</seq><title>패트리샤 피치니니: 킨쉽</title>
<startDate>20260723</startDate><endDate>20261101</endDate>
<place>수원시립미술관</place><placeAddr>경기도 수원시 팔달구 정조로 833</placeAddr>
<area>경기</area><sigungu>수원시</sigungu>
<url>https://suma.suwon.go.kr/exhi/current_view.do?lang=ko&amp;ge_idx=1266</url>
<imgUrl>https://example.invalid/poster.jpg</imgUrl><contents1>수집하지 않을 설명</contents1>
</item></body></response>""",
            "348222": """<response><header><resultCode>00</resultCode></header><body><item>
<seq>348222</seq><title>다시 만난 하늘</title>
<startDate>20250917</startDate><endDate>20251103</endDate>
<place>국립민속박물관</place><placeAddr>서울특별시 종로구 삼청로 37</placeAddr>
<area>서울</area><sigungu>종로구</sigungu><url></url>
</item></body></response>""",
        }
        return details[seq].encode("utf-8")


class CultureInfoApiCollectorTests(unittest.TestCase):
    def test_expands_period_results_and_keeps_only_allowed_fact_fields(self) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        transport = StaticXmlTransport()
        collector = CultureInfoApiCollector(
            registry,
            service_key="test-service-key",
            transport=transport,
        )

        records = collector.collect({"from": "20250101", "to": "20271231"})

        self.assertEqual(
            [(record.source_record_id, record.institution_id) for record in records],
            [("394181", "suma-haenggung"), ("348222", "nfm-seoul-main")],
        )
        self.assertEqual(records[0].official_url, "https://suma.suwon.go.kr/exhi/current_view.do?lang=ko&ge_idx=1266")
        self.assertIsNone(records[1].official_url)
        self.assertNotIn("imgUrl", records[0].raw)
        self.assertNotIn("contents1", records[0].raw)
        period_params = transport.calls[0][1]
        self.assertEqual(period_params["PageNo"], "1")
        self.assertEqual(period_params["numOfrows"], "100")
        self.assertEqual(period_params["serviceTp"], "A")

    def test_reads_all_period_pages_sequentially(self) -> None:
        class PaginatedTransport:
            def __init__(self) -> None:
                self.period_pages: list[str] = []

            def get(self, url: str, params: Mapping[str, str]) -> bytes:
                if url.endswith("/period2"):
                    page = params["PageNo"]
                    self.period_pages.append(page)
                    seq = {"1": "394181", "2": "394182"}[page]
                    return f"""<response><header><resultCode>00</resultCode></header><body>
<items><item><seq>{seq}</seq></item></items><totalCount>2</totalCount>
<PageNo>{page}</PageNo><numOfrows>1</numOfrows></body></response>""".encode()
                seq = params["seq"]
                return f"""<response><header><resultCode>00</resultCode></header><body><item>
<seq>{seq}</seq><title>전시 {seq}</title><startDate>20260723</startDate>
<endDate>20261101</endDate><place>수원시립미술관</place>
<placeAddr>경기도 수원시 팔달구 정조로 833</placeAddr><area>경기</area>
<sigungu>수원시</sigungu><url>https://suma.suwon.go.kr/exhi/{seq}</url>
</item></body></response>""".encode()

        registry = SourceRegistry.load(ROOT / "sources.yaml")
        transport = PaginatedTransport()
        collector = CultureInfoApiCollector(
            registry,
            service_key="test-service-key",
            transport=transport,
        )

        records = collector.collect(
            {"from": "20250101", "to": "20271231", "numOfrows": "1"}
        )

        self.assertEqual(
            [record.source_record_id for record in records],
            ["394181", "394182"],
        )
        self.assertEqual(transport.period_pages, ["1", "2"])


if __name__ == "__main__":
    unittest.main()

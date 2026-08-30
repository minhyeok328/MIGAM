from io import StringIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from backend.apps.data_quality.models import ExhibitionCandidate
from backend.apps.sources.models import IngestionRun, SourceRecord


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures" / "source-qualification.json"


class StaticResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> "StaticResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def culture_api_response(request: object, timeout: float) -> StaticResponse:
    del timeout
    url = str(getattr(request, "full_url"))
    if "/period2?" in url:
        return StaticResponse(
            b"""<response><header><resultCode>00</resultCode></header><body>
<items><item><seq>394181</seq></item></items><totalCount>1</totalCount>
<PageNo>1</PageNo><numOfrows>100</numOfrows></body></response>"""
        )
    return StaticResponse(
        """<response><header><resultCode>00</resultCode></header><body><item>
<seq>394181</seq><title>패트리샤 피치니니: 킨쉽</title>
<startDate>20260723</startDate><endDate>20261101</endDate>
<place>수원시립미술관</place><placeAddr>경기도 수원시 팔달구 정조로 833</placeAddr>
<area>경기</area><sigungu>수원시</sigungu>
<url>https://suma.suwon.go.kr/exhi/current_view.do?lang=ko&amp;ge_idx=1266</url>
</item></body></response>""".encode("utf-8")
    )


class SyncExhibitionsCommandTests(TestCase):
    def test_imports_sejong_csv_file_through_live_collector(self) -> None:
        with TemporaryDirectory() as directory:
            csv_path = Path(directory) / "sejong.csv"
            csv_path.write_text(
                """PERFORM_IDX,GENRE_NAME,TITLE,START_DATE,END_DATE,PLACE_LIST,INFO_URL
37607,전시기타,제3회 호반미술상,2026-09-02,2026-09-29,세종미술관 1관,https://www.sejongpac.or.kr/portal/performance/performance/performTicket.do?performIdx=37607&menuNo=200558
""",
                encoding="utf-8-sig",
            )

            call_command(
                "sync_exhibitions",
                fixture=None,
                sejong_csv=str(csv_path),
                source="seoul-oa-2708-sejong",
                as_of="2026-08-30",
                stdout=StringIO(),
            )

        run = IngestionRun.objects.get()
        source_record = SourceRecord.objects.get()
        candidate = ExhibitionCandidate.objects.get()
        self.assertEqual(run.received_count, 1)
        self.assertEqual(source_record.source_record_id, "37607")
        self.assertEqual(candidate.core_result, "PASS")

    def test_imports_sema_csv_file_through_live_collector(self) -> None:
        with TemporaryDirectory() as directory:
            csv_path = Path(directory) / "sema.csv"
            csv_path.write_text(
                """DP_EX_NO,DP_NAME,DP_START,DP_END,DP_PLACE,DP_LNK
1553791,마틴 파,2026-07-16,2026-10-18,서울시립 사진미술관,https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1553791
""",
                encoding="utf-8-sig",
            )

            call_command(
                "sync_exhibitions",
                fixture=None,
                sema_csv=str(csv_path),
                source="seoul-oa-15323-sema",
                as_of="2026-08-30",
                stdout=StringIO(),
            )

        source_record = SourceRecord.objects.get()
        candidate = ExhibitionCandidate.objects.get()
        self.assertEqual(source_record.institution_id, "sema-photo")
        self.assertEqual(source_record.source_record_id, "1553791")
        self.assertEqual(candidate.core_result, "PASS")

    def test_combines_all_supplied_live_csv_inputs_in_one_run(self) -> None:
        with TemporaryDirectory() as directory:
            sejong_path = Path(directory) / "sejong.csv"
            sejong_path.write_text(
                """PERFORM_IDX,GENRE_NAME,TITLE,START_DATE,END_DATE,PLACE_LIST,INFO_URL
37607,전시기타,제3회 호반미술상,2026-09-02,2026-09-29,세종미술관 1관,https://www.sejongpac.or.kr/portal/performance/performance/performTicket.do?performIdx=37607&menuNo=200558
""",
                encoding="utf-8-sig",
            )
            sema_path = Path(directory) / "sema.csv"
            sema_path.write_text(
                """DP_EX_NO,DP_NAME,DP_START,DP_END,DP_PLACE,DP_LNK
1553791,마틴 파,2026-07-16,2026-10-18,서울시립 사진미술관,https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1553791
""",
                encoding="utf-8-sig",
            )

            call_command(
                "sync_exhibitions",
                fixture=None,
                sejong_csv=str(sejong_path),
                sema_csv=str(sema_path),
                as_of="2026-08-30",
                stdout=StringIO(),
            )

        run = IngestionRun.objects.get()
        self.assertEqual(run.received_count, 2)
        self.assertEqual(
            set(SourceRecord.objects.values_list("source_id", flat=True)),
            {"seoul-oa-2708-sejong", "seoul-oa-15323-sema"},
        )

    def test_imports_culture_api_period_using_dotenv_key(self) -> None:
        with TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            env_path.write_text(
                'CULTURE_PORTAL_SERVICE_KEY="dotenv-test-key"\n',
                encoding="utf-8",
            )
            with (
                patch.dict(
                    os.environ,
                    {"CULTURE_PORTAL_SERVICE_KEY": ""},
                ),
                patch(
                    "backend.data_pipeline.collectors.culture_info.urlopen",
                    side_effect=culture_api_response,
                ),
            ):
                call_command(
                    "sync_exhibitions",
                    fixture=None,
                    env_file=str(env_path),
                    culture_from="20260801",
                    culture_to="20261231",
                    source="kcisa-cultureinfo",
                    as_of="2026-08-30",
                    stdout=StringIO(),
                )

        source_record = SourceRecord.objects.get()
        candidate = ExhibitionCandidate.objects.get()
        self.assertEqual(source_record.institution_id, "suma-haenggung")
        self.assertEqual(source_record.source_record_id, "394181")
        self.assertEqual(candidate.core_result, "PASS")

    def test_rejects_malformed_culture_period_before_persistence(self) -> None:
        with (
            patch.dict(
                os.environ,
                {"CULTURE_PORTAL_SERVICE_KEY": "test-service-key"},
            ),
            patch(
                "backend.data_pipeline.collectors.culture_info.urlopen",
                side_effect=culture_api_response,
            ),
        ):
            with self.assertRaisesRegex(CommandError, "YYYYMMDD"):
                call_command(
                    "sync_exhibitions",
                    fixture=None,
                    culture_from="2026-08-01",
                    culture_to="20261231",
                    source="kcisa-cultureinfo",
                    as_of="2026-08-30",
                    stdout=StringIO(),
                )

        self.assertFalse(IngestionRun.objects.exists())

    def test_imports_approved_fixture_through_the_quality_pipeline(self) -> None:
        output = StringIO()

        call_command(
            "sync_exhibitions",
            fixture=str(FIXTURE),
            as_of="2026-08-30",
            stdout=output,
        )

        run = IngestionRun.objects.get()
        self.assertEqual(run.status, IngestionRun.Status.SUCCESS)
        self.assertEqual(run.received_count, 25)
        self.assertEqual(run.verified_count, 24)
        self.assertEqual(run.excluded_count, 1)
        self.assertEqual(run.quarantined_count, 1)
        self.assertEqual(SourceRecord.objects.count(), 25)
        self.assertEqual(ExhibitionCandidate.objects.count(), 25)
        self.assertIn(
            "received=25 verified=24 excluded=1 quarantined=1",
            output.getvalue(),
        )

    def test_filters_fixture_by_registered_source(self) -> None:
        call_command(
            "sync_exhibitions",
            fixture=str(FIXTURE),
            as_of="2026-08-30",
            source="seoul-oa-2708-sejong",
            stdout=StringIO(),
        )

        run = IngestionRun.objects.get()
        self.assertEqual(run.source_id, "seoul-oa-2708-sejong")
        self.assertEqual(run.received_count, 5)
        self.assertEqual(SourceRecord.objects.count(), 5)

    def test_rejects_unknown_source_before_creating_a_run(self) -> None:
        with self.assertRaisesRegex(CommandError, "unknown source"):
            call_command(
                "sync_exhibitions",
                fixture=str(FIXTURE),
                as_of="2026-08-30",
                source="not-registered",
                stdout=StringIO(),
            )

        self.assertFalse(IngestionRun.objects.exists())

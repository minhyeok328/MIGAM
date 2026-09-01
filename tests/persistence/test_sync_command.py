from datetime import datetime
from io import StringIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from backend.apps.data_quality.models import ExhibitionCandidate
from backend.apps.sources.models import (
    CollectionIssue,
    IngestionRun,
    InstitutionAllowlistEntry,
    InstitutionQualificationRun,
    InstitutionRunResult,
    PromotionEvidence,
    Source,
    SourceRecord,
)
from backend.data_pipeline.registry import SourceRegistry
from backend.data_pipeline.registry_state import sync_registry_state
from backend.data_pipeline.institution_runs import (
    record_institution_results as actual_record_institution_results,
)
from backend.data_pipeline.collection_gate import (
    select_collectible_entries as actual_select_collectible_entries,
)


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
        result = InstitutionRunResult.objects.get()
        self.assertEqual(result.institution.registry_id, "sejong-center-main-exhibition")
        self.assertEqual(result.status, InstitutionRunResult.Status.SUCCESS)

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
        self.assertFalse(run.qualification_mode)
        self.assertEqual(run.received_count, 25)
        self.assertEqual(run.verified_count, 24)
        self.assertEqual(run.excluded_count, 1)
        self.assertEqual(run.quarantined_count, 1)
        self.assertEqual(SourceRecord.objects.count(), 25)
        self.assertEqual(ExhibitionCandidate.objects.count(), 25)
        self.assertEqual(InstitutionRunResult.objects.count(), 5)
        self.assertEqual(
            set(InstitutionRunResult.objects.values_list("status", flat=True)),
            {InstitutionRunResult.Status.SUCCESS},
        )
        self.assertFalse(InstitutionQualificationRun.objects.exists())
        self.assertIn(
            "received=25 verified=24 excluded=1 quarantined=1",
            output.getvalue(),
        )

    def test_qualification_fixture_promotes_all_entries_after_three_dates(
        self,
    ) -> None:
        seoul = ZoneInfo("Asia/Seoul")
        for finished_at in (
            datetime(2026, 9, 1, tzinfo=seoul),
            datetime(2026, 9, 7, tzinfo=seoul),
            datetime(2026, 9, 13, tzinfo=seoul),
        ):
            with patch(
                "backend.data_pipeline.persistence.timezone.now",
                return_value=finished_at,
            ):
                call_command(
                    "sync_exhibitions",
                    fixture=str(FIXTURE),
                    qualification=True,
                    as_of=finished_at.date().isoformat(),
                    stdout=StringIO(),
                )

        self.assertEqual(IngestionRun.objects.count(), 3)
        self.assertEqual(
            set(IngestionRun.objects.values_list("status", flat=True)),
            {IngestionRun.Status.SUCCESS},
        )
        self.assertEqual(InstitutionQualificationRun.objects.count(), 15)
        self.assertEqual(
            set(
                InstitutionQualificationRun.objects.values_list(
                    "status",
                    flat=True,
                )
            ),
            {InstitutionQualificationRun.Status.SUCCESS},
        )
        nfm_latest = InstitutionQualificationRun.objects.filter(
            institution__registry_id="nfm-seoul-main"
        ).latest("finished_at")
        self.assertEqual(nfm_latest.target_count, 5)
        self.assertEqual(nfm_latest.received_count, 5)
        self.assertEqual(nfm_latest.verified_count, 4)
        self.assertEqual(nfm_latest.quarantined_count, 1)
        self.assertEqual(nfm_latest.approved_record_exception_count, 1)
        self.assertEqual(nfm_latest.completed_core_target_count, 5)
        self.assertEqual(PromotionEvidence.objects.count(), 5)
        self.assertEqual(
            set(
                InstitutionAllowlistEntry.objects.values_list(
                    "lifecycle",
                    flat=True,
                )
            ),
            {InstitutionAllowlistEntry.Lifecycle.ACTIVE},
        )
        self.assertTrue(
            all(
                evidence.qualification_runs.count() == 3
                for evidence in PromotionEvidence.objects.all()
            )
        )

        with patch(
            "backend.data_pipeline.persistence.timezone.now",
            return_value=datetime(2026, 9, 14, tzinfo=seoul),
        ):
            call_command(
                "sync_exhibitions",
                fixture=str(FIXTURE),
                qualification=True,
                as_of="2026-09-14",
                stdout=StringIO(),
            )
        self.assertEqual(InstitutionQualificationRun.objects.count(), 15)
        self.assertEqual(PromotionEvidence.objects.count(), 5)

    def test_incomplete_qualification_keeps_processed_data_and_fails_run(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            csv_path = Path(directory) / "sejong.csv"
            csv_path.write_text(
                """PERFORM_IDX,GENRE_NAME,TITLE,START_DATE,END_DATE,PLACE_LIST,INFO_URL
37607,전시기타,제3회 호반미술상,2026-09-02,2026-09-29,세종미술관 1관,https://www.sejongpac.or.kr/portal/performance/performance/performTicket.do?performIdx=37607&menuNo=200558
""",
                encoding="utf-8-sig",
            )

            with self.assertRaisesRegex(CommandError, "qualification failed"):
                call_command(
                    "sync_exhibitions",
                    fixture=None,
                    sejong_csv=str(csv_path),
                    source="seoul-oa-2708-sejong",
                    qualification=True,
                    as_of="2026-09-01",
                    stdout=StringIO(),
                )

        run = IngestionRun.objects.get()
        result = InstitutionRunResult.objects.get()
        qualification = InstitutionQualificationRun.objects.get()
        self.assertEqual(run.status, IngestionRun.Status.FAILED)
        self.assertEqual(result.status, InstitutionRunResult.Status.FAILED)
        self.assertEqual(qualification.status, InstitutionQualificationRun.Status.FAILED)
        self.assertEqual(qualification.final_missing_core_target_count, 4)
        self.assertTrue(SourceRecord.objects.exists())

    def test_shared_failed_run_preserves_other_institution_successes(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["records"] = [
            record
            for record in payload["records"]
            if not (
                record["institution_id"] == "sejong-center-main-exhibition"
                and record["source_record_id"] == "37607"
            )
        ]
        with TemporaryDirectory() as directory:
            fixture_path = Path(directory) / "incomplete-qualification.json"
            fixture_path.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(CommandError, "qualification failed"):
                call_command(
                    "sync_exhibitions",
                    fixture=str(fixture_path),
                    qualification=True,
                    as_of="2026-09-01",
                    stdout=StringIO(),
                )

        self.assertEqual(IngestionRun.objects.get().status, IngestionRun.Status.FAILED)
        self.assertEqual(
            InstitutionRunResult.objects.get(
                institution__registry_id="sejong-center-main-exhibition"
            ).status,
            InstitutionRunResult.Status.FAILED,
        )
        self.assertEqual(
            InstitutionRunResult.objects.exclude(
                institution__registry_id="sejong-center-main-exhibition"
            ).filter(status=InstitutionRunResult.Status.SUCCESS).count(),
            4,
        )
        self.assertEqual(
            InstitutionQualificationRun.objects.filter(status="FAILED").count(),
            1,
        )
        self.assertEqual(
            InstitutionQualificationRun.objects.filter(status="SUCCESS").count(),
            4,
        )

    def test_unapproved_core_failure_resets_qualification_and_blocks_promotion(
        self,
    ) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        for record in payload["records"]:
            if (
                record["institution_id"] == "sejong-center-main-exhibition"
                and record["source_record_id"] == "37607"
            ):
                record["official_url"] = None
                break

        seoul = ZoneInfo("Asia/Seoul")
        with TemporaryDirectory() as directory:
            fixture_path = Path(directory) / "unapproved-core-failure.json"
            fixture_path.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )
            for finished_at in (
                datetime(2026, 9, 1, tzinfo=seoul),
                datetime(2026, 9, 7, tzinfo=seoul),
                datetime(2026, 9, 13, tzinfo=seoul),
            ):
                with (
                    patch(
                        "backend.data_pipeline.persistence.timezone.now",
                        return_value=finished_at,
                    ),
                    self.assertRaisesRegex(CommandError, "qualification failed"),
                ):
                    call_command(
                        "sync_exhibitions",
                        fixture=str(fixture_path),
                        qualification=True,
                        as_of=finished_at.date().isoformat(),
                        stdout=StringIO(),
                    )

        sejong_results = InstitutionRunResult.objects.filter(
            institution__registry_id="sejong-center-main-exhibition"
        )
        sejong_qualifications = InstitutionQualificationRun.objects.filter(
            institution__registry_id="sejong-center-main-exhibition"
        )
        entry = InstitutionAllowlistEntry.objects.get(
            registry_id="sejong-center-main-exhibition"
        )
        self.assertEqual(sejong_results.count(), 3)
        self.assertEqual(
            set(sejong_results.values_list("status", flat=True)),
            {InstitutionRunResult.Status.FAILED},
        )
        self.assertEqual(
            set(sejong_qualifications.values_list("status", flat=True)),
            {InstitutionQualificationRun.Status.FAILED},
        )
        self.assertEqual(entry.lifecycle, InstitutionAllowlistEntry.Lifecycle.PROVISIONAL)
        self.assertFalse(PromotionEvidence.objects.filter(institution=entry).exists())

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

    def test_rejects_non_normal_source_before_reading_input_or_creating_run(
        self,
    ) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        sync_registry_state(registry)
        source = Source.objects.get(registry_id="seoul-oa-2708-sejong")
        source.operation_status = Source.OperationStatus.PAUSED
        source.save(update_fields=("operation_status", "updated_at"))

        with self.assertRaisesRegex(CommandError, "source is not normal"):
            call_command(
                "sync_exhibitions",
                fixture=None,
                sejong_csv=str(ROOT / "fixtures" / "must-not-be-read.csv"),
                source="seoul-oa-2708-sejong",
                as_of="2026-08-30",
                stdout=StringIO(),
            )

        self.assertFalse(IngestionRun.objects.exists())
        self.assertFalse(InstitutionRunResult.objects.exists())

    def test_collection_failure_records_failed_run_and_active_institution_result(
        self,
    ) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        sync_registry_state(registry)
        entry = InstitutionAllowlistEntry.objects.get(
            registry_id="sejong-center-main-exhibition"
        )
        entry.lifecycle = InstitutionAllowlistEntry.Lifecycle.ACTIVE
        entry.save(update_fields=("lifecycle", "updated_at"))

        with self.assertRaises(CommandError):
            call_command(
                "sync_exhibitions",
                fixture=None,
                sejong_csv=str(ROOT / "fixtures" / "missing-source.csv"),
                source="seoul-oa-2708-sejong",
                as_of="2026-08-30",
                stdout=StringIO(),
            )

        run = IngestionRun.objects.get()
        result = InstitutionRunResult.objects.get()
        entry.refresh_from_db()
        self.assertEqual(run.status, IngestionRun.Status.FAILED)
        self.assertEqual(result.status, InstitutionRunResult.Status.FAILED)
        self.assertEqual(entry.lifecycle, InstitutionAllowlistEntry.Lifecycle.ACTIVE)
        self.assertEqual(entry.health, InstitutionAllowlistEntry.Health.DEGRADED)
        self.assertEqual(entry.consecutive_final_failed_count, 1)

    def test_full_fixture_skips_only_entry_scoped_critical_in_shared_source(
        self,
    ) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        sync_registry_state(registry)
        source = Source.objects.get(registry_id="seoul-oa-15323-sema")
        blocked = InstitutionAllowlistEntry.objects.get(
            registry_id="sema-seoseoul"
        )
        CollectionIssue.objects.create(
            registry_id="test-seoseoul-command-critical",
            classification=CollectionIssue.Classification.STRUCTURAL_CRITICAL,
            scope=CollectionIssue.Scope.ENTRY,
            source=source,
            institution=blocked,
            status=CollectionIssue.Status.OPEN,
        )

        call_command(
            "sync_exhibitions",
            fixture=str(FIXTURE),
            as_of="2026-08-30",
            stdout=StringIO(),
        )

        run = IngestionRun.objects.get()
        self.assertEqual(run.received_count, 20)
        self.assertFalse(
            SourceRecord.objects.filter(institution_id="sema-seoseoul").exists()
        )
        self.assertTrue(
            SourceRecord.objects.filter(institution_id="sema-photo").exists()
        )
        self.assertEqual(
            set(
                InstitutionRunResult.objects.values_list(
                    "institution__registry_id",
                    flat=True,
                )
            ),
            {
                "sejong-center-main-exhibition",
                "sema-photo",
                "suma-haenggung",
                "nfm-seoul-main",
            },
        )

    def test_result_finalization_failure_rolls_back_successful_persistence(
        self,
    ) -> None:
        calls = 0

        def fail_once(*args: object, **kwargs: object) -> object:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise RuntimeError("result finalization failed")
            return actual_record_institution_results(*args, **kwargs)

        with (
            patch(
                "backend.apps.sources.management.commands."
                "sync_exhibitions.record_institution_results",
                side_effect=fail_once,
            ),
            self.assertRaisesRegex(CommandError, "result finalization failed"),
        ):
            call_command(
                "sync_exhibitions",
                fixture=str(FIXTURE),
                source="seoul-oa-2708-sejong",
                as_of="2026-08-30",
                stdout=StringIO(),
            )

        run = IngestionRun.objects.get(command="sync_exhibitions")
        result = InstitutionRunResult.objects.get(ingestion_run=run)
        self.assertEqual(calls, 2)
        self.assertEqual(run.status, IngestionRun.Status.FAILED)
        self.assertEqual(result.status, InstitutionRunResult.Status.FAILED)
        self.assertFalse(SourceRecord.objects.exists())
        self.assertFalse(ExhibitionCandidate.objects.exists())

    def test_critical_opened_after_gate_aborts_success_finalization(self) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        sync_registry_state(registry)
        entry = InstitutionAllowlistEntry.objects.get(
            registry_id="sejong-center-main-exhibition"
        )
        entry.lifecycle = InstitutionAllowlistEntry.Lifecycle.ACTIVE
        entry.save(update_fields=("lifecycle", "updated_at"))

        def open_critical_after_gate(**kwargs: object) -> object:
            institutions = actual_select_collectible_entries(**kwargs)
            CollectionIssue.objects.create(
                registry_id="test-post-gate-critical",
                classification=CollectionIssue.Classification.ACCESS_BLOCK,
                scope=CollectionIssue.Scope.ENTRY,
                source=entry.source,
                institution=entry,
                status=CollectionIssue.Status.OPEN,
            )
            return institutions

        with (
            patch(
                "backend.apps.sources.management.commands."
                "sync_exhibitions.select_collectible_entries",
                side_effect=open_critical_after_gate,
            ),
            self.assertRaisesRegex(
                CommandError,
                "critical collection issue opened before finalization",
            ),
        ):
            call_command(
                "sync_exhibitions",
                fixture=str(FIXTURE),
                source="seoul-oa-2708-sejong",
                as_of="2026-08-30",
                stdout=StringIO(),
            )

        run = IngestionRun.objects.get(command="sync_exhibitions")
        result = InstitutionRunResult.objects.get(ingestion_run=run)
        entry.refresh_from_db()
        self.assertEqual(run.status, IngestionRun.Status.FAILED)
        self.assertEqual(result.status, InstitutionRunResult.Status.FAILED)
        self.assertEqual(
            entry.lifecycle,
            InstitutionAllowlistEntry.Lifecycle.SUSPENDED,
        )
        self.assertEqual(entry.lifecycle_change_reason, "OPEN_CRITICAL")
        self.assertFalse(SourceRecord.objects.exists())
        self.assertFalse(ExhibitionCandidate.objects.exists())

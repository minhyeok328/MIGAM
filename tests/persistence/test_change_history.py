from dataclasses import replace
from datetime import date
from importlib import import_module
from pathlib import Path

from django.test import TestCase

from backend.apps.catalog.models import Exhibition
from backend.apps.sources.models import IngestionRun
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


class ChangeHistoryTests(TestCase):
    def setUp(self) -> None:
        self.registry = SourceRegistry.load(ROOT / "sources.yaml")

    def history_model(self) -> object:
        catalog_models = import_module("backend.apps.catalog.models")
        self.assertTrue(
            hasattr(catalog_models, "ChangeHistory"),
            "catalog.ChangeHistory model is missing",
        )
        return catalog_models.ChangeHistory

    def test_new_exhibition_records_meaningful_change_history(self) -> None:
        persist_records(
            [valid_record()],
            self.registry,
            as_of=date(2026, 8, 30),
            command_name="sync_exhibitions",
        )

        ChangeHistory = self.history_model()
        history = ChangeHistory.objects.get()
        exhibition = Exhibition.objects.get()
        run = IngestionRun.objects.get()
        self.assertEqual(history.exhibition, exhibition)
        self.assertEqual(history.ingestion_run, run)
        self.assertEqual(history.change_type, "CREATED")
        self.assertEqual(history.meaningful_type, "NEW_EXHIBITION")
        self.assertTrue(history.meaningful_for_promotion)
        self.assertIsNone(history.old_value)
        self.assertEqual(history.new_value["end_date"], "2026-09-29")
        self.assertEqual(history.rule_version, "1.0.0")

    def test_canonical_field_changes_apply_promotion_allowlist(self) -> None:
        persist_records(
            [valid_record()],
            self.registry,
            as_of=date(2026, 8, 30),
            command_name="sync_exhibitions",
        )
        persist_records(
            [
                valid_record(
                    title="제3회 호반미술상 연장전",
                    end_date="2026-10-05",
                    venue="세종미술관 2관",
                )
            ],
            self.registry,
            as_of=date(2026, 9, 1),
            command_name="sync_exhibitions",
        )

        ChangeHistory = self.history_model()
        changes = {
            history.field_name: history
            for history in ChangeHistory.objects.filter(
                change_type="FIELD_CHANGED"
            )
        }
        self.assertEqual(set(changes), {"title", "end_date", "venue"})
        self.assertFalse(changes["title"].meaningful_for_promotion)
        self.assertEqual(changes["title"].meaningful_type, "NONE")
        self.assertEqual(changes["title"].old_value, "제3회 호반미술상")
        self.assertEqual(changes["title"].new_value, "제3회 호반미술상 연장전")
        self.assertTrue(changes["end_date"].meaningful_for_promotion)
        self.assertEqual(changes["end_date"].meaningful_type, "END_DATE_CHANGED")
        self.assertEqual(changes["end_date"].old_value, "2026-09-29")
        self.assertEqual(changes["end_date"].new_value, "2026-10-05")
        self.assertTrue(changes["venue"].meaningful_for_promotion)
        self.assertEqual(changes["venue"].meaningful_type, "VENUE_CHANGED")

    def test_cancellation_is_a_meaningful_lifecycle_change(self) -> None:
        persist_records(
            [valid_record()],
            self.registry,
            as_of=date(2026, 8, 30),
            command_name="sync_exhibitions",
        )
        persist_records(
            [valid_record(canceled=True)],
            self.registry,
            as_of=date(2026, 9, 1),
            command_name="sync_exhibitions",
        )

        ChangeHistory = self.history_model()
        history = ChangeHistory.objects.get(
            change_type="FIELD_CHANGED",
            field_name="lifecycle",
        )
        self.assertEqual(history.old_value, "UPCOMING")
        self.assertEqual(history.new_value, "CANCELED")
        self.assertTrue(history.meaningful_for_promotion)
        self.assertEqual(history.meaningful_type, "CANCELED")

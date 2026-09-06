from dataclasses import replace
from datetime import date
from decimal import Decimal
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from backend.apps.catalog.models import Exhibition, PriceOption
from backend.apps.discovery.models import ContentFeatureSnapshot
from backend.apps.discovery.features import FeatureAssertionInput, record_content_feature_snapshot
from backend.apps.discovery.visit_conditions import VisitEvidenceResolver
from backend.apps.discovery.operating_schedule import OperatingScheduleResolver
from backend.data_pipeline.collectors.culture_info import CultureInfoApiCollector
from backend.data_pipeline.collectors.seoul_csv import SeoulCsvCollector
from backend.data_pipeline.fixture_loader import load_qualification_fixture
from backend.data_pipeline.persistence import persist_records
from backend.data_pipeline.registry import SourceRegistry
from tests.data_pipeline.test_culture_info import StaticXmlTransport


ROOT = Path(__file__).resolve().parents[2]


class SourceEnrichmentTests(TestCase):
    def setUp(self):
        self.registry = SourceRegistry.load(ROOT / "sources.yaml")
        self.raw = next(
            row for row in load_qualification_fixture(
                ROOT / "fixtures/source-qualification.json", self.registry
            ) if row.source_id == "seoul-oa-15323-sema"
        )

    def persist(self, *, price="무료", media="사진, 영상", schedule=""):
        raw = replace(self.raw, raw={
            **self.raw.raw, "관람료(원)": price,
            "전시부문": media, "전시(관람)시간": schedule,
        })
        persist_records([raw], self.registry, as_of=date(2026, 9, 6), command_name="test")
        return Exhibition.objects.get()

    def test_official_optional_fields_reach_price_and_features_without_inference(self):
        exhibition = self.persist()
        price = VisitEvidenceResolver().resolve(exhibition).price
        self.assertEqual(price.amount, Decimal("0"))
        self.assertEqual(price.state, "CONFIRMED")
        self.assertEqual(exhibition.priceoption_records.get().rule_version, "source-optional-1.0.0")
        features = ContentFeatureSnapshot.objects.get(is_current=True).assertions
        self.assertEqual(set(features.values_list("axis", "value")), {
            ("MEDIA_GROUP", "PHOTOGRAPHY"), ("MEDIA_GROUP", "VIDEO"),
        })
        self.assertTrue(all(row.rule_version == "source-optional-1.0.0" for row in features.all()))
        self.assertEqual(exhibition.accessibilityfact_records.count(), 0)
        self.assertEqual(exhibition.sensorynotice_records.count(), 0)

    def test_complex_price_is_unknown_and_title_does_not_create_mood(self):
        for price in ("어린이 무료, 성인 10,000원", "5,000~10,000원", "얼리버드 5,000원", "", "가족권 20,000원"):
            with self.subTest(price=price):
                exhibition = self.persist(price=price, media="차분하고 몰입감 있는 전시")
                self.assertEqual(VisitEvidenceResolver().resolve(exhibition).price.state, "UNKNOWN")
                self.assertFalse(ContentFeatureSnapshot.objects.get(is_current=True).assertions.exists())

    def test_repeated_backfill_preserves_ids_history_and_verification_time(self):
        exhibition = self.persist()
        before = (exhibition.pk, exhibition.last_verified_at)
        snapshot_id = ContentFeatureSnapshot.objects.get(is_current=True).pk
        prices = PriceOption.objects.count()
        call_command("rebuild_discovery_data", stdout=StringIO())
        call_command("rebuild_discovery_data", stdout=StringIO())
        exhibition.refresh_from_db()
        self.assertEqual((exhibition.pk, exhibition.last_verified_at), before)
        self.assertEqual(ContentFeatureSnapshot.objects.get(is_current=True).pk, snapshot_id)
        self.assertEqual(PriceOption.objects.count(), prices)

    def test_changed_source_replaces_current_features_and_price_evidence(self):
        self.persist()
        exhibition = self.persist(price="성인 12,000원", media="설치")
        self.assertEqual(VisitEvidenceResolver().resolve(exhibition).price.amount, Decimal("12000"))
        self.assertEqual(list(ContentFeatureSnapshot.objects.get(is_current=True).assertions.values_list("value", flat=True)), ["INSTALLATION"])
        self.assertEqual(ContentFeatureSnapshot.objects.count(), 2)

    def test_backfill_preserves_independently_recorded_features(self):
        exhibition = self.persist()
        source = exhibition.source_links.get().latest_source_record
        record_content_feature_snapshot(exhibition=exhibition, assertions=[
            FeatureAssertionInput(axis="MOOD", value="CALM", evidence_kind="DERIVED", source_record=source, rule_version="reviewed-1.0.0"),
        ])
        call_command("rebuild_discovery_data", stdout=StringIO())
        features = ContentFeatureSnapshot.objects.get(is_current=True).assertions
        self.assertIn(("MOOD", "CALM"), features.values_list("axis", "value"))
        self.assertIn(("MEDIA_GROUP", "PHOTOGRAPHY"), features.values_list("axis", "value"))

    def test_unchanged_official_recheck_updates_optional_evidence_time(self):
        exhibition = self.persist(schedule="매일 10:00~18:00")
        self.persist(schedule="매일 10:00~18:00")
        source = exhibition.source_links.get().latest_source_record
        self.assertEqual(exhibition.priceoption_records.get().verified_at, source.last_seen_at)
        self.assertEqual(exhibition.operatingschedule_records.get().verified_at, source.last_seen_at)

    def test_unchanged_source_advances_lifecycle_when_period_begins(self):
        raw = replace(self.raw, start_date="2026-09-07", end_date="2026-09-10")
        for as_of, expected in [(date(2026, 9, 6), "UPCOMING"), (date(2026, 9, 7), "CURRENT"), (date(2026, 9, 11), "ENDED")]:
            with self.subTest(as_of=as_of):
                persist_records([raw], self.registry, as_of=as_of, command_name="test")
                self.assertEqual(Exhibition.objects.get().lifecycle, expected)

    def test_csv_schedule_excludes_closed_weekday_and_returns_first_open_day(self):
        exhibition = self.persist(schedule="10:00~18:00 (매주 월요일 휴관)")
        resolver = OperatingScheduleResolver()
        self.assertEqual(resolver.resolve(exhibition, date(2026, 9, 7), date(2026, 9, 7)).state, "CLOSED")
        result = resolver.resolve(exhibition, date(2026, 9, 7), date(2026, 9, 8))
        self.assertEqual(result.first_open_date, date(2026, 9, 8))
        self.persist(schedule="10:00~18:00 (매주 월요일 휴관)")
        self.assertEqual(exhibition.operatingschedule_records.count(), 2)

    def test_complex_opening_text_does_not_invent_open_days(self):
        exhibition = self.persist(schedule="10:00~18:00 (공휴일에는 변경)")
        result = OperatingScheduleResolver().resolve(exhibition, date(2026, 9, 7), date(2026, 9, 9))
        self.assertEqual(result.state, "UNKNOWN")

    def test_csv_collects_only_registered_optional_columns(self):
        source = self.registry.source(self.raw.source_id)
        headers = list(source["fields"].values()) + ["관람료(원)", "전시부문", "전시(관람)시간", "전시설명"]
        from io import StringIO as Buffer
        import csv
        data = Buffer()
        writer = csv.DictWriter(data, fieldnames=headers)
        writer.writeheader()
        writer.writerow({
            **{column: self.raw.source_record_id if field == "record_id" else getattr(self.raw, field)
               for field, column in source["fields"].items()},
            "관람료(원)": "무료", "전시부문": "사진", "전시설명": "not collected",
        })
        records = SeoulCsvCollector(self.registry, self.raw.source_id).collect(data.getvalue())
        self.assertEqual(records[0].raw["관람료(원)"], "무료")
        self.assertNotIn("전시설명", records[0].raw)

    def test_targeted_api_refresh_uses_detail_without_period_expansion(self):
        transport = StaticXmlTransport()
        collector = CultureInfoApiCollector(self.registry, "test-service-key", transport)
        self.assertTrue(hasattr(collector, "collect_ids"), "Targeted official refresh is missing")
        rows = collector.collect_ids(["394181", "394181"])
        self.assertEqual([row.source_record_id for row in rows], ["394181"])
        self.assertEqual(len(transport.calls), 1)
        self.assertTrue(transport.calls[0][0].endswith("/detail2"))

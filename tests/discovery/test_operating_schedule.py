from datetime import date, time
from hashlib import sha256
from importlib import import_module, util

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from backend.apps.catalog import models as catalog
from backend.apps.discovery.recommendation import (
    ORMRecommendationService,
    RecommendationQuery,
    VisitDateRange,
)
from backend.apps.sources.models import SourceRecord


class OperatingScheduleTests(TestCase):
    def setUp(self) -> None:
        self.institution = catalog.Institution.objects.create(
            registry_id="schedule-museum", name="운영일 미술관",
        )
        self.exhibition = catalog.Exhibition.objects.create(
            institution=self.institution, title="운영일 근거 전시",
            start_date=date(2026, 9, 1), end_date=date(2026, 9, 30),
            venue="운영일 미술관", region_area="서울", region_district="종로구",
            lifecycle=catalog.Exhibition.Lifecycle.CURRENT,
            official_url="https://example.com/exhibitions/schedule",
        )
        self.source = self.source_record("schedule-1")
        self.link = catalog.ExhibitionSourceLink.objects.create(
            exhibition=self.exhibition, source_id=self.source.source_id,
            source_record_id=self.source.source_record_id, latest_source_record=self.source,
        )

    def source_record(self, identity: str) -> SourceRecord:
        return SourceRecord.objects.create(
            source_id="official-schedule", source_record_id=identity,
            institution_id=self.institution.registry_id, source_owner=self.institution.name,
            payload={"id": identity}, content_hash=sha256(identity.encode()).hexdigest(),
        )

    def schedule(self, **overrides: object) -> object:
        self.assertTrue(hasattr(catalog, "OperatingSchedule"), "OperatingSchedule model is missing")
        values = {
            "exhibition": self.exhibition, "source_record": self.source,
            "status": "CONFIRMED", "kind": "REGULAR",
            "effective_from": date(2026, 9, 1), "effective_to": date(2026, 9, 30),
            "weekdays": [1, 2, 3, 4, 5, 6], "is_open": True,
            "opens_at": time(10), "closes_at": time(18), "rule_version": "test-v1",
        }
        values.update(overrides)
        return catalog.OperatingSchedule.objects.create(**values)

    def resolve(self, start: date, end: date | None = None) -> object:
        self.assertIsNotNone(util.find_spec("backend.apps.discovery.operating_schedule"))
        module = import_module("backend.apps.discovery.operating_schedule")
        return module.OperatingScheduleResolver().resolve(self.exhibition, start, end or start)

    def test_date_request_excludes_missing_schedule_without_affecting_undated(self) -> None:
        service = ORMRecommendationService()
        dated = service.recommend(RecommendationQuery(
            visit_dates=VisitDateRange(date(2026, 9, 8), date(2026, 9, 8)),
        ))
        self.assertEqual(dated.recommendations, ())
        self.assertEqual(dated.needs_verification, ())
        undated = service.recommend(RecommendationQuery())
        self.assertEqual([row.exhibition_id for row in undated.recommendations], [self.exhibition.pk])

    def test_open_day_returns_first_date_times_and_source_evidence(self) -> None:
        schedule = self.schedule()
        result = self.resolve(date(2026, 9, 7), date(2026, 9, 10))
        self.assertEqual(result.state, "OPEN")
        self.assertEqual(result.first_open_date, date(2026, 9, 8))
        self.assertEqual((result.opens_at, result.closes_at), (time(10), time(18)))
        self.assertEqual(result.source_record_ids, (self.source.pk,))
        self.assertEqual(result.verified_at, schedule.verified_at)

    def test_explicit_weekly_closure_and_unstated_weekday_are_distinct(self) -> None:
        self.schedule()
        self.assertEqual(self.resolve(date(2026, 9, 7)).state, "UNKNOWN")
        self.schedule(weekdays=[0], is_open=False, opens_at=None, closes_at=None)
        closed = self.resolve(date(2026, 9, 7))
        self.assertEqual(closed.state, "CLOSED")
        self.assertIsNone(closed.first_open_date)

    def test_temporary_closure_overrides_regular_opening(self) -> None:
        self.schedule()
        self.schedule(kind="OVERRIDE", weekdays=[], is_open=False, opens_at=None,
                      closes_at=None, effective_from=date(2026, 9, 8), effective_to=date(2026, 9, 9))
        self.assertEqual(self.resolve(date(2026, 9, 8)).state, "CLOSED")
        self.assertEqual(self.resolve(date(2026, 9, 8), date(2026, 9, 10)).first_open_date, date(2026, 9, 10))

    def test_temporary_opening_overrides_regular_closure(self) -> None:
        self.schedule(weekdays=[0], is_open=False, opens_at=None, closes_at=None)
        self.schedule(kind="OVERRIDE", weekdays=[], effective_from=date(2026, 9, 7),
                      effective_to=date(2026, 9, 7), opens_at=time(12), closes_at=time(17))
        result = self.resolve(date(2026, 9, 7))
        self.assertEqual(result.state, "OPEN")
        self.assertEqual(result.opens_at, time(12))

    def test_institution_override_closure_wins_over_exhibition_regular(self) -> None:
        self.schedule()
        self.schedule(exhibition=None, institution=self.institution, kind="OVERRIDE", weekdays=[],
                      is_open=False, opens_at=None, closes_at=None)
        self.assertEqual(self.resolve(date(2026, 9, 8)).state, "CLOSED")

    def test_exhibition_same_kind_precedes_institution_within_effective_period(self) -> None:
        self.schedule(exhibition=None, institution=self.institution, weekdays=list(range(7)))
        self.schedule(status="UNKNOWN", weekdays=[], is_open=None, opens_at=None, closes_at=None,
                      effective_from=date(2026, 9, 8), effective_to=date(2026, 9, 8))
        self.assertEqual(self.resolve(date(2026, 9, 8)).state, "UNKNOWN")
        self.assertEqual(self.resolve(date(2026, 9, 9)).state, "OPEN")

    def test_equal_priority_different_times_or_open_state_are_unknown(self) -> None:
        self.schedule()
        second_source = self.source_record("schedule-2")
        catalog.ExhibitionSourceLink.objects.create(
            exhibition=self.exhibition, source_id=second_source.source_id,
            source_record_id=second_source.source_record_id, latest_source_record=second_source,
        )
        conflict = self.schedule(source_record=second_source, opens_at=time(11))
        self.assertEqual(self.resolve(date(2026, 9, 8)).state, "UNKNOWN")
        conflict.is_open, conflict.opens_at, conflict.closes_at = False, None, None
        conflict.save()
        self.assertEqual(self.resolve(date(2026, 9, 8)).state, "UNKNOWN")

    def test_replaced_source_cannot_confirm_exhibition_or_institution_schedule(self) -> None:
        self.schedule()
        self.schedule(exhibition=None, institution=self.institution)
        replacement = self.source_record("replacement")
        self.link.latest_source_record = replacement
        self.link.save()
        self.assertEqual(self.resolve(date(2026, 9, 8)).state, "UNKNOWN")

    def test_request_and_exhibition_boundaries_are_inclusive(self) -> None:
        self.schedule(weekdays=list(range(7)))
        self.assertEqual(self.resolve(date(2026, 8, 31), date(2026, 9, 1)).first_open_date, date(2026, 9, 1))
        self.assertEqual(self.resolve(date(2026, 9, 30), date(2026, 10, 1)).first_open_date, date(2026, 9, 30))
        self.assertIsNone(self.resolve(date(2026, 10, 1)).first_open_date)

    def test_long_closed_period_jumps_to_schedule_boundary(self) -> None:
        self.exhibition.start_date, self.exhibition.end_date = date.min, date.max
        self.exhibition.save()
        self.schedule(effective_from=date.min, effective_to=date.max, weekdays=list(range(7)))
        self.schedule(kind="OVERRIDE", weekdays=[], is_open=False, opens_at=None, closes_at=None,
                      effective_from=date.min, effective_to=date(9999, 12, 30))
        result = self.resolve(date.min, date.max)
        self.assertEqual(result.first_open_date, date.max)

    def test_invalid_target_weekdays_hours_and_date_range_are_rejected(self) -> None:
        invalid_values = (
            {"institution": self.institution}, {"exhibition": None},
            {"weekdays": [7]}, {"weekdays": [True]}, {"weekdays": [1, 1]},
            {"weekdays": []}, {"weekdays": "Tuesday"},
            {"opens_at": time(18)}, {"closes_at": None},
            {"effective_from": date(2026, 10, 1)},
            {"status": "UNKNOWN"}, {"kind": "OVERRIDE"},
        )
        for values in invalid_values:
            with self.subTest(values=values), self.assertRaises(ValidationError):
                self.schedule(**values)

    def test_mismatched_source_institution_is_rejected(self) -> None:
        self.source.institution_id = "different-museum"
        self.source.save()
        with self.assertRaises(ValidationError):
            self.schedule()

    def test_invalid_raw_date_and_time_report_validation_errors(self) -> None:
        for values in ({"effective_from": "not-a-date"}, {"opens_at": "not-a-time"}):
            with self.subTest(values=values):
                with self.assertRaises(Exception) as raised:
                    self.schedule(**values)
                self.assertIsInstance(raised.exception, ValidationError)

    def test_database_rejects_confirmed_schedule_without_open_state(self) -> None:
        row = self.schedule()
        with self.assertRaises(IntegrityError), transaction.atomic():
            catalog.OperatingSchedule.objects.filter(pk=row.pk).update(
                is_open=None, opens_at=None, closes_at=None,
            )

    def test_recommendation_carries_confirmed_day_without_per_row_queries(self) -> None:
        self.schedule()
        service = ORMRecommendationService()
        query = RecommendationQuery(visit_dates=VisitDateRange(date(2026, 9, 8), date(2026, 9, 10)))
        with CaptureQueriesContext(connection) as one_queries:
            result = service.recommend(query)
        self.assertEqual(result.recommendations[0].visit_availability.first_open_date, date(2026, 9, 8))
        for index in range(4):
            exhibition = catalog.Exhibition.objects.get(pk=self.exhibition.pk)
            exhibition.pk = None
            exhibition.title = f"추가 일정 전시 {index}"
            exhibition.save()
            source = self.source_record(f"extra-{index}")
            catalog.ExhibitionSourceLink.objects.create(
                exhibition=exhibition, source_id=source.source_id,
                source_record_id=source.source_record_id, latest_source_record=source,
            )
            self.schedule(exhibition=exhibition, source_record=source)
        with CaptureQueriesContext(connection) as many_queries:
            result = service.recommend(query)
        self.assertEqual(len(result.recommendations), 5)
        self.assertEqual(len(many_queries), len(one_queries))

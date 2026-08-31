from datetime import date, datetime, timedelta, timezone as datetime_timezone

from django.test import TestCase

from backend.apps.catalog.models import Exhibition, Institution
from backend.data_pipeline.freshness.schedule import refresh_schedule_for


UTC = datetime_timezone.utc


class FreshnessScheduleTests(TestCase):
    def setUp(self) -> None:
        self.institution = Institution.objects.create(
            registry_id="schedule-institution",
            name="일정 테스트 기관",
            region_area="서울",
            region_district="종로구",
        )

    def exhibition(
        self,
        *,
        lifecycle: str,
        start_date: date,
        end_date: date,
        last_verified_at: datetime,
    ) -> Exhibition:
        return Exhibition.objects.create(
            institution=self.institution,
            title="일정 테스트 전시",
            start_date=start_date,
            end_date=end_date,
            venue="일정 테스트 전시장",
            region_area="서울",
            region_district="종로구",
            lifecycle=lifecycle,
            official_url="https://example.com/exhibitions/schedule",
            last_verified_at=last_verified_at,
        )

    def test_current_exhibition_becomes_due_after_one_day(self) -> None:
        verified_at = datetime(2026, 8, 29, 3, 0, tzinfo=UTC)
        exhibition = self.exhibition(
            lifecycle=Exhibition.Lifecycle.CURRENT,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 9, 30),
            last_verified_at=verified_at,
        )

        before_due = refresh_schedule_for(
            exhibition,
            now=datetime(2026, 8, 30, 2, 59, 59, tzinfo=UTC),
        )
        at_due = refresh_schedule_for(
            exhibition,
            now=datetime(2026, 8, 30, 3, 0, tzinfo=UTC),
        )

        self.assertFalse(before_due.is_due)
        self.assertTrue(at_due.is_due)
        self.assertEqual(
            at_due.next_refresh_at,
            datetime(2026, 8, 30, 3, 0, tzinfo=UTC),
        )
        self.assertEqual(at_due.freshness, Exhibition.Freshness.FRESH)

    def test_current_exhibition_is_fresh_at_48_hours_and_stale_after(self) -> None:
        verified_at = datetime(2026, 8, 29, 3, 0, tzinfo=UTC)
        exhibition = self.exhibition(
            lifecycle=Exhibition.Lifecycle.CURRENT,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 9, 30),
            last_verified_at=verified_at,
        )

        at_boundary = refresh_schedule_for(
            exhibition,
            now=datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
        )
        after_boundary = refresh_schedule_for(
            exhibition,
            now=datetime(2026, 8, 31, 3, 0, 0, 1, tzinfo=UTC),
        )

        self.assertEqual(at_boundary.freshness, Exhibition.Freshness.FRESH)
        self.assertEqual(after_boundary.freshness, Exhibition.Freshness.STALE)
        self.assertEqual(
            at_boundary.stale_at,
            datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
        )

    def test_upcoming_in_exactly_seven_local_days_uses_daily_schedule(self) -> None:
        verified_at = datetime(2026, 8, 29, 3, 0, tzinfo=UTC)
        exhibition = self.exhibition(
            lifecycle=Exhibition.Lifecycle.UPCOMING,
            start_date=date(2026, 9, 7),
            end_date=date(2026, 10, 1),
            last_verified_at=verified_at,
        )

        schedule = refresh_schedule_for(
            exhibition,
            now=datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
        )

        self.assertEqual(
            schedule.next_refresh_at,
            datetime(2026, 8, 30, 3, 0, tzinfo=UTC),
        )
        self.assertEqual(
            schedule.stale_at,
            datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
        )

    def test_far_upcoming_is_due_at_72_hours_and_stale_only_after(self) -> None:
        verified_at = datetime(2026, 8, 28, 3, 0, tzinfo=UTC)
        exhibition = self.exhibition(
            lifecycle=Exhibition.Lifecycle.UPCOMING,
            start_date=date(2026, 9, 8),
            end_date=date(2026, 10, 1),
            last_verified_at=verified_at,
        )

        at_boundary = refresh_schedule_for(
            exhibition,
            now=datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
        )
        after_boundary = refresh_schedule_for(
            exhibition,
            now=datetime(2026, 8, 31, 3, 0, 0, 1, tzinfo=UTC),
        )

        self.assertTrue(at_boundary.is_due)
        self.assertEqual(at_boundary.freshness, Exhibition.Freshness.FRESH)
        self.assertEqual(after_boundary.freshness, Exhibition.Freshness.STALE)
        self.assertEqual(
            at_boundary.next_refresh_at,
            datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
        )

    def test_ended_exhibition_has_no_periodic_schedule(self) -> None:
        exhibition = self.exhibition(
            lifecycle=Exhibition.Lifecycle.ENDED,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 8, 1),
            last_verified_at=datetime(2026, 7, 30, 3, 0, tzinfo=UTC),
        )

        schedule = refresh_schedule_for(
            exhibition,
            now=datetime(2026, 8, 31, 3, 0, tzinfo=UTC),
        )

        self.assertFalse(schedule.is_due)
        self.assertIsNone(schedule.next_refresh_at)
        self.assertIsNone(schedule.stale_at)
        self.assertEqual(schedule.reason, "ENDED_NOT_PERIODIC")

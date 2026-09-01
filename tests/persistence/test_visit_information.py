from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from backend.apps.catalog.models import (
    AccessibilityFact,
    Exhibition,
    Institution,
    PriceOption,
    ReservationInfo,
    SensoryNotice,
    VisitDuration,
)
from backend.apps.sources.models import SourceRecord


class VisitInformationModelTests(TestCase):
    def setUp(self) -> None:
        self.institution = Institution.objects.create(
            registry_id="institution-a",
            name="기관 A",
            region_area="서울",
            region_district="종로구",
        )
        self.exhibition = Exhibition.objects.create(
            institution=self.institution,
            title="근거 있는 전시",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
            venue="기관 A 전시장",
            region_area="서울",
            region_district="종로구",
            lifecycle=Exhibition.Lifecycle.CURRENT,
            official_url="https://example.com/exhibitions/a",
            eligibility=Exhibition.Eligibility.VERIFIED,
        )
        self.source_record = SourceRecord.objects.create(
            source_id="official-a",
            institution_id=self.institution.registry_id,
            source_record_id="record-a",
            source_owner="기관 A",
            payload={"title": "근거 있는 전시"},
            content_hash="a" * 64,
        )

    def test_unknown_visit_information_has_no_inferred_values_or_core_side_effect(self) -> None:
        price = PriceOption(
            exhibition=self.exhibition,
            source_record=self.source_record,
            status=PriceOption.Status.UNKNOWN,
        )
        reservation = ReservationInfo(
            exhibition=self.exhibition,
            source_record=self.source_record,
            reservation_type=ReservationInfo.Type.UNKNOWN,
        )
        duration = VisitDuration(
            exhibition=self.exhibition,
            source_record=self.source_record,
            status=VisitDuration.Status.UNKNOWN,
        )
        accessibility_unknown = AccessibilityFact(
            exhibition=self.exhibition,
            source_record=self.source_record,
            kind=AccessibilityFact.Kind.WHEELCHAIR_ACCESS,
            state=AccessibilityFact.State.UNKNOWN,
        )
        accessibility_negative = AccessibilityFact(
            exhibition=self.exhibition,
            source_record=self.source_record,
            kind=AccessibilityFact.Kind.CAPTIONS,
            state=AccessibilityFact.State.CONFIRMED_NEGATIVE,
        )
        sensory_unknown = SensoryNotice(
            exhibition=self.exhibition,
            source_record=self.source_record,
            kind=SensoryNotice.Kind.FLASHING_LIGHTS,
            state=SensoryNotice.State.UNKNOWN,
        )
        sensory_negative = SensoryNotice(
            exhibition=self.exhibition,
            source_record=self.source_record,
            kind=SensoryNotice.Kind.LOUD_SOUND,
            state=SensoryNotice.State.CONFIRMED_NEGATIVE,
        )

        records = (
            price,
            reservation,
            duration,
            accessibility_unknown,
            accessibility_negative,
            sensory_unknown,
            sensory_negative,
        )
        for record in records:
            record.full_clean()
            record.save()

        self.exhibition.refresh_from_db()
        self.assertEqual(self.exhibition.eligibility, Exhibition.Eligibility.VERIFIED)
        self.assertIsNone(price.amount_min)
        self.assertIsNone(price.amount_max)
        self.assertIsNone(price.is_free)
        self.assertIsNone(duration.minimum_minutes)
        self.assertIsNone(duration.maximum_minutes)
        self.assertNotEqual(accessibility_unknown.state, accessibility_negative.state)
        self.assertNotEqual(sensory_unknown.state, sensory_negative.state)

    def test_unknown_rows_reject_fact_values(self) -> None:
        invalid_records = (
            PriceOption(
                exhibition=self.exhibition,
                source_record=self.source_record,
                status=PriceOption.Status.UNKNOWN,
                amount_min=Decimal("10000"),
            ),
            ReservationInfo(
                exhibition=self.exhibition,
                source_record=self.source_record,
                reservation_type=ReservationInfo.Type.UNKNOWN,
                official_url="https://example.com/reserve",
            ),
            VisitDuration(
                exhibition=self.exhibition,
                source_record=self.source_record,
                status=VisitDuration.Status.UNKNOWN,
                minimum_minutes=60,
            ),
            AccessibilityFact(
                exhibition=self.exhibition,
                source_record=self.source_record,
                kind=AccessibilityFact.Kind.SIGN_LANGUAGE,
                state=AccessibilityFact.State.UNKNOWN,
                details="수어 통역 제공",
            ),
            SensoryNotice(
                exhibition=self.exhibition,
                source_record=self.source_record,
                kind=SensoryNotice.Kind.DARK_SPACE,
                state=SensoryNotice.State.UNKNOWN,
                details="어두운 공간 있음",
            ),
        )

        for record in invalid_records:
            with self.subTest(model=record.__class__.__name__):
                with self.assertRaises(ValidationError):
                    record.full_clean()

    def test_database_rejects_unknown_price_with_an_amount(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            PriceOption.objects.bulk_create(
                [
                    PriceOption(
                        exhibition=self.exhibition,
                        source_record=self.source_record,
                        status=PriceOption.Status.UNKNOWN,
                        amount_min=Decimal("10000"),
                    )
                ]
            )

    def test_confirmed_price_and_official_duration_preserve_ranges(self) -> None:
        price = PriceOption(
            exhibition=self.exhibition,
            source_record=self.source_record,
            status=PriceOption.Status.CONFIRMED,
            category=PriceOption.Category.STANDARD,
            audience="ADULT",
            currency="KRW",
            amount_min=Decimal("15000"),
            amount_max=Decimal("25000"),
            is_free=False,
            is_standard_adult_admission=True,
        )
        duration = VisitDuration(
            exhibition=self.exhibition,
            source_record=self.source_record,
            status=VisitDuration.Status.OFFICIAL,
            minimum_minutes=60,
            maximum_minutes=90,
        )

        price.full_clean()
        duration.full_clean()

        self.assertEqual(price.amount_min, Decimal("15000"))
        self.assertEqual(duration.maximum_minutes, 90)

    def test_rejects_invalid_price_and_duration_ranges(self) -> None:
        invalid_price = PriceOption(
            exhibition=self.exhibition,
            source_record=self.source_record,
            status=PriceOption.Status.CONFIRMED,
            category=PriceOption.Category.STANDARD,
            audience="ADULT",
            currency="KRW",
            amount_min=Decimal("25000"),
            amount_max=Decimal("15000"),
            is_free=False,
        )
        invalid_duration = VisitDuration(
            exhibition=self.exhibition,
            source_record=self.source_record,
            status=VisitDuration.Status.OFFICIAL,
            minimum_minutes=90,
            maximum_minutes=60,
        )

        with self.assertRaises(ValidationError):
            invalid_price.full_clean()
        with self.assertRaises(ValidationError):
            invalid_duration.full_clean()

    def test_requires_exactly_one_target(self) -> None:
        no_target = ReservationInfo(
            source_record=self.source_record,
            reservation_type=ReservationInfo.Type.NOT_REQUIRED,
        )
        two_targets = ReservationInfo(
            exhibition=self.exhibition,
            institution=self.institution,
            source_record=self.source_record,
            reservation_type=ReservationInfo.Type.NOT_REQUIRED,
        )

        with self.assertRaises(ValidationError):
            no_target.full_clean()
        with self.assertRaises(ValidationError):
            two_targets.full_clean()

    def test_rejects_evidence_from_another_institution(self) -> None:
        other_source = SourceRecord.objects.create(
            source_id="official-b",
            institution_id="institution-b",
            source_record_id="record-b",
            source_owner="기관 B",
            payload={},
            content_hash="b" * 64,
        )
        fact = AccessibilityFact(
            exhibition=self.exhibition,
            source_record=other_source,
            kind=AccessibilityFact.Kind.MOBILITY_ACCESS,
            state=AccessibilityFact.State.CONFIRMED_POSITIVE,
        )

        with self.assertRaises(ValidationError):
            fact.full_clean()

        with self.assertRaises(ValidationError):
            ReservationInfo.objects.create(
                exhibition=self.exhibition,
                source_record=other_source,
                reservation_type=ReservationInfo.Type.NOT_REQUIRED,
            )

    def test_reservation_link_must_use_https(self) -> None:
        reservation = ReservationInfo(
            exhibition=self.exhibition,
            source_record=self.source_record,
            reservation_type=ReservationInfo.Type.REQUIRED,
            official_url="http://example.com/reserve",
        )

        with self.assertRaises(ValidationError):
            reservation.full_clean()

    def test_supports_institution_scoped_facts(self) -> None:
        fact = AccessibilityFact(
            institution=self.institution,
            source_record=self.source_record,
            kind=AccessibilityFact.Kind.MOBILITY_ACCESS,
            state=AccessibilityFact.State.CONFIRMED_POSITIVE,
            details="엘리베이터 운영",
        )

        fact.full_clean()
        fact.save()

        self.assertEqual(fact.institution, self.institution)
        self.assertIsNone(fact.exhibition_id)

from datetime import date, timedelta
from decimal import Decimal
from hashlib import sha256
from importlib import import_module, util

from django.test import TestCase
from django.utils import timezone

from backend.apps.catalog.models import (
    AccessibilityFact,
    Exhibition,
    ExhibitionSourceLink,
    Institution,
    PriceOption,
    ReservationInfo,
    SensoryNotice,
    VisitDuration,
)
from backend.apps.sources.models import SourceRecord


class VisitEvidenceResolverTests(TestCase):
    def setUp(self) -> None:
        self.institution = Institution.objects.create(
            registry_id="visit-resolver",
            name="방문 근거 미술관",
            region_area="서울",
            region_district="종로구",
        )
        self.exhibition = Exhibition.objects.create(
            institution=self.institution,
            title="방문 근거 전시",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 10, 1),
            venue="방문 근거 미술관",
            region_area="서울",
            region_district="종로구",
            lifecycle=Exhibition.Lifecycle.CURRENT,
            official_url="https://example.com/exhibitions/visit-evidence",
            eligibility=Exhibition.Eligibility.VERIFIED,
        )
        self.old_source = self.create_source("visit-old")
        self.current_source = self.create_source("visit-current")
        self.second_current_source = self.create_source("visit-current-second")
        ExhibitionSourceLink.objects.create(
            exhibition=self.exhibition,
            source_id=self.current_source.source_id,
            source_record_id=self.current_source.source_record_id,
            latest_source_record=self.current_source,
        )

    def create_source(self, source_record_id: str) -> SourceRecord:
        return SourceRecord.objects.create(
            source_id=f"official-{source_record_id}",
            institution_id=self.institution.registry_id,
            source_record_id=source_record_id,
            source_owner=self.institution.name,
            payload={"id": source_record_id},
            content_hash=sha256(source_record_id.encode()).hexdigest(),
        )

    def feature(self) -> tuple[object, object]:
        self.assertIsNotNone(
            util.find_spec("backend.apps.discovery.visit_conditions"),
            "visit evidence resolver is missing",
        )
        module = import_module("backend.apps.discovery.visit_conditions")
        return module, module.VisitEvidenceResolver()

    def create_adult_price(
        self,
        *,
        source_record: SourceRecord,
        amount: int,
        exhibition: Exhibition | None = None,
        institution: Institution | None = None,
        verified_at: object | None = None,
    ) -> PriceOption:
        values: dict[str, object] = {
            "exhibition": exhibition,
            "institution": institution,
            "source_record": source_record,
            "status": PriceOption.Status.CONFIRMED,
            "category": PriceOption.Category.STANDARD,
            "audience": "ADULT",
            "currency": "KRW",
            "amount_min": Decimal(amount),
            "amount_max": Decimal(amount),
            "is_free": amount == 0,
            "is_standard_adult_admission": True,
        }
        if verified_at is not None:
            values["verified_at"] = verified_at
        return PriceOption.objects.create(**values)

    def test_current_exhibition_evidence_wins_and_old_source_is_ignored(self) -> None:
        module, resolver = self.feature()
        self.create_adult_price(
            exhibition=self.exhibition,
            source_record=self.old_source,
            amount=30000,
        )
        self.create_adult_price(
            exhibition=self.exhibition,
            source_record=self.current_source,
            amount=10000,
        )
        self.create_adult_price(
            institution=self.institution,
            source_record=self.second_current_source,
            amount=5000,
        )

        resolved = resolver.resolve(self.exhibition)

        self.assertEqual(resolved.price.state, module.EvidenceState.CONFIRMED)
        self.assertEqual(resolved.price.amount, Decimal("10000"))
        self.assertEqual(resolved.price.currency, "KRW")

    def test_institution_fallback_uses_only_the_latest_verified_precedence(self) -> None:
        module, resolver = self.feature()
        now = timezone.now()
        self.create_adult_price(
            institution=self.institution,
            source_record=self.old_source,
            amount=30000,
            verified_at=now - timedelta(days=1),
        )
        self.create_adult_price(
            institution=self.institution,
            source_record=self.second_current_source,
            amount=12000,
            verified_at=now,
        )

        resolved = resolver.resolve(self.exhibition)

        self.assertEqual(resolved.price.state, module.EvidenceState.CONFIRMED)
        self.assertEqual(resolved.price.amount, Decimal("12000"))

    def test_non_adult_exhibition_price_does_not_block_adult_institution_fallback(
        self,
    ) -> None:
        module, resolver = self.feature()
        PriceOption.objects.create(
            exhibition=self.exhibition,
            source_record=self.current_source,
            status=PriceOption.Status.CONFIRMED,
            category=PriceOption.Category.STANDARD,
            audience="CHILD",
            currency="KRW",
            amount_min=Decimal("5000"),
            amount_max=Decimal("5000"),
            is_free=False,
            is_standard_adult_admission=False,
        )
        self.create_adult_price(
            institution=self.institution,
            source_record=self.second_current_source,
            amount=12000,
        )

        resolved = resolver.resolve(self.exhibition)

        self.assertEqual(resolved.price.state, module.EvidenceState.CONFIRMED)
        self.assertEqual(resolved.price.amount, Decimal("12000"))

    def test_equal_priority_disagreement_is_a_conflict(self) -> None:
        module, resolver = self.feature()
        ExhibitionSourceLink.objects.create(
            exhibition=self.exhibition,
            source_id=self.second_current_source.source_id,
            source_record_id=self.second_current_source.source_record_id,
            latest_source_record=self.second_current_source,
        )
        ReservationInfo.objects.create(
            exhibition=self.exhibition,
            source_record=self.current_source,
            reservation_type=ReservationInfo.Type.REQUIRED,
        )
        ReservationInfo.objects.create(
            exhibition=self.exhibition,
            source_record=self.second_current_source,
            reservation_type=ReservationInfo.Type.NOT_REQUIRED,
        )

        resolved = resolver.resolve(self.exhibition)

        self.assertEqual(
            resolved.reservation.state,
            module.EvidenceState.CONFLICT,
        )
        self.assertIsNone(resolved.reservation.reservation_type)

    def test_equal_priority_free_prices_ignore_irrelevant_currency_notation(
        self,
    ) -> None:
        module, resolver = self.feature()
        ExhibitionSourceLink.objects.create(
            exhibition=self.exhibition,
            source_id=self.second_current_source.source_id,
            source_record_id=self.second_current_source.source_record_id,
            latest_source_record=self.second_current_source,
        )
        PriceOption.objects.create(
            exhibition=self.exhibition,
            source_record=self.current_source,
            status=PriceOption.Status.CONFIRMED,
            category=PriceOption.Category.STANDARD,
            audience="ADULT",
            is_free=True,
            is_standard_adult_admission=True,
        )
        PriceOption.objects.create(
            exhibition=self.exhibition,
            source_record=self.second_current_source,
            status=PriceOption.Status.CONFIRMED,
            category=PriceOption.Category.STANDARD,
            audience="ADULT",
            currency="KRW",
            amount_min=Decimal("0"),
            amount_max=Decimal("0"),
            is_free=True,
            is_standard_adult_admission=True,
        )

        resolved = resolver.resolve(self.exhibition)

        self.assertEqual(resolved.price.state, module.EvidenceState.CONFIRMED)
        self.assertTrue(resolved.price.is_free)
        self.assertEqual(resolved.price.amount, Decimal("0"))
        self.assertIsNone(resolved.price.currency)

    def test_explicit_unknown_and_missing_values_stay_unknown(self) -> None:
        module, resolver = self.feature()
        PriceOption.objects.create(
            exhibition=self.exhibition,
            source_record=self.current_source,
            status=PriceOption.Status.UNKNOWN,
        )
        ReservationInfo.objects.create(
            exhibition=self.exhibition,
            source_record=self.current_source,
            reservation_type=ReservationInfo.Type.UNKNOWN,
        )

        resolved = resolver.resolve(self.exhibition)

        self.assertEqual(resolved.price.state, module.EvidenceState.UNKNOWN)
        self.assertIsNone(resolved.price.amount)
        self.assertEqual(resolved.reservation.state, module.EvidenceState.UNKNOWN)
        self.assertEqual(resolved.duration.state, module.EvidenceState.UNKNOWN)

    def test_official_duration_preserves_the_confirmed_range(self) -> None:
        module, resolver = self.feature()
        VisitDuration.objects.create(
            exhibition=self.exhibition,
            source_record=self.current_source,
            status=VisitDuration.Status.OFFICIAL,
            minimum_minutes=60,
            maximum_minutes=90,
        )

        resolved = resolver.resolve(self.exhibition)

        self.assertEqual(resolved.duration.state, module.EvidenceState.CONFIRMED)
        self.assertEqual(resolved.duration.minimum_minutes, 60)
        self.assertEqual(resolved.duration.maximum_minutes, 90)

    def test_confirmed_negative_is_distinct_from_unknown_for_safety_facts(self) -> None:
        module, resolver = self.feature()
        AccessibilityFact.objects.create(
            exhibition=self.exhibition,
            source_record=self.current_source,
            kind=AccessibilityFact.Kind.WHEELCHAIR_ACCESS,
            state=AccessibilityFact.State.CONFIRMED_NEGATIVE,
        )
        AccessibilityFact.objects.create(
            exhibition=self.exhibition,
            source_record=self.current_source,
            kind=AccessibilityFact.Kind.CAPTIONS,
            state=AccessibilityFact.State.UNKNOWN,
        )
        SensoryNotice.objects.create(
            exhibition=self.exhibition,
            source_record=self.current_source,
            kind=SensoryNotice.Kind.FLASHING_LIGHTS,
            state=SensoryNotice.State.CONFIRMED_NEGATIVE,
        )

        resolved = resolver.resolve(self.exhibition)

        wheelchair = resolved.accessibility[
            AccessibilityFact.Kind.WHEELCHAIR_ACCESS
        ]
        captions = resolved.accessibility[AccessibilityFact.Kind.CAPTIONS]
        flashing = resolved.sensory[SensoryNotice.Kind.FLASHING_LIGHTS]
        self.assertEqual(wheelchair.state, module.EvidenceState.CONFIRMED)
        self.assertEqual(
            wheelchair.value,
            AccessibilityFact.State.CONFIRMED_NEGATIVE,
        )
        self.assertEqual(captions.state, module.EvidenceState.UNKNOWN)
        self.assertIsNone(captions.value)
        self.assertEqual(flashing.state, module.EvidenceState.CONFIRMED)
        self.assertEqual(
            flashing.value,
            SensoryNotice.State.CONFIRMED_NEGATIVE,
        )

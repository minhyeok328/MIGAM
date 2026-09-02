from datetime import date
from decimal import Decimal
from hashlib import sha256

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from backend.apps.catalog.models import (
    AccessibilityFact,
    Exhibition,
    ExhibitionSourceLink,
    Institution,
    MediaAsset,
    MediaRights,
    PriceOption,
    ReservationInfo,
    SensoryNotice,
    VisitDuration,
)
from backend.apps.catalog.rights import record_media_rights
from backend.apps.discovery.features import (
    FeatureAssertionInput,
    record_content_feature_snapshot,
)
from backend.apps.sources.models import SourceRecord


RECOMMENDATION_URL = "/api/internal/v1/recommendations/"


class InternalRecommendationAPITests(TestCase):
    def setUp(self) -> None:
        self.institution = Institution.objects.create(
            registry_id="recommend-api",
            name="추천 API 미술관",
            region_area="서울",
            region_district="종로구",
        )
        self.sequence = 0
        self.current, self.current_source = self.create_exhibition("현재 일반 전시")
        self.featured, self.featured_source = self.create_exhibition(
            "차분한 조건 전시"
        )
        self.unknown_price, self.unknown_price_source = self.create_exhibition(
            "가격 확인 필요 전시"
        )
        self.add_price(self.current, self.current_source, 12000)
        self.add_price(self.featured, self.featured_source, 8000)
        PriceOption.objects.create(
            exhibition=self.unknown_price,
            source_record=self.unknown_price_source,
            status=PriceOption.Status.UNKNOWN,
        )
        record_content_feature_snapshot(
            exhibition=self.featured,
            assertions=(
                FeatureAssertionInput(
                    axis="MOOD",
                    value="CALM",
                    evidence_kind="DIRECT",
                    source_record=self.featured_source,
                ),
            ),
        )
        self.add_required_visit_evidence()
        self.add_hidden_media()

    def create_exhibition(
        self,
        title: str,
    ) -> tuple[Exhibition, SourceRecord]:
        self.sequence += 1
        source_record_id = f"recommend-api-{self.sequence}"
        source = SourceRecord.objects.create(
            source_id="official-recommend-api",
            institution_id=self.institution.registry_id,
            source_record_id=source_record_id,
            source_owner=self.institution.name,
            payload={"title": title, "private_note": "응답 금지"},
            content_hash=sha256(source_record_id.encode()).hexdigest(),
        )
        exhibition = Exhibition.objects.create(
            institution=self.institution,
            title=title,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
            venue="추천 API 미술관 전시장",
            region_area="서울",
            region_district="종로구",
            lifecycle=Exhibition.Lifecycle.CURRENT,
            official_url=f"https://example.com/exhibitions/{source_record_id}",
            freshness=Exhibition.Freshness.FRESH,
            eligibility=Exhibition.Eligibility.VERIFIED,
        )
        ExhibitionSourceLink.objects.create(
            exhibition=exhibition,
            source_id=source.source_id,
            source_record_id=source.source_record_id,
            latest_source_record=source,
        )
        return exhibition, source

    def add_price(
        self,
        exhibition: Exhibition,
        source: SourceRecord,
        amount: int,
    ) -> None:
        PriceOption.objects.create(
            exhibition=exhibition,
            source_record=source,
            status=PriceOption.Status.CONFIRMED,
            category=PriceOption.Category.STANDARD,
            audience="ADULT",
            currency="KRW",
            amount_min=Decimal(amount),
            amount_max=Decimal(amount),
            is_free=False,
            is_standard_adult_admission=True,
        )

    def add_required_visit_evidence(self) -> None:
        AccessibilityFact.objects.create(
            exhibition=self.featured,
            source_record=self.featured_source,
            kind=AccessibilityFact.Kind.WHEELCHAIR_ACCESS,
            state=AccessibilityFact.State.CONFIRMED_POSITIVE,
        )
        SensoryNotice.objects.create(
            exhibition=self.featured,
            source_record=self.featured_source,
            kind=SensoryNotice.Kind.FLASHING_LIGHTS,
            state=SensoryNotice.State.CONFIRMED_NEGATIVE,
        )
        ReservationInfo.objects.create(
            exhibition=self.featured,
            source_record=self.featured_source,
            reservation_type=ReservationInfo.Type.REQUIRED,
            official_url="https://example.com/reservations/featured",
        )
        VisitDuration.objects.create(
            exhibition=self.featured,
            source_record=self.featured_source,
            status=VisitDuration.Status.OFFICIAL,
            minimum_minutes=60,
            maximum_minutes=90,
        )

    def add_hidden_media(self) -> None:
        asset = MediaAsset.objects.create(
            exhibition=self.featured,
            source_record=self.featured_source,
            media_type=MediaAsset.MediaType.IMAGE,
            role=MediaAsset.Role.POSTER,
            origin_url="https://private.example.com/featured.jpg",
            source_page_url="https://example.com/media/featured",
        )
        record_media_rights(
            asset=asset,
            source_record=self.featured_source,
            policy_status=MediaRights.PolicyStatus.RIGHTS_UNKNOWN,
        )

    def complete_request(self) -> dict[str, object]:
        return {
            "region": {"area": "서울", "district": "종로구"},
            "visit_dates": {"start": "2026-09-15", "end": "2026-09-15"},
            "max_budget_krw": 10000,
            "required_accessibility": ["WHEELCHAIR_ACCESS"],
            "avoided_sensory": ["FLASHING_LIGHTS"],
            "reservation": {"mode": "REQUIRED", "types": ["REQUIRED"]},
            "duration": {
                "mode": "REQUIRED",
                "minimum_minutes": 60,
                "maximum_minutes": 90,
            },
            "preferred_features": [{"axis": "MOOD", "value": "CALM"}],
            "liked_exhibition_ids": [],
            "liked_institution_ids": [self.institution.pk],
            "limit": 6,
        }

    def test_empty_request_returns_canonical_recommendations(self) -> None:
        response = self.client.post(
            RECOMMENDATION_URL,
            data={},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            set(payload),
            {
                "algorithm_version",
                "candidate_count",
                "recommendations",
                "needs_verification",
            },
        )
        self.assertEqual(payload["algorithm_version"], "p0-recommendation-1.0.0")
        self.assertEqual(payload["candidate_count"], 3)
        self.assertEqual(len(payload["recommendations"]), 3)
        first = payload["recommendations"][0]
        self.assertEqual(
            set(first),
            {
                "type",
                "id",
                "title",
                "institution",
                "lifecycle",
                "start_date",
                "end_date",
                "venue",
                "region",
                "official_url",
                "freshness",
                "eligibility",
                "last_verified_at",
                "source",
                "media",
                "match_level",
                "is_exploration",
                "reasons",
            },
        )
        self.assertNotIn("score", first)
        self.assertNotIn("percentage", first)
        self.assertEqual(set(first["reasons"][0]), {"code", "text", "feature"})
        self.assertNotIn("응답 금지", response.content.decode())

    def test_complete_request_applies_conditions_and_returns_safe_reasoned_result(
        self,
    ) -> None:
        response = self.client.post(
            RECOMMENDATION_URL,
            data=self.complete_request(),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            [item["id"] for item in payload["recommendations"]],
            [self.featured.pk],
        )
        item = payload["recommendations"][0]
        self.assertEqual(item["match_level"], "GOOD_MATCH")
        self.assertEqual(item["reasons"][0]["code"], "PREFERRED_FEATURE")
        self.assertEqual(
            item["reasons"][0]["feature"],
            {"axis": "MOOD", "value": "CALM"},
        )
        self.assertEqual(item["source"]["source_record_id"], self.featured_source.source_record_id)
        self.assertEqual(item["media"]["status"], "HIDDEN")
        self.assertIsNone(item["media"]["media_url"])
        self.assertNotIn("private.example.com", response.content.decode())

    def test_unknown_price_is_returned_only_as_needs_verification(self) -> None:
        response = self.client.post(
            RECOMMENDATION_URL,
            data={"max_budget_krw": 10000, "limit": 24},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            [item["id"] for item in payload["recommendations"]],
            [self.featured.pk],
        )
        self.assertEqual(
            [item["id"] for item in payload["needs_verification"]],
            [self.unknown_price.pk],
        )
        verification = payload["needs_verification"][0]
        self.assertEqual(verification["verification_reasons"], ["PRICE_UNKNOWN"])
        self.assertNotIn("match_level", verification)
        self.assertNotIn("score", verification)

    def test_zero_result_is_a_success_without_relaxing_conditions(self) -> None:
        response = self.client.post(
            RECOMMENDATION_URL,
            data={"region": {"area": "부산", "district": "해운대구"}},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["candidate_count"], 0)
        self.assertEqual(response.json()["recommendations"], [])
        self.assertEqual(response.json()["needs_verification"], [])

    def test_invalid_nested_inputs_return_machine_readable_400(self) -> None:
        invalid_requests = (
            {"visit_dates": {"start": "2026-09-20", "end": "2026-09-10"}},
            {"max_budget_krw": -1},
            {"required_accessibility": ["UNKNOWN_KIND"]},
            {"reservation": {"mode": "REQUIRED", "types": ["UNKNOWN"]}},
            {
                "duration": {
                    "mode": "REQUIRED",
                    "minimum_minutes": 90,
                    "maximum_minutes": 60,
                }
            },
            {
                "preferred_features": [
                    {"axis": "MOOD", "value": "CALM"},
                    {"axis": "MOOD", "value": "CALM"},
                ]
            },
            {"limit": 25},
        )

        for request_payload in invalid_requests:
            with self.subTest(request_payload=request_payload):
                response = self.client.post(
                    RECOMMENDATION_URL,
                    data=request_payload,
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 400)
                payload = response.json()
                self.assertEqual(
                    payload["error"]["code"],
                    "INVALID_RECOMMENDATION_REQUEST",
                )
                self.assertEqual(
                    set(payload["error"]),
                    {"code", "message", "details"},
                )

    def test_request_signals_are_not_persisted(self) -> None:
        request_payload = {
            "preferred_features": [{"axis": "MOOD", "value": "CALM"}],
            "liked_exhibition_ids": [self.current.pk],
            "liked_institution_ids": [self.institution.pk],
        }

        with CaptureQueriesContext(connection) as captured:
            response = self.client.post(
                RECOMMENDATION_URL,
                data=request_payload,
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        mutating_sql = [
            query["sql"]
            for query in captured.captured_queries
            if query["sql"].lstrip().upper().startswith(
                ("INSERT", "UPDATE", "DELETE", "REPLACE")
            )
        ]
        self.assertEqual(mutating_sql, [])

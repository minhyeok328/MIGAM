from datetime import date, time, timedelta
from decimal import Decimal
from hashlib import sha256
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from backend.apps.catalog.models import (
    AccessibilityFact, Exhibition, ExhibitionSourceLink, Institution, MediaAsset,
    MediaRights, OperatingSchedule, PriceOption, ReservationInfo, SensoryNotice,
    SourceConflict, VisitDuration,
)
from backend.apps.catalog.rights import record_media_rights
from backend.apps.discovery.features import FeatureAssertionInput, record_content_feature_snapshot
from backend.apps.sources.models import SourceRecord


class InternalDetailAPITests(TestCase):
    def setUp(self) -> None:
        self.institution = Institution.objects.create(
            registry_id="detail-museum", name="상세 미술관", region_area="서울", region_district="종로구",
        )
        self.sequence = 0
        self.exhibition, self.source = self.create_exhibition("현재 전시")
        self.url = f"/api/internal/v1/exhibitions/{self.exhibition.pk}/"
        self.institution_url = f"/api/internal/v1/institutions/{self.institution.pk}/"

    def create_exhibition(self, title: str, **changes: object) -> tuple[Exhibition, SourceRecord]:
        self.sequence += 1
        identifier = f"detail-{self.sequence}"
        source = SourceRecord.objects.create(
            source_id="official-detail", institution_id=self.institution.registry_id,
            source_record_id=identifier, source_owner=self.institution.name,
            payload={"title": title, "private_note": "never-expose-raw-payload"},
            content_hash=sha256(identifier.encode()).hexdigest(),
        )
        exhibition = Exhibition.objects.create(**{
            "institution": self.institution, "title": title,
            "start_date": date(2026, 9, 1), "end_date": date(2026, 9, 30),
            "venue": "상세 미술관 전시실", "region_area": "서울", "region_district": "종로구",
            "lifecycle": "CURRENT", "official_url": f"https://example.com/exhibitions/{identifier}",
            "freshness": "FRESH", "eligibility": "VERIFIED", **changes,
        })
        ExhibitionSourceLink.objects.create(
            exhibition=exhibition, source_id=source.source_id,
            source_record_id=source.source_record_id, latest_source_record=source,
        )
        return exhibition, source

    def add_price(self, source: SourceRecord, amount: int, **target: object) -> PriceOption:
        return PriceOption.objects.create(
            **(target or {"exhibition": self.exhibition}), source_record=source,
            status="CONFIRMED", category="STANDARD", audience="ADULT", currency="KRW",
            amount_min=Decimal(amount), amount_max=Decimal(amount), is_free=amount == 0,
            is_standard_adult_admission=True,
        )

    def test_detail_resolves_visit_conditions_with_matching_provenance(self) -> None:
        self.add_price(self.source, 12000)
        ReservationInfo.objects.create(
            exhibition=self.exhibition, source_record=self.source, reservation_type="REQUIRED",
            official_url="https://example.com/reservation", guidance="공식 예약 안내를 확인하세요.",
        )
        VisitDuration.objects.create(exhibition=self.exhibition, source_record=self.source,
                                    status="OFFICIAL", minimum_minutes=60, maximum_minutes=90)
        AccessibilityFact.objects.create(exhibition=self.exhibition, source_record=self.source,
                                         kind="WHEELCHAIR_ACCESS", state="CONFIRMED_POSITIVE")
        SensoryNotice.objects.create(exhibition=self.exhibition, source_record=self.source,
                                     kind="FLASHING_LIGHTS", state="CONFIRMED_NEGATIVE")
        record_content_feature_snapshot(exhibition=self.exhibition, assertions=(
            FeatureAssertionInput(axis="MEDIA_GROUP", value="PAINTING", evidence_kind="DIRECT", source_record=self.source),
        ))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(set(body), {"exhibition", "content", "visit_information", "features", "operating_schedule"})
        self.assertEqual(body["exhibition"]["id"], self.exhibition.pk)
        info = body["visit_information"]
        self.assertEqual(info["price"]["amount"], 12000)
        self.assertEqual(info["price"]["state"], "CONFIRMED")
        evidence = info["price"]["evidence"][0]
        self.assertEqual(evidence["scope"], "EXHIBITION")
        self.assertEqual(evidence["source"]["source_record_id"], self.source.source_record_id)
        self.assertIn("verified_at", evidence)
        self.assertEqual(info["reservation"]["official_urls"], ["https://example.com/reservation"])
        self.assertEqual(info["duration"]["maximum_minutes"], 90)
        self.assertEqual(info["accessibility"][0]["value"], "CONFIRMED_POSITIVE")
        self.assertEqual(len(info["accessibility"]), 6)
        self.assertEqual(len(info["sensory"]), 5)
        self.assertEqual(body["features"][0]["value"], "PAINTING")
        self.assertNotIn("payload", response.content.decode())

    def test_absent_information_is_explicitly_unknown(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["visit_information"]["price"], {
            "state": "UNKNOWN", "amount": None, "currency": None, "is_free": None, "evidence": [],
        })
        self.assertEqual(body["features"], [])
        self.assertEqual(body["operating_schedule"], {"state": "UNKNOWN", "visit_availability": None, "rules": []})
        self.assertTrue(all(row["state"] == "UNKNOWN" and row["value"] is None
                            for row in body["visit_information"]["sensory"]))

    def test_ended_and_canceled_detail_remain_readable_without_visitable_claim(self) -> None:
        for lifecycle in ("ENDED", "CANCELED"):
            with self.subTest(lifecycle=lifecycle):
                Exhibition.objects.filter(pk=self.exhibition.pk).update(lifecycle=lifecycle)
                response = self.client.get(self.url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["exhibition"]["lifecycle"], lifecycle)
                self.assertIsNone(response.json()["operating_schedule"]["visit_availability"])

    def test_missing_and_nonvisible_exhibitions_return_same_safe_404(self) -> None:
        missing = self.client.get("/api/internal/v1/exhibitions/999999999/")
        self.assertEqual(missing.status_code, 404)
        for fields in (
            {"eligibility": "EXCLUDED"}, {"eligibility": "DISCOVERY_ONLY"},
            {"freshness": "UNVERIFIED"}, {"lifecycle": "UNKNOWN"},
            {"official_url": "javascript:alert(1)"}, {"official_url": "https://user:secret@example.com"},
            {"official_url": "https://127.0.0.1/private"}, {"venue": ""}, {"end_date": date(2026, 8, 1)},
        ):
            with self.subTest(fields=fields):
                exhibition, _ = self.create_exhibition("비공개", **fields)
                response = self.client.get(f"/api/internal/v1/exhibitions/{exhibition.pk}/")
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json(), missing.json())

    def test_missing_source_and_open_core_conflict_are_not_visible(self) -> None:
        conflict, source = self.create_exhibition("핵심 충돌")
        SourceConflict.objects.create(exhibition=conflict, field_name="end_date", canonical_value="2026-09-30",
                                      candidate_value="2026-10-01", candidate_source_record=source)
        ExhibitionSourceLink.objects.filter(exhibition=self.exhibition).delete()
        for exhibition in (self.exhibition, conflict):
            self.assertEqual(self.client.get(f"/api/internal/v1/exhibitions/{exhibition.pk}/").status_code, 404)
        self.assertEqual(self.client.get(self.institution_url).status_code, 404)

    def test_conflicting_price_does_not_expose_a_single_amount(self) -> None:
        self.add_price(self.source, 10000)
        _, alternative = self.create_exhibition("다른 근거")
        ExhibitionSourceLink.objects.filter(latest_source_record=alternative).update(exhibition=self.exhibition)
        self.add_price(alternative, 20000)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        price = response.json()["visit_information"]["price"]
        self.assertEqual(price["state"], "CONFLICT")
        self.assertIsNone(price["amount"])
        self.assertEqual(len(price["evidence"]), 2)

    def test_replaced_source_facts_and_features_do_not_leak(self) -> None:
        self.add_price(self.source, 10000)
        record_content_feature_snapshot(exhibition=self.exhibition, assertions=(
            FeatureAssertionInput(axis="MOOD", value="CALM", evidence_kind="DIRECT", source_record=self.source),
        ))
        updated = SourceRecord.objects.create(source_id=self.source.source_id, institution_id=self.institution.registry_id,
            source_record_id=self.source.source_record_id, source_owner=self.institution.name,
            payload={"version": "updated"}, content_hash="b" * 64)
        ExhibitionSourceLink.objects.filter(exhibition=self.exhibition).update(latest_source_record=updated)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["visit_information"]["price"]["state"], "UNKNOWN")
        self.assertEqual(response.json()["features"], [])

    def test_institution_fallback_uses_latest_evidence_and_keeps_scope(self) -> None:
        old = self.add_price(self.source, 1000, institution=self.institution)
        PriceOption.objects.filter(pk=old.pk).update(verified_at=timezone.now() - timedelta(days=2))
        _, newest = self.create_exhibition("기관 안내")
        self.add_price(newest, 5000, institution=self.institution)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        price = response.json()["visit_information"]["price"]
        self.assertEqual(price["amount"], 5000)
        self.assertEqual(price["evidence"][0]["scope"], "INSTITUTION")

    def test_rights_unknown_media_and_unsafe_reservation_links_are_hidden(self) -> None:
        asset = MediaAsset.objects.create(exhibition=self.exhibition, source_record=self.source, media_type="IMAGE", role="POSTER",
            origin_url="https://example.com/secret-image.jpg", source_page_url="https://example.com/media")
        record_media_rights(asset=asset, source_record=self.source, policy_status=MediaRights.PolicyStatus.RIGHTS_UNKNOWN)
        reservation = ReservationInfo.objects.create(exhibition=self.exhibition, source_record=self.source,
            reservation_type="REQUIRED", official_url="https://example.com/booking")
        ReservationInfo.objects.filter(pk=reservation.pk).update(official_url="javascript:alert(1)")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["exhibition"]["media"]["status"], "HIDDEN")
        self.assertEqual(response.json()["visit_information"]["reservation"]["official_urls"], [])
        self.assertNotIn("secret-image", response.content.decode())
        self.assertNotIn("javascript:", response.content.decode())

    def test_schedule_exposes_first_confirmed_open_day_and_safe_rule_evidence(self) -> None:
        OperatingSchedule.objects.create(exhibition=self.exhibition, source_record=self.source, status="CONFIRMED", kind="REGULAR",
            effective_from=self.exhibition.start_date, effective_to=self.exhibition.end_date,
            weekdays=[1], is_open=True, opens_at=time(10), closes_at=time(18), rule_version="detail-test-1")
        with patch("backend.apps.discovery.detail.timezone.localdate", return_value=date(2026, 9, 6)):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        schedule = response.json()["operating_schedule"]
        self.assertEqual(schedule["state"], "OPEN")
        self.assertEqual(schedule["visit_availability"]["first_open_date"], "2026-09-08")
        self.assertEqual(schedule["visit_availability"]["opens_at"], "10:00:00")
        self.assertEqual(schedule["rules"][0]["evidence"]["source"]["source_record_id"], self.source.source_record_id)

    def test_institution_listing_is_paginated_and_filters_hidden_exhibitions(self) -> None:
        self.create_exhibition("종료 전시", lifecycle="ENDED")
        self.create_exhibition("예정 전시", lifecycle="UPCOMING")
        self.create_exhibition("노출 금지", eligibility="EXCLUDED")
        response = self.client.get(self.institution_url, {"page_size": 2})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["institution"]["searchable_exhibition_count"], 3)
        self.assertEqual(body["total"], 3)
        self.assertTrue(body["has_more"])
        self.assertEqual([row["lifecycle"] for row in body["exhibitions"]], ["CURRENT", "UPCOMING"])
        page_two = self.client.get(self.institution_url, {"page_size": 2, "page": 2}).json()
        self.assertFalse(page_two["has_more"])
        self.assertEqual(page_two["exhibitions"][0]["lifecycle"], "ENDED")
        for query in ({"page_size": 25}, {"page": 0}, {"page_size": "bad"}):
            with self.subTest(query=query):
                invalid = self.client.get(self.institution_url, query)
                self.assertEqual(invalid.status_code, 400)
                self.assertEqual(invalid.json()["error"]["code"], "INVALID_DETAIL_QUERY")

    def test_detail_endpoints_are_read_only(self) -> None:
        self.assertEqual(self.client.post(self.url, {}, content_type="application/json").status_code, 405)
        self.assertEqual(self.client.post(self.institution_url, {}, content_type="application/json").status_code, 405)

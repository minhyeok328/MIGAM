from datetime import date
from hashlib import sha256

from django.test import TestCase

from backend.apps.catalog.models import (
    Exhibition,
    ExhibitionSourceLink,
    Institution,
    MediaAsset,
    MediaRights,
)
from backend.apps.catalog.rights import record_media_rights
from backend.apps.discovery.projection import rebuild_search_documents
from backend.apps.sources.models import SourceRecord


SEARCH_URL = "/api/internal/v1/search/"


class InternalSearchAPITests(TestCase):
    def setUp(self) -> None:
        self.primary = Institution.objects.create(
            registry_id="api-light",
            name="서울 빛 미술관",
            region_area="서울",
            region_district="종로구",
        )
        self.secondary = Institution.objects.create(
            registry_id="api-sound",
            name="인천 소리 전시관",
            region_area="인천",
            region_district="중구",
        )
        self.current, self.current_source = self.create_exhibition(
            institution=self.primary,
            source_record_id="api-current",
            title="빛의 미술관 산책",
            lifecycle=Exhibition.Lifecycle.CURRENT,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 9, 30),
        )
        self.upcoming, self.upcoming_source = self.create_exhibition(
            institution=self.secondary,
            source_record_id="api-upcoming",
            title="소리로 만나는 도시",
            lifecycle=Exhibition.Lifecycle.UPCOMING,
            start_date=date(2026, 9, 20),
            end_date=date(2026, 10, 20),
        )
        self.ended, self.ended_source = self.create_exhibition(
            institution=self.primary,
            source_record_id="api-ended",
            title="빛의 기록 보관소",
            lifecycle=Exhibition.Lifecycle.ENDED,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 2, 1),
        )
        self.canceled, _ = self.create_exhibition(
            institution=self.primary,
            source_record_id="api-canceled",
            title="취소된 빛의 정원",
            lifecycle=Exhibition.Lifecycle.CANCELED,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 15),
        )
        self._add_media()
        rebuild_search_documents()

    def create_exhibition(
        self,
        *,
        institution: Institution,
        source_record_id: str,
        title: str,
        lifecycle: str,
        start_date: date,
        end_date: date,
    ) -> tuple[Exhibition, SourceRecord]:
        source_record = SourceRecord.objects.create(
            source_id=f"official-{institution.registry_id}",
            institution_id=institution.registry_id,
            source_record_id=source_record_id,
            source_owner=institution.name,
            payload={"title": title, "private_note": "응답 금지"},
            content_hash=sha256(source_record_id.encode()).hexdigest(),
        )
        exhibition = Exhibition.objects.create(
            institution=institution,
            title=title,
            start_date=start_date,
            end_date=end_date,
            venue=f"{institution.name} 전시장",
            region_area=institution.region_area,
            region_district=institution.region_district,
            lifecycle=lifecycle,
            official_url=f"https://example.com/exhibitions/{source_record_id}",
            freshness=Exhibition.Freshness.FRESH,
            eligibility=Exhibition.Eligibility.VERIFIED,
        )
        ExhibitionSourceLink.objects.create(
            exhibition=exhibition,
            source_id=source_record.source_id,
            source_record_id=source_record.source_record_id,
            latest_source_record=source_record,
        )
        return exhibition, source_record

    def _add_media(self) -> None:
        inline_asset = MediaAsset.objects.create(
            exhibition=self.current,
            source_record=self.current_source,
            media_type=MediaAsset.MediaType.IMAGE,
            role=MediaAsset.Role.POSTER,
            origin_url="https://cdn.example.com/current.jpg",
            source_page_url="https://example.com/current-media",
        )
        record_media_rights(
            asset=inline_asset,
            source_record=self.current_source,
            policy_status=MediaRights.PolicyStatus.REUSE_ALLOWED,
            rights_holder="서울 빛 미술관",
            license_name="공식 표시 허용",
            credit_line="서울 빛 미술관 제공",
            display_allowed=True,
            hotlink_allowed=True,
        )
        link_only_asset = MediaAsset.objects.create(
            exhibition=self.upcoming,
            source_record=self.upcoming_source,
            media_type=MediaAsset.MediaType.IMAGE,
            role=MediaAsset.Role.POSTER,
            origin_url="https://private.example.com/upcoming.jpg",
            source_page_url="https://example.com/upcoming-media",
        )
        record_media_rights(
            asset=link_only_asset,
            source_record=self.upcoming_source,
            policy_status=MediaRights.PolicyStatus.LINK_ONLY,
        )
        hidden_asset = MediaAsset.objects.create(
            exhibition=self.ended,
            source_record=self.ended_source,
            media_type=MediaAsset.MediaType.IMAGE,
            role=MediaAsset.Role.POSTER,
            origin_url="https://private.example.com/ended.jpg",
            source_page_url="https://example.com/ended-media",
        )
        record_media_rights(
            asset=hidden_asset,
            source_record=self.ended_source,
            policy_status=MediaRights.PolicyStatus.RIGHTS_UNKNOWN,
        )

    def test_default_response_lists_current_and_upcoming_canonical_records(self) -> None:
        response = self.client.get(SEARCH_URL)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            set(payload),
            {"total", "page", "page_size", "has_more", "results"},
        )
        self.assertEqual(payload["total"], 2)
        self.assertEqual(payload["page"], 1)
        self.assertEqual(payload["page_size"], 24)
        self.assertFalse(payload["has_more"])
        self.assertEqual(
            [result["id"] for result in payload["results"]],
            [self.current.pk, self.upcoming.pk],
        )
        current = payload["results"][0]
        self.assertEqual(
            set(current),
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
            },
        )
        self.assertEqual(current["type"], "EXHIBITION")
        self.assertEqual(
            current["institution"],
            {"id": self.primary.pk, "name": self.primary.name},
        )
        self.assertEqual(
            current["region"], {"area": "서울", "district": "종로구"}
        )
        self.assertNotIn("payload", current["source"])
        self.assertNotIn("content_hash", current["source"])
        self.assertEqual(
            current["media"],
            {
                "status": "INLINE",
                "media_url": "https://cdn.example.com/current.jpg",
                "page_url": "https://example.com/current-media",
                "credit_line": "서울 빛 미술관 제공",
            },
        )
        upcoming = payload["results"][1]
        self.assertEqual(
            upcoming["media"],
            {
                "status": "LINK_ONLY",
                "media_url": None,
                "page_url": "https://example.com/upcoming-media",
                "credit_line": None,
            },
        )
        self.assertNotIn("private.example.com", str(upcoming))

    def test_keyword_includes_ended_but_canceled_requires_explicit_filter(self) -> None:
        ended_response = self.client.get(SEARCH_URL, {"q": "기록"})
        default_canceled = self.client.get(SEARCH_URL, {"q": "취소된"})
        explicit_canceled = self.client.get(
            SEARCH_URL,
            {"q": "취소된", "lifecycle": "CANCELED"},
        )

        self.assertEqual(ended_response.status_code, 200)
        ended = ended_response.json()["results"][0]
        self.assertEqual(ended["id"], self.ended.pk)
        self.assertEqual(
            ended["media"],
            {
                "status": "HIDDEN",
                "media_url": None,
                "page_url": None,
                "credit_line": None,
            },
        )
        self.assertNotIn("private.example.com", str(ended))
        self.assertEqual(default_canceled.json()["total"], 0)
        self.assertEqual(
            [result["id"] for result in explicit_canceled.json()["results"]],
            [self.canceled.pk],
        )

    def test_institution_search_returns_region_and_searchable_exhibition_count(self) -> None:
        response = self.client.get(
            SEARCH_URL,
            {
                "q": "소리",
                "type": "INSTITUTION",
                "region_area": "인천",
                "region_district": "중구",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["results"],
            [
                {
                    "type": "INSTITUTION",
                    "id": self.secondary.pk,
                    "name": self.secondary.name,
                    "region": {"area": "인천", "district": "중구"},
                    "searchable_exhibition_count": 1,
                }
            ],
        )

    def test_repeated_lifecycle_and_each_sort_are_supported(self) -> None:
        filtered = self.client.get(
            SEARCH_URL,
            {"lifecycle": ["CURRENT", "ENDED"]},
        )

        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(
            {result["id"] for result in filtered.json()["results"]},
            {self.current.pk, self.ended.pk},
        )

        expected_first = {
            "RELEVANCE": self.current.pk,
            "LATEST_START": self.upcoming.pk,
            "ENDING_SOON": self.current.pk,
            "UPCOMING_START": self.upcoming.pk,
        }
        for sort, exhibition_id in expected_first.items():
            with self.subTest(sort=sort):
                response = self.client.get(SEARCH_URL, {"sort": sort})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["results"][0]["id"], exhibition_id)

    def test_response_reloads_facts_from_canonical_record(self) -> None:
        Exhibition.objects.filter(pk=self.current.pk).update(
            title="정본에서 바뀐 산책"
        )

        response = self.client.get(SEARCH_URL, {"q": "미술관"})

        result = next(
            item for item in response.json()["results"] if item["id"] == self.current.pk
        )
        self.assertEqual(result["title"], "정본에서 바뀐 산책")

    def test_zero_results_are_200_and_invalid_inputs_have_field_details(self) -> None:
        empty = self.client.get(SEARCH_URL, {"q": "존재하지않는검색어"})
        far_page_number = 10**30
        far_page = self.client.get(SEARCH_URL, {"page": far_page_number})

        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.json()["total"], 0)
        self.assertEqual(empty.json()["results"], [])
        self.assertEqual(far_page.status_code, 200)
        self.assertEqual(far_page.json()["page"], far_page_number)
        self.assertEqual(far_page.json()["results"], [])

        invalid_inputs = (
            ({"q": "!!!"}, "q"),
            ({"q": "가" * 101}, "q"),
            ({"type": "ARTWORK"}, "type"),
            ({"lifecycle": "UNKNOWN"}, "lifecycle"),
            ({"sort": "RECOMMENDATION"}, "sort"),
            ({"page": 0}, "page"),
            ({"page_size": 25}, "page_size"),
        )
        for parameters, field in invalid_inputs:
            with self.subTest(parameters=parameters):
                response = self.client.get(SEARCH_URL, parameters)
                self.assertEqual(response.status_code, 400)
                error = response.json()["error"]
                self.assertEqual(error["code"], "INVALID_SEARCH_QUERY")
                self.assertEqual(error["message"], "검색 조건을 확인해주세요.")
                self.assertIn(field, error["details"])

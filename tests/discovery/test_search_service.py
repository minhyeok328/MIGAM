from datetime import date
from importlib import import_module, util

from django.test import TestCase

from backend.apps.catalog.models import (
    Exhibition,
    ExhibitionSourceLink,
    Institution,
)
from backend.apps.sources.models import SourceRecord


class SearchServiceTests(TestCase):
    def setUp(self) -> None:
        self.primary = Institution.objects.create(
            registry_id="institution-light",
            name="서울 빛 미술관",
            region_area="서울",
            region_district="종로구",
        )
        self.secondary = Institution.objects.create(
            registry_id="institution-sound",
            name="인천 소리 전시관",
            region_area="인천",
            region_district="중구",
        )
        self.current = self.create_exhibition(
            institution=self.primary,
            source_record_id="current-light",
            title="빛의 미술관 산책",
            lifecycle=Exhibition.Lifecycle.CURRENT,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 9, 30),
        )
        self.upcoming = self.create_exhibition(
            institution=self.secondary,
            source_record_id="upcoming-sound",
            title="소리로 만나는 도시",
            lifecycle=Exhibition.Lifecycle.UPCOMING,
            start_date=date(2026, 9, 20),
            end_date=date(2026, 10, 20),
        )
        self.ended = self.create_exhibition(
            institution=self.primary,
            source_record_id="ended-light",
            title="빛의 기록 보관소",
            lifecycle=Exhibition.Lifecycle.ENDED,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 2, 1),
        )
        self.canceled = self.create_exhibition(
            institution=self.primary,
            source_record_id="canceled-light",
            title="취소된 빛의 정원",
            lifecycle=Exhibition.Lifecycle.CANCELED,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 15),
        )
        self.create_exhibition(
            institution=self.primary,
            source_record_id="excluded-secret",
            title="노출되면 안 되는 비밀 전시",
            lifecycle=Exhibition.Lifecycle.CURRENT,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 9, 30),
            eligibility=Exhibition.Eligibility.EXCLUDED,
        )
        self.create_exhibition(
            institution=self.primary,
            source_record_id="unverified-secret",
            title="확인되지 않은 비밀 전시",
            lifecycle=Exhibition.Lifecycle.CURRENT,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 9, 30),
            freshness=Exhibition.Freshness.UNVERIFIED,
        )

    def feature(self) -> tuple[object, object, object]:
        self.assertIsNotNone(
            util.find_spec("backend.apps.discovery"),
            "discovery app is missing",
        )
        self.assertIsNotNone(
            util.find_spec("backend.apps.discovery.search"),
            "discovery SearchService is missing",
        )
        self.assertIsNotNone(
            util.find_spec("backend.apps.discovery.projection"),
            "discovery search projection is missing",
        )
        search = import_module("backend.apps.discovery.search")
        projection = import_module("backend.apps.discovery.projection")
        return search, projection, search.get_search_service()

    def rebuild(self) -> tuple[object, object]:
        search, projection, service = self.feature()
        projection.rebuild_search_documents()
        return search, service

    def create_exhibition(
        self,
        *,
        institution: Institution,
        source_record_id: str,
        title: str,
        lifecycle: str,
        start_date: date,
        end_date: date,
        eligibility: str = Exhibition.Eligibility.VERIFIED,
        freshness: str = Exhibition.Freshness.FRESH,
    ) -> Exhibition:
        source_record = SourceRecord.objects.create(
            source_id=f"official-{institution.registry_id}",
            institution_id=institution.registry_id,
            source_record_id=source_record_id,
            source_owner=institution.name,
            payload={"title": title},
            content_hash=(source_record_id[0] * 64),
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
            freshness=freshness,
            eligibility=eligibility,
        )
        ExhibitionSourceLink.objects.create(
            exhibition=exhibition,
            source_id=source_record.source_id,
            source_record_id=source_record.source_record_id,
            latest_source_record=source_record,
        )
        return exhibition

    def test_rebuild_indexes_only_service_eligible_canonical_records(self) -> None:
        search, projection, _ = self.feature()

        summary = projection.rebuild_search_documents()

        models = import_module("backend.apps.discovery.models")
        self.assertEqual(summary.exhibition_count, 4)
        self.assertEqual(summary.institution_count, 2)
        self.assertEqual(models.SearchDocument.objects.count(), 6)
        self.assertFalse(
            models.SearchDocument.objects.filter(title__contains="비밀").exists()
        )
        self.assertEqual(search.SEARCH_DOCUMENT_VERSION, "1.0.0")

    def test_blank_query_defaults_to_current_and_upcoming_exhibitions(self) -> None:
        search, service = self.rebuild()

        page = service.search(search.SearchQuery())

        self.assertEqual(page.total, 2)
        self.assertEqual(
            {hit.object_id for hit in page.results},
            {self.current.pk, self.upcoming.pk},
        )
        self.assertEqual(
            {hit.result_type for hit in page.results},
            {search.SearchResultType.EXHIBITION},
        )

    def test_keyword_uses_korean_prefix_and_searches_ended_records(self) -> None:
        search, service = self.rebuild()

        page = service.search(search.SearchQuery(query="미술"))

        self.assertEqual(page.total, 2)
        self.assertEqual(page.results[0].object_id, self.current.pk)
        self.assertEqual(
            {hit.object_id for hit in page.results},
            {self.current.pk, self.ended.pk},
        )

    def test_all_type_searches_exhibition_and_institution_fields(self) -> None:
        search, service = self.rebuild()

        page = service.search(
            search.SearchQuery(
                query="소리",
                result_type=search.SearchResultType.ALL,
            )
        )

        self.assertEqual(
            {(hit.result_type, hit.object_id) for hit in page.results},
            {
                (search.SearchResultType.EXHIBITION, self.upcoming.pk),
                (search.SearchResultType.INSTITUTION, self.secondary.pk),
            },
        )

    def test_explicit_canceled_filter_is_required_to_find_canceled_record(self) -> None:
        search, service = self.rebuild()

        default_page = service.search(search.SearchQuery(query="취소된"))
        canceled_page = service.search(
            search.SearchQuery(
                query="취소된",
                lifecycles=(Exhibition.Lifecycle.CANCELED,),
            )
        )

        self.assertEqual(default_page.total, 0)
        self.assertEqual(
            [hit.object_id for hit in canceled_page.results],
            [self.canceled.pk],
        )

    def test_region_and_type_filters_do_not_leak_other_results(self) -> None:
        search, service = self.rebuild()

        page = service.search(
            search.SearchQuery(
                query="전시",
                result_type=search.SearchResultType.INSTITUTION,
                region_area="인천",
                region_district="중구",
            )
        )

        self.assertEqual(page.total, 1)
        self.assertEqual(page.results[0].object_id, self.secondary.pk)
        self.assertEqual(page.results[0].result_type, search.SearchResultType.INSTITUTION)

    def test_fts_triggers_keep_updated_documents_searchable(self) -> None:
        search, service = self.rebuild()
        models = import_module("backend.apps.discovery.models")
        document = models.SearchDocument.objects.get(
            result_type=search.SearchResultType.EXHIBITION,
            object_id=self.current.pk,
        )

        document.title = "유리 조각 정원"
        document.subtitle = ""
        document.keywords = "유리 조각 정원"
        document.save(
            update_fields=("title", "subtitle", "keywords", "updated_at")
        )

        self.assertEqual(service.search(search.SearchQuery(query="유리")).total, 1)
        self.assertEqual(service.search(search.SearchQuery(query="미술")).total, 1)

    def test_rebuild_reflects_canonical_changes_and_removes_ineligible_targets(
        self,
    ) -> None:
        search, projection, service = self.feature()
        projection.rebuild_search_documents()
        self.current.title = "유리 정원 산책"
        self.current.venue = "새 전시장"
        self.current.region_district = "중구"
        self.current.save(
            update_fields=("title", "venue", "region_district", "updated_at")
        )
        self.upcoming.eligibility = Exhibition.Eligibility.EXCLUDED
        self.upcoming.save(update_fields=("eligibility", "updated_at"))

        summary = projection.rebuild_search_documents()

        models = import_module("backend.apps.discovery.models")
        document = models.SearchDocument.objects.get(
            result_type=search.SearchResultType.EXHIBITION,
            object_id=self.current.pk,
        )
        self.assertEqual(document.title, "유리 정원 산책")
        self.assertEqual(document.subtitle, self.primary.name)
        self.assertEqual(document.region_district, "중구")
        self.assertIn("새 전시장", document.keywords)
        self.assertFalse(
            models.SearchDocument.objects.filter(
                result_type=search.SearchResultType.EXHIBITION,
                object_id=self.upcoming.pk,
            ).exists()
        )
        self.assertEqual(summary.exhibition_count, 3)
        self.assertEqual(summary.institution_count, 1)
        self.assertEqual(service.search(search.SearchQuery(query="산책")).total, 1)
        self.assertEqual(service.search(search.SearchQuery(query="소리")).total, 0)

    def test_query_operators_are_treated_as_plain_prefix_tokens(self) -> None:
        search, service = self.rebuild()

        page = service.search(search.SearchQuery(query='빛" OR 소리'))

        self.assertEqual(page.total, 0)

    def test_pagination_has_total_has_more_and_no_duplicate_rows(self) -> None:
        for index in range(25):
            self.create_exhibition(
                institution=self.primary,
                source_record_id=f"page-{index:02d}",
                title=f"페이지 전시 {index:02d}",
                lifecycle=Exhibition.Lifecycle.CURRENT,
                start_date=date(2026, 8, 1),
                end_date=date(2026, 12, 31),
            )
        search, service = self.rebuild()

        first = service.search(search.SearchQuery(query="페이지", page_size=24))
        second = service.search(
            search.SearchQuery(query="페이지", page=2, page_size=24)
        )

        self.assertEqual(first.total, 25)
        self.assertTrue(first.has_more)
        self.assertEqual(len(first.results), 24)
        self.assertFalse(second.has_more)
        self.assertEqual(len(second.results), 1)
        self.assertFalse(
            {hit.document_id for hit in first.results}
            & {hit.document_id for hit in second.results}
        )

    def test_invalid_query_tokens_and_pagination_are_rejected(self) -> None:
        search, service = self.rebuild()

        invalid_queries = (
            search.SearchQuery(query="!!!"),
            search.SearchQuery(query="가" * 101),
            search.SearchQuery(page=0),
            search.SearchQuery(page_size=25),
        )
        for query in invalid_queries:
            with self.subTest(query=query):
                with self.assertRaises(search.InvalidSearchQuery):
                    service.search(query)

    def test_page_beyond_sqlite_integer_range_returns_an_empty_page(self) -> None:
        search, service = self.rebuild()
        far_page = 10**30

        page = service.search(search.SearchQuery(page=far_page))

        self.assertEqual(page.total, 2)
        self.assertEqual(page.page, far_page)
        self.assertEqual(page.results, ())
        self.assertFalse(page.has_more)

from datetime import date
from decimal import Decimal
from hashlib import sha256
from importlib import import_module, util

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from backend.apps.catalog.models import (
    AccessibilityFact,
    Exhibition,
    ExhibitionSourceLink,
    Institution,
    PriceOption,
    ReservationInfo,
    SensoryNotice,
    SourceConflict,
    VisitDuration,
)
from backend.apps.sources.models import SourceRecord


class RecommendationServiceTests(TestCase):
    def setUp(self) -> None:
        self.seoul = Institution.objects.create(
            registry_id="recommend-seoul",
            name="서울 추천 미술관",
            region_area="서울",
            region_district="종로구",
        )
        self.incheon = Institution.objects.create(
            registry_id="recommend-incheon",
            name="인천 추천 미술관",
            region_area="인천",
            region_district="중구",
        )
        self.sequence = 0

    def feature(self) -> tuple[object, object]:
        self.assertIsNotNone(
            util.find_spec("backend.apps.discovery.recommendation"),
            "RecommendationService is missing",
        )
        module = import_module("backend.apps.discovery.recommendation")
        return module, module.get_recommendation_service()

    def create_exhibition(
        self,
        title: str,
        *,
        institution: Institution | None = None,
        lifecycle: str = Exhibition.Lifecycle.CURRENT,
        freshness: str = Exhibition.Freshness.FRESH,
        eligibility: str = Exhibition.Eligibility.VERIFIED,
        start_date: date = date(2026, 9, 1),
        end_date: date = date(2026, 9, 30),
        with_source: bool = True,
    ) -> tuple[Exhibition, SourceRecord]:
        self.sequence += 1
        institution = institution or self.seoul
        source_record_id = f"recommend-{self.sequence}"
        source = SourceRecord.objects.create(
            source_id=f"official-{institution.registry_id}",
            institution_id=institution.registry_id,
            source_record_id=source_record_id,
            source_owner=institution.name,
            payload={"title": title},
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
            freshness=freshness,
            eligibility=eligibility,
        )
        if with_source:
            ExhibitionSourceLink.objects.create(
                exhibition=exhibition,
                source_id=source.source_id,
                source_record_id=source.source_record_id,
                latest_source_record=source,
            )
        return exhibition, source

    def ids(self, items: object) -> list[int]:
        return [item.exhibition_id for item in items]

    def add_features(
        self,
        exhibition: Exhibition,
        source: SourceRecord,
        *features_to_add: tuple[str, str],
    ) -> None:
        features = import_module("backend.apps.discovery.features")
        features.record_content_feature_snapshot(
            exhibition=exhibition,
            assertions=tuple(
                features.FeatureAssertionInput(
                    axis=axis,
                    value=value,
                    evidence_kind="DIRECT",
                    source_record=source,
                )
                for axis, value in features_to_add
            ),
        )

    def test_candidate_gate_excludes_unservable_records_before_ranking(self) -> None:
        module, service = self.feature()
        fresh, _ = self.create_exhibition("정상 최신 전시")
        stale, _ = self.create_exhibition(
            "정상 오래된 전시",
            freshness=Exhibition.Freshness.STALE,
        )
        self.create_exhibition("종료 전시", lifecycle=Exhibition.Lifecycle.ENDED)
        self.create_exhibition(
            "취소 전시",
            lifecycle=Exhibition.Lifecycle.CANCELED,
        )
        self.create_exhibition(
            "부분 적격 전시",
            eligibility=Exhibition.Eligibility.PARTIAL,
        )
        self.create_exhibition(
            "검증 불가 전시",
            freshness=Exhibition.Freshness.UNVERIFIED,
        )
        invalid_freshness, _ = self.create_exhibition("잘못된 최신성 전시")
        Exhibition.objects.filter(pk=invalid_freshness.pk).update(
            freshness="BROKEN"
        )
        self.create_exhibition("공식 출처 없는 전시", with_source=False)
        conflicted, conflict_source = self.create_exhibition("충돌 전시")
        SourceConflict.objects.create(
            exhibition=conflicted,
            field_name="end_date",
            canonical_value="2026-09-30",
            candidate_value="2026-10-15",
            candidate_source_record=conflict_source,
        )

        result = service.recommend(module.RecommendationQuery(limit=24))

        self.assertEqual(
            set(self.ids(result.recommendations)),
            {fresh.pk, stale.pk},
        )
        self.assertEqual(result.needs_verification, ())

    def test_region_and_inclusive_date_range_are_hard_filters(self) -> None:
        module, service = self.feature()
        seoul_match, _ = self.create_exhibition(
            "서울 경계일 전시",
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 20),
        )
        self.create_exhibition(
            "서울 기간 밖 전시",
            start_date=date(2026, 9, 21),
            end_date=date(2026, 9, 30),
        )
        self.create_exhibition(
            "인천 같은 기간 전시",
            institution=self.incheon,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
        )

        result = service.recommend(
            module.RecommendationQuery(
                region=module.RegionFilter(area="서울", district="종로구"),
                visit_dates=module.VisitDateRange(
                    start=date(2026, 9, 20),
                    end=date(2026, 9, 20),
                ),
            )
        )

        self.assertEqual(self.ids(result.recommendations), [seoul_match.pk])

    def test_budget_uses_adult_standard_price_and_splits_unknown(self) -> None:
        module, service = self.feature()
        under, under_source = self.create_exhibition("예산 이하")
        equal, equal_source = self.create_exhibition("예산 경계")
        over, over_source = self.create_exhibition("예산 초과")
        unknown, unknown_source = self.create_exhibition("가격 미확인")
        for exhibition, source, amount in (
            (under, under_source, 5000),
            (equal, equal_source, 10000),
            (over, over_source, 15000),
        ):
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
        PriceOption.objects.create(
            exhibition=unknown,
            source_record=unknown_source,
            status=PriceOption.Status.UNKNOWN,
        )

        result = service.recommend(
            module.RecommendationQuery(max_budget_krw=10000, limit=24)
        )

        self.assertEqual(
            set(self.ids(result.recommendations)),
            {under.pk, equal.pk},
        )
        self.assertNotIn(over.pk, self.ids(result.recommendations))
        self.assertEqual(self.ids(result.needs_verification), [unknown.pk])
        self.assertEqual(
            result.needs_verification[0].verification_reasons,
            ("PRICE_UNKNOWN",),
        )

    def test_required_accessibility_accepts_only_confirmed_positive(self) -> None:
        module, service = self.feature()
        supported, supported_source = self.create_exhibition("휠체어 지원")
        unsupported, unsupported_source = self.create_exhibition("휠체어 미지원")
        unknown, unknown_source = self.create_exhibition("휠체어 미확인")
        missing, _ = self.create_exhibition("휠체어 근거 없음")
        for exhibition, source, state in (
            (
                supported,
                supported_source,
                AccessibilityFact.State.CONFIRMED_POSITIVE,
            ),
            (
                unsupported,
                unsupported_source,
                AccessibilityFact.State.CONFIRMED_NEGATIVE,
            ),
            (unknown, unknown_source, AccessibilityFact.State.UNKNOWN),
        ):
            AccessibilityFact.objects.create(
                exhibition=exhibition,
                source_record=source,
                kind=AccessibilityFact.Kind.WHEELCHAIR_ACCESS,
                state=state,
            )

        result = service.recommend(
            module.RecommendationQuery(
                required_accessibility=(
                    AccessibilityFact.Kind.WHEELCHAIR_ACCESS,
                ),
                limit=24,
            )
        )

        self.assertEqual(self.ids(result.recommendations), [supported.pk])
        self.assertFalse(
            {unsupported.pk, unknown.pk, missing.pk}
            & set(self.ids(result.needs_verification))
        )

    def test_avoided_sensory_accepts_only_confirmed_absence(self) -> None:
        module, service = self.feature()
        absent, absent_source = self.create_exhibition("섬광 없음")
        present, present_source = self.create_exhibition("섬광 있음")
        unknown, unknown_source = self.create_exhibition("섬광 미확인")
        for exhibition, source, state in (
            (absent, absent_source, SensoryNotice.State.CONFIRMED_NEGATIVE),
            (present, present_source, SensoryNotice.State.CONFIRMED_POSITIVE),
            (unknown, unknown_source, SensoryNotice.State.UNKNOWN),
        ):
            SensoryNotice.objects.create(
                exhibition=exhibition,
                source_record=source,
                kind=SensoryNotice.Kind.FLASHING_LIGHTS,
                state=state,
            )

        result = service.recommend(
            module.RecommendationQuery(
                avoided_sensory=(SensoryNotice.Kind.FLASHING_LIGHTS,),
                limit=24,
            )
        )

        self.assertEqual(self.ids(result.recommendations), [absent.pk])
        self.assertFalse(
            {present.pk, unknown.pk}
            & set(self.ids(result.needs_verification))
        )

    def test_required_reservation_separates_unknown_from_known_mismatch(self) -> None:
        module, service = self.feature()
        matched, matched_source = self.create_exhibition("예약 일치")
        mismatched, mismatched_source = self.create_exhibition("예약 불일치")
        unknown, unknown_source = self.create_exhibition("예약 미확인")
        ReservationInfo.objects.create(
            exhibition=matched,
            source_record=matched_source,
            reservation_type=ReservationInfo.Type.REQUIRED,
        )
        ReservationInfo.objects.create(
            exhibition=mismatched,
            source_record=mismatched_source,
            reservation_type=ReservationInfo.Type.NOT_REQUIRED,
        )
        ReservationInfo.objects.create(
            exhibition=unknown,
            source_record=unknown_source,
            reservation_type=ReservationInfo.Type.UNKNOWN,
        )

        result = service.recommend(
            module.RecommendationQuery(
                reservation=module.ReservationPreference(
                    mode=module.PreferenceMode.REQUIRED,
                    types=(ReservationInfo.Type.REQUIRED,),
                ),
                limit=24,
            )
        )

        self.assertEqual(self.ids(result.recommendations), [matched.pk])
        self.assertNotIn(mismatched.pk, self.ids(result.needs_verification))
        self.assertEqual(self.ids(result.needs_verification), [unknown.pk])
        self.assertEqual(
            result.needs_verification[0].verification_reasons,
            ("RESERVATION_UNKNOWN",),
        )

    def test_required_duration_requires_confirmed_range_containment(self) -> None:
        module, service = self.feature()
        matched, matched_source = self.create_exhibition("시간 일치")
        too_wide, too_wide_source = self.create_exhibition("시간 초과")
        unknown, unknown_source = self.create_exhibition("시간 미확인")
        VisitDuration.objects.create(
            exhibition=matched,
            source_record=matched_source,
            status=VisitDuration.Status.OFFICIAL,
            minimum_minutes=60,
            maximum_minutes=90,
        )
        VisitDuration.objects.create(
            exhibition=too_wide,
            source_record=too_wide_source,
            status=VisitDuration.Status.OFFICIAL,
            minimum_minutes=30,
            maximum_minutes=120,
        )
        VisitDuration.objects.create(
            exhibition=unknown,
            source_record=unknown_source,
            status=VisitDuration.Status.UNKNOWN,
        )

        result = service.recommend(
            module.RecommendationQuery(
                duration=module.DurationPreference(
                    mode=module.PreferenceMode.REQUIRED,
                    minimum_minutes=60,
                    maximum_minutes=90,
                ),
                limit=24,
            )
        )

        self.assertEqual(self.ids(result.recommendations), [matched.pk])
        self.assertNotIn(too_wide.pk, self.ids(result.needs_verification))
        self.assertEqual(self.ids(result.needs_verification), [unknown.pk])
        self.assertEqual(
            result.needs_verification[0].verification_reasons,
            ("DURATION_UNKNOWN",),
        )

    def test_required_maximum_duration_splits_an_unbounded_official_value(self) -> None:
        module, service = self.feature()
        partial, partial_source = self.create_exhibition("상한 없는 공식 시간")
        VisitDuration.objects.create(
            exhibition=partial,
            source_record=partial_source,
            status=VisitDuration.Status.OFFICIAL,
            minimum_minutes=60,
        )

        result = service.recommend(
            module.RecommendationQuery(
                duration=module.DurationPreference(
                    mode=module.PreferenceMode.REQUIRED,
                    maximum_minutes=90,
                )
            )
        )

        self.assertEqual(result.recommendations, ())
        self.assertEqual(self.ids(result.needs_verification), [partial.pk])
        self.assertEqual(
            result.needs_verification[0].verification_reasons,
            ("DURATION_UNKNOWN",),
        )

    def test_empty_candidate_pool_is_honest(self) -> None:
        module, service = self.feature()
        self.create_exhibition("종료만 있음", lifecycle=Exhibition.Lifecycle.ENDED)

        result = service.recommend(module.RecommendationQuery())

        self.assertEqual(result.recommendations, ())
        self.assertEqual(result.needs_verification, ())
        self.assertEqual(result.candidate_count, 0)

    def test_cold_start_prefers_fresh_data_without_personalized_language(self) -> None:
        module, service = self.feature()
        stale, _ = self.create_exhibition(
            "오래된 일반 추천",
            freshness=Exhibition.Freshness.STALE,
        )
        fresh, _ = self.create_exhibition("최신 일반 추천")

        result = service.recommend(module.RecommendationQuery())

        self.assertEqual(self.ids(result.recommendations), [fresh.pk, stale.pk])
        first = result.recommendations[0]
        self.assertEqual(first.match_level, module.MatchLevel.GENERAL)
        self.assertEqual(first.reasons[0].code, "FRESH_OFFICIAL_INFORMATION")
        self.assertNotIn("취향", first.reasons[0].text)

    def test_explicit_feature_match_contributes_to_rank_level_and_reason(self) -> None:
        module, service = self.feature()
        generic, generic_source = self.create_exhibition("일반 현재 전시")
        matched, matched_source = self.create_exhibition(
            "차분한 예정 전시",
            lifecycle=Exhibition.Lifecycle.UPCOMING,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 10, 10),
        )
        self.add_features(generic, generic_source, ("MOOD", "LIVELY"))
        self.add_features(matched, matched_source, ("MOOD", "CALM"))

        result = service.recommend(
            module.RecommendationQuery(
                preferred_features=(
                    module.FeaturePreference(axis="MOOD", value="CALM"),
                ),
            )
        )

        first = result.recommendations[0]
        self.assertEqual(first.exhibition_id, matched.pk)
        self.assertEqual(first.match_level, module.MatchLevel.GOOD_MATCH)
        self.assertEqual(first.reasons[0].code, "PREFERRED_FEATURE")
        self.assertEqual(
            first.reasons[0].feature,
            module.FeaturePreference(axis="MOOD", value="CALM"),
        )

    def test_ended_liked_exhibition_transfers_features_but_is_not_a_candidate(self) -> None:
        module, service = self.feature()
        liked, liked_source = self.create_exhibition(
            "관심 종료 전시",
            lifecycle=Exhibition.Lifecycle.ENDED,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 2, 1),
        )
        connected, connected_source = self.create_exhibition("연결된 현재 전시")
        other, other_source = self.create_exhibition("다른 현재 전시")
        self.add_features(
            liked,
            liked_source,
            ("MEDIA_GROUP", "SOUND_PERFORMANCE"),
        )
        self.add_features(
            connected,
            connected_source,
            ("MEDIA_GROUP", "SOUND_PERFORMANCE"),
        )
        self.add_features(other, other_source, ("MEDIA_GROUP", "PHOTOGRAPHY"))

        result = service.recommend(
            module.RecommendationQuery(liked_exhibition_ids=(liked.pk,))
        )

        self.assertEqual(result.recommendations[0].exhibition_id, connected.pk)
        self.assertNotIn(liked.pk, self.ids(result.recommendations))
        self.assertEqual(
            result.recommendations[0].reasons[0].code,
            "LIKED_EXHIBITION_FEATURE",
        )

    def test_ineligible_liked_exhibition_does_not_contribute_features(self) -> None:
        module, service = self.feature()
        liked, liked_source = self.create_exhibition(
            "부적격 관심 종료 전시",
            lifecycle=Exhibition.Lifecycle.ENDED,
            eligibility=Exhibition.Eligibility.EXCLUDED,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 2, 1),
        )
        connected, connected_source = self.create_exhibition("겉보기 연결 전시")
        self.add_features(liked, liked_source, ("MOOD", "CALM"))
        self.add_features(connected, connected_source, ("MOOD", "CALM"))

        result = service.recommend(
            module.RecommendationQuery(liked_exhibition_ids=(liked.pk,))
        )

        self.assertEqual(result.recommendations[0].exhibition_id, connected.pk)
        self.assertEqual(
            result.recommendations[0].match_level,
            module.MatchLevel.GENERAL,
        )
        self.assertNotEqual(
            result.recommendations[0].reasons[0].code,
            "LIKED_EXHIBITION_FEATURE",
        )

    def test_liked_institution_is_a_weak_positive_signal(self) -> None:
        module, service = self.feature()
        other, _ = self.create_exhibition("먼저 생성된 다른 기관 전시")
        liked, _ = self.create_exhibition(
            "관심 기관 전시",
            institution=self.incheon,
        )

        result = service.recommend(
            module.RecommendationQuery(
                liked_institution_ids=(self.incheon.pk,),
            )
        )

        self.assertEqual(result.recommendations[0].exhibition_id, liked.pk)
        self.assertEqual(
            result.recommendations[0].reasons[0].code,
            "LIKED_INSTITUTION",
        )
        self.assertIn(other.pk, self.ids(result.recommendations))

    def test_preferred_visit_information_scores_matches_and_keeps_unknown_neutral(
        self,
    ) -> None:
        module, service = self.feature()
        matched, matched_source = self.create_exhibition("선호 방문정보 일치")
        mismatched, mismatched_source = self.create_exhibition("선호 방문정보 불일치")
        unknown, unknown_source = self.create_exhibition("선호 방문정보 미확인")
        ReservationInfo.objects.create(
            exhibition=matched,
            source_record=matched_source,
            reservation_type=ReservationInfo.Type.REQUIRED,
        )
        VisitDuration.objects.create(
            exhibition=matched,
            source_record=matched_source,
            status=VisitDuration.Status.OFFICIAL,
            minimum_minutes=60,
            maximum_minutes=90,
        )
        ReservationInfo.objects.create(
            exhibition=mismatched,
            source_record=mismatched_source,
            reservation_type=ReservationInfo.Type.NOT_REQUIRED,
        )
        VisitDuration.objects.create(
            exhibition=mismatched,
            source_record=mismatched_source,
            status=VisitDuration.Status.OFFICIAL,
            minimum_minutes=120,
            maximum_minutes=150,
        )
        ReservationInfo.objects.create(
            exhibition=unknown,
            source_record=unknown_source,
            reservation_type=ReservationInfo.Type.UNKNOWN,
        )
        VisitDuration.objects.create(
            exhibition=unknown,
            source_record=unknown_source,
            status=VisitDuration.Status.UNKNOWN,
        )

        result = service.recommend(
            module.RecommendationQuery(
                reservation=module.ReservationPreference(
                    mode=module.PreferenceMode.PREFERRED,
                    types=(ReservationInfo.Type.REQUIRED,),
                ),
                duration=module.DurationPreference(
                    mode=module.PreferenceMode.PREFERRED,
                    minimum_minutes=60,
                    maximum_minutes=90,
                ),
            )
        )

        self.assertEqual(result.recommendations[0].exhibition_id, matched.pk)
        self.assertEqual(
            [reason.code for reason in result.recommendations[0].reasons],
            ["PREFERRED_DURATION", "PREFERRED_RESERVATION"],
        )
        self.assertEqual(set(self.ids(result.recommendations)), {matched.pk, mismatched.pk, unknown.pk})
        unknown_hit = next(
            hit for hit in result.recommendations if hit.exhibition_id == unknown.pk
        )
        self.assertEqual(unknown_hit.match_level, module.MatchLevel.GENERAL)
        self.assertNotIn(
            "PREFERRED_RESERVATION",
            [reason.code for reason in unknown_hit.reasons],
        )

    def test_same_request_is_reproducible_and_public_hits_have_no_score(self) -> None:
        module, service = self.feature()
        for index in range(4):
            self.create_exhibition(f"동점 전시 {index}")
        query = module.RecommendationQuery(limit=4)

        first = service.recommend(query)
        second = service.recommend(query)

        self.assertEqual(first, second)
        self.assertEqual(first.algorithm_version, "p0-recommendation-1.0.0")
        self.assertEqual(
            self.ids(first.recommendations),
            sorted(self.ids(first.recommendations)),
        )
        self.assertTrue(
            all(not hasattr(hit, "score") for hit in first.recommendations)
        )

    def test_diversity_reduces_same_institution_concentration(self) -> None:
        module, service = self.feature()
        created: list[Exhibition] = []
        for index in range(6):
            exhibition, source = self.create_exhibition(f"서울 반복 {index}")
            self.add_features(
                exhibition,
                source,
                ("MEDIA_GROUP", "MOVING_IMAGE_DIGITAL"),
            )
            created.append(exhibition)
        alternatives: list[Exhibition] = []
        for index in range(2):
            exhibition, source = self.create_exhibition(
                f"인천 대안 {index}",
                institution=self.incheon,
            )
            self.add_features(
                exhibition,
                source,
                ("MEDIA_GROUP", "PHOTOGRAPHY"),
            )
            alternatives.append(exhibition)

        result = service.recommend(module.RecommendationQuery(limit=6))

        selected_ids = set(self.ids(result.recommendations))
        self.assertTrue(selected_ids & {item.pk for item in alternatives})
        selected_institutions = {
            Exhibition.objects.get(pk=exhibition_id).institution_id
            for exhibition_id in selected_ids
        }
        self.assertEqual(selected_institutions, {self.seoul.pk, self.incheon.pk})

    def test_six_item_result_can_reserve_one_connected_exploration_slot(self) -> None:
        module, service = self.feature()
        for index in range(6):
            exhibition, source = self.create_exhibition(f"익숙한 전시 {index}")
            self.add_features(exhibition, source, ("MOOD", "CALM"))
        exploration, exploration_source = self.create_exhibition(
            "연결된 탐색 전시",
            lifecycle=Exhibition.Lifecycle.UPCOMING,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 10, 10),
        )
        self.add_features(
            exploration,
            exploration_source,
            ("MOOD", "CALM"),
            ("MEDIA_GROUP", "SOUND_PERFORMANCE"),
        )

        result = service.recommend(
            module.RecommendationQuery(
                preferred_features=(
                    module.FeaturePreference(axis="MOOD", value="CALM"),
                ),
                limit=6,
            )
        )

        exploration_hits = [
            hit for hit in result.recommendations if hit.is_exploration
        ]
        self.assertEqual(len(exploration_hits), 1)
        self.assertEqual(exploration_hits[0].exhibition_id, exploration.pk)
        self.assertEqual(exploration_hits[0].match_level, module.MatchLevel.EXPLORATION)
        self.assertEqual(
            {reason.code for reason in exploration_hits[0].reasons},
            {"EXPLORATION_CONNECTION", "EXPLORATION_NOVELTY"},
        )
        self.assertEqual(len(set(self.ids(result.recommendations))), 6)

    def test_exploration_is_not_fabricated_without_a_connected_feature(self) -> None:
        module, service = self.feature()
        for index in range(7):
            exhibition, source = self.create_exhibition(f"연결 없음 {index}")
            self.add_features(
                exhibition,
                source,
                ("MEDIA_GROUP", "PHOTOGRAPHY"),
            )

        result = service.recommend(
            module.RecommendationQuery(
                preferred_features=(
                    module.FeaturePreference(axis="MOOD", value="CALM"),
                ),
                limit=6,
            )
        )

        self.assertFalse(any(hit.is_exploration for hit in result.recommendations))
        self.assertTrue(
            all(len(hit.reasons) <= 3 for hit in result.recommendations)
        )

    def test_visit_evidence_queries_are_bounded_for_many_candidates(self) -> None:
        module, service = self.feature()
        for index in range(12):
            exhibition, source = self.create_exhibition(f"쿼리 후보 {index}")
            AccessibilityFact.objects.create(
                exhibition=exhibition,
                source_record=source,
                kind=AccessibilityFact.Kind.WHEELCHAIR_ACCESS,
                state=AccessibilityFact.State.CONFIRMED_POSITIVE,
            )
            SensoryNotice.objects.create(
                exhibition=exhibition,
                source_record=source,
                kind=SensoryNotice.Kind.FLASHING_LIGHTS,
                state=SensoryNotice.State.CONFIRMED_NEGATIVE,
            )

        with CaptureQueriesContext(connection) as captured:
            result = service.recommend(
                module.RecommendationQuery(
                    required_accessibility=(
                        AccessibilityFact.Kind.WHEELCHAIR_ACCESS,
                    ),
                    avoided_sensory=(SensoryNotice.Kind.FLASHING_LIGHTS,),
                    limit=12,
                )
            )

        self.assertEqual(len(result.recommendations), 12)
        self.assertLessEqual(len(captured.captured_queries), 15)

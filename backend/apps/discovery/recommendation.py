from dataclasses import dataclass
from datetime import date
from enum import StrEnum
import re
from typing import Protocol

from django.db.models import Prefetch

from backend.apps.catalog.models import (
    AccessibilityFact,
    Exhibition,
    ExhibitionSourceLink,
    PriceOption,
    ReservationInfo,
    SensoryNotice,
    SourceConflict,
    VisitDuration,
)
from backend.apps.discovery.visit_conditions import (
    EvidenceState,
    ResolvedDuration,
    ResolvedVisitEvidence,
    VisitEvidenceResolver,
)
from backend.apps.discovery.models import ContentFeatureAssertion


ALGORITHM_VERSION = "p0-recommendation-1.0.0"
DEFAULT_LIMIT = 6
MAX_LIMIT = 24
MAX_SIGNAL_ITEMS = 100
_FEATURE_VALUE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_:-]{0,63}$")
PREFERRED_FEATURE_WEIGHT = 24
LIKED_EXHIBITION_FEATURE_WEIGHT = 10
LIKED_INSTITUTION_WEIGHT = 6
PREFERRED_VISIT_INFORMATION_WEIGHT = 5
INSTITUTION_REPEAT_PENALTY = 7
PRIMARY_MEDIA_REPEAT_PENALTY = 4


class InvalidRecommendationRequest(ValueError):
    pass


class PreferenceMode(StrEnum):
    REQUIRED = "REQUIRED"
    PREFERRED = "PREFERRED"


class MatchLevel(StrEnum):
    VERY_CLOSE = "VERY_CLOSE"
    GOOD_MATCH = "GOOD_MATCH"
    SOME_MATCH = "SOME_MATCH"
    GENERAL = "GENERAL"
    EXPLORATION = "EXPLORATION"


@dataclass(frozen=True, slots=True)
class RegionFilter:
    area: str
    district: str = ""


@dataclass(frozen=True, slots=True)
class VisitDateRange:
    start: date
    end: date


@dataclass(frozen=True, slots=True)
class ReservationPreference:
    mode: PreferenceMode | str
    types: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DurationPreference:
    mode: PreferenceMode | str
    minimum_minutes: int | None = None
    maximum_minutes: int | None = None


@dataclass(frozen=True, slots=True)
class FeaturePreference:
    axis: str
    value: str


@dataclass(frozen=True, slots=True)
class RecommendationQuery:
    region: RegionFilter | None = None
    visit_dates: VisitDateRange | None = None
    max_budget_krw: int | None = None
    required_accessibility: tuple[str, ...] = ()
    avoided_sensory: tuple[str, ...] = ()
    reservation: ReservationPreference | None = None
    duration: DurationPreference | None = None
    preferred_features: tuple[FeaturePreference, ...] = ()
    liked_exhibition_ids: tuple[int, ...] = ()
    liked_institution_ids: tuple[int, ...] = ()
    limit: int = DEFAULT_LIMIT


@dataclass(frozen=True, slots=True)
class RecommendationReason:
    code: str
    text: str
    feature: FeaturePreference | None = None


@dataclass(frozen=True, slots=True)
class RecommendationHit:
    exhibition_id: int
    match_level: MatchLevel
    is_exploration: bool
    reasons: tuple[RecommendationReason, ...]


@dataclass(frozen=True, slots=True)
class VerificationCandidate:
    exhibition_id: int
    verification_reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RecommendationResult:
    algorithm_version: str
    candidate_count: int
    recommendations: tuple[RecommendationHit, ...]
    needs_verification: tuple[VerificationCandidate, ...]


class RecommendationService(Protocol):
    def recommend(self, query: RecommendationQuery) -> RecommendationResult: ...


@dataclass(frozen=True, slots=True)
class _RankedCandidate:
    exhibition: Exhibition
    score: int
    personal_score: int
    features: frozenset[FeaturePreference]
    contributions: tuple["_Contribution", ...]


@dataclass(frozen=True, slots=True)
class _Contribution:
    code: str
    weight: int
    text: str
    feature: FeaturePreference | None = None


class ORMRecommendationService:
    def __init__(self, evidence_resolver: VisitEvidenceResolver | None = None) -> None:
        self.evidence_resolver = evidence_resolver or VisitEvidenceResolver()

    def recommend(self, query: RecommendationQuery) -> RecommendationResult:
        validated = _validate_query(query)
        candidates = list(
            Exhibition.objects.filter(
                lifecycle__in=(
                    Exhibition.Lifecycle.CURRENT,
                    Exhibition.Lifecycle.UPCOMING,
                ),
                eligibility=Exhibition.Eligibility.VERIFIED,
                freshness__in=(
                    Exhibition.Freshness.FRESH,
                    Exhibition.Freshness.STALE,
                ),
                source_links__latest_source_record__isnull=False,
            )
            .exclude(source_conflicts__status=SourceConflict.Status.OPEN)
            .select_related("institution")
            .prefetch_related(*_visit_evidence_prefetches())
            .distinct()
        )

        candidate_features = _features_for_exhibitions(
            exhibition_ids=tuple(exhibition.pk for exhibition in candidates)
        )
        liked_features = _features_for_liked_exhibitions(
            validated.liked_exhibition_ids
        )
        preferred_features = frozenset(validated.preferred_features)
        connection_features = preferred_features | liked_features

        ranked: list[_RankedCandidate] = []
        verification: list[VerificationCandidate] = []
        for exhibition in candidates:
            if not _matches_region_and_dates(exhibition, validated):
                continue
            evidence = self.evidence_resolver.resolve(exhibition)
            excluded, verification_reasons = _apply_hard_conditions(
                evidence,
                validated,
            )
            if excluded:
                continue
            if verification_reasons:
                verification.append(
                    VerificationCandidate(
                        exhibition_id=exhibition.pk,
                        verification_reasons=verification_reasons,
                    )
                )
                continue
            features = candidate_features.get(exhibition.pk, frozenset())
            contributions = _score_contributions(
                exhibition=exhibition,
                evidence=evidence,
                features=features,
                query=validated,
                preferred_features=preferred_features,
                liked_features=liked_features,
            )
            personal_score = sum(item.weight for item in contributions)
            ranked.append(
                _RankedCandidate(
                    exhibition=exhibition,
                    score=(
                        _base_score(exhibition, evidence, features)
                        + personal_score
                    ),
                    personal_score=personal_score,
                    features=features,
                    contributions=contributions,
                )
            )

        ranked.sort(key=_rank_key)
        verification.sort(key=lambda item: item.exhibition_id)
        selected = _diverse_select(ranked, validated.limit)
        selected, exploration_id = _apply_exploration(
            selected=selected,
            all_ranked=ranked,
            connection_features=connection_features,
            limit=validated.limit,
        )
        recommendations = tuple(
            _to_hit(item, is_exploration=item.exhibition.pk == exploration_id)
            for item in selected
        )
        return RecommendationResult(
            algorithm_version=ALGORITHM_VERSION,
            candidate_count=len(ranked) + len(verification),
            recommendations=recommendations,
            needs_verification=tuple(verification[: validated.limit]),
        )


def get_recommendation_service() -> RecommendationService:
    return ORMRecommendationService()


def _visit_evidence_prefetches() -> tuple[Prefetch, ...]:
    prefetches: list[Prefetch] = [
        Prefetch(
            "source_links",
            queryset=ExhibitionSourceLink.objects.select_related(
                "latest_source_record"
            ),
            to_attr="recommendation_source_links",
        )
    ]
    for related_name, model in (
        ("priceoption_records", PriceOption),
        ("reservationinfo_records", ReservationInfo),
        ("visitduration_records", VisitDuration),
        ("accessibilityfact_records", AccessibilityFact),
        ("sensorynotice_records", SensoryNotice),
    ):
        queryset = model.objects.select_related("source_record")
        prefetches.append(
            Prefetch(
                related_name,
                queryset=queryset,
                to_attr=f"recommendation_{related_name}",
            )
        )
        prefetches.append(
            Prefetch(
                f"institution__{related_name}",
                queryset=queryset,
                to_attr=f"recommendation_{related_name}",
            )
        )
    return tuple(prefetches)


def _validate_query(query: RecommendationQuery) -> RecommendationQuery:
    if isinstance(query.limit, bool) or not isinstance(query.limit, int):
        raise InvalidRecommendationRequest("limit must be an integer")
    if not 1 <= query.limit <= MAX_LIMIT:
        raise InvalidRecommendationRequest(f"limit must be between 1 and {MAX_LIMIT}")
    if query.region is not None:
        if not isinstance(query.region.area, str) or not query.region.area.strip():
            raise InvalidRecommendationRequest("region.area is required")
        if not isinstance(query.region.district, str):
            raise InvalidRecommendationRequest("region.district must be a string")
    if query.visit_dates is not None and query.visit_dates.start > query.visit_dates.end:
        raise InvalidRecommendationRequest("visit_dates start must not exceed end")
    if query.max_budget_krw is not None and (
        isinstance(query.max_budget_krw, bool)
        or not isinstance(query.max_budget_krw, int)
        or query.max_budget_krw < 0
    ):
        raise InvalidRecommendationRequest(
            "max_budget_krw must be a non-negative integer"
        )

    _validate_unique_enum_items(
        "required_accessibility",
        query.required_accessibility,
        set(AccessibilityFact.Kind.values),
    )
    _validate_unique_enum_items(
        "avoided_sensory",
        query.avoided_sensory,
        set(SensoryNotice.Kind.values),
    )
    _validate_positive_ids("liked_exhibition_ids", query.liked_exhibition_ids)
    _validate_positive_ids("liked_institution_ids", query.liked_institution_ids)

    if query.reservation is not None:
        try:
            PreferenceMode(query.reservation.mode)
        except (TypeError, ValueError) as error:
            raise InvalidRecommendationRequest("reservation mode is invalid") from error
        allowed_types = set(ReservationInfo.Type.values) - {
            ReservationInfo.Type.UNKNOWN
        }
        _validate_unique_enum_items(
            "reservation.types",
            query.reservation.types,
            allowed_types,
            require_items=True,
        )

    if query.duration is not None:
        try:
            PreferenceMode(query.duration.mode)
        except (TypeError, ValueError) as error:
            raise InvalidRecommendationRequest("duration mode is invalid") from error
        minimum = query.duration.minimum_minutes
        maximum = query.duration.maximum_minutes
        if minimum is None and maximum is None:
            raise InvalidRecommendationRequest("duration requires a bound")
        for name, value in (("minimum_minutes", minimum), ("maximum_minutes", maximum)):
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
            ):
                raise InvalidRecommendationRequest(
                    f"duration {name} must be a positive integer"
                )
        if minimum is not None and maximum is not None and minimum > maximum:
            raise InvalidRecommendationRequest(
                "duration minimum_minutes must not exceed maximum_minutes"
            )

    feature_keys: list[tuple[str, str]] = []
    allowed_axes = set(ContentFeatureAssertion.Axis.values)
    for feature in query.preferred_features:
        if feature.axis not in allowed_axes:
            raise InvalidRecommendationRequest("preferred_features axis is invalid")
        if not isinstance(feature.value, str) or not _FEATURE_VALUE_PATTERN.fullmatch(
            feature.value
        ):
            raise InvalidRecommendationRequest("preferred_features value is invalid")
        feature_keys.append((feature.axis, feature.value))
    if len(feature_keys) > MAX_SIGNAL_ITEMS:
        raise InvalidRecommendationRequest("preferred_features has too many items")
    if len(feature_keys) != len(set(feature_keys)):
        raise InvalidRecommendationRequest("preferred_features contains duplicates")
    return query


def _validate_unique_enum_items(
    field: str,
    items: tuple[str, ...],
    allowed: set[str],
    *,
    require_items: bool = False,
) -> None:
    if require_items and not items:
        raise InvalidRecommendationRequest(f"{field} requires at least one item")
    if len(items) > MAX_SIGNAL_ITEMS:
        raise InvalidRecommendationRequest(f"{field} has too many items")
    if len(items) != len(set(items)):
        raise InvalidRecommendationRequest(f"{field} contains duplicates")
    if any(item not in allowed for item in items):
        raise InvalidRecommendationRequest(f"{field} contains an invalid value")


def _validate_positive_ids(field: str, items: tuple[int, ...]) -> None:
    if len(items) > MAX_SIGNAL_ITEMS:
        raise InvalidRecommendationRequest(f"{field} has too many items")
    if len(items) != len(set(items)):
        raise InvalidRecommendationRequest(f"{field} contains duplicates")
    if any(isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in items):
        raise InvalidRecommendationRequest(f"{field} must contain positive integers")


def _matches_region_and_dates(
    exhibition: Exhibition,
    query: RecommendationQuery,
) -> bool:
    if query.region is not None:
        if exhibition.region_area != query.region.area.strip():
            return False
        district = query.region.district.strip()
        if district and exhibition.region_district != district:
            return False
    if query.visit_dates is not None:
        if exhibition.start_date > query.visit_dates.end:
            return False
        if exhibition.end_date < query.visit_dates.start:
            return False
    return True


def _apply_hard_conditions(
    evidence: ResolvedVisitEvidence,
    query: RecommendationQuery,
) -> tuple[bool, tuple[str, ...]]:
    verification_reasons: list[str] = []

    for kind in query.required_accessibility:
        fact = evidence.accessibility[kind]
        if fact.state != EvidenceState.CONFIRMED or fact.value != (
            AccessibilityFact.State.CONFIRMED_POSITIVE
        ):
            return True, ()

    for kind in query.avoided_sensory:
        fact = evidence.sensory[kind]
        if fact.state != EvidenceState.CONFIRMED or fact.value != (
            SensoryNotice.State.CONFIRMED_NEGATIVE
        ):
            return True, ()

    if query.max_budget_krw is not None:
        if (
            evidence.price.state != EvidenceState.CONFIRMED
            or evidence.price.amount is None
            or (not evidence.price.is_free and evidence.price.currency != "KRW")
        ):
            verification_reasons.append("PRICE_UNKNOWN")
        elif evidence.price.amount > query.max_budget_krw:
            return True, ()

    if query.reservation is not None and (
        PreferenceMode(query.reservation.mode) == PreferenceMode.REQUIRED
    ):
        if (
            evidence.reservation.state != EvidenceState.CONFIRMED
            or evidence.reservation.reservation_type is None
        ):
            verification_reasons.append("RESERVATION_UNKNOWN")
        elif evidence.reservation.reservation_type not in query.reservation.types:
            return True, ()

    if query.duration is not None and (
        PreferenceMode(query.duration.mode) == PreferenceMode.REQUIRED
    ):
        if (
            evidence.duration.state != EvidenceState.CONFIRMED
            or not _duration_is_decidable(evidence.duration, query.duration)
        ):
            verification_reasons.append("DURATION_UNKNOWN")
        elif not _duration_within(evidence.duration, query.duration):
            return True, ()

    return False, tuple(verification_reasons)


def _duration_within(
    resolved: ResolvedDuration,
    requested: DurationPreference,
) -> bool:
    if resolved.minimum_minutes is None:
        return False
    if (
        requested.minimum_minutes is not None
        and resolved.minimum_minutes < requested.minimum_minutes
    ):
        return False
    if requested.maximum_minutes is not None:
        if resolved.maximum_minutes is None:
            return False
        if resolved.maximum_minutes > requested.maximum_minutes:
            return False
    return True


def _duration_is_decidable(
    resolved: ResolvedDuration,
    requested: DurationPreference,
) -> bool:
    if resolved.minimum_minutes is None:
        return False
    return not (
        requested.maximum_minutes is not None
        and resolved.maximum_minutes is None
    )


def _features_for_exhibitions(
    *,
    exhibition_ids: tuple[int, ...],
) -> dict[int, frozenset[FeaturePreference]]:
    features: dict[int, set[FeaturePreference]] = {
        exhibition_id: set() for exhibition_id in exhibition_ids
    }
    rows = ContentFeatureAssertion.objects.filter(
        snapshot__is_current=True,
        snapshot__exhibition_id__in=exhibition_ids,
    ).values_list("snapshot__exhibition_id", "axis", "value")
    for exhibition_id, axis, value in rows:
        features.setdefault(exhibition_id, set()).add(
            FeaturePreference(axis=axis, value=value)
        )
    return {
        exhibition_id: frozenset(values)
        for exhibition_id, values in features.items()
    }


def _features_for_liked_exhibitions(
    exhibition_ids: tuple[int, ...],
) -> frozenset[FeaturePreference]:
    if not exhibition_ids:
        return frozenset()
    rows = (
        ContentFeatureAssertion.objects.filter(
            snapshot__is_current=True,
            snapshot__exhibition_id__in=exhibition_ids,
            snapshot__exhibition__eligibility=Exhibition.Eligibility.VERIFIED,
            snapshot__exhibition__freshness__in=(
                Exhibition.Freshness.FRESH,
                Exhibition.Freshness.STALE,
            ),
            snapshot__exhibition__source_links__latest_source_record__isnull=False,
        )
        .exclude(
            snapshot__exhibition__source_conflicts__status=SourceConflict.Status.OPEN
        )
        .values_list("axis", "value")
        .distinct()
    )
    return frozenset(
        FeaturePreference(axis=axis, value=value)
        for axis, value in rows
    )


def _score_contributions(
    *,
    exhibition: Exhibition,
    evidence: ResolvedVisitEvidence,
    features: frozenset[FeaturePreference],
    query: RecommendationQuery,
    preferred_features: frozenset[FeaturePreference],
    liked_features: frozenset[FeaturePreference],
) -> tuple[_Contribution, ...]:
    contributions: list[_Contribution] = []
    for feature in sorted(
        features & preferred_features,
        key=lambda item: (item.axis, item.value),
    ):
        contributions.append(
            _Contribution(
                code="PREFERRED_FEATURE",
                weight=PREFERRED_FEATURE_WEIGHT,
                text="선호한 콘텐츠 특성과 연결돼요.",
                feature=feature,
            )
        )
    for feature in sorted(
        features & liked_features,
        key=lambda item: (item.axis, item.value),
    ):
        contributions.append(
            _Contribution(
                code="LIKED_EXHIBITION_FEATURE",
                weight=LIKED_EXHIBITION_FEATURE_WEIGHT,
                text="관심 있게 본 전시와 확인된 특성이 이어져요.",
                feature=feature,
            )
        )
    if exhibition.institution_id in query.liked_institution_ids:
        contributions.append(
            _Contribution(
                code="LIKED_INSTITUTION",
                weight=LIKED_INSTITUTION_WEIGHT,
                text="관심 있는 기관의 현재·예정 전시예요.",
            )
        )
    if query.reservation is not None and (
        PreferenceMode(query.reservation.mode) == PreferenceMode.PREFERRED
        and evidence.reservation.state == EvidenceState.CONFIRMED
        and evidence.reservation.reservation_type in query.reservation.types
    ):
        contributions.append(
            _Contribution(
                code="PREFERRED_RESERVATION",
                weight=PREFERRED_VISIT_INFORMATION_WEIGHT,
                text="선호한 예약 방식과 일치해요.",
            )
        )
    if query.duration is not None and (
        PreferenceMode(query.duration.mode) == PreferenceMode.PREFERRED
        and evidence.duration.state == EvidenceState.CONFIRMED
        and _duration_within(evidence.duration, query.duration)
    ):
        contributions.append(
            _Contribution(
                code="PREFERRED_DURATION",
                weight=PREFERRED_VISIT_INFORMATION_WEIGHT,
                text="선호한 예상 관람시간 범위와 일치해요.",
            )
        )
    return tuple(
        sorted(
            contributions,
            key=lambda item: (
                -item.weight,
                item.code,
                item.feature.axis if item.feature else "",
                item.feature.value if item.feature else "",
            ),
        )
    )


def _base_score(
    exhibition: Exhibition,
    evidence: ResolvedVisitEvidence,
    features: frozenset[FeaturePreference],
) -> int:
    lifecycle_score = (
        40 if exhibition.lifecycle == Exhibition.Lifecycle.CURRENT else 30
    )
    freshness_score = 10 if exhibition.freshness == Exhibition.Freshness.FRESH else 0
    known_visit_information = sum(
        item.state == EvidenceState.CONFIRMED
        for item in (evidence.price, evidence.reservation, evidence.duration)
    )
    feature_completeness = min(len(features), 3)
    return (
        lifecycle_score
        + freshness_score
        + known_visit_information
        + feature_completeness
    )


def _rank_key(candidate: _RankedCandidate) -> tuple[object, ...]:
    exhibition = candidate.exhibition
    lifecycle_order = (
        0 if exhibition.lifecycle == Exhibition.Lifecycle.CURRENT else 1
    )
    date_order = (
        exhibition.end_date
        if exhibition.lifecycle == Exhibition.Lifecycle.CURRENT
        else exhibition.start_date
    )
    return -candidate.score, lifecycle_order, date_order, exhibition.pk


def _diverse_select(
    ranked: list[_RankedCandidate],
    limit: int,
) -> list[_RankedCandidate]:
    remaining = list(ranked)
    selected: list[_RankedCandidate] = []
    institution_counts: dict[int, int] = {}
    media_counts: dict[tuple[str, str], int] = {}
    while remaining and len(selected) < limit:
        def selection_key(candidate: _RankedCandidate) -> tuple[object, ...]:
            institution_penalty = (
                institution_counts.get(candidate.exhibition.institution_id, 0)
                * INSTITUTION_REPEAT_PENALTY
            )
            primary_media = _primary_media(candidate.features)
            media_penalty = (
                media_counts.get(primary_media, 0) * PRIMARY_MEDIA_REPEAT_PENALTY
                if primary_media is not None
                else 0
            )
            adjusted_score = candidate.score - institution_penalty - media_penalty
            return (-adjusted_score, *_rank_key(candidate))

        chosen = min(remaining, key=selection_key)
        remaining.remove(chosen)
        selected.append(chosen)
        institution_id = chosen.exhibition.institution_id
        institution_counts[institution_id] = institution_counts.get(institution_id, 0) + 1
        primary_media = _primary_media(chosen.features)
        if primary_media is not None:
            media_counts[primary_media] = media_counts.get(primary_media, 0) + 1
    return selected


def _primary_media(
    features: frozenset[FeaturePreference],
) -> tuple[str, str] | None:
    for axis in (
        ContentFeatureAssertion.Axis.MEDIA_DETAIL,
        ContentFeatureAssertion.Axis.MEDIA_GROUP,
    ):
        values = sorted(
            feature.value for feature in features if feature.axis == axis
        )
        if values:
            return axis, values[0]
    return None


def _apply_exploration(
    *,
    selected: list[_RankedCandidate],
    all_ranked: list[_RankedCandidate],
    connection_features: frozenset[FeaturePreference],
    limit: int,
) -> tuple[list[_RankedCandidate], int | None]:
    if limit < 6 or len(selected) < 6 or not connection_features:
        return selected, None
    protected_ids = {item.exhibition.pk for item in selected[:5]}
    exploration_candidates = [
        item
        for item in all_ranked
        if item.exhibition.pk not in protected_ids
        and item.features & connection_features
        and item.features - connection_features
    ]
    if not exploration_candidates:
        return selected, None
    chosen = min(exploration_candidates, key=_rank_key)
    reordered = [
        item for item in selected if item.exhibition.pk != chosen.exhibition.pk
    ]
    reordered.insert(5, chosen)
    return reordered[:limit], chosen.exhibition.pk


def _to_hit(
    candidate: _RankedCandidate,
    *,
    is_exploration: bool,
) -> RecommendationHit:
    if is_exploration:
        return RecommendationHit(
            exhibition_id=candidate.exhibition.pk,
            match_level=MatchLevel.EXPLORATION,
            is_exploration=True,
            reasons=_exploration_reasons(candidate),
        )
    reasons = tuple(
        RecommendationReason(
            code=item.code,
            text=item.text,
            feature=item.feature,
        )
        for item in candidate.contributions[:3]
    )
    if not reasons:
        reasons = (_general_reason(candidate.exhibition),)
    return RecommendationHit(
        exhibition_id=candidate.exhibition.pk,
        match_level=_match_level(candidate.personal_score),
        is_exploration=False,
        reasons=reasons,
    )


def _match_level(personal_score: int) -> MatchLevel:
    if personal_score >= 48:
        return MatchLevel.VERY_CLOSE
    if personal_score >= 24:
        return MatchLevel.GOOD_MATCH
    if personal_score > 0:
        return MatchLevel.SOME_MATCH
    return MatchLevel.GENERAL


def _exploration_reasons(
    candidate: _RankedCandidate,
) -> tuple[RecommendationReason, ...]:
    contribution_features = frozenset(
        item.feature
        for item in candidate.contributions
        if item.feature is not None
    )
    connected = sorted(
        candidate.features & contribution_features,
        key=lambda item: (item.axis, item.value),
    )
    novel = sorted(
        candidate.features - contribution_features,
        key=lambda item: (item.axis, item.value),
    )
    if not connected or not novel:
        return (_general_reason(candidate.exhibition),)
    return (
        RecommendationReason(
            code="EXPLORATION_CONNECTION",
            text="선호한 특성과 연결되는 지점이 있어요.",
            feature=connected[0],
        ),
        RecommendationReason(
            code="EXPLORATION_NOVELTY",
            text="연결된 취향에서 새로운 특성을 함께 탐색할 수 있어요.",
            feature=novel[0],
        ),
    )


def _general_reason(exhibition: Exhibition) -> RecommendationReason:
    if exhibition.freshness == Exhibition.Freshness.FRESH:
        return RecommendationReason(
            code="FRESH_OFFICIAL_INFORMATION",
            text="최근 공식 정보가 확인된 현재·예정 전시예요.",
        )
    return RecommendationReason(
        code="OFFICIAL_INFORMATION",
        text="공식 정보가 확인된 현재·예정 전시예요.",
    )

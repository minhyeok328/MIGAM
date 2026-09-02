from backend.apps.discovery.presenters import present_exhibitions_by_id
from backend.apps.discovery.recommendation import (
    FeaturePreference,
    RecommendationHit,
    RecommendationReason,
    RecommendationResult,
    VerificationCandidate,
)


def present_recommendation_result(
    result: RecommendationResult,
) -> dict[str, object]:
    recommendation_ids = tuple(
        item.exhibition_id for item in result.recommendations
    )
    verification_ids = tuple(
        item.exhibition_id for item in result.needs_verification
    )
    recommendation_records = {
        item["id"]: item
        for item in present_exhibitions_by_id(recommendation_ids)
    }
    verification_records = {
        item["id"]: item
        for item in present_exhibitions_by_id(verification_ids)
    }

    return {
        "algorithm_version": result.algorithm_version,
        "candidate_count": result.candidate_count,
        "recommendations": [
            _present_recommendation(item, recommendation_records[item.exhibition_id])
            for item in result.recommendations
            if item.exhibition_id in recommendation_records
        ],
        "needs_verification": [
            _present_verification(item, verification_records[item.exhibition_id])
            for item in result.needs_verification
            if item.exhibition_id in verification_records
        ],
    }


def _present_recommendation(
    hit: RecommendationHit,
    exhibition: dict[str, object],
) -> dict[str, object]:
    return {
        **exhibition,
        "match_level": hit.match_level.value,
        "is_exploration": hit.is_exploration,
        "reasons": [_present_reason(reason) for reason in hit.reasons],
    }


def _present_reason(reason: RecommendationReason) -> dict[str, object]:
    return {
        "code": reason.code,
        "text": reason.text,
        "feature": _present_feature(reason.feature),
    }


def _present_feature(
    feature: FeaturePreference | None,
) -> dict[str, str] | None:
    if feature is None:
        return None
    return {"axis": feature.axis, "value": feature.value}


def _present_verification(
    candidate: VerificationCandidate,
    exhibition: dict[str, object],
) -> dict[str, object]:
    return {
        **exhibition,
        "verification_reasons": list(candidate.verification_reasons),
    }

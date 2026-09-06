"""Read-only artwork metadata with a closed gate for unapproved real sources."""

from django.conf import settings
from django.core.exceptions import ValidationError
from backend.apps.catalog.models import Artwork


def _source_evidence(source) -> dict:
    return {
        "source_id": source.source_id, "source_record_id": source.source_record_id,
        "source_owner": source.source_owner, "last_seen_at": source.last_seen_at.isoformat(),
    }


def _visible_artworks() -> list[Artwork]:
    # No currently approved source registry entry permits artwork publication.
    # Do not open the normal gate from an editable row's VERIFIED flag alone.
    if not getattr(settings, "MIGAM_DEMO_MODE", False):
        return []
    candidates = Artwork.objects.filter(
        is_demo=True, eligibility=Artwork.Eligibility.DEMO,
        source_id="fictional-demo-only", source_record__source_id="fictional-demo-only",
    ).select_related("source_record", "collection_institution").prefetch_related("feature_assertions__source_record")
    visible = []
    for artwork in candidates:
        try:
            artwork.full_clean(validate_unique=False, validate_constraints=False)
        except ValidationError:
            continue
        visible.append(artwork)
    return visible


def _features(artwork: Artwork) -> list[dict]:
    result = []
    for assertion in artwork.feature_assertions.all():
        if assertion.source_record_id != artwork.source_record_id:
            continue
        try:
            assertion.full_clean(validate_unique=False, validate_constraints=False)
        except ValidationError:
            continue
        result.append({
            "axis": assertion.axis, "value": assertion.value,
            "evidence_kind": assertion.evidence_kind, "rule_version": None,
            "source": _source_evidence(assertion.source_record),
        })
    return result


def _present(artwork: Artwork) -> dict:
    return {
        "type": "ARTWORK", "id": artwork.pk, "source_artwork_id": artwork.source_artwork_id,
        "title": artwork.title,
        "creator": {"name": artwork.creator_name, "official_id": artwork.creator_official_id or None,
                    "state": artwork.creator_state},
        "production_year": artwork.production_year, "medium": artwork.medium,
        "collection_institution": {"id": artwork.collection_institution_id, "name": artwork.collection_institution.name},
        "cultural_context": {"state": artwork.culture_state, "value": artwork.cultural_context or None,
                             "is_korean": artwork.is_korean},
        "official_url": artwork.official_url, "last_verified_at": artwork.last_verified_at.isoformat(),
        "eligibility": artwork.eligibility, "is_demo": artwork.is_demo,
        "source": _source_evidence(artwork.source_record),
        "media": {"status": "HIDDEN", "media_url": None, "page_url": None, "credit_line": None},
        "features": _features(artwork),
    }


def artwork_list(*, q: str = "", institution_id: int | None = None,
                 media_group: str = "", page: int = 1, page_size: int = 24) -> dict:
    rows = []
    normalized_query = q.casefold()
    for artwork in _visible_artworks():
        if institution_id is not None and artwork.collection_institution_id != institution_id:
            continue
        if normalized_query and not any(normalized_query in value.casefold() for value in (
            artwork.title, artwork.creator_name, artwork.collection_institution.name,
        )):
            continue
        item = _present(artwork)
        if media_group and not any(feature["axis"] == "MEDIA_GROUP" and feature["value"] == media_group
                                  for feature in item["features"]):
            continue
        rows.append(item)
    offset = (page - 1) * page_size
    return {
        "total": len(rows), "page": page, "page_size": page_size,
        "has_more": offset + page_size < len(rows), "results": rows[offset:offset + page_size],
        "availability": "DEMO" if getattr(settings, "MIGAM_DEMO_MODE", False) else "SOURCE_PENDING",
    }


def artwork_detail(id: int) -> dict | None:
    visible = _visible_artworks()
    artwork = next((row for row in visible if row.pk == id), None)
    if artwork is None:
        return None
    similar = []
    for row in visible:
        if row.pk == artwork.pk:
            continue
        reasons = []
        if (artwork.creator_state == Artwork.CreatorState.KNOWN and row.creator_state == Artwork.CreatorState.KNOWN
                and artwork.creator_official_id and row.source_id == artwork.source_id
                and row.creator_official_id == artwork.creator_official_id):
            reasons.append("SAME_CREATOR")
        if row.collection_institution_id == artwork.collection_institution_id:
            reasons.append("SAME_COLLECTION")
        if reasons:
            similar.append({"artwork": _present(row), "reasons": reasons})
    return {
        "artwork": _present(artwork), "similar_artworks": similar[:6],
        # Collection and creator similarity never imply exhibition participation.
        "exhibition_links": {"state": "UNCONFIRMED", "exhibitions": []},
    }

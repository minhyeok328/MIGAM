from collections.abc import Iterable

from django.db.models import Count, Prefetch, Q

from backend.apps.catalog.media_access import (
    MediaPresentation,
    MediaPresentationStatus,
    resolve_media_presentation,
)
from backend.apps.catalog.models import (
    Exhibition,
    ExhibitionSourceLink,
    Institution,
    MediaAsset,
)
from backend.apps.discovery.search import SearchHit, SearchResultType


def present_search_hits(hits: Iterable[SearchHit]) -> list[dict[str, object]]:
    ordered_hits = tuple(hits)
    exhibition_ids = [
        hit.object_id
        for hit in ordered_hits
        if hit.result_type == SearchResultType.EXHIBITION
    ]
    institution_ids = [
        hit.object_id
        for hit in ordered_hits
        if hit.result_type == SearchResultType.INSTITUTION
    ]

    exhibitions = {
        exhibition.pk: exhibition
        for exhibition in Exhibition.objects.filter(pk__in=exhibition_ids)
        .select_related("institution")
        .prefetch_related(
            Prefetch(
                "source_links",
                queryset=ExhibitionSourceLink.objects.select_related(
                    "latest_source_record"
                ).order_by("-updated_at", "-id"),
                to_attr="search_source_links",
            ),
            Prefetch(
                "mediaasset_records",
                queryset=MediaAsset.objects.prefetch_related(
                    "rights_history"
                ).order_by("id"),
                to_attr="search_media_assets",
            ),
        )
    }
    searchable_exhibition_filter = (
        Q(exhibitions__eligibility=Exhibition.Eligibility.VERIFIED)
        & ~Q(exhibitions__freshness=Exhibition.Freshness.UNVERIFIED)
        & Q(exhibitions__source_links__latest_source_record__isnull=False)
    )
    institutions = {
        institution.pk: institution
        for institution in Institution.objects.filter(pk__in=institution_ids).annotate(
            searchable_exhibition_count=Count(
                "exhibitions",
                filter=searchable_exhibition_filter,
                distinct=True,
            )
        )
    }

    results: list[dict[str, object]] = []
    for hit in ordered_hits:
        if hit.result_type == SearchResultType.EXHIBITION:
            exhibition = exhibitions.get(hit.object_id)
            if exhibition is not None:
                results.append(_present_exhibition(exhibition))
        else:
            institution = institutions.get(hit.object_id)
            if institution is not None:
                results.append(_present_institution(institution))
    return results


def _present_exhibition(exhibition: Exhibition) -> dict[str, object]:
    source_links = getattr(exhibition, "search_source_links", ())
    source_record = (
        source_links[0].latest_source_record if source_links else None
    )
    source = None
    if source_record is not None:
        source = {
            "source_id": source_record.source_id,
            "source_record_id": source_record.source_record_id,
            "source_owner": source_record.source_owner,
            "last_seen_at": source_record.last_seen_at,
        }

    presentation = _preferred_media_presentation(
        getattr(exhibition, "search_media_assets", ())
    )
    return {
        "type": SearchResultType.EXHIBITION.value,
        "id": exhibition.pk,
        "title": exhibition.title,
        "institution": {
            "id": exhibition.institution_id,
            "name": exhibition.institution.name,
        },
        "lifecycle": exhibition.lifecycle,
        "start_date": exhibition.start_date,
        "end_date": exhibition.end_date,
        "venue": exhibition.venue,
        "region": {
            "area": exhibition.region_area,
            "district": exhibition.region_district,
        },
        "official_url": exhibition.official_url,
        "freshness": exhibition.freshness,
        "eligibility": exhibition.eligibility,
        "last_verified_at": exhibition.last_verified_at,
        "source": source,
        "media": {
            "status": presentation.status.value,
            "media_url": presentation.media_url,
            "page_url": presentation.page_url,
            "credit_line": presentation.credit_line,
        },
    }


def _present_institution(institution: Institution) -> dict[str, object]:
    return {
        "type": SearchResultType.INSTITUTION.value,
        "id": institution.pk,
        "name": institution.name,
        "region": {
            "area": institution.region_area,
            "district": institution.region_district,
        },
        "searchable_exhibition_count": institution.searchable_exhibition_count,
    }


def _preferred_media_presentation(
    assets: Iterable[MediaAsset],
) -> MediaPresentation:
    best = MediaPresentation(status=MediaPresentationStatus.HIDDEN)
    for asset in assets:
        presentation = resolve_media_presentation(asset)
        if presentation.status == MediaPresentationStatus.INLINE:
            return presentation
        if presentation.status == MediaPresentationStatus.LINK_ONLY:
            best = presentation
    return best

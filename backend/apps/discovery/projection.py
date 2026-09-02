from dataclasses import dataclass

from django.db import transaction

from backend.apps.catalog.models import Exhibition, Institution
from backend.apps.discovery.models import SearchDocument
from backend.apps.discovery.search import SEARCH_DOCUMENT_VERSION


@dataclass(frozen=True, slots=True)
class SearchProjectionSummary:
    exhibition_count: int
    institution_count: int


@transaction.atomic
def rebuild_search_documents() -> SearchProjectionSummary:
    exhibitions = list(
        Exhibition.objects.filter(
            eligibility=Exhibition.Eligibility.VERIFIED,
            source_links__latest_source_record__isnull=False,
        )
        .exclude(freshness=Exhibition.Freshness.UNVERIFIED)
        .select_related("institution")
        .distinct()
    )
    institution_ids = {exhibition.institution_id for exhibition in exhibitions}
    institutions = list(Institution.objects.filter(pk__in=institution_ids))

    documents = [
        _exhibition_document(exhibition) for exhibition in exhibitions
    ]
    documents.extend(_institution_document(institution) for institution in institutions)

    SearchDocument.objects.all().delete()
    SearchDocument.objects.bulk_create(documents)

    return SearchProjectionSummary(
        exhibition_count=len(exhibitions),
        institution_count=len(institutions),
    )


def _exhibition_document(exhibition: Exhibition) -> SearchDocument:
    institution = exhibition.institution
    return SearchDocument(
        result_type=SearchDocument.ResultType.EXHIBITION,
        object_id=exhibition.pk,
        title=exhibition.title,
        subtitle=institution.name,
        keywords=_keywords(
            exhibition.title,
            institution.name,
            exhibition.venue,
            exhibition.region_area,
            exhibition.region_district,
        ),
        lifecycle=exhibition.lifecycle,
        region_area=exhibition.region_area,
        region_district=exhibition.region_district,
        start_date=exhibition.start_date,
        end_date=exhibition.end_date,
        document_version=SEARCH_DOCUMENT_VERSION,
    )


def _institution_document(institution: Institution) -> SearchDocument:
    region = _keywords(institution.region_area, institution.region_district)
    return SearchDocument(
        result_type=SearchDocument.ResultType.INSTITUTION,
        object_id=institution.pk,
        title=institution.name,
        subtitle=region,
        keywords=_keywords(institution.name, region),
        region_area=institution.region_area,
        region_district=institution.region_district,
        document_version=SEARCH_DOCUMENT_VERSION,
    )


def _keywords(*values: str) -> str:
    return " ".join(dict.fromkeys(value.strip() for value in values if value.strip()))

from collections.abc import Iterable
from datetime import datetime

from django.db import transaction

from backend.apps.catalog.models import Exhibition, VerificationRecord
from backend.apps.discovery.projection import rebuild_search_documents
from backend.apps.sources.models import IngestionRun
from backend.data_pipeline.freshness.schedule import refresh_schedule_for


@transaction.atomic
def apply_time_based_freshness(
    exhibitions: Iterable[Exhibition],
    *,
    now: datetime,
) -> tuple[int, ...]:
    updated_ids: list[int] = []
    for exhibition in exhibitions:
        schedule = refresh_schedule_for(exhibition, now=now)
        if (
            exhibition.freshness == Exhibition.Freshness.FRESH
            and schedule.freshness == Exhibition.Freshness.STALE
        ):
            exhibition.freshness = Exhibition.Freshness.STALE
            exhibition.save(update_fields=("freshness", "updated_at"))
            updated_ids.append(exhibition.pk)
    return tuple(updated_ids)


@transaction.atomic
def record_refresh_failure(
    exhibition: Exhibition,
    *,
    ingestion_run: IngestionRun,
    checked_at: datetime,
    error_message: str,
) -> VerificationRecord:
    exhibition = Exhibition.objects.select_for_update().get(pk=exhibition.pk)
    record, created = VerificationRecord.objects.get_or_create(
        exhibition=exhibition,
        ingestion_run=ingestion_run,
        defaults={
            "outcome": VerificationRecord.Outcome.FAILED,
            "checked_at": checked_at,
            "error_message": error_message[:2000],
        },
    )
    if not created:
        return record

    latest_outcomes = tuple(
        exhibition.verification_records.order_by("-checked_at", "-id")
        .values_list("outcome", flat=True)[:2]
    )
    if latest_outcomes == (
        VerificationRecord.Outcome.FAILED,
        VerificationRecord.Outcome.FAILED,
    ) and exhibition.eligibility != Exhibition.Eligibility.EXCLUDED:
        exhibition.freshness = Exhibition.Freshness.UNVERIFIED
        exhibition.eligibility = Exhibition.Eligibility.DISCOVERY_ONLY
        exhibition.save(
            update_fields=("freshness", "eligibility", "updated_at")
        )
        rebuild_search_documents()
    return record


@transaction.atomic
def record_refresh_success(
    exhibition: Exhibition,
    *,
    ingestion_run: IngestionRun,
    checked_at: datetime,
    source_id: str,
    source_record_id: str,
) -> VerificationRecord:
    exhibition = Exhibition.objects.select_for_update().get(pk=exhibition.pk)
    record, _ = VerificationRecord.objects.get_or_create(
        exhibition=exhibition,
        ingestion_run=ingestion_run,
        defaults={
            "source_id": source_id,
            "source_record_id": source_record_id,
            "outcome": VerificationRecord.Outcome.SUCCESS,
            "checked_at": checked_at,
        },
    )
    exhibition.last_verified_at = checked_at
    exhibition.freshness = Exhibition.Freshness.FRESH
    update_fields: list[str] = ["last_verified_at", "freshness", "updated_at"]
    eligibility_restored = False
    if exhibition.eligibility == Exhibition.Eligibility.DISCOVERY_ONLY:
        exhibition.eligibility = Exhibition.Eligibility.VERIFIED
        update_fields.append("eligibility")
        eligibility_restored = True
    exhibition.save(update_fields=tuple(update_fields))
    if eligibility_restored:
        rebuild_search_documents()
    return record

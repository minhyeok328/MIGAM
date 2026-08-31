from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, datetime

from backend.apps.catalog.models import Exhibition, ExhibitionSourceLink
from backend.apps.data_quality.models import ExhibitionCandidate
from backend.apps.sources.models import IngestionRun
from backend.data_pipeline.freshness.state import (
    apply_time_based_freshness,
    record_refresh_failure,
    record_refresh_success,
)
from backend.data_pipeline.models import RawExhibitionRecord
from backend.data_pipeline.persistence import persist_records
from backend.data_pipeline.registry import SourceRegistry


class RefreshExecutionError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RefreshExecutionSummary:
    run_id: int
    target_count: int
    success_count: int
    failure_count: int


def refresh_exhibitions(
    exhibitions: Iterable[Exhibition],
    *,
    collect: Callable[[], Iterable[RawExhibitionRecord]],
    registry: SourceRegistry,
    as_of: date,
    now: datetime,
    command_name: str,
) -> RefreshExecutionSummary:
    targets = tuple(exhibitions)
    if not targets:
        raise ValueError("at least one exhibition is required")

    target_by_id = {exhibition.pk: exhibition for exhibition in targets}
    links = tuple(
        ExhibitionSourceLink.objects.filter(exhibition_id__in=target_by_id)
        .select_related("exhibition")
        .order_by("id")
    )
    identities_by_exhibition: dict[int, list[tuple[str, str]]] = {
        exhibition_id: [] for exhibition_id in target_by_id
    }
    for link in links:
        identities_by_exhibition[link.exhibition_id].append(
            (link.source_id, link.source_record_id)
        )
    target_identities = {
        identity
        for identities in identities_by_exhibition.values()
        for identity in identities
    }
    source_ids = {source_id for source_id, _ in target_identities}
    run = IngestionRun.objects.create(
        command=command_name,
        source_id=next(iter(source_ids)) if len(source_ids) == 1 else "",
    )

    apply_time_based_freshness(targets, now=now)
    try:
        collected = tuple(collect())
        selected_records = tuple(
            record
            for record in collected
            if (record.source_id, record.source_record_id) in target_identities
        )
        persist_records(
            selected_records,
            registry,
            as_of=as_of,
            command_name=command_name,
            source_id=run.source_id,
            run=run,
        )
    except Exception as error:
        _mark_run_failed(run, now=now, error=error)
        for exhibition in targets:
            record_refresh_failure(
                exhibition,
                ingestion_run=run,
                checked_at=now,
                error_message=str(error),
            )
        raise RefreshExecutionError(str(error)) from error

    valid_identities = set(
        ExhibitionCandidate.objects.filter(
            source_record__observations__ingestion_run=run,
            core_result=ExhibitionCandidate.CoreResult.PASS,
            eligibility=ExhibitionCandidate.Eligibility.VERIFIED,
            quarantined=False,
        ).values_list(
            "source_record__source_id",
            "source_record__source_record_id",
        )
    )
    successful: list[Exhibition] = []
    failed: list[Exhibition] = []
    successful_identity: dict[int, tuple[str, str]] = {}
    for exhibition in targets:
        identity = next(
            (
                candidate
                for candidate in identities_by_exhibition[exhibition.pk]
                if candidate in valid_identities
            ),
            None,
        )
        if identity is None:
            failed.append(exhibition)
        else:
            successful.append(exhibition)
            successful_identity[exhibition.pk] = identity

    for exhibition in successful:
        source_id, source_record_id = successful_identity[exhibition.pk]
        record_refresh_success(
            exhibition,
            ingestion_run=run,
            checked_at=now,
            source_id=source_id,
            source_record_id=source_record_id,
        )

    if failed:
        failed_ids = ", ".join(str(exhibition.pk) for exhibition in failed)
        error = RefreshExecutionError(
            f"target records not returned or failed quality: {failed_ids}"
        )
        _mark_run_failed(run, now=now, error=error)
        for exhibition in failed:
            record_refresh_failure(
                exhibition,
                ingestion_run=run,
                checked_at=now,
                error_message=str(error),
            )
        raise error

    return RefreshExecutionSummary(
        run_id=run.pk,
        target_count=len(targets),
        success_count=len(successful),
        failure_count=0,
    )


def _mark_run_failed(
    run: IngestionRun,
    *,
    now: datetime,
    error: Exception,
) -> None:
    run.status = IngestionRun.Status.FAILED
    run.finished_at = now
    run.error_message = f"{type(error).__name__}: {error}"[:2000]
    run.save(update_fields=("status", "finished_at", "error_message"))

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
import json

from django.db import transaction
from django.utils import timezone

from backend.apps.data_quality.models import ExhibitionCandidate
from backend.apps.sources.models import (
    IngestionObservation,
    IngestionRun,
    SourceRecord,
)
from backend.data_pipeline.canonicalization import canonicalize_candidates
from backend.data_pipeline.models import RawExhibitionRecord
from backend.data_pipeline.pipeline import ProcessedExhibition, process_records
from backend.data_pipeline.registry import SourceRegistry


@dataclass(frozen=True, slots=True)
class PersistenceSummary:
    run_id: int
    received_count: int
    verified_count: int
    excluded_count: int
    quarantined_count: int


def persist_records(
    records: Iterable[RawExhibitionRecord],
    registry: SourceRegistry,
    *,
    as_of: date,
    command_name: str,
    source_id: str = "",
    run: IngestionRun | None = None,
) -> PersistenceSummary:
    if run is None:
        run = IngestionRun.objects.create(
            command=command_name,
            source_id=source_id,
        )
    elif run.status != IngestionRun.Status.RUNNING:
        raise ValueError("precreated ingestion run must be RUNNING")
    try:
        with transaction.atomic():
            processed = process_records(records, registry, as_of=as_of)
            candidates: list[ExhibitionCandidate] = []
            for item in processed:
                raw = item.normalized.raw_record
                payload = _raw_payload(raw)
                source_record, created = SourceRecord.objects.get_or_create(
                    source_id=raw.source_id,
                    source_record_id=raw.source_record_id,
                    content_hash=_content_hash(payload),
                    defaults={
                        "institution_id": raw.institution_id,
                        "source_owner": raw.source_owner,
                        "payload": payload,
                    },
                )
                if not created:
                    SourceRecord.objects.filter(pk=source_record.pk).update(
                        last_seen_at=timezone.now()
                    )
                IngestionObservation.objects.get_or_create(
                    ingestion_run=run,
                    source_record=source_record,
                )
                candidate, _ = ExhibitionCandidate.objects.get_or_create(
                    source_record=source_record,
                    rule_version=item.normalized.rule_version,
                    defaults=_candidate_fields(item),
                )
                candidates.append(candidate)

            canonicalize_candidates(
                candidates,
                registry=registry,
                ingestion_run=run,
            )

            run.received_count = len(processed)
            run.verified_count = sum(
                item.quality.core_result == "PASS" for item in processed
            )
            run.excluded_count = sum(
                item.quality.eligibility == "EXCLUDED" for item in processed
            )
            run.quarantined_count = sum(
                item.quality.quarantine for item in processed
            )
            run.status = IngestionRun.Status.SUCCESS
            run.finished_at = timezone.now()
            run.save(
                update_fields=(
                    "received_count",
                    "verified_count",
                    "excluded_count",
                    "quarantined_count",
                    "status",
                    "finished_at",
                )
            )
    except Exception as error:
        run.status = IngestionRun.Status.FAILED
        run.finished_at = timezone.now()
        run.error_message = f"{type(error).__name__}: {error}"[:2000]
        run.save(update_fields=("status", "finished_at", "error_message"))
        raise

    return PersistenceSummary(
        run_id=run.pk,
        received_count=run.received_count,
        verified_count=run.verified_count,
        excluded_count=run.excluded_count,
        quarantined_count=run.quarantined_count,
    )


def _raw_payload(record: RawExhibitionRecord) -> dict[str, object]:
    return {
        "source_id": record.source_id,
        "institution_id": record.institution_id,
        "source_record_id": record.source_record_id,
        "source_owner": record.source_owner,
        "title": record.title,
        "start_date": record.start_date,
        "end_date": record.end_date,
        "venue": record.venue,
        "region_area": record.region_area,
        "region_district": record.region_district,
        "official_url": record.official_url,
        "canceled": record.canceled,
        "conflicts": sorted(record.conflicts),
        "source_payload": _sorted_mapping(record.raw),
    }


def _sorted_mapping(values: Mapping[str, object]) -> dict[str, object]:
    return {key: values[key] for key in sorted(values)}


def _content_hash(payload: Mapping[str, object]) -> str:
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(serialized.encode("utf-8")).hexdigest()


def _candidate_fields(item: ProcessedExhibition) -> dict[str, object]:
    normalized = item.normalized
    quality = item.quality
    return {
        "title": normalized.title,
        "start_date": normalized.start_date,
        "end_date": normalized.end_date,
        "venue": normalized.venue,
        "region_area": normalized.region_area,
        "region_district": normalized.region_district,
        "lifecycle": normalized.lifecycle,
        "official_url": normalized.official_url,
        "core_result": quality.core_result,
        "eligibility": quality.eligibility,
        "quality_issues": [
            {
                "code": issue.code,
                "field": issue.field,
                "message": issue.message,
            }
            for issue in quality.issues
        ],
        "quarantined": quality.quarantine,
    }

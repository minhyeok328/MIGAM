from collections.abc import Mapping
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from django.db import transaction

from backend.apps.sources.models import (
    CollectionIssue,
    InstitutionAllowlistEntry,
    Source,
)
from backend.data_pipeline.registry import SourceRegistry


SEOUL = ZoneInfo("Asia/Seoul")


@transaction.atomic
def sync_registry_state(registry: SourceRegistry) -> None:
    defaults = _mapping(registry.data.get("defaults"), "defaults")
    sources: dict[str, Source] = {}
    for payload in _mapping_items(registry.data.get("sources"), "sources"):
        registry_id = str(payload["id"])
        operation_status = str(
            payload.get("source_status", defaults.get("source_status", "NORMAL"))
        )
        if operation_status not in Source.OperationStatus.values:
            raise ValueError(f"invalid source status: {operation_status}")
        source, created = Source.objects.get_or_create(
            registry_id=registry_id,
            defaults={
                "name": str(payload["name"]),
                "owner": str(payload["owner"]),
                "kind": str(payload["kind"]),
                "operation_status": operation_status,
            },
        )
        if not created:
            source.name = str(payload["name"])
            source.owner = str(payload["owner"])
            source.kind = str(payload["kind"])
            source.save(update_fields=("name", "owner", "kind", "updated_at"))
        sources[registry_id] = source

    institutions: dict[str, InstitutionAllowlistEntry] = {}
    for payload in _mapping_items(
        registry.data.get("institution_allowlist"),
        "institution_allowlist",
    ):
        registry_id = str(payload["id"])
        source_id = str(payload["source_id"])
        try:
            source = sources[source_id]
        except KeyError as error:
            raise ValueError(
                f"institution {registry_id} references unknown source: {source_id}"
            ) from error
        lifecycle = str(payload["lifecycle"])
        health = str(payload["health"])
        if lifecycle not in InstitutionAllowlistEntry.Lifecycle.values:
            raise ValueError(f"invalid institution lifecycle: {lifecycle}")
        if health not in InstitutionAllowlistEntry.Health.values:
            raise ValueError(f"invalid institution health: {health}")
        region = _mapping(payload.get("region"), f"institution {registry_id} region")
        qualification = _mapping(
            payload.get("qualification"),
            f"institution {registry_id} qualification",
        )
        qualification_target_count = int(qualification["sample_count"])
        if qualification_target_count <= 0:
            raise ValueError(
                f"institution {registry_id} qualification sample_count must be positive"
            )
        entry, created = InstitutionAllowlistEntry.objects.get_or_create(
            registry_id=registry_id,
            defaults={
                "source": source,
                "name": str(payload["name"]),
                "region_area": str(region.get("area", "")),
                "region_district": str(region.get("district", "")),
                "lifecycle": lifecycle,
                "health": health,
                "consecutive_final_failed_count": int(
                    payload.get("consecutive_final_failed_count", 0)
                ),
                "promotion_validation_started_at": _as_seoul_datetime(
                    payload.get("promotion_validation_started_at")
                ),
                "qualification_target_count": qualification_target_count,
            },
        )
        if not created:
            entry.source = source
            entry.name = str(payload["name"])
            entry.region_area = str(region.get("area", ""))
            entry.region_district = str(region.get("district", ""))
            entry.qualification_target_count = qualification_target_count
            entry.save(
                update_fields=(
                    "source",
                    "name",
                    "region_area",
                    "region_district",
                    "qualification_target_count",
                    "updated_at",
                )
            )
        institutions[registry_id] = entry

    for payload in _mapping_items(
        registry.data.get("collection_issues", ()),
        "collection_issues",
    ):
        registry_id = str(payload["id"])
        source_id = str(payload["source_id"])
        institution_id = payload.get("institution_id")
        try:
            source = sources[source_id]
        except KeyError as error:
            raise ValueError(
                f"collection issue {registry_id} references unknown source: {source_id}"
            ) from error
        institution = None
        if institution_id is not None:
            try:
                institution = institutions[str(institution_id)]
            except KeyError as error:
                raise ValueError(
                    "collection issue "
                    f"{registry_id} references unknown institution: {institution_id}"
                ) from error
        classification = str(payload["classification"])
        scope = str(payload["scope"])
        status = str(payload.get("status", "OPEN"))
        if classification not in CollectionIssue.Classification.values:
            raise ValueError(f"invalid collection issue classification: {classification}")
        if scope not in CollectionIssue.Scope.values:
            raise ValueError(f"invalid collection issue scope: {scope}")
        if status not in CollectionIssue.Status.values:
            raise ValueError(f"invalid collection issue status: {status}")
        if scope == CollectionIssue.Scope.ENTRY and institution is None:
            raise ValueError(f"entry collection issue needs an institution: {registry_id}")
        issue, created = CollectionIssue.objects.get_or_create(
            registry_id=registry_id,
            defaults={
                "classification": classification,
                "scope": scope,
                "source": source,
                "institution": institution,
                "source_record_id": str(payload.get("source_record_id", "")),
                "field": str(payload.get("field", "")),
                "action": str(payload.get("action", "")),
                "scope_evidence": str(payload.get("scope_evidence", "")),
                "status": status,
            },
        )
        if not created:
            issue.classification = classification
            issue.scope = scope
            issue.source = source
            issue.institution = institution
            issue.source_record_id = str(payload.get("source_record_id", ""))
            issue.field = str(payload.get("field", ""))
            issue.action = str(payload.get("action", ""))
            issue.scope_evidence = str(payload.get("scope_evidence", ""))
            issue.save(
                update_fields=(
                    "classification",
                    "scope",
                    "source",
                    "institution",
                    "source_record_id",
                    "field",
                    "action",
                    "scope_evidence",
                    "updated_at",
                )
            )


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return value


def _mapping_items(value: object, name: str) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{name} must be a list")
    items: list[Mapping[str, object]] = []
    for item in value:
        items.append(_mapping(item, f"{name} item"))
    return tuple(items)


def _as_seoul_datetime(value: object) -> datetime | None:
    if value is None or str(value).strip() == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=SEOUL)
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=SEOUL)
    parsed = datetime.fromisoformat(str(value))
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=SEOUL)

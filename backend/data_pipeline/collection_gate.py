from collections.abc import Iterable

from backend.apps.sources.models import (
    CollectionIssue,
    InstitutionAllowlistEntry,
    Source,
)


CRITICAL_CLASSIFICATIONS = (
    CollectionIssue.Classification.POLICY_BLOCK,
    CollectionIssue.Classification.ACCESS_BLOCK,
    CollectionIssue.Classification.STRUCTURAL_CRITICAL,
)


class CollectionGateError(ValueError):
    pass


def select_collectible_entries(
    *,
    source_ids: Iterable[str] | None = None,
    institution_ids: Iterable[str] | None = None,
) -> tuple[InstitutionAllowlistEntry, ...]:
    requested_source_ids = tuple(dict.fromkeys(source_ids or ()))
    requested_institution_ids = tuple(dict.fromkeys(institution_ids or ()))
    queryset = InstitutionAllowlistEntry.objects.select_related("source")
    if requested_source_ids:
        queryset = queryset.filter(source__registry_id__in=requested_source_ids)
    if requested_institution_ids:
        queryset = queryset.filter(registry_id__in=requested_institution_ids)
    candidates = tuple(queryset.order_by("registry_id"))

    if requested_source_ids:
        registered_source_ids = set(
            Source.objects.filter(registry_id__in=requested_source_ids).values_list(
                "registry_id",
                flat=True,
            )
        )
        missing = set(requested_source_ids) - registered_source_ids
        if missing:
            raise CollectionGateError(
                f"unknown source registration: {', '.join(sorted(missing))}"
            )

    non_normal_source_ids = {
        entry.source_id
        for entry in candidates
        if entry.source.operation_status != Source.OperationStatus.NORMAL
    }
    source_critical_ids = set(
        CollectionIssue.objects.filter(
            source_id__in={entry.source_id for entry in candidates},
            status=CollectionIssue.Status.OPEN,
            classification__in=CRITICAL_CLASSIFICATIONS,
            scope=CollectionIssue.Scope.SOURCE,
        ).values_list("source_id", flat=True)
    )
    entry_critical_ids = set(
        CollectionIssue.objects.filter(
            institution_id__in={entry.pk for entry in candidates},
            status=CollectionIssue.Status.OPEN,
            classification__in=CRITICAL_CLASSIFICATIONS,
            scope=CollectionIssue.Scope.ENTRY,
        ).values_list("institution_id", flat=True)
    )

    collectible = tuple(
        entry
        for entry in candidates
        if entry.lifecycle
        in (
            InstitutionAllowlistEntry.Lifecycle.PROVISIONAL,
            InstitutionAllowlistEntry.Lifecycle.ACTIVE,
        )
        and entry.source_id not in non_normal_source_ids
        and entry.source_id not in source_critical_ids
        and entry.pk not in entry_critical_ids
    )
    if collectible:
        return collectible
    if non_normal_source_ids:
        raise CollectionGateError("source is not normal")
    if source_critical_ids:
        raise CollectionGateError("source critical collection issue is open")
    raise CollectionGateError("no collectible institution in requested scope")

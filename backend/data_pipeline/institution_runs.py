from datetime import datetime

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from backend.apps.sources.models import (
    CollectionIssue,
    IngestionObservation,
    IngestionRun,
    InstitutionAllowlistEntry,
    InstitutionRunResult,
)
from backend.apps.data_quality.models import ExhibitionCandidate
from backend.data_pipeline.collection_gate import (
    CRITICAL_CLASSIFICATIONS,
    CollectionGateError,
)
from backend.data_pipeline.qualification import record_qualification_result


@transaction.atomic
def record_institution_result(
    ingestion_run: IngestionRun,
    institution: InstitutionAllowlistEntry,
    *,
    status: str,
    received_count: int = 0,
    verified_count: int = 0,
    quarantined_count: int = 0,
    approved_record_exception_count: int = 0,
    completed_core_target_count: int | None = None,
    retry_count: int | None = None,
    error_message: str = "",
    finished_at: datetime | None = None,
) -> InstitutionRunResult:
    if status not in InstitutionRunResult.Status.values:
        raise ValueError(f"invalid institution run status: {status}")
    institution = InstitutionAllowlistEntry.objects.select_for_update().get(
        pk=institution.pk
    )
    effective_completed_core_target_count = min(
        received_count,
        (
            verified_count + approved_record_exception_count
            if completed_core_target_count is None
            else completed_core_target_count
        ),
    )
    qualification_target_missing = (
        ingestion_run.qualification_mode
        and institution.lifecycle
        == InstitutionAllowlistEntry.Lifecycle.PROVISIONAL
        and (
            institution.qualification_target_count <= 0
            or effective_completed_core_target_count
            < institution.qualification_target_count
        )
    )
    if (
        qualification_target_missing
        and status == InstitutionRunResult.Status.SUCCESS
    ):
        status = InstitutionRunResult.Status.FAILED
        if not error_message:
            error_message = (
                "QUALIFICATION_TARGET_MISSING:"
                f"expected={institution.qualification_target_count} "
                f"completed={effective_completed_core_target_count} "
                f"received={received_count}"
            )
    existing = InstitutionRunResult.objects.filter(
        ingestion_run=ingestion_run,
        institution=institution,
    ).first()
    if existing is not None:
        record_qualification_result(existing)
        return existing

    effective_finished_at = finished_at or timezone.now()
    lifecycle_before = institution.lifecycle
    health_before = institution.health
    failed_count_before = institution.consecutive_final_failed_count
    open_issues = tuple(
        CollectionIssue.objects.filter(
            Q(institution=institution)
            | Q(scope=CollectionIssue.Scope.SOURCE, source=institution.source),
            status=CollectionIssue.Status.OPEN,
        ).order_by("registry_id")
    )
    issue_classifications = sorted(
        {issue.classification for issue in open_issues}
    )
    critical_issue_ids = [
        issue.registry_id
        for issue in open_issues
        if issue.classification in CRITICAL_CLASSIFICATIONS
    ]

    if status == InstitutionRunResult.Status.SUCCESS:
        if critical_issue_ids:
            raise CollectionGateError(
                "critical collection issue opened before finalization: "
                f"{', '.join(critical_issue_ids)}"
            )
        optional_issue_ids = [
            issue.registry_id
            for issue in open_issues
            if issue.classification
            == CollectionIssue.Classification.STRUCTURAL_OPTIONAL
        ]
        institution.consecutive_final_failed_count = 0
        institution.priority_reverify_at = None
        institution.priority_reverify_reason = ""
        if optional_issue_ids:
            institution.health = InstitutionAllowlistEntry.Health.DEGRADED
            institution.health_reasons = optional_issue_ids
        else:
            institution.health = InstitutionAllowlistEntry.Health.HEALTHY
            institution.health_reasons = []
    else:
        institution.health = InstitutionAllowlistEntry.Health.DEGRADED
        institution.health_reasons = ["FINAL_FAILED", *critical_issue_ids]
        if institution.lifecycle == InstitutionAllowlistEntry.Lifecycle.ACTIVE:
            institution.consecutive_final_failed_count += 1
            institution.priority_reverify_at = effective_finished_at
            institution.priority_reverify_reason = "FINAL_FAILED"
            if critical_issue_ids:
                institution.lifecycle = InstitutionAllowlistEntry.Lifecycle.SUSPENDED
                institution.lifecycle_changed_at = effective_finished_at
                institution.lifecycle_changed_by = "SYSTEM"
                institution.lifecycle_change_reason = "OPEN_CRITICAL"
                institution.suspension_reason = (
                    f"OPEN_CRITICAL:{','.join(critical_issue_ids)}"
                )
            elif institution.consecutive_final_failed_count >= 2:
                institution.lifecycle = InstitutionAllowlistEntry.Lifecycle.SUSPENDED
                institution.lifecycle_changed_at = effective_finished_at
                institution.lifecycle_changed_by = "SYSTEM"
                institution.lifecycle_change_reason = "CONSECUTIVE_FINAL_FAILED"
                institution.suspension_reason = "CONSECUTIVE_FINAL_FAILED"
        else:
            institution.consecutive_final_failed_count = 0

    if institution.health != health_before:
        institution.health_changed_at = effective_finished_at
    institution.save(
        update_fields=(
            "lifecycle",
            "lifecycle_changed_at",
            "lifecycle_changed_by",
            "lifecycle_change_reason",
            "suspension_reason",
            "health",
            "health_changed_at",
            "health_reasons",
            "consecutive_final_failed_count",
            "priority_reverify_at",
            "priority_reverify_reason",
            "updated_at",
        )
    )
    result = InstitutionRunResult.objects.create(
        ingestion_run=ingestion_run,
        institution=institution,
        status=status,
        received_count=received_count,
        verified_count=verified_count,
        quarantined_count=quarantined_count,
        approved_record_exception_count=approved_record_exception_count,
        completed_core_target_count=effective_completed_core_target_count,
        retry_count=retry_count,
        issue_classifications=issue_classifications,
        lifecycle_before=lifecycle_before,
        lifecycle_after=institution.lifecycle,
        health_before=health_before,
        health_after=institution.health,
        failed_count_before=failed_count_before,
        failed_count_after=institution.consecutive_final_failed_count,
        error_message=error_message[:2000],
        finished_at=effective_finished_at,
    )
    record_qualification_result(result)
    result.refresh_from_db(fields=("lifecycle_after",))
    return result


@transaction.atomic
def record_institution_results(
    ingestion_run: IngestionRun,
    institutions: tuple[InstitutionAllowlistEntry, ...],
    *,
    failed_institution_ids: set[str] | None = None,
    error_message: str = "",
    finished_at: datetime | None = None,
) -> tuple[InstitutionRunResult, ...]:
    failed_ids = failed_institution_ids or set()
    results: list[InstitutionRunResult] = []
    for institution in institutions:
        observations = IngestionObservation.objects.filter(
            ingestion_run=ingestion_run,
            source_record__institution_id=institution.registry_id,
        )
        candidates = ExhibitionCandidate.objects.filter(
            source_record__observations__ingestion_run=ingestion_run,
            source_record__institution_id=institution.registry_id,
        ).distinct()
        received_count = observations.count()
        verified_filter = Q(
            core_result=ExhibitionCandidate.CoreResult.PASS,
            eligibility=ExhibitionCandidate.Eligibility.VERIFIED,
            quarantined=False,
        )
        verified_count = candidates.filter(verified_filter).count()
        approved_exception_record_ids = tuple(
            CollectionIssue.objects.filter(
                classification=CollectionIssue.Classification.RECORD_EXCEPTION,
                scope=CollectionIssue.Scope.ENTRY,
                source=institution.source,
                institution=institution,
                action="QUARANTINE_RECORD",
                status=CollectionIssue.Status.OPEN,
            )
            .exclude(source_record_id="")
            .values_list("source_record_id", flat=True)
        )
        approved_exception_filter = Q(
            core_result=ExhibitionCandidate.CoreResult.FAIL,
            eligibility=ExhibitionCandidate.Eligibility.EXCLUDED,
            quarantined=True,
            source_record__source_record_id__in=approved_exception_record_ids,
        )
        approved_record_exception_count = (
            candidates.filter(approved_exception_filter)
            .values("source_record__source_record_id")
            .distinct()
            .count()
        )
        completed_core_target_count = (
            candidates.filter(verified_filter | approved_exception_filter)
            .values("source_record__source_record_id")
            .distinct()
            .count()
        )
        qualification_target_missing = (
            ingestion_run.qualification_mode
            and institution.lifecycle
            == InstitutionAllowlistEntry.Lifecycle.PROVISIONAL
            and (
                institution.qualification_target_count <= 0
                or completed_core_target_count
                < institution.qualification_target_count
            )
        )
        institution_failed = (
            institution.registry_id in failed_ids or qualification_target_missing
        )
        institution_error = (
            error_message
            if institution.registry_id in failed_ids
            else (
                "QUALIFICATION_TARGET_MISSING:"
                f"expected={institution.qualification_target_count} "
                f"completed={completed_core_target_count} "
                f"received={received_count}"
                if qualification_target_missing
                else ""
            )
        )
        results.append(
            record_institution_result(
                ingestion_run,
                institution,
                status=(
                    InstitutionRunResult.Status.FAILED
                    if institution_failed
                    else InstitutionRunResult.Status.SUCCESS
                ),
                received_count=received_count,
                verified_count=verified_count,
                quarantined_count=candidates.filter(quarantined=True).count(),
                approved_record_exception_count=(
                    approved_record_exception_count
                ),
                completed_core_target_count=completed_core_target_count,
                error_message=institution_error,
                finished_at=finished_at,
            )
        )
    qualification_failures = [
        result
        for result in results
        if ingestion_run.qualification_mode
        and result.lifecycle_before
        == InstitutionAllowlistEntry.Lifecycle.PROVISIONAL
        and result.status == InstitutionRunResult.Status.FAILED
    ]
    if qualification_failures:
        failed_registry_ids = ", ".join(
            result.institution.registry_id for result in qualification_failures
        )
        ingestion_run.status = IngestionRun.Status.FAILED
        if not ingestion_run.error_message:
            ingestion_run.error_message = (
                f"qualification failed for: {failed_registry_ids}"
            )
        ingestion_run.save(update_fields=("status", "error_message"))
    return tuple(results)

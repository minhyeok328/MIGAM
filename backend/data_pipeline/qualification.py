from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Q

from backend.apps.catalog.models import ChangeHistory, SourceConflict
from backend.apps.sources.models import (
    CollectionIssue,
    InstitutionAllowlistEntry,
    InstitutionQualificationRun,
    InstitutionRunResult,
    PromotionEvidence,
    Source,
)
from backend.data_pipeline.collection_gate import CRITICAL_CLASSIFICATIONS


SEOUL = ZoneInfo("Asia/Seoul")
PROMOTION_REASON = "QUALIFICATION_PROMOTION"
POLICY_ACCESS_CLASSIFICATIONS = {
    CollectionIssue.Classification.POLICY_BLOCK,
    CollectionIssue.Classification.ACCESS_BLOCK,
}


@transaction.atomic
def record_qualification_result(
    institution_result: InstitutionRunResult,
) -> InstitutionQualificationRun | None:
    result = InstitutionRunResult.objects.select_related(
        "ingestion_run",
        "institution__source",
    ).get(pk=institution_result.pk)
    if (
        not result.ingestion_run.qualification_mode
        or result.lifecycle_before
        != InstitutionAllowlistEntry.Lifecycle.PROVISIONAL
    ):
        return None

    institution = result.institution
    open_issues = tuple(_open_issues(institution))
    structural_count = sum(
        issue.classification
        == CollectionIssue.Classification.STRUCTURAL_CRITICAL
        for issue in open_issues
    )
    policy_access_count = sum(
        issue.classification in POLICY_ACCESS_CLASSIFICATIONS
        for issue in open_issues
    )
    missing_target_count = max(
        institution.qualification_target_count
        - result.completed_core_target_count,
        0,
    )
    conflict_count = _open_conflict_count(institution)
    meaningful_count = _meaningful_changes_for_result(result).count()
    status = (
        InstitutionQualificationRun.Status.FAILED
        if result.status == InstitutionRunResult.Status.FAILED
        or institution.qualification_target_count <= 0
        or missing_target_count
        or structural_count
        or policy_access_count
        else InstitutionQualificationRun.Status.SUCCESS
    )
    qualification, _ = InstitutionQualificationRun.objects.get_or_create(
        institution_result=result,
        defaults={
            "institution": institution,
            "status": status,
            "finished_at": result.finished_at,
            "service_date": result.finished_at.astimezone(SEOUL).date(),
            "retry_count": result.retry_count,
            "target_count": institution.qualification_target_count,
            "received_count": result.received_count,
            "verified_count": result.verified_count,
            "quarantined_count": result.quarantined_count,
            "approved_record_exception_count": (
                result.approved_record_exception_count
            ),
            "completed_core_target_count": result.completed_core_target_count,
            "final_missing_core_target_count": missing_target_count,
            "structural_core_issue_count": structural_count,
            "policy_access_issue_count": policy_access_count,
            "source_operation_status": institution.source.operation_status,
            "unresolved_conflict_count": conflict_count,
            "meaningful_change_count": meaningful_count,
            "failure_reasons": _failure_reasons(
                result,
                missing_target_count=missing_target_count,
                open_issues=open_issues,
            ),
        },
    )
    if qualification.status == InstitutionQualificationRun.Status.SUCCESS:
        evaluate_promotion(qualification)
    return qualification


@transaction.atomic
def evaluate_promotion(
    qualification: InstitutionQualificationRun,
) -> PromotionEvidence | None:
    qualification = InstitutionQualificationRun.objects.select_related(
        "institution_result",
        "institution__source",
    ).get(pk=qualification.pk)
    institution = InstitutionAllowlistEntry.objects.select_for_update().select_related(
        "source"
    ).get(pk=qualification.institution_id)
    if (
        institution.lifecycle != InstitutionAllowlistEntry.Lifecycle.PROVISIONAL
        or qualification.status != InstitutionQualificationRun.Status.SUCCESS
        or institution.promotion_validation_started_at is None
        or qualification.finished_at
        < institution.promotion_validation_started_at + timedelta(days=14)
    ):
        return None

    all_runs = list(
        InstitutionQualificationRun.objects.filter(
            institution=institution,
            finished_at__gte=institution.promotion_validation_started_at,
        ).order_by("finished_at", "id")
    )
    if not all_runs or all_runs[-1].pk != qualification.pk:
        return None
    last_failure_index = max(
        (
            index
            for index, run in enumerate(all_runs)
            if run.status == InstitutionQualificationRun.Status.FAILED
        ),
        default=-1,
    )
    representatives: dict[object, InstitutionQualificationRun] = {}
    for run in all_runs[last_failure_index + 1 :]:
        if run.status != InstitutionQualificationRun.Status.SUCCESS:
            continue
        current = representatives.get(run.service_date)
        if current is None or _prefer_representative(run, current):
            representatives[run.service_date] = run
    if len(representatives) < 3:
        return None
    selected = tuple(
        representatives[service_date]
        for service_date in sorted(representatives)[-3:]
    )
    if any(
        run.final_missing_core_target_count
        or run.structural_core_issue_count
        or run.policy_access_issue_count
        for run in selected
    ):
        return None

    selected_run_ids = [
        run.institution_result.ingestion_run_id for run in selected
    ]
    meaningful_change = (
        ChangeHistory.objects.filter(
            ingestion_run_id__in=selected_run_ids,
            exhibition__institution__registry_id=institution.registry_id,
            meaningful_for_promotion=True,
        )
        .order_by("created_at", "id")
        .first()
    )
    if meaningful_change is None:
        return None
    if institution.source.operation_status != Source.OperationStatus.NORMAL:
        return None
    if _open_issues(institution).filter(
        classification__in=CRITICAL_CLASSIFICATIONS
    ).exists():
        return None
    conflict_count = _open_conflict_count(institution)
    if conflict_count:
        return None

    evidence, created = PromotionEvidence.objects.get_or_create(
        institution=institution,
        validation_started_at=institution.promotion_validation_started_at,
        defaults={
            "promoted_at": qualification.finished_at,
            "last_qualification_run": selected[-1],
            "meaningful_change_history": meaningful_change,
            "source_operation_status": institution.source.operation_status,
            "unresolved_conflict_count": conflict_count,
            "decision_reason": PROMOTION_REASON,
        },
    )
    if created:
        evidence.qualification_runs.add(*selected)

    institution.lifecycle = InstitutionAllowlistEntry.Lifecycle.ACTIVE
    institution.lifecycle_changed_at = qualification.finished_at
    institution.lifecycle_changed_by = "SYSTEM"
    institution.lifecycle_change_reason = PROMOTION_REASON
    institution.suspension_reason = ""
    institution.save(
        update_fields=(
            "lifecycle",
            "lifecycle_changed_at",
            "lifecycle_changed_by",
            "lifecycle_change_reason",
            "suspension_reason",
            "updated_at",
        )
    )
    InstitutionRunResult.objects.filter(
        pk=qualification.institution_result_id
    ).update(lifecycle_after=InstitutionAllowlistEntry.Lifecycle.ACTIVE)
    return evidence


def _prefer_representative(
    candidate: InstitutionQualificationRun,
    current: InstitutionQualificationRun,
) -> bool:
    candidate_meaningful = candidate.meaningful_change_count > 0
    current_meaningful = current.meaningful_change_count > 0
    if candidate_meaningful != current_meaningful:
        return candidate_meaningful
    return (candidate.finished_at, candidate.pk) > (current.finished_at, current.pk)


def _open_issues(institution: InstitutionAllowlistEntry):
    return CollectionIssue.objects.filter(
        Q(institution=institution)
        | Q(scope=CollectionIssue.Scope.SOURCE, source=institution.source),
        status=CollectionIssue.Status.OPEN,
    )


def _open_conflict_count(institution: InstitutionAllowlistEntry) -> int:
    return SourceConflict.objects.filter(
        exhibition__institution__registry_id=institution.registry_id,
        status=SourceConflict.Status.OPEN,
    ).count()


def _meaningful_changes_for_result(institution_result: InstitutionRunResult):
    return ChangeHistory.objects.filter(
        ingestion_run=institution_result.ingestion_run,
        exhibition__institution__registry_id=(
            institution_result.institution.registry_id
        ),
        meaningful_for_promotion=True,
    )


def _failure_reasons(
    result: InstitutionRunResult,
    *,
    missing_target_count: int,
    open_issues: tuple[CollectionIssue, ...],
) -> list[str]:
    reasons: list[str] = []
    if result.error_message:
        reasons.append(result.error_message)
    if missing_target_count:
        reasons.append(f"MISSING_CORE_TARGETS:{missing_target_count}")
    reasons.extend(
        sorted(
            {
                issue.classification
                for issue in open_issues
                if issue.classification in CRITICAL_CLASSIFICATIONS
            }
        )
    )
    return reasons

from django.db import models
from django.db.models import Q
from django.utils import timezone


class Source(models.Model):
    class OperationStatus(models.TextChoices):
        NORMAL = "NORMAL", "Normal"
        PAUSED = "PAUSED", "Paused"
        DISABLED = "DISABLED", "Disabled"

    registry_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)
    kind = models.CharField(max_length=64)
    operation_status = models.CharField(
        max_length=16,
        choices=OperationStatus.choices,
        default=OperationStatus.NORMAL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("registry_id",)


class InstitutionAllowlistEntry(models.Model):
    class Lifecycle(models.TextChoices):
        CANDIDATE = "CANDIDATE", "Candidate"
        PROVISIONAL = "PROVISIONAL", "Provisional"
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"

    class Health(models.TextChoices):
        HEALTHY = "HEALTHY", "Healthy"
        DEGRADED = "DEGRADED", "Degraded"

    registry_id = models.CharField(max_length=128, unique=True)
    source = models.ForeignKey(
        Source,
        on_delete=models.PROTECT,
        related_name="allowlist_entries",
    )
    name = models.CharField(max_length=255)
    region_area = models.CharField(max_length=100, blank=True)
    region_district = models.CharField(max_length=100, blank=True)
    lifecycle = models.CharField(max_length=16, choices=Lifecycle.choices)
    lifecycle_changed_at = models.DateTimeField(default=timezone.now)
    lifecycle_changed_by = models.CharField(max_length=128, blank=True)
    lifecycle_change_reason = models.CharField(max_length=64, blank=True)
    suspension_reason = models.TextField(blank=True)
    health = models.CharField(max_length=16, choices=Health.choices)
    health_changed_at = models.DateTimeField(default=timezone.now)
    health_reasons = models.JSONField(default=list)
    consecutive_final_failed_count = models.PositiveIntegerField(default=0)
    priority_reverify_at = models.DateTimeField(null=True, blank=True)
    priority_reverify_reason = models.TextField(blank=True)
    promotion_validation_started_at = models.DateTimeField(null=True, blank=True)
    qualification_target_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("registry_id",)


class CollectionIssue(models.Model):
    class Classification(models.TextChoices):
        POLICY_BLOCK = "POLICY_BLOCK", "Policy block"
        ACCESS_BLOCK = "ACCESS_BLOCK", "Access block"
        STRUCTURAL_CRITICAL = "STRUCTURAL_CRITICAL", "Structural critical"
        STRUCTURAL_OPTIONAL = "STRUCTURAL_OPTIONAL", "Structural optional"
        RECORD_EXCEPTION = "RECORD_EXCEPTION", "Record exception"

    class Scope(models.TextChoices):
        ENTRY = "ENTRY", "Entry"
        SOURCE = "SOURCE", "Source"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        RESOLVED = "RESOLVED", "Resolved"

    registry_id = models.CharField(max_length=128, unique=True)
    classification = models.CharField(
        max_length=32,
        choices=Classification.choices,
    )
    scope = models.CharField(max_length=16, choices=Scope.choices)
    source = models.ForeignKey(
        Source,
        on_delete=models.PROTECT,
        related_name="collection_issues",
    )
    institution = models.ForeignKey(
        InstitutionAllowlistEntry,
        on_delete=models.PROTECT,
        related_name="collection_issues",
        null=True,
        blank=True,
    )
    source_record_id = models.CharField(max_length=255, blank=True)
    field = models.CharField(max_length=128, blank=True)
    action = models.CharField(max_length=64, blank=True)
    scope_evidence = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
    )
    first_seen_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_reason = models.TextField(blank=True)

    class Meta:
        ordering = ("registry_id",)
        constraints = [
            models.CheckConstraint(
                condition=Q(scope="SOURCE") | Q(institution__isnull=False),
                name="sources_entry_issue_has_institution",
            )
        ]
        indexes = [
            models.Index(
                fields=("source", "status", "classification", "scope"),
                name="sources_issue_gate_lookup",
            )
        ]


class IngestionRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "RUNNING", "Running"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    command = models.CharField(max_length=64)
    source_id = models.CharField(max_length=128, blank=True)
    qualification_mode = models.BooleanField(default=False)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.RUNNING,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    received_count = models.PositiveIntegerField(default=0)
    verified_count = models.PositiveIntegerField(default=0)
    excluded_count = models.PositiveIntegerField(default=0)
    quarantined_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ("-started_at", "-id")


class SourceRecord(models.Model):
    source_id = models.CharField(max_length=128)
    institution_id = models.CharField(max_length=128)
    source_record_id = models.CharField(max_length=255)
    source_owner = models.CharField(max_length=255)
    payload = models.JSONField()
    content_hash = models.CharField(max_length=64)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("source_id", "source_record_id", "content_hash"),
                name="sources_unique_record_version",
            )
        ]
        indexes = [
            models.Index(
                fields=("source_id", "source_record_id"),
                name="sources_record_lookup",
            )
        ]


class IngestionObservation(models.Model):
    ingestion_run = models.ForeignKey(
        IngestionRun,
        on_delete=models.PROTECT,
        related_name="observations",
    )
    source_record = models.ForeignKey(
        SourceRecord,
        on_delete=models.PROTECT,
        related_name="observations",
    )
    observed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("ingestion_run", "source_record"),
                name="sources_unique_run_observation",
            )
        ]


class InstitutionRunResult(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    ingestion_run = models.ForeignKey(
        IngestionRun,
        on_delete=models.PROTECT,
        related_name="institution_results",
    )
    institution = models.ForeignKey(
        InstitutionAllowlistEntry,
        on_delete=models.PROTECT,
        related_name="run_results",
    )
    status = models.CharField(max_length=16, choices=Status.choices)
    received_count = models.PositiveIntegerField(default=0)
    verified_count = models.PositiveIntegerField(default=0)
    quarantined_count = models.PositiveIntegerField(default=0)
    approved_record_exception_count = models.PositiveIntegerField(default=0)
    completed_core_target_count = models.PositiveIntegerField(default=0)
    retry_count = models.PositiveIntegerField(null=True, blank=True)
    issue_classifications = models.JSONField(default=list)
    lifecycle_before = models.CharField(
        max_length=16,
        choices=InstitutionAllowlistEntry.Lifecycle.choices,
    )
    lifecycle_after = models.CharField(
        max_length=16,
        choices=InstitutionAllowlistEntry.Lifecycle.choices,
    )
    health_before = models.CharField(
        max_length=16,
        choices=InstitutionAllowlistEntry.Health.choices,
    )
    health_after = models.CharField(
        max_length=16,
        choices=InstitutionAllowlistEntry.Health.choices,
    )
    failed_count_before = models.PositiveIntegerField(default=0)
    failed_count_after = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    finished_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-finished_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("ingestion_run", "institution"),
                name="sources_unique_run_institution_result",
            )
        ]
        indexes = [
            models.Index(
                fields=("institution", "status", "finished_at"),
                name="sources_inst_result_lookup",
            )
        ]


class InstitutionQualificationRun(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    institution_result = models.OneToOneField(
        InstitutionRunResult,
        on_delete=models.PROTECT,
        related_name="qualification_run",
    )
    institution = models.ForeignKey(
        InstitutionAllowlistEntry,
        on_delete=models.PROTECT,
        related_name="qualification_runs",
    )
    status = models.CharField(max_length=16, choices=Status.choices)
    finished_at = models.DateTimeField()
    service_date = models.DateField()
    retry_count = models.PositiveIntegerField(null=True, blank=True)
    target_count = models.PositiveIntegerField(default=0)
    received_count = models.PositiveIntegerField(default=0)
    verified_count = models.PositiveIntegerField(default=0)
    quarantined_count = models.PositiveIntegerField(default=0)
    approved_record_exception_count = models.PositiveIntegerField(default=0)
    completed_core_target_count = models.PositiveIntegerField(default=0)
    final_missing_core_target_count = models.PositiveIntegerField(default=0)
    structural_core_issue_count = models.PositiveIntegerField(default=0)
    policy_access_issue_count = models.PositiveIntegerField(default=0)
    source_operation_status = models.CharField(
        max_length=16,
        choices=Source.OperationStatus.choices,
    )
    unresolved_conflict_count = models.PositiveIntegerField(default=0)
    meaningful_change_count = models.PositiveIntegerField(default=0)
    failure_reasons = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("finished_at", "id")
        indexes = [
            models.Index(
                fields=("institution", "status", "finished_at"),
                name="sources_qual_inst_result",
            ),
            models.Index(
                fields=("institution", "service_date"),
                name="sources_qual_inst_date",
            ),
        ]


class PromotionEvidence(models.Model):
    institution = models.ForeignKey(
        InstitutionAllowlistEntry,
        on_delete=models.PROTECT,
        related_name="promotion_evidence",
    )
    validation_started_at = models.DateTimeField()
    promoted_at = models.DateTimeField()
    qualification_runs = models.ManyToManyField(
        InstitutionQualificationRun,
        related_name="promotion_evidence",
    )
    last_qualification_run = models.ForeignKey(
        InstitutionQualificationRun,
        on_delete=models.PROTECT,
        related_name="last_for_promotion_evidence",
    )
    meaningful_change_history = models.ForeignKey(
        "catalog.ChangeHistory",
        on_delete=models.PROTECT,
        related_name="promotion_evidence",
    )
    source_operation_status = models.CharField(
        max_length=16,
        choices=Source.OperationStatus.choices,
    )
    unresolved_conflict_count = models.PositiveIntegerField(default=0)
    decision_reason = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-promoted_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("institution", "validation_started_at"),
                name="sources_unique_promotion_cycle",
            )
        ]

from django.db import models


class IngestionRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "RUNNING", "Running"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    command = models.CharField(max_length=64)
    source_id = models.CharField(max_length=128, blank=True)
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

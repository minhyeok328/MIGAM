from django.db import models
from django.utils import timezone

from backend.apps.data_quality.models import ExhibitionCandidate
from backend.apps.sources.models import SourceRecord


class Institution(models.Model):
    registry_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=255)
    region_area = models.CharField(max_length=100, blank=True)
    region_district = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("registry_id",)


class Exhibition(models.Model):
    class Lifecycle(models.TextChoices):
        UPCOMING = "UPCOMING", "Upcoming"
        CURRENT = "CURRENT", "Current"
        ENDED = "ENDED", "Ended"
        CANCELED = "CANCELED", "Canceled"
        UNKNOWN = "UNKNOWN", "Unknown"

    class Freshness(models.TextChoices):
        FRESH = "FRESH", "Fresh"
        STALE = "STALE", "Stale"
        UNVERIFIED = "UNVERIFIED", "Unverified"

    class Eligibility(models.TextChoices):
        VERIFIED = "VERIFIED", "Verified"
        PARTIAL = "PARTIAL", "Partial"
        DISCOVERY_ONLY = "DISCOVERY_ONLY", "Discovery only"
        EXCLUDED = "EXCLUDED", "Excluded"

    institution = models.ForeignKey(
        Institution,
        on_delete=models.PROTECT,
        related_name="exhibitions",
    )
    title = models.CharField(max_length=500)
    start_date = models.DateField()
    end_date = models.DateField()
    venue = models.CharField(max_length=500)
    region_area = models.CharField(max_length=100)
    region_district = models.CharField(max_length=100)
    lifecycle = models.CharField(max_length=16, choices=Lifecycle.choices)
    official_url = models.URLField(max_length=2048)
    freshness = models.CharField(
        max_length=16,
        choices=Freshness.choices,
        default=Freshness.FRESH,
    )
    eligibility = models.CharField(
        max_length=20,
        choices=Eligibility.choices,
        default=Eligibility.VERIFIED,
    )
    last_verified_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-start_date", "title", "id")
        indexes = [
            models.Index(
                fields=("institution", "start_date", "end_date"),
                name="catalog_exhibition_match",
            )
        ]


class ExhibitionSourceLink(models.Model):
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.PROTECT,
        related_name="source_links",
    )
    source_id = models.CharField(max_length=128)
    source_record_id = models.CharField(max_length=255)
    latest_source_record = models.ForeignKey(
        SourceRecord,
        on_delete=models.PROTECT,
        related_name="canonical_links",
    )
    linked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("source_id", "source_record_id"),
                name="catalog_unique_source_identity",
            )
        ]


class FieldEvidence(models.Model):
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.PROTECT,
        related_name="field_evidence",
    )
    candidate = models.ForeignKey(
        ExhibitionCandidate,
        on_delete=models.PROTECT,
        related_name="field_evidence",
    )
    source_record = models.ForeignKey(
        SourceRecord,
        on_delete=models.PROTECT,
        related_name="field_evidence",
    )
    field_name = models.CharField(max_length=64)
    canonical_value = models.TextField()
    raw_value = models.JSONField(null=True, blank=True)
    adopted = models.BooleanField(default=False)
    decision_reason = models.CharField(max_length=64)
    verified_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("exhibition", "source_record", "field_name"),
                name="catalog_unique_field_evidence",
            )
        ]
        indexes = [
            models.Index(
                fields=("exhibition", "field_name", "adopted"),
                name="catalog_evidence_lookup",
            )
        ]


class SourceConflict(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        RESOLVED = "RESOLVED", "Resolved"

    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.PROTECT,
        related_name="source_conflicts",
    )
    field_name = models.CharField(max_length=64)
    canonical_value = models.TextField()
    candidate_value = models.TextField()
    candidate_source_record = models.ForeignKey(
        SourceRecord,
        on_delete=models.PROTECT,
        related_name="source_conflicts",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
    )
    resolution_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("exhibition", "field_name", "candidate_source_record"),
                name="catalog_unique_source_conflict",
            )
        ]


class DuplicateCandidate(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        DISTINCT = "DISTINCT", "Distinct"
        MERGED = "MERGED", "Merged"

    primary_exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.PROTECT,
        related_name="duplicate_candidates_primary",
    )
    related_exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.PROTECT,
        related_name="duplicate_candidates_related",
    )
    reason = models.CharField(max_length=64)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
    )
    resolution_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("primary_exhibition", "related_exhibition"),
                name="catalog_unique_duplicate_pair",
            )
        ]

from django.db import models

from backend.apps.sources.models import SourceRecord


class ExhibitionCandidate(models.Model):
    class Lifecycle(models.TextChoices):
        UPCOMING = "UPCOMING", "Upcoming"
        CURRENT = "CURRENT", "Current"
        ENDED = "ENDED", "Ended"
        CANCELED = "CANCELED", "Canceled"
        UNKNOWN = "UNKNOWN", "Unknown"

    class CoreResult(models.TextChoices):
        PASS = "PASS", "Pass"
        FAIL = "FAIL", "Fail"

    class Eligibility(models.TextChoices):
        VERIFIED = "VERIFIED", "Verified"
        EXCLUDED = "EXCLUDED", "Excluded"

    source_record = models.ForeignKey(
        SourceRecord,
        on_delete=models.PROTECT,
        related_name="quality_candidates",
    )
    rule_version = models.CharField(max_length=32)
    title = models.CharField(max_length=500, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    venue = models.CharField(max_length=500, null=True, blank=True)
    region_area = models.CharField(max_length=100, null=True, blank=True)
    region_district = models.CharField(max_length=100, null=True, blank=True)
    lifecycle = models.CharField(max_length=16, choices=Lifecycle.choices)
    official_url = models.URLField(max_length=2048, null=True, blank=True)
    core_result = models.CharField(max_length=8, choices=CoreResult.choices)
    eligibility = models.CharField(max_length=16, choices=Eligibility.choices)
    quality_issues = models.JSONField(default=list)
    quarantined = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("source_record", "rule_version"),
                name="quality_unique_record_rule",
            )
        ]

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from backend.apps.catalog.models import Exhibition
from backend.apps.sources.models import SourceRecord


class SearchDocument(models.Model):
    class ResultType(models.TextChoices):
        EXHIBITION = "EXHIBITION", "Exhibition"
        INSTITUTION = "INSTITUTION", "Institution"

    result_type = models.CharField(max_length=16, choices=ResultType.choices)
    object_id = models.PositiveBigIntegerField()
    title = models.CharField(max_length=500)
    subtitle = models.CharField(max_length=500, blank=True)
    keywords = models.TextField(blank=True)
    lifecycle = models.CharField(max_length=16, blank=True)
    region_area = models.CharField(max_length=100, blank=True)
    region_district = models.CharField(max_length=100, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    document_version = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("result_type", "title", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("result_type", "object_id"),
                name="discovery_unique_search_target",
            )
        ]
        indexes = [
            models.Index(
                fields=(
                    "result_type",
                    "lifecycle",
                    "region_area",
                    "region_district",
                ),
                name="discovery_search_filters",
            )
        ]


FEATURE_VALUE_VALIDATOR = RegexValidator(
    regex=r"^[A-Z0-9][A-Z0-9_:-]{0,63}$",
    message=(
        "Feature value must be a 1-64 character uppercase stable code."
    ),
)


class ContentFeatureSnapshot(models.Model):
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.PROTECT,
        related_name="content_feature_snapshots",
    )
    schema_version = models.CharField(max_length=32)
    is_current = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("exhibition_id", "-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("exhibition",),
                condition=models.Q(is_current=True),
                name="discovery_unique_current_feature_snapshot",
            )
        ]


class ContentFeatureAssertion(models.Model):
    class Axis(models.TextChoices):
        MEDIA_GROUP = "MEDIA_GROUP", "Media group"
        MEDIA_DETAIL = "MEDIA_DETAIL", "Media detail"
        THEME = "THEME", "Theme"
        MOOD = "MOOD", "Mood"
        EXPERIENCE = "EXPERIENCE", "Experience"
        SPACE_TYPE = "SPACE_TYPE", "Space type"
        EVENT_FORMAT = "EVENT_FORMAT", "Event format"

    class EvidenceKind(models.TextChoices):
        DIRECT = "DIRECT", "Direct"
        DERIVED = "DERIVED", "Derived"

    snapshot = models.ForeignKey(
        ContentFeatureSnapshot,
        on_delete=models.PROTECT,
        related_name="assertions",
    )
    axis = models.CharField(max_length=16, choices=Axis.choices)
    value = models.CharField(max_length=64, validators=(FEATURE_VALUE_VALIDATOR,))
    evidence_kind = models.CharField(max_length=16, choices=EvidenceKind.choices)
    source_record = models.ForeignKey(
        SourceRecord,
        on_delete=models.PROTECT,
        related_name="content_feature_assertions",
    )
    rule_version = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("snapshot_id", "axis", "value", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("snapshot", "axis", "value"),
                name="discovery_unique_snapshot_feature",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(evidence_kind="DIRECT", rule_version="")
                    | (
                        models.Q(evidence_kind="DERIVED")
                        & ~models.Q(rule_version="")
                    )
                ),
                name="discovery_feature_evidence_rule",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.evidence_kind == self.EvidenceKind.DIRECT and self.rule_version:
            errors["rule_version"] = "Direct evidence must not have a rule version."
        if (
            self.evidence_kind == self.EvidenceKind.DERIVED
            and not self.rule_version.strip()
        ):
            errors["rule_version"] = "Derived evidence requires a rule version."
        if self.source_record_id and self.snapshot_id:
            target_registry_id = self.snapshot.exhibition.institution.registry_id
            if self.source_record.institution_id != target_registry_id:
                errors["source_record"] = (
                    "SourceRecord institution must match the exhibition institution."
                )
        if errors:
            raise ValidationError(errors)

    def save(self, *args: object, **kwargs: object) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

from django.db import models


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

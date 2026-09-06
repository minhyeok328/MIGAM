from django.contrib import admin

from backend.apps.sources.admin import EvidenceAdmin

from . import models


@admin.register(models.Exhibition)
class ExhibitionAdmin(EvidenceAdmin):
    list_display = ("id", "title", "lifecycle", "freshness", "eligibility", "start_date", "end_date", "last_verified_at")
    list_filter = ("lifecycle", "freshness", "eligibility", "region_area")
    search_fields = ("title", "venue")


@admin.register(models.Institution)
class InstitutionAdmin(EvidenceAdmin):
    list_display = ("registry_id", "name", "region_area", "region_district")
    search_fields = ("registry_id", "name")


@admin.register(models.SourceConflict)
class SourceConflictAdmin(EvidenceAdmin):
    list_display = ("id", "field_name", "status", "created_at", "resolved_at")
    list_filter = ("status", "field_name")


@admin.register(models.DuplicateCandidate)
class DuplicateCandidateAdmin(EvidenceAdmin):
    list_display = ("id", "reason", "status", "created_at", "resolved_at")
    list_filter = ("status", "reason")


@admin.register(models.MediaRights)
class MediaRightsAdmin(EvidenceAdmin):
    list_display = ("id", "policy_status", "rights_holder", "license_name", "display_allowed", "is_current", "reviewed_at")
    list_filter = ("policy_status", "is_current", "display_allowed")


@admin.register(models.ChangeHistory)
class ChangeHistoryAdmin(EvidenceAdmin):
    list_display = ("id", "change_type", "field_name", "meaningful_for_promotion", "created_at")
    list_filter = ("change_type", "meaningful_for_promotion")


for model in (
    models.ExhibitionSourceLink, models.VerificationRecord, models.FieldEvidence,
    models.OperatingSchedule, models.PriceOption, models.ReservationInfo,
    models.VisitDuration, models.AccessibilityFact, models.SensoryNotice, models.MediaAsset,
    models.Artwork, models.ArtworkFeatureAssertion,
):
    admin.site.register(model, EvidenceAdmin)

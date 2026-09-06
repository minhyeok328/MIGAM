from django.contrib import admin

from backend.apps.sources.admin import EvidenceAdmin

from .models import ExhibitionCandidate


@admin.register(ExhibitionCandidate)
class ExhibitionCandidateAdmin(EvidenceAdmin):
    list_display = ("id", "title", "core_result", "eligibility", "quarantined", "rule_version")
    list_filter = ("core_result", "eligibility", "quarantined")
    search_fields = ("title", "venue")

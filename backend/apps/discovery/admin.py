from django.contrib import admin

from backend.apps.sources.admin import EvidenceAdmin

from .models import ContentFeatureAssertion, ContentFeatureSnapshot, SearchDocument


@admin.register(SearchDocument)
class SearchDocumentAdmin(EvidenceAdmin):
    list_display = ("id", "result_type", "object_id", "title", "document_version", "updated_at")
    list_filter = ("result_type",)
    search_fields = ("title",)


admin.site.register(ContentFeatureSnapshot, EvidenceAdmin)
admin.site.register(ContentFeatureAssertion, EvidenceAdmin)

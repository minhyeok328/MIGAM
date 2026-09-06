from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html_join

from . import models


def can_view_model(user, model):
    opts = model._meta
    return user.has_perm(f"{opts.app_label}.view_{opts.model_name}") or user.has_perm(
        f"{opts.app_label}.change_{opts.model_name}"
    )


class EvidenceAdmin(admin.ModelAdmin):
    """Domain services own mutations; Admin provides permission-aware evidence."""

    actions = None
    list_per_page = 50
    hidden_fields = frozenset({"payload", "raw_value", "error_message", "scope_evidence"})

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return can_view_model(request.user, self.model)

    def get_fields(self, request, obj=None):
        return tuple(
            field.name for field in self.model._meta.concrete_fields
            if not field.is_relation and field.name not in self.hidden_fields
        ) + ("related_records",)

    def get_readonly_fields(self, request, obj=None):
        return self.get_fields(request, obj)

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)
        if obj is not None:
            # Attach permissions to this request's object, never the shared ModelAdmin.
            obj._admin_visible_relations = frozenset(
                field.name for field in obj._meta.get_fields()
                if field.is_relation and field.related_model
                and can_view_model(request.user, field.related_model)
                and self.admin_site.is_registered(field.related_model)
            )
        return obj

    @admin.display(description="관련 증거")
    def related_records(self, obj):
        links = []
        visible = getattr(obj, "_admin_visible_relations", ())
        for field in obj._meta.concrete_fields:
            if field.name not in visible:
                continue
            target_id = getattr(obj, field.attname)
            if target_id is not None:
                opts = field.related_model._meta
                links.append((reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[target_id]), f"{field.name} #{target_id}"))
        for field in obj._meta.many_to_many:
            if field.name not in visible:
                continue
            opts = field.related_model._meta
            for target_id in getattr(obj, field.name).values_list("pk", flat=True)[:20]:
                links.append((reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[target_id]), f"{field.name} #{target_id}"))
        return format_html_join(" · ", '<a href="{}">{}</a>', links) if links else "—"


@admin.register(models.Source)
class SourceAdmin(EvidenceAdmin):
    list_display = ("registry_id", "name", "owner", "operation_status", "updated_at")
    list_filter = ("operation_status", "kind")
    search_fields = ("registry_id", "name", "owner")


@admin.register(models.InstitutionAllowlistEntry)
class InstitutionAllowlistEntryAdmin(EvidenceAdmin):
    list_display = ("registry_id", "name", "lifecycle", "health", "consecutive_final_failed_count", "priority_reverify_at")
    list_filter = ("lifecycle", "health")
    search_fields = ("registry_id", "name")


@admin.register(models.CollectionIssue)
class CollectionIssueAdmin(EvidenceAdmin):
    list_display = ("registry_id", "classification", "scope", "status", "field", "action", "updated_at")
    list_filter = ("classification", "scope", "status")
    search_fields = ("registry_id", "source_record_id", "field")


@admin.register(models.IngestionRun)
class IngestionRunAdmin(EvidenceAdmin):
    list_display = ("id", "command", "source_id", "status", "received_count", "verified_count", "started_at", "finished_at")
    list_filter = ("status", "qualification_mode", "command")
    search_fields = ("source_id",)


@admin.register(models.SourceRecord)
class SourceRecordAdmin(EvidenceAdmin):
    list_display = ("id", "source_id", "institution_id", "source_record_id", "last_seen_at")
    list_filter = ("source_id",)
    search_fields = ("source_id", "institution_id", "source_record_id")


@admin.register(models.InstitutionRunResult)
class InstitutionRunResultAdmin(EvidenceAdmin):
    list_display = ("id", "status", "received_count", "verified_count", "lifecycle_before", "lifecycle_after", "health_after", "finished_at")
    list_filter = ("status", "lifecycle_after", "health_after")


@admin.register(models.InstitutionQualificationRun)
class InstitutionQualificationRunAdmin(EvidenceAdmin):
    list_display = ("id", "status", "service_date", "target_count", "verified_count", "final_missing_core_target_count", "meaningful_change_count")
    list_filter = ("status", "service_date")


@admin.register(models.PromotionEvidence)
class PromotionEvidenceAdmin(EvidenceAdmin):
    list_display = ("id", "validation_started_at", "promoted_at", "decision_reason")


admin.site.register(models.IngestionObservation, EvidenceAdmin)
admin.site.site_header = "미감 운영"
admin.site.site_title = "미감 Admin"
admin.site.index_title = "운영 데이터와 증거"

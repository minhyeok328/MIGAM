import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("sources", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Source",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("registry_id", models.CharField(max_length=128, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("owner", models.CharField(max_length=255)),
                ("kind", models.CharField(max_length=64)),
                ("operation_status", models.CharField(choices=[("NORMAL", "Normal"), ("PAUSED", "Paused"), ("DISABLED", "Disabled")], default="NORMAL", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ("registry_id",)},
        ),
        migrations.CreateModel(
            name="InstitutionAllowlistEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("registry_id", models.CharField(max_length=128, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("region_area", models.CharField(blank=True, max_length=100)),
                ("region_district", models.CharField(blank=True, max_length=100)),
                ("lifecycle", models.CharField(choices=[("CANDIDATE", "Candidate"), ("PROVISIONAL", "Provisional"), ("ACTIVE", "Active"), ("SUSPENDED", "Suspended")], max_length=16)),
                ("health", models.CharField(choices=[("HEALTHY", "Healthy"), ("DEGRADED", "Degraded")], max_length=16)),
                ("health_changed_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("health_reasons", models.JSONField(default=list)),
                ("consecutive_final_failed_count", models.PositiveIntegerField(default=0)),
                ("priority_reverify_at", models.DateTimeField(blank=True, null=True)),
                ("priority_reverify_reason", models.TextField(blank=True)),
                ("promotion_validation_started_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="allowlist_entries", to="sources.source")),
            ],
            options={"ordering": ("registry_id",)},
        ),
        migrations.CreateModel(
            name="CollectionIssue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("registry_id", models.CharField(max_length=128, unique=True)),
                ("classification", models.CharField(choices=[("POLICY_BLOCK", "Policy block"), ("ACCESS_BLOCK", "Access block"), ("STRUCTURAL_CRITICAL", "Structural critical"), ("STRUCTURAL_OPTIONAL", "Structural optional"), ("RECORD_EXCEPTION", "Record exception")], max_length=32)),
                ("scope", models.CharField(choices=[("ENTRY", "Entry"), ("SOURCE", "Source")], max_length=16)),
                ("source_record_id", models.CharField(blank=True, max_length=255)),
                ("field", models.CharField(blank=True, max_length=128)),
                ("action", models.CharField(blank=True, max_length=64)),
                ("scope_evidence", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("OPEN", "Open"), ("RESOLVED", "Resolved")], default="OPEN", max_length=16)),
                ("first_seen_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("resolution_reason", models.TextField(blank=True)),
                ("institution", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="collection_issues", to="sources.institutionallowlistentry")),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="collection_issues", to="sources.source")),
            ],
            options={
                "ordering": ("registry_id",),
                "indexes": [models.Index(fields=["source", "status", "classification", "scope"], name="sources_issue_gate_lookup")],
                "constraints": [models.CheckConstraint(condition=Q(("scope", "SOURCE"), ("institution__isnull", False), _connector="OR"), name="sources_entry_issue_has_institution")],
            },
        ),
    ]

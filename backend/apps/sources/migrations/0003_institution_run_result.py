import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sources", "0002_operational_registry"),
    ]

    operations = [
        migrations.CreateModel(
            name="InstitutionRunResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("SUCCESS", "Success"), ("FAILED", "Failed")], max_length=16)),
                ("received_count", models.PositiveIntegerField(default=0)),
                ("verified_count", models.PositiveIntegerField(default=0)),
                ("quarantined_count", models.PositiveIntegerField(default=0)),
                ("retry_count", models.PositiveIntegerField(default=0)),
                ("issue_classifications", models.JSONField(default=list)),
                ("lifecycle_before", models.CharField(choices=[("CANDIDATE", "Candidate"), ("PROVISIONAL", "Provisional"), ("ACTIVE", "Active"), ("SUSPENDED", "Suspended")], max_length=16)),
                ("lifecycle_after", models.CharField(choices=[("CANDIDATE", "Candidate"), ("PROVISIONAL", "Provisional"), ("ACTIVE", "Active"), ("SUSPENDED", "Suspended")], max_length=16)),
                ("health_before", models.CharField(choices=[("HEALTHY", "Healthy"), ("DEGRADED", "Degraded")], max_length=16)),
                ("health_after", models.CharField(choices=[("HEALTHY", "Healthy"), ("DEGRADED", "Degraded")], max_length=16)),
                ("failed_count_before", models.PositiveIntegerField(default=0)),
                ("failed_count_after", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
                ("finished_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("ingestion_run", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="institution_results", to="sources.ingestionrun")),
                ("institution", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="run_results", to="sources.institutionallowlistentry")),
            ],
            options={
                "ordering": ("-finished_at", "-id"),
                "indexes": [models.Index(fields=["institution", "status", "finished_at"], name="sources_inst_result_lookup")],
                "constraints": [models.UniqueConstraint(fields=("ingestion_run", "institution"), name="sources_unique_run_institution_result")],
            },
        ),
    ]

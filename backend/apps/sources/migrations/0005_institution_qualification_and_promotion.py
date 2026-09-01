import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0003_change_history"),
        ("sources", "0004_lifecycle_evidence_and_retry_unknown"),
    ]

    operations = [
        migrations.AddField(
            model_name="ingestionrun",
            name="qualification_mode",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="institutionallowlistentry",
            name="qualification_target_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="institutionrunresult",
            name="approved_record_exception_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="institutionrunresult",
            name="completed_core_target_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.CreateModel(
            name="InstitutionQualificationRun",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("SUCCESS", "Success"), ("FAILED", "Failed")],
                        max_length=16,
                    ),
                ),
                ("finished_at", models.DateTimeField()),
                ("service_date", models.DateField()),
                ("retry_count", models.PositiveIntegerField(blank=True, null=True)),
                ("target_count", models.PositiveIntegerField(default=0)),
                ("received_count", models.PositiveIntegerField(default=0)),
                ("verified_count", models.PositiveIntegerField(default=0)),
                ("quarantined_count", models.PositiveIntegerField(default=0)),
                (
                    "approved_record_exception_count",
                    models.PositiveIntegerField(default=0),
                ),
                (
                    "completed_core_target_count",
                    models.PositiveIntegerField(default=0),
                ),
                (
                    "final_missing_core_target_count",
                    models.PositiveIntegerField(default=0),
                ),
                (
                    "structural_core_issue_count",
                    models.PositiveIntegerField(default=0),
                ),
                (
                    "policy_access_issue_count",
                    models.PositiveIntegerField(default=0),
                ),
                (
                    "source_operation_status",
                    models.CharField(
                        choices=[
                            ("NORMAL", "Normal"),
                            ("PAUSED", "Paused"),
                            ("DISABLED", "Disabled"),
                        ],
                        max_length=16,
                    ),
                ),
                (
                    "unresolved_conflict_count",
                    models.PositiveIntegerField(default=0),
                ),
                ("meaningful_change_count", models.PositiveIntegerField(default=0)),
                ("failure_reasons", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "institution",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="qualification_runs",
                        to="sources.institutionallowlistentry",
                    ),
                ),
                (
                    "institution_result",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="qualification_run",
                        to="sources.institutionrunresult",
                    ),
                ),
            ],
            options={
                "ordering": ("finished_at", "id"),
                "indexes": [
                    models.Index(
                        fields=["institution", "status", "finished_at"],
                        name="sources_qual_inst_result",
                    ),
                    models.Index(
                        fields=["institution", "service_date"],
                        name="sources_qual_inst_date",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="PromotionEvidence",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("validation_started_at", models.DateTimeField()),
                ("promoted_at", models.DateTimeField()),
                (
                    "source_operation_status",
                    models.CharField(
                        choices=[
                            ("NORMAL", "Normal"),
                            ("PAUSED", "Paused"),
                            ("DISABLED", "Disabled"),
                        ],
                        max_length=16,
                    ),
                ),
                (
                    "unresolved_conflict_count",
                    models.PositiveIntegerField(default=0),
                ),
                ("decision_reason", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "institution",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="promotion_evidence",
                        to="sources.institutionallowlistentry",
                    ),
                ),
                (
                    "last_qualification_run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="last_for_promotion_evidence",
                        to="sources.institutionqualificationrun",
                    ),
                ),
                (
                    "meaningful_change_history",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="promotion_evidence",
                        to="catalog.changehistory",
                    ),
                ),
                (
                    "qualification_runs",
                    models.ManyToManyField(
                        related_name="promotion_evidence",
                        to="sources.institutionqualificationrun",
                    ),
                ),
            ],
            options={
                "ordering": ("-promoted_at", "-id"),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("institution", "validation_started_at"),
                        name="sources_unique_promotion_cycle",
                    )
                ],
            },
        ),
    ]

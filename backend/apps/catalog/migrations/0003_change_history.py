import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_verification_record"),
        ("sources", "0004_lifecycle_evidence_and_retry_unknown"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChangeHistory",
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
                    "change_type",
                    models.CharField(
                        choices=[
                            ("CREATED", "Created"),
                            ("FIELD_CHANGED", "Field changed"),
                        ],
                        max_length=32,
                    ),
                ),
                ("field_name", models.CharField(blank=True, max_length=64)),
                ("old_value", models.JSONField(blank=True, null=True)),
                ("new_value", models.JSONField(blank=True, null=True)),
                ("rule_version", models.CharField(max_length=32)),
                ("meaningful_for_promotion", models.BooleanField(default=False)),
                (
                    "meaningful_type",
                    models.CharField(
                        choices=[
                            ("NONE", "None"),
                            ("NEW_EXHIBITION", "New exhibition"),
                            ("END_DATE_CHANGED", "End date changed"),
                            ("VENUE_CHANGED", "Venue changed"),
                            ("CANCELED", "Canceled"),
                        ],
                        default="NONE",
                        max_length=32,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "candidate",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="change_history",
                        to="data_quality.exhibitioncandidate",
                    ),
                ),
                (
                    "exhibition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="change_history",
                        to="catalog.exhibition",
                    ),
                ),
                (
                    "ingestion_run",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="canonical_changes",
                        to="sources.ingestionrun",
                    ),
                ),
                (
                    "source_record",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="change_history",
                        to="sources.sourcerecord",
                    ),
                ),
            ],
            options={
                "ordering": ("created_at", "id"),
                "indexes": [
                    models.Index(
                        fields=["ingestion_run", "meaningful_for_promotion"],
                        name="catalog_change_run_meaningful",
                    )
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=(
                            "ingestion_run",
                            "exhibition",
                            "source_record",
                            "change_type",
                            "field_name",
                        ),
                        name="catalog_unique_canonical_change",
                    )
                ],
            },
        ),
    ]

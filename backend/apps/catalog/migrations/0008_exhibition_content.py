import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0007_artwork"),
        ("sources", "0005_institution_qualification_and_promotion"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExhibitionContent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_record_hash", models.CharField(max_length=64)),
                ("canonical_fingerprint", models.CharField(max_length=64)),
                ("review_hash", models.CharField(max_length=64, unique=True)),
                ("introduction", models.TextField(max_length=2000)),
                ("highlights", models.JSONField(blank=True, default=list)),
                ("visit_notes", models.JSONField(blank=True, default=list)),
                ("official_url", models.URLField(max_length=2048, validators=[django.core.validators.URLValidator(schemes=("https",))])),
                ("source_owner", models.CharField(max_length=255)),
                ("evidence_notes", models.TextField(max_length=2000)),
                ("reviewed_at", models.DateTimeField()),
                ("expires_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("exhibition", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="content_snapshots", to="catalog.exhibition")),
                ("source_record", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="exhibition_content", to="sources.sourcerecord")),
            ],
            options={
                "ordering": ("-reviewed_at", "-id"),
                "indexes": [models.Index(fields=["exhibition", "reviewed_at"], name="catalog_content_lookup")],
                "constraints": [models.CheckConstraint(condition=models.Q(expires_at__gt=models.F("reviewed_at")), name="catalog_content_valid_period")],
            },
        ),
    ]

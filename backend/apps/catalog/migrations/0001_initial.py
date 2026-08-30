import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("data_quality", "0001_initial"),
        ("sources", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Institution",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("registry_id", models.CharField(max_length=128, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("region_area", models.CharField(blank=True, max_length=100)),
                ("region_district", models.CharField(blank=True, max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ("registry_id",)},
        ),
        migrations.CreateModel(
            name="Exhibition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=500)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("venue", models.CharField(max_length=500)),
                ("region_area", models.CharField(max_length=100)),
                ("region_district", models.CharField(max_length=100)),
                ("lifecycle", models.CharField(choices=[("UPCOMING", "Upcoming"), ("CURRENT", "Current"), ("ENDED", "Ended"), ("CANCELED", "Canceled"), ("UNKNOWN", "Unknown")], max_length=16)),
                ("official_url", models.URLField(max_length=2048)),
                ("freshness", models.CharField(choices=[("FRESH", "Fresh"), ("STALE", "Stale"), ("UNVERIFIED", "Unverified")], default="FRESH", max_length=16)),
                ("eligibility", models.CharField(choices=[("VERIFIED", "Verified"), ("PARTIAL", "Partial"), ("DISCOVERY_ONLY", "Discovery only"), ("EXCLUDED", "Excluded")], default="VERIFIED", max_length=20)),
                ("last_verified_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("institution", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="exhibitions", to="catalog.institution")),
            ],
            options={"ordering": ("-start_date", "title", "id")},
        ),
        migrations.CreateModel(
            name="DuplicateCandidate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.CharField(max_length=64)),
                ("status", models.CharField(choices=[("OPEN", "Open"), ("DISTINCT", "Distinct"), ("MERGED", "Merged")], default="OPEN", max_length=16)),
                ("resolution_reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("primary_exhibition", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="duplicate_candidates_primary", to="catalog.exhibition")),
                ("related_exhibition", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="duplicate_candidates_related", to="catalog.exhibition")),
            ],
        ),
        migrations.CreateModel(
            name="ExhibitionSourceLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_id", models.CharField(max_length=128)),
                ("source_record_id", models.CharField(max_length=255)),
                ("linked_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("exhibition", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="source_links", to="catalog.exhibition")),
                ("latest_source_record", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="canonical_links", to="sources.sourcerecord")),
            ],
        ),
        migrations.CreateModel(
            name="FieldEvidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("field_name", models.CharField(max_length=64)),
                ("canonical_value", models.TextField()),
                ("raw_value", models.JSONField(blank=True, null=True)),
                ("adopted", models.BooleanField(default=False)),
                ("decision_reason", models.CharField(max_length=64)),
                ("verified_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("candidate", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="field_evidence", to="data_quality.exhibitioncandidate")),
                ("exhibition", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="field_evidence", to="catalog.exhibition")),
                ("source_record", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="field_evidence", to="sources.sourcerecord")),
            ],
        ),
        migrations.CreateModel(
            name="SourceConflict",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("field_name", models.CharField(max_length=64)),
                ("canonical_value", models.TextField()),
                ("candidate_value", models.TextField()),
                ("status", models.CharField(choices=[("OPEN", "Open"), ("RESOLVED", "Resolved")], default="OPEN", max_length=16)),
                ("resolution_reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("candidate_source_record", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="source_conflicts", to="sources.sourcerecord")),
                ("exhibition", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="source_conflicts", to="catalog.exhibition")),
            ],
        ),
        migrations.AddIndex(
            model_name="exhibition",
            index=models.Index(fields=["institution", "start_date", "end_date"], name="catalog_exhibition_match"),
        ),
        migrations.AddConstraint(
            model_name="duplicatecandidate",
            constraint=models.UniqueConstraint(fields=("primary_exhibition", "related_exhibition"), name="catalog_unique_duplicate_pair"),
        ),
        migrations.AddConstraint(
            model_name="exhibitionsourcelink",
            constraint=models.UniqueConstraint(fields=("source_id", "source_record_id"), name="catalog_unique_source_identity"),
        ),
        migrations.AddIndex(
            model_name="fieldevidence",
            index=models.Index(fields=["exhibition", "field_name", "adopted"], name="catalog_evidence_lookup"),
        ),
        migrations.AddConstraint(
            model_name="fieldevidence",
            constraint=models.UniqueConstraint(fields=("exhibition", "source_record", "field_name"), name="catalog_unique_field_evidence"),
        ),
        migrations.AddConstraint(
            model_name="sourceconflict",
            constraint=models.UniqueConstraint(fields=("exhibition", "field_name", "candidate_source_record"), name="catalog_unique_source_conflict"),
        ),
    ]

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [("sources", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="ExhibitionCandidate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rule_version", models.CharField(max_length=32)),
                ("title", models.CharField(blank=True, max_length=500, null=True)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("venue", models.CharField(blank=True, max_length=500, null=True)),
                ("region_area", models.CharField(blank=True, max_length=100, null=True)),
                ("region_district", models.CharField(blank=True, max_length=100, null=True)),
                ("lifecycle", models.CharField(choices=[("UPCOMING", "Upcoming"), ("CURRENT", "Current"), ("ENDED", "Ended"), ("CANCELED", "Canceled"), ("UNKNOWN", "Unknown")], max_length=16)),
                ("official_url", models.URLField(blank=True, max_length=2048, null=True)),
                ("core_result", models.CharField(choices=[("PASS", "Pass"), ("FAIL", "Fail")], max_length=8)),
                ("eligibility", models.CharField(choices=[("VERIFIED", "Verified"), ("EXCLUDED", "Excluded")], max_length=16)),
                ("quality_issues", models.JSONField(default=list)),
                ("quarantined", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("source_record", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="quality_candidates", to="sources.sourcerecord")),
            ],
        ),
        migrations.AddConstraint(
            model_name="exhibitioncandidate",
            constraint=models.UniqueConstraint(fields=("source_record", "rule_version"), name="quality_unique_record_rule"),
        ),
    ]

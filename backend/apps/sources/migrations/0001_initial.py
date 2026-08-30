import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="IngestionRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("command", models.CharField(max_length=64)),
                ("source_id", models.CharField(blank=True, max_length=128)),
                ("status", models.CharField(choices=[("RUNNING", "Running"), ("SUCCESS", "Success"), ("FAILED", "Failed")], default="RUNNING", max_length=16)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("received_count", models.PositiveIntegerField(default=0)),
                ("verified_count", models.PositiveIntegerField(default=0)),
                ("excluded_count", models.PositiveIntegerField(default=0)),
                ("quarantined_count", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
            ],
            options={"ordering": ("-started_at", "-id")},
        ),
        migrations.CreateModel(
            name="SourceRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_id", models.CharField(max_length=128)),
                ("institution_id", models.CharField(max_length=128)),
                ("source_record_id", models.CharField(max_length=255)),
                ("source_owner", models.CharField(max_length=255)),
                ("payload", models.JSONField()),
                ("content_hash", models.CharField(max_length=64)),
                ("first_seen_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="IngestionObservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("observed_at", models.DateTimeField(auto_now_add=True)),
                ("ingestion_run", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="observations", to="sources.ingestionrun")),
                ("source_record", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="observations", to="sources.sourcerecord")),
            ],
        ),
        migrations.AddConstraint(
            model_name="sourcerecord",
            constraint=models.UniqueConstraint(fields=("source_id", "source_record_id", "content_hash"), name="sources_unique_record_version"),
        ),
        migrations.AddIndex(
            model_name="sourcerecord",
            index=models.Index(fields=["source_id", "source_record_id"], name="sources_record_lookup"),
        ),
        migrations.AddConstraint(
            model_name="ingestionobservation",
            constraint=models.UniqueConstraint(fields=("ingestion_run", "source_record"), name="sources_unique_run_observation"),
        ),
    ]

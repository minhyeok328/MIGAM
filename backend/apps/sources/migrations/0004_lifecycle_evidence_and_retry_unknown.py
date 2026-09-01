import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sources", "0003_institution_run_result"),
    ]

    operations = [
        migrations.AddField(
            model_name="institutionallowlistentry",
            name="lifecycle_change_reason",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="institutionallowlistentry",
            name="lifecycle_changed_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="institutionallowlistentry",
            name="lifecycle_changed_by",
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name="institutionallowlistentry",
            name="suspension_reason",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="institutionrunresult",
            name="retry_count",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]

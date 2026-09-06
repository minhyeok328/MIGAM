from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0005_operating_schedule")]

    operations = [
        migrations.AddField(
            model_name="priceoption",
            name="rule_version",
            field=models.CharField(blank=True, max_length=64),
        ),
    ]

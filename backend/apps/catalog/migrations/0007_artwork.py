import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0006_priceoption_rule_version"),
        ("sources", "0005_institution_qualification_and_promotion"),
    ]

    operations = [
        migrations.CreateModel(
            name="Artwork",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_id", models.CharField(max_length=128)),
                ("source_artwork_id", models.CharField(max_length=255)),
                ("title", models.CharField(max_length=500)),
                ("creator_name", models.CharField(max_length=255)),
                ("creator_official_id", models.CharField(blank=True, max_length=255)),
                ("creator_state", models.CharField(choices=[("KNOWN", "Known"), ("UNKNOWN", "Officially unknown")], max_length=16)),
                ("production_year", models.CharField(max_length=100)),
                ("medium", models.CharField(max_length=500)),
                ("culture_state", models.CharField(choices=[("CONFIRMED", "Confirmed"), ("UNKNOWN", "Unknown")], default="UNKNOWN", max_length=16)),
                ("cultural_context", models.CharField(blank=True, max_length=255)),
                ("is_korean", models.BooleanField(blank=True, null=True)),
                ("official_url", models.URLField(max_length=2048, validators=[django.core.validators.URLValidator(schemes=("https",))])),
                ("last_verified_at", models.DateTimeField(blank=True, null=True)),
                ("eligibility", models.CharField(choices=[("UNVERIFIED", "Unverified"), ("VERIFIED", "Verified"), ("EXCLUDED", "Excluded"), ("DEMO", "Fictional demo only")], default="UNVERIFIED", max_length=16)),
                ("is_demo", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("collection_institution", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="artworks", to="catalog.institution")),
                ("source_record", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="artworks", to="sources.sourcerecord")),
            ],
            options={"ordering": ("id",)},
        ),
        migrations.CreateModel(
            name="ArtworkFeatureAssertion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("axis", models.CharField(choices=[("MEDIA_GROUP", "Media group"), ("MOOD", "Mood")], max_length=16)),
                ("value", models.CharField(max_length=64)),
                ("evidence_kind", models.CharField(choices=[("DIRECT", "Direct")], default="DIRECT", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("artwork", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="feature_assertions", to="catalog.artwork")),
                ("source_record", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="artwork_feature_assertions", to="sources.sourcerecord")),
            ],
            options={"ordering": ("artwork_id", "axis", "value", "id")},
        ),
        migrations.AddConstraint(
            model_name="artwork",
            constraint=models.UniqueConstraint(fields=("source_id", "source_artwork_id"), name="catalog_unique_artwork_identity"),
        ),
        migrations.AddConstraint(
            model_name="artwork",
            constraint=models.CheckConstraint(condition=~models.Q(creator_state="UNKNOWN") | models.Q(creator_official_id=""), name="catalog_artwork_unknown_creator"),
        ),
        migrations.AddConstraint(
            model_name="artwork",
            constraint=models.CheckConstraint(condition=~models.Q(culture_state="UNKNOWN") | models.Q(cultural_context="", is_korean__isnull=True), name="catalog_artwork_unknown_culture"),
        ),
        migrations.AddConstraint(
            model_name="artwork",
            constraint=models.CheckConstraint(condition=~models.Q(eligibility="DEMO") | models.Q(is_demo=True), name="catalog_artwork_demo_flag"),
        ),
        migrations.AddConstraint(
            model_name="artworkfeatureassertion",
            constraint=models.UniqueConstraint(fields=("artwork", "axis", "value"), name="catalog_unique_artwork_feature"),
        ),
    ]

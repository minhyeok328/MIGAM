from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0004_visit_information_and_media_rights"),
    ]

    operations = [
        migrations.CreateModel(
            name="SearchDocument",
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
                    "result_type",
                    models.CharField(
                        choices=[
                            ("EXHIBITION", "Exhibition"),
                            ("INSTITUTION", "Institution"),
                        ],
                        max_length=16,
                    ),
                ),
                ("object_id", models.PositiveBigIntegerField()),
                ("title", models.CharField(max_length=500)),
                ("subtitle", models.CharField(blank=True, max_length=500)),
                ("keywords", models.TextField(blank=True)),
                ("lifecycle", models.CharField(blank=True, max_length=16)),
                ("region_area", models.CharField(blank=True, max_length=100)),
                (
                    "region_district",
                    models.CharField(blank=True, max_length=100),
                ),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("document_version", models.CharField(max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ("result_type", "title", "id"),
                "indexes": [
                    models.Index(
                        fields=[
                            "result_type",
                            "lifecycle",
                            "region_area",
                            "region_district",
                        ],
                        name="discovery_search_filters",
                    )
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("result_type", "object_id"),
                        name="discovery_unique_search_target",
                    )
                ],
            },
        ),
        migrations.RunSQL(
            sql="""
                CREATE VIRTUAL TABLE discovery_searchdocument_fts USING fts5(
                    title,
                    subtitle,
                    keywords,
                    content='discovery_searchdocument',
                    content_rowid='id',
                    tokenize='unicode61 remove_diacritics 2'
                )
            """,
            reverse_sql="DROP TABLE IF EXISTS discovery_searchdocument_fts",
        ),
        migrations.RunSQL(
            sql="""
                CREATE TRIGGER discovery_searchdocument_fts_insert
                AFTER INSERT ON discovery_searchdocument
                BEGIN
                    INSERT INTO discovery_searchdocument_fts(
                        rowid, title, subtitle, keywords
                    ) VALUES (new.id, new.title, new.subtitle, new.keywords);
                END
            """,
            reverse_sql=(
                "DROP TRIGGER IF EXISTS discovery_searchdocument_fts_insert"
            ),
        ),
        migrations.RunSQL(
            sql="""
                CREATE TRIGGER discovery_searchdocument_fts_delete
                AFTER DELETE ON discovery_searchdocument
                BEGIN
                    INSERT INTO discovery_searchdocument_fts(
                        discovery_searchdocument_fts,
                        rowid,
                        title,
                        subtitle,
                        keywords
                    ) VALUES (
                        'delete', old.id, old.title, old.subtitle, old.keywords
                    );
                END
            """,
            reverse_sql=(
                "DROP TRIGGER IF EXISTS discovery_searchdocument_fts_delete"
            ),
        ),
        migrations.RunSQL(
            sql="""
                CREATE TRIGGER discovery_searchdocument_fts_update
                AFTER UPDATE ON discovery_searchdocument
                BEGIN
                    INSERT INTO discovery_searchdocument_fts(
                        discovery_searchdocument_fts,
                        rowid,
                        title,
                        subtitle,
                        keywords
                    ) VALUES (
                        'delete', old.id, old.title, old.subtitle, old.keywords
                    );
                    INSERT INTO discovery_searchdocument_fts(
                        rowid, title, subtitle, keywords
                    ) VALUES (new.id, new.title, new.subtitle, new.keywords);
                END
            """,
            reverse_sql=(
                "DROP TRIGGER IF EXISTS discovery_searchdocument_fts_update"
            ),
        ),
    ]

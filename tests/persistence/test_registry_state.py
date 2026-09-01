from importlib import import_module, util
from pathlib import Path

from django.test import TestCase

from backend.data_pipeline.registry import SourceRegistry


ROOT = Path(__file__).resolve().parents[2]


class RegistryStateTests(TestCase):
    def feature(self) -> tuple[object, object, object, object]:
        source_models = import_module("backend.apps.sources.models")
        for model_name in ("Source", "InstitutionAllowlistEntry", "CollectionIssue"):
            self.assertTrue(
                hasattr(source_models, model_name),
                f"sources.{model_name} model is missing",
            )
        self.assertIsNotNone(
            util.find_spec("backend.data_pipeline.registry_state"),
            "registry_state service is missing",
        )
        registry_state = import_module("backend.data_pipeline.registry_state")
        return (
            source_models.Source,
            source_models.InstitutionAllowlistEntry,
            source_models.CollectionIssue,
            registry_state.sync_registry_state,
        )

    def test_bootstraps_the_approved_registry_into_operational_models(self) -> None:
        Source, InstitutionAllowlistEntry, CollectionIssue, synchronize = (
            self.feature()
        )
        registry = SourceRegistry.load(ROOT / "sources.yaml")

        synchronize(registry)

        self.assertEqual(Source.objects.count(), 3)
        self.assertEqual(InstitutionAllowlistEntry.objects.count(), 5)
        self.assertEqual(CollectionIssue.objects.count(), 1)
        entry = InstitutionAllowlistEntry.objects.get(registry_id="nfm-seoul-main")
        self.assertEqual(entry.source.registry_id, "kcisa-cultureinfo")
        self.assertEqual(entry.lifecycle, "PROVISIONAL")
        self.assertEqual(entry.health, "HEALTHY")
        issue = CollectionIssue.objects.get(
            registry_id="nfm-348222-missing-official-url"
        )
        self.assertEqual(issue.classification, "RECORD_EXCEPTION")
        self.assertEqual(issue.scope, "ENTRY")
        self.assertEqual(issue.institution, entry)

    def test_repeated_bootstrap_preserves_mutable_operational_state(self) -> None:
        Source, InstitutionAllowlistEntry, CollectionIssue, synchronize = (
            self.feature()
        )
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        synchronize(registry)
        source = Source.objects.get(registry_id="kcisa-cultureinfo")
        source.operation_status = "PAUSED"
        source.save(update_fields=("operation_status", "updated_at"))
        entry = InstitutionAllowlistEntry.objects.get(registry_id="nfm-seoul-main")
        entry.lifecycle = "SUSPENDED"
        entry.health = "DEGRADED"
        entry.consecutive_final_failed_count = 2
        entry.save(
            update_fields=(
                "lifecycle",
                "health",
                "consecutive_final_failed_count",
                "updated_at",
            )
        )
        issue = CollectionIssue.objects.get(
            registry_id="nfm-348222-missing-official-url"
        )
        issue.status = "RESOLVED"
        issue.save(update_fields=("status", "updated_at"))

        synchronize(registry)

        source.refresh_from_db()
        entry.refresh_from_db()
        issue.refresh_from_db()
        self.assertEqual(source.operation_status, "PAUSED")
        self.assertEqual(entry.lifecycle, "SUSPENDED")
        self.assertEqual(entry.health, "DEGRADED")
        self.assertEqual(entry.consecutive_final_failed_count, 2)
        self.assertEqual(issue.status, "RESOLVED")

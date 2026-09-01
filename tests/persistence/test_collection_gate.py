from importlib import import_module, util
from pathlib import Path

from django.test import TestCase

from backend.apps.sources.models import (
    CollectionIssue,
    InstitutionAllowlistEntry,
    Source,
)
from backend.data_pipeline.registry import SourceRegistry
from backend.data_pipeline.registry_state import sync_registry_state


ROOT = Path(__file__).resolve().parents[2]
SEMA_SOURCE = "seoul-oa-15323-sema"
CULTURE_SOURCE = "kcisa-cultureinfo"


class CollectionGateTests(TestCase):
    def setUp(self) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        sync_registry_state(registry)

    def feature(self) -> tuple[object, type[Exception]]:
        self.assertIsNotNone(
            util.find_spec("backend.data_pipeline.collection_gate"),
            "collection_gate service is missing",
        )
        module = import_module("backend.data_pipeline.collection_gate")
        self.assertTrue(hasattr(module, "select_collectible_entries"))
        self.assertTrue(hasattr(module, "CollectionGateError"))
        return module.select_collectible_entries, module.CollectionGateError

    def test_provisional_active_and_degraded_entries_remain_collectible(self) -> None:
        select_entries, _ = self.feature()
        provisional = InstitutionAllowlistEntry.objects.get(
            registry_id="sema-seoseoul"
        )
        provisional.health = InstitutionAllowlistEntry.Health.DEGRADED
        provisional.save(update_fields=("health", "updated_at"))
        active = InstitutionAllowlistEntry.objects.get(registry_id="sema-photo")
        active.lifecycle = InstitutionAllowlistEntry.Lifecycle.ACTIVE
        active.save(update_fields=("lifecycle", "updated_at"))

        entries = select_entries(source_ids=(SEMA_SOURCE,))

        self.assertEqual(
            {entry.registry_id for entry in entries},
            {"sema-seoseoul", "sema-photo"},
        )

    def test_candidate_and_suspended_entries_are_rejected(self) -> None:
        select_entries, CollectionGateError = self.feature()
        candidate = InstitutionAllowlistEntry.objects.get(
            registry_id="sema-seoseoul"
        )
        candidate.lifecycle = InstitutionAllowlistEntry.Lifecycle.CANDIDATE
        candidate.save(update_fields=("lifecycle", "updated_at"))
        suspended = InstitutionAllowlistEntry.objects.get(registry_id="sema-photo")
        suspended.lifecycle = InstitutionAllowlistEntry.Lifecycle.SUSPENDED
        suspended.save(update_fields=("lifecycle", "updated_at"))

        with self.assertRaisesRegex(CollectionGateError, "no collectible institution"):
            select_entries(source_ids=(SEMA_SOURCE,))

    def test_non_normal_source_is_rejected(self) -> None:
        select_entries, CollectionGateError = self.feature()
        source = Source.objects.get(registry_id=SEMA_SOURCE)
        source.operation_status = Source.OperationStatus.PAUSED
        source.save(update_fields=("operation_status", "updated_at"))

        with self.assertRaisesRegex(CollectionGateError, "source is not normal"):
            select_entries(source_ids=(SEMA_SOURCE,))

    def test_entry_critical_blocks_only_the_affected_shared_source_entry(self) -> None:
        select_entries, _ = self.feature()
        source = Source.objects.get(registry_id=SEMA_SOURCE)
        blocked = InstitutionAllowlistEntry.objects.get(
            registry_id="sema-seoseoul"
        )
        CollectionIssue.objects.create(
            registry_id="test-seoseoul-critical",
            classification=CollectionIssue.Classification.STRUCTURAL_CRITICAL,
            scope=CollectionIssue.Scope.ENTRY,
            source=source,
            institution=blocked,
            status=CollectionIssue.Status.OPEN,
        )

        entries = select_entries(source_ids=(SEMA_SOURCE,))

        self.assertEqual(
            tuple(entry.registry_id for entry in entries),
            ("sema-photo",),
        )

    def test_source_critical_blocks_every_connected_entry(self) -> None:
        select_entries, CollectionGateError = self.feature()
        source = Source.objects.get(registry_id=SEMA_SOURCE)
        CollectionIssue.objects.create(
            registry_id="test-sema-source-critical",
            classification=CollectionIssue.Classification.POLICY_BLOCK,
            scope=CollectionIssue.Scope.SOURCE,
            source=source,
            status=CollectionIssue.Status.OPEN,
        )

        with self.assertRaisesRegex(CollectionGateError, "source critical"):
            select_entries(source_ids=(SEMA_SOURCE,))

    def test_resolved_critical_and_open_record_exception_do_not_block(self) -> None:
        select_entries, _ = self.feature()
        source = Source.objects.get(registry_id=CULTURE_SOURCE)
        CollectionIssue.objects.create(
            registry_id="test-resolved-critical",
            classification=CollectionIssue.Classification.ACCESS_BLOCK,
            scope=CollectionIssue.Scope.SOURCE,
            source=source,
            status=CollectionIssue.Status.RESOLVED,
        )

        entries = select_entries(source_ids=(CULTURE_SOURCE,))

        self.assertEqual(
            {entry.registry_id for entry in entries},
            {"suma-haenggung", "nfm-seoul-main"},
        )

from datetime import datetime, timezone as datetime_timezone
from importlib import import_module, util
from pathlib import Path

from django.test import TestCase

from backend.apps.sources.models import (
    CollectionIssue,
    IngestionRun,
    InstitutionAllowlistEntry,
)
from backend.data_pipeline.registry import SourceRegistry
from backend.data_pipeline.registry_state import sync_registry_state
from backend.data_pipeline.collection_gate import CollectionGateError


ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 9, 1, 3, 0, tzinfo=datetime_timezone.utc)


class InstitutionRunTests(TestCase):
    def setUp(self) -> None:
        registry = SourceRegistry.load(ROOT / "sources.yaml")
        sync_registry_state(registry)
        self.entry = InstitutionAllowlistEntry.objects.get(
            registry_id="sejong-center-main-exhibition"
        )

    def feature(self) -> tuple[object, object]:
        source_models = import_module("backend.apps.sources.models")
        self.assertTrue(
            hasattr(source_models, "InstitutionRunResult"),
            "sources.InstitutionRunResult model is missing",
        )
        self.assertIsNotNone(
            util.find_spec("backend.data_pipeline.institution_runs"),
            "institution_runs service is missing",
        )
        module = import_module("backend.data_pipeline.institution_runs")
        return source_models.InstitutionRunResult, module.record_institution_result

    def new_run(self) -> IngestionRun:
        return IngestionRun.objects.create(command="test-institution-result")

    def test_active_success_resets_failure_count_and_recovers_health(self) -> None:
        InstitutionRunResult, record_result = self.feature()
        self.entry.lifecycle = InstitutionAllowlistEntry.Lifecycle.ACTIVE
        self.entry.health = InstitutionAllowlistEntry.Health.DEGRADED
        self.entry.consecutive_final_failed_count = 1
        self.entry.save(
            update_fields=(
                "lifecycle",
                "health",
                "consecutive_final_failed_count",
                "updated_at",
            )
        )

        result = record_result(
            self.new_run(),
            self.entry,
            status=InstitutionRunResult.Status.SUCCESS,
            received_count=3,
            verified_count=3,
            finished_at=NOW,
        )

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.lifecycle, InstitutionAllowlistEntry.Lifecycle.ACTIVE)
        self.assertEqual(self.entry.health, InstitutionAllowlistEntry.Health.HEALTHY)
        self.assertEqual(self.entry.consecutive_final_failed_count, 0)
        self.assertEqual(result.health_before, "DEGRADED")
        self.assertEqual(result.health_after, "HEALTHY")
        self.assertEqual(result.failed_count_before, 1)
        self.assertEqual(result.failed_count_after, 0)
        self.assertEqual(result.received_count, 3)

    def test_two_distinct_active_failures_suspend_the_entry(self) -> None:
        InstitutionRunResult, record_result = self.feature()
        self.entry.lifecycle = InstitutionAllowlistEntry.Lifecycle.ACTIVE
        self.entry.save(update_fields=("lifecycle", "updated_at"))

        first = record_result(
            self.new_run(),
            self.entry,
            status=InstitutionRunResult.Status.FAILED,
            error_message="first failure",
            finished_at=NOW,
        )
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.lifecycle, InstitutionAllowlistEntry.Lifecycle.ACTIVE)
        self.assertEqual(self.entry.health, InstitutionAllowlistEntry.Health.DEGRADED)
        self.assertEqual(self.entry.consecutive_final_failed_count, 1)
        self.assertEqual(first.failed_count_after, 1)

        second = record_result(
            self.new_run(),
            self.entry,
            status=InstitutionRunResult.Status.FAILED,
            error_message="second failure",
            finished_at=NOW,
        )

        self.entry.refresh_from_db()
        self.assertEqual(
            self.entry.lifecycle,
            InstitutionAllowlistEntry.Lifecycle.SUSPENDED,
        )
        self.assertEqual(self.entry.consecutive_final_failed_count, 2)
        self.assertEqual(
            self.entry.lifecycle_change_reason,
            "CONSECUTIVE_FINAL_FAILED",
        )
        self.assertEqual(self.entry.lifecycle_changed_at, NOW)
        self.assertEqual(self.entry.lifecycle_changed_by, "SYSTEM")
        self.assertEqual(
            self.entry.suspension_reason,
            "CONSECUTIVE_FINAL_FAILED",
        )
        self.assertEqual(second.failed_count_before, 1)
        self.assertEqual(second.failed_count_after, 2)

    def test_first_active_failure_with_entry_critical_suspends_immediately(self) -> None:
        InstitutionRunResult, record_result = self.feature()
        self.entry.lifecycle = InstitutionAllowlistEntry.Lifecycle.ACTIVE
        self.entry.save(update_fields=("lifecycle", "updated_at"))
        CollectionIssue.objects.create(
            registry_id="test-entry-critical",
            classification=CollectionIssue.Classification.STRUCTURAL_CRITICAL,
            scope=CollectionIssue.Scope.ENTRY,
            source=self.entry.source,
            institution=self.entry,
            status=CollectionIssue.Status.OPEN,
        )

        result = record_result(
            self.new_run(),
            self.entry,
            status=InstitutionRunResult.Status.FAILED,
            finished_at=NOW,
        )

        self.entry.refresh_from_db()
        self.assertEqual(
            self.entry.lifecycle,
            InstitutionAllowlistEntry.Lifecycle.SUSPENDED,
        )
        self.assertEqual(self.entry.consecutive_final_failed_count, 1)
        self.assertEqual(self.entry.lifecycle_change_reason, "OPEN_CRITICAL")
        self.assertEqual(self.entry.lifecycle_changed_at, NOW)
        self.assertEqual(self.entry.lifecycle_changed_by, "SYSTEM")
        self.assertEqual(
            self.entry.suspension_reason,
            "OPEN_CRITICAL:test-entry-critical",
        )
        self.assertEqual(result.lifecycle_after, "SUSPENDED")

    def test_first_active_failure_with_source_critical_suspends_immediately(self) -> None:
        InstitutionRunResult, record_result = self.feature()
        self.entry.lifecycle = InstitutionAllowlistEntry.Lifecycle.ACTIVE
        self.entry.save(update_fields=("lifecycle", "updated_at"))
        CollectionIssue.objects.create(
            registry_id="test-source-critical",
            classification=CollectionIssue.Classification.POLICY_BLOCK,
            scope=CollectionIssue.Scope.SOURCE,
            source=self.entry.source,
            status=CollectionIssue.Status.OPEN,
        )

        record_result(
            self.new_run(),
            self.entry,
            status=InstitutionRunResult.Status.FAILED,
            finished_at=NOW,
        )

        self.entry.refresh_from_db()
        self.assertEqual(
            self.entry.lifecycle,
            InstitutionAllowlistEntry.Lifecycle.SUSPENDED,
        )
        self.assertEqual(
            self.entry.suspension_reason,
            "OPEN_CRITICAL:test-source-critical",
        )

    def test_repeating_the_same_run_result_does_not_increment_twice(self) -> None:
        InstitutionRunResult, record_result = self.feature()
        self.entry.lifecycle = InstitutionAllowlistEntry.Lifecycle.ACTIVE
        self.entry.save(update_fields=("lifecycle", "updated_at"))
        run = self.new_run()

        first = record_result(
            run,
            self.entry,
            status=InstitutionRunResult.Status.FAILED,
            finished_at=NOW,
        )
        second = record_result(
            run,
            self.entry,
            status=InstitutionRunResult.Status.FAILED,
            finished_at=NOW,
        )

        self.entry.refresh_from_db()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(self.entry.consecutive_final_failed_count, 1)
        self.assertEqual(InstitutionRunResult.objects.count(), 1)

    def test_provisional_failure_degrades_without_using_active_counter(self) -> None:
        InstitutionRunResult, record_result = self.feature()

        result = record_result(
            self.new_run(),
            self.entry,
            status=InstitutionRunResult.Status.FAILED,
            finished_at=NOW,
        )

        self.entry.refresh_from_db()
        self.assertEqual(
            self.entry.lifecycle,
            InstitutionAllowlistEntry.Lifecycle.PROVISIONAL,
        )
        self.assertEqual(self.entry.health, InstitutionAllowlistEntry.Health.DEGRADED)
        self.assertEqual(self.entry.consecutive_final_failed_count, 0)
        self.assertEqual(result.failed_count_after, 0)

    def test_success_keeps_degraded_health_while_optional_issue_is_open(self) -> None:
        InstitutionRunResult, record_result = self.feature()
        CollectionIssue.objects.create(
            registry_id="test-optional-issue",
            classification=CollectionIssue.Classification.STRUCTURAL_OPTIONAL,
            scope=CollectionIssue.Scope.ENTRY,
            source=self.entry.source,
            institution=self.entry,
            status=CollectionIssue.Status.OPEN,
        )

        result = record_result(
            self.new_run(),
            self.entry,
            status=InstitutionRunResult.Status.SUCCESS,
            finished_at=NOW,
        )

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.health, InstitutionAllowlistEntry.Health.DEGRADED)
        self.assertEqual(result.health_after, "DEGRADED")
        self.assertEqual(result.issue_classifications, ["STRUCTURAL_OPTIONAL"])

    def test_retry_count_is_unknown_without_institution_telemetry(self) -> None:
        InstitutionRunResult, record_result = self.feature()

        result = record_result(
            self.new_run(),
            self.entry,
            status=InstitutionRunResult.Status.SUCCESS,
            finished_at=NOW,
        )

        self.assertIsNone(result.retry_count)


    def test_success_finalization_rejects_an_open_critical_issue(self) -> None:
        InstitutionRunResult, record_result = self.feature()
        CollectionIssue.objects.create(
            registry_id="test-late-critical",
            classification=CollectionIssue.Classification.ACCESS_BLOCK,
            scope=CollectionIssue.Scope.ENTRY,
            source=self.entry.source,
            institution=self.entry,
            status=CollectionIssue.Status.OPEN,
        )

        with self.assertRaisesRegex(
            CollectionGateError,
            "critical collection issue opened before finalization",
        ):
            record_result(
                self.new_run(),
                self.entry,
                status=InstitutionRunResult.Status.SUCCESS,
                finished_at=NOW,
            )

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.health, InstitutionAllowlistEntry.Health.HEALTHY)
        self.assertFalse(InstitutionRunResult.objects.exists())

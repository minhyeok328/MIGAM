from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from backend.apps.catalog.models import Exhibition
from backend.data_pipeline.collection_gate import (
    CollectionGateError,
    select_collectible_entries,
)
from backend.data_pipeline.fixture_loader import load_qualification_fixture
from backend.data_pipeline.freshness.execution import (
    RefreshExecutionError,
    refresh_exhibitions,
)
from backend.data_pipeline.freshness.schedule import refresh_schedule_for
from backend.data_pipeline.registry import SourceRegistry
from backend.data_pipeline.registry_state import sync_registry_state


class Command(BaseCommand):
    help = "Refresh canonical exhibitions that are due at the current time."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--fixture",
            default=str(
                settings.REPOSITORY_ROOT
                / "fixtures"
                / "source-qualification.json"
            ),
            help="Approved offline source snapshot used by the P0 demo collector.",
        )
        parser.add_argument(
            "--as-of",
            dest="as_of",
            help="Lifecycle reference date in YYYY-MM-DD format.",
        )

    def handle(self, *args: object, **options: object) -> None:
        del args
        now = timezone.now()
        as_of = _as_of_date(options.get("as_of"), now=now)
        registry = SourceRegistry.load(settings.REPOSITORY_ROOT / "sources.yaml")
        sync_registry_state(registry)
        try:
            collectible_entries = select_collectible_entries()
        except CollectionGateError:
            collectible_entries = ()
        collectible_institution_ids = {
            entry.registry_id for entry in collectible_entries
        }
        targets = tuple(
            exhibition
            for exhibition in Exhibition.objects.select_related("institution")
            if exhibition.institution.registry_id in collectible_institution_ids
            and refresh_schedule_for(exhibition, now=now).is_due
        )
        if not targets:
            self.stdout.write("target=0 success=0 failure=0")
            return

        fixture_path = Path(str(options["fixture"])).resolve()
        try:
            summary = refresh_exhibitions(
                targets,
                collect=lambda: load_qualification_fixture(fixture_path, registry),
                registry=registry,
                as_of=as_of,
                now=now,
                command_name="refresh_due_exhibitions",
            )
        except (RefreshExecutionError, OSError, ValueError, KeyError) as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            self.style.SUCCESS(
                " ".join(
                    (
                        f"run={summary.run_id}",
                        f"target={summary.target_count}",
                        f"success={summary.success_count}",
                        f"failure={summary.failure_count}",
                    )
                )
            )
        )


def _as_of_date(value: object, *, now: object) -> date:
    if value is None:
        return timezone.localdate(now)
    try:
        return date.fromisoformat(str(value))
    except ValueError as error:
        raise CommandError("--as-of must use YYYY-MM-DD format") from error

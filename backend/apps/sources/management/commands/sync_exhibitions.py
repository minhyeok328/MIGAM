from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from backend.data_pipeline.fixture_loader import load_qualification_fixture
from backend.data_pipeline.persistence import persist_records
from backend.data_pipeline.registry import SourceRegistry


class Command(BaseCommand):
    help = "Validate and persist approved exhibition fixture records."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--fixture",
            default=str(
                settings.REPOSITORY_ROOT
                / "fixtures"
                / "source-qualification.json"
            ),
            help="Path to an approved qualification fixture JSON file.",
        )
        parser.add_argument(
            "--source",
            help="Restrict the fixture import to one registered source ID.",
        )
        parser.add_argument(
            "--as-of",
            dest="as_of",
            default=date.today().isoformat(),
            help="Lifecycle reference date in YYYY-MM-DD format.",
        )

    def handle(self, *args: object, **options: object) -> None:
        registry = SourceRegistry.load(settings.REPOSITORY_ROOT / "sources.yaml")
        source_id = str(options.get("source") or "")
        if source_id:
            try:
                registry.source(source_id)
            except KeyError as error:
                raise CommandError(str(error)) from error

        try:
            as_of = date.fromisoformat(str(options["as_of"]))
        except ValueError as error:
            raise CommandError("--as-of must use YYYY-MM-DD format") from error

        fixture_path = Path(str(options["fixture"])).resolve()
        try:
            records = load_qualification_fixture(fixture_path, registry)
            if source_id:
                records = tuple(
                    record for record in records if record.source_id == source_id
                )
            summary = persist_records(
                records,
                registry,
                as_of=as_of,
                command_name="sync_exhibitions",
                source_id=source_id,
            )
        except (OSError, ValueError, KeyError) as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            self.style.SUCCESS(
                " ".join(
                    (
                        f"run={summary.run_id}",
                        f"received={summary.received_count}",
                        f"verified={summary.verified_count}",
                        f"excluded={summary.excluded_count}",
                        f"quarantined={summary.quarantined_count}",
                    )
                )
            )
        )

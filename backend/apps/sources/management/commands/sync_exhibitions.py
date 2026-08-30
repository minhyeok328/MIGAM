from datetime import date, datetime
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from backend.data_pipeline.collectors.culture_info import (
    CultureInfoApiCollector,
    CultureInfoApiError,
)
from backend.data_pipeline.collectors.seoul_csv import SeoulCsvCollector
from backend.data_pipeline.fixture_loader import load_qualification_fixture
from backend.data_pipeline.persistence import persist_records
from backend.data_pipeline.registry import SourceRegistry


SEJONG_SOURCE_ID = "seoul-oa-2708-sejong"
SEMA_SOURCE_ID = "seoul-oa-15323-sema"
CULTURE_SOURCE_ID = "kcisa-cultureinfo"


def environment_value(name: str, env_file: Path) -> str:
    process_value = os.environ.get(name, "").strip()
    if process_value:
        return process_value

    try:
        lines = env_file.read_text(encoding="utf-8-sig").splitlines()
    except FileNotFoundError:
        return ""
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if separator and key.strip() == name:
            cleaned = value.strip()
            if (
                len(cleaned) >= 2
                and cleaned[0] == cleaned[-1]
                and cleaned[0] in {'"', "'"}
            ):
                cleaned = cleaned[1:-1]
            return cleaned.strip()
    return ""


def culture_date(value: object, option_name: str) -> str:
    cleaned = str(value)
    try:
        datetime.strptime(cleaned, "%Y%m%d")
    except ValueError as error:
        raise ValueError(f"{option_name} must use YYYYMMDD format") from error
    if len(cleaned) != 8:
        raise ValueError(f"{option_name} must use YYYYMMDD format")
    return cleaned


class Command(BaseCommand):
    help = "Collect, validate, and persist approved exhibition source records."

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
            help="Restrict the sync to one registered source ID.",
        )
        parser.add_argument(
            "--sejong-csv",
            dest="sejong_csv",
            help="Path to a Seoul Open Data Sejong Center CSV file.",
        )
        parser.add_argument(
            "--sema-csv",
            dest="sema_csv",
            help="Path to a Seoul Museum of Art CSV file.",
        )
        parser.add_argument(
            "--culture-from",
            dest="culture_from",
            help="Culture API period start in YYYYMMDD format.",
        )
        parser.add_argument(
            "--culture-to",
            dest="culture_to",
            help="Culture API period end in YYYYMMDD format.",
        )
        parser.add_argument(
            "--env-file",
            dest="env_file",
            default=str(settings.REPOSITORY_ROOT / ".env"),
            help="Path to the local environment file.",
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

        try:
            collected = []
            sejong_csv = options.get("sejong_csv")
            if sejong_csv:
                if source_id and source_id != SEJONG_SOURCE_ID:
                    raise ValueError(
                        "--sejong-csv can only be used with "
                        f"--source={SEJONG_SOURCE_ID}"
                    )
                collected.extend(
                    SeoulCsvCollector(
                        registry,
                        SEJONG_SOURCE_ID,
                    ).collect(Path(str(sejong_csv)).read_bytes())
                )

            sema_csv = options.get("sema_csv")
            if sema_csv:
                if source_id and source_id != SEMA_SOURCE_ID:
                    raise ValueError(
                        "--sema-csv can only be used with "
                        f"--source={SEMA_SOURCE_ID}"
                    )
                collected.extend(
                    SeoulCsvCollector(
                        registry,
                        SEMA_SOURCE_ID,
                    ).collect(Path(str(sema_csv)).read_bytes())
                )

            culture_requested = bool(
                options.get("culture_from") or options.get("culture_to")
            )
            if culture_requested:
                if not options.get("culture_from") or not options.get("culture_to"):
                    raise ValueError(
                        "--culture-from and --culture-to must be provided together"
                    )
                if source_id and source_id != CULTURE_SOURCE_ID:
                    raise ValueError(
                        "culture period options can only be used with "
                        f"--source={CULTURE_SOURCE_ID}"
                    )
                culture_from = culture_date(
                    options["culture_from"],
                    "--culture-from",
                )
                culture_to = culture_date(
                    options["culture_to"],
                    "--culture-to",
                )
                collected.extend(
                    CultureInfoApiCollector(
                        registry,
                        service_key=environment_value(
                            "CULTURE_PORTAL_SERVICE_KEY",
                            Path(str(options["env_file"])),
                        ),
                    ).collect(
                        {
                            "from": culture_from,
                            "to": culture_to,
                        }
                    )
                )

            if sejong_csv or sema_csv or culture_requested:
                records = tuple(collected)
            else:
                fixture_path = Path(str(options["fixture"])).resolve()
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
        except (OSError, ValueError, KeyError, CultureInfoApiError) as error:
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

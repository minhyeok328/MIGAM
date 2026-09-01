from datetime import date, datetime
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from backend.apps.sources.models import IngestionRun, InstitutionAllowlistEntry
from backend.data_pipeline.collection_gate import (
    CollectionGateError,
    select_collectible_entries,
)
from backend.data_pipeline.collectors.culture_info import CultureInfoApiCollector
from backend.data_pipeline.collectors.seoul_csv import SeoulCsvCollector
from backend.data_pipeline.fixture_loader import load_qualification_fixture
from backend.data_pipeline.institution_runs import record_institution_results
from backend.data_pipeline.persistence import persist_records
from backend.data_pipeline.registry import SourceRegistry
from backend.data_pipeline.registry_state import sync_registry_state


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
            "--qualification",
            action="store_true",
            help="Record this sync as an institution promotion qualification run.",
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
        del args
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

        sejong_csv = options.get("sejong_csv")
        sema_csv = options.get("sema_csv")
        culture_requested = bool(
            options.get("culture_from") or options.get("culture_to")
        )
        try:
            if sejong_csv and source_id and source_id != SEJONG_SOURCE_ID:
                raise ValueError(
                    "--sejong-csv can only be used with "
                    f"--source={SEJONG_SOURCE_ID}"
                )
            if sema_csv and source_id and source_id != SEMA_SOURCE_ID:
                raise ValueError(
                    "--sema-csv can only be used with "
                    f"--source={SEMA_SOURCE_ID}"
                )
            culture_from = ""
            culture_to = ""
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
        except ValueError as error:
            raise CommandError(str(error)) from error

        requested_source_ids = _requested_source_ids(
            registry,
            source_id=source_id,
            sejong_csv=bool(sejong_csv),
            sema_csv=bool(sema_csv),
            culture_requested=culture_requested,
        )
        try:
            sync_registry_state(registry)
            institutions = select_collectible_entries(
                source_ids=requested_source_ids,
            )
        except (CollectionGateError, ValueError, KeyError) as error:
            raise CommandError(str(error)) from error

        eligible_source_ids = {entry.source.registry_id for entry in institutions}
        eligible_institution_ids = {entry.registry_id for entry in institutions}
        run = IngestionRun.objects.create(
            command="sync_exhibitions",
            source_id=(
                requested_source_ids[0] if len(requested_source_ids) == 1 else ""
            ),
            qualification_mode=bool(options.get("qualification")),
        )
        try:
            collected = []
            if sejong_csv and SEJONG_SOURCE_ID in eligible_source_ids:
                collected.extend(
                    SeoulCsvCollector(
                        registry,
                        SEJONG_SOURCE_ID,
                    ).collect(Path(str(sejong_csv)).read_bytes())
                )

            if sema_csv and SEMA_SOURCE_ID in eligible_source_ids:
                collected.extend(
                    SeoulCsvCollector(
                        registry,
                        SEMA_SOURCE_ID,
                    ).collect(Path(str(sema_csv)).read_bytes())
                )

            if culture_requested and CULTURE_SOURCE_ID in eligible_source_ids:
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
                records = tuple(
                    record
                    for record in collected
                    if record.institution_id in eligible_institution_ids
                )
            else:
                fixture_path = Path(str(options["fixture"])).resolve()
                records = tuple(
                    record
                    for record in load_qualification_fixture(fixture_path, registry)
                    if record.institution_id in eligible_institution_ids
                )
            with transaction.atomic():
                summary = persist_records(
                    records,
                    registry,
                    as_of=as_of,
                    command_name="sync_exhibitions",
                    source_id=run.source_id,
                    run=run,
                )
                record_institution_results(
                    run,
                    institutions,
                    finished_at=run.finished_at,
                )
        except Exception as error:
            _record_failed_execution(run, institutions, error)
            raise CommandError(str(error)) from error

        run.refresh_from_db()
        if run.status == IngestionRun.Status.FAILED:
            raise CommandError(run.error_message or "qualification failed")

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


def _requested_source_ids(
    registry: SourceRegistry,
    *,
    source_id: str,
    sejong_csv: bool,
    sema_csv: bool,
    culture_requested: bool,
) -> tuple[str, ...]:
    if source_id:
        return (source_id,)
    requested: list[str] = []
    if sejong_csv:
        requested.append(SEJONG_SOURCE_ID)
    if sema_csv:
        requested.append(SEMA_SOURCE_ID)
    if culture_requested:
        requested.append(CULTURE_SOURCE_ID)
    return tuple(requested) if requested else registry.source_ids


def _mark_run_failed(run: IngestionRun, error: Exception) -> None:
    run.status = IngestionRun.Status.FAILED
    run.finished_at = timezone.now()
    run.error_message = f"{type(error).__name__}: {error}"[:2000]
    run.save(update_fields=("status", "finished_at", "error_message"))


def _record_failed_execution(
    run: IngestionRun,
    institutions: tuple[InstitutionAllowlistEntry, ...],
    error: Exception,
) -> None:
    failed_ids = {
        institution.registry_id for institution in institutions
    }
    try:
        with transaction.atomic():
            _mark_run_failed(run, error)
            record_institution_results(
                run,
                institutions,
                failed_institution_ids=failed_ids,
                error_message=str(error),
                finished_at=run.finished_at,
            )
    except Exception:
        _mark_run_failed(run, error)
        raise

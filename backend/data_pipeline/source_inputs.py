"""Select explicit offline evidence or official inputs for a targeted refresh."""

from pathlib import Path

from django.conf import settings
from django.core.management.base import CommandError

from backend.apps.catalog.models import ExhibitionSourceLink
from backend.data_pipeline.collectors.culture_info import CultureInfoApiCollector
from backend.data_pipeline.collectors.seoul_csv import SeoulCsvCollector
from backend.data_pipeline.fixture_loader import load_qualification_fixture


CSV_OPTIONS = {
    "seoul-oa-2708-sejong": "sejong_csv",
    "seoul-oa-15323-sema": "sema_csv",
}


def add_refresh_inputs(parser):
    parser.add_argument("--source", help="Limit targets to one approved source.")
    parser.add_argument("--sejong-csv", help="Latest official Sejong CSV download.")
    parser.add_argument("--sema-csv", help="Latest official SeMA CSV download.")
    parser.add_argument("--env-file", default=str(settings.REPOSITORY_ROOT / ".env"))


def refresh_collector(targets, registry, options):
    """Validate inputs before creating a run; network stays inside the gated service."""
    fixture = options.get("fixture")
    if fixture:
        if options.get("sejong_csv") or options.get("sema_csv"):
            raise CommandError("--fixture cannot be combined with official CSV inputs")
        return lambda: load_qualification_fixture(Path(str(fixture)).resolve(), registry)

    identities = tuple(ExhibitionSourceLink.objects.filter(
        exhibition_id__in=[row.pk for row in targets],
    ).values_list("source_id", "source_record_id"))
    source_ids = {source for source, _ in identities}
    for source_id, option in CSV_OPTIONS.items():
        if source_id in source_ids and not options.get(option):
            raise CommandError(f"Official CSV required: --{option.replace('_', '-')}; use --fixture only for offline tests")
    from backend.apps.sources.management.commands.sync_exhibitions import environment_value
    key = ""
    if "kcisa-cultureinfo" in source_ids:
        key = environment_value("CULTURE_PORTAL_SERVICE_KEY", Path(str(options["env_file"])))
        if not key:
            raise CommandError("CULTURE_PORTAL_SERVICE_KEY is required for official refresh")

    def collect():
        records = []
        for source_id in sorted(source_ids):
            if source_id in CSV_OPTIONS:
                content = Path(str(options[CSV_OPTIONS[source_id]])).read_bytes()
                records.extend(SeoulCsvCollector(registry, source_id).collect(content))
            elif source_id == "kcisa-cultureinfo":
                records.extend(CultureInfoApiCollector(registry, key).collect_ids([
                    identity for source, identity in identities if source == source_id
                ]))
            else:
                raise ValueError(f"No official collector for source: {source_id}")
        return records
    return collect

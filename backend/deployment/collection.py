"""Daily approved collection. No visitor data enters this module."""

from dataclasses import asdict
from datetime import timedelta
import json
import os
from pathlib import Path
from time import monotonic

from backend.data_pipeline.collectors.seoul_download import (
    download_csv, observed_revision, DownloadError, RetryableDownloadError,
)
from backend.data_pipeline.collectors.seoul_csv import SeoulCsvCollector
from backend.data_pipeline.collectors.culture_info import CultureInfoApiCollector, UrllibXmlTransport
from backend.data_pipeline.models import RawExhibitionRecord


class BudgetTransport(UrllibXmlTransport):
    def __init__(self):
        super().__init__(timeout=12)
        self.started = monotonic()
        self.calls = 0

    def get(self, url, params):
        self.calls += 1
        if self.calls > 100 or monotonic() - self.started > 90:
            raise RuntimeError("daily culture collection budget reached")
        return super().get(url, params)


def csv_records(source_id, registry, directory, blobs):
    revision = observed_revision(source_id)
    cache_path = f"inputs/{source_id}.json"
    cached = blobs.get(cache_path)
    cache = json.loads(cached) if cached else None
    if cache and cache["revision"] > revision:
        raise DownloadError("dataset revision moved backwards")
    if cache and cache["revision"] == revision:
        # Today's successful official metadata check confirms the cached revision.
        return [RawExhibitionRecord(**{**row, "conflicts": frozenset(row["conflicts"])})
                for row in cache["records"]]
    marker = f"downloads/{source_id}/{revision}.json"
    try:
        blobs.put(marker, b'{"attempted":true}')
    except FileExistsError as error:
        raise DownloadError("this official revision was already downloaded; operator review required") from error
    try:
        path, metadata = download_csv(source_id, directory)
    except RetryableDownloadError:
        blobs.delete(marker)
        raise
    records = SeoulCsvCollector(registry, source_id).collect(path.read_bytes())
    path.unlink()
    rows = [{**asdict(row), "conflicts": sorted(row.conflicts)} for row in records]
    blobs.put(cache_path, json.dumps({"revision": revision, "metadata": metadata, "records": rows},
                                    ensure_ascii=False).encode(), overwrite=True)
    return records


def collect_source(source_id, registry, institutions, targets, directory, blobs, today):
    if source_id.startswith("seoul-"):
        records = csv_records(source_id, registry, directory, blobs)
    else:
        from backend.apps.catalog.models import ExhibitionSourceLink
        key = os.environ.get("CULTURE_PORTAL_SERVICE_KEY", "")
        collector = CultureInfoApiCollector(registry, key, transport=BudgetTransport())
        identities = ExhibitionSourceLink.objects.filter(exhibition__in=targets, source_id=source_id)
        records = collector.collect_ids(list(identities.values_list("source_record_id", flat=True)))
        places = frozenset(str(registry.institution(row.registry_id)["source_filter"]["place"])
                           for row in institutions)
        new = collector.collect({"from": (today - timedelta(days=365)).strftime("%Y%m%d"),
                                 "to": (today + timedelta(days=180)).strftime("%Y%m%d"),
                                 "numOfrows": "100"}, summary_places=places)
        known = {row.source_record_id for row in records}
        records.extend(row for row in new if row.source_record_id not in known)
    allowed = {row.registry_id for row in institutions}
    return [row for row in records if row.institution_id in allowed]


def refresh_sources(directory, blobs):
    from django.conf import settings
    from django.utils import timezone
    from backend.apps.catalog.models import Exhibition, ExhibitionSourceLink
    from backend.apps.sources.models import IngestionRun
    from backend.apps.sources.management.commands.sync_exhibitions import _record_failed_execution
    from backend.data_pipeline.collection_gate import CollectionGateError, select_collectible_entries
    from backend.data_pipeline.freshness.execution import refresh_exhibitions
    from backend.data_pipeline.freshness.schedule import refresh_schedule_for
    from backend.data_pipeline.institution_runs import record_institution_results
    from backend.data_pipeline.persistence import persist_records, _content_hash, _raw_payload
    from backend.data_pipeline.registry import SourceRegistry
    from backend.data_pipeline.registry_state import sync_registry_state
    from .derived import update_derived_state

    registry = SourceRegistry.load(settings.REPOSITORY_ROOT / "sources.yaml")
    sync_registry_state(registry)
    update_derived_state()
    now = timezone.now()
    today = timezone.localdate(now)
    statuses = {}
    for source_id in registry.source_ids:
        try:
            institutions = select_collectible_entries(source_ids=(source_id,))
        except CollectionGateError:
            statuses[source_id] = "BLOCKED"
            continue
        targets = tuple(row for row in Exhibition.objects.filter(
            institution__registry_id__in=[entry.registry_id for entry in institutions],
        ).select_related("institution") if refresh_schedule_for(row, now=now).is_due)
        collected = []
        discovery_run = None
        discovery_institutions = institutions

        def collect():
            records = collect_source(source_id, registry, institutions, targets, directory, blobs, today)
            collected.extend(records)
            return records

        try:
            if targets:
                refresh_exhibitions(targets, collect=collect, registry=registry, as_of=today,
                                    now=now, command_name="daily_public_refresh")
            else:
                discovery_run = IngestionRun.objects.create(command="daily_public_discovery", source_id=source_id)
                collect()
            existing = dict(ExhibitionSourceLink.objects.filter(source_id=source_id)
                            .values_list("source_record_id", "latest_source_record__content_hash"))
            changed = [row for row in collected
                       if existing.get(row.source_record_id) != _content_hash(_raw_payload(row))]
            if changed or not targets:
                if discovery_run is None:
                    discovery_run = IngestionRun.objects.create(command="daily_public_discovery", source_id=source_id)
                    involved = {row.institution_id for row in changed}
                    discovery_institutions = tuple(row for row in institutions if row.registry_id in involved)
                summary = persist_records(changed, registry, as_of=today, command_name="daily_public_discovery",
                                          source_id=source_id, run=discovery_run)
                discovery_run.refresh_from_db()
                record_institution_results(discovery_run, discovery_institutions,
                                           finished_at=discovery_run.finished_at)
                statuses[source_id] = f"SUCCESS changed={summary.received_count} checked={len(targets)}"
            else:
                statuses[source_id] = f"SUCCESS changed=0 checked={len(targets)}"
        except Exception:
            # Existing pipeline owns failure evidence. Never emit transport errors/keys.
            if discovery_run is not None:
                _record_failed_execution(discovery_run, discovery_institutions,
                                         RuntimeError("official discovery processing failed"))
            statuses[source_id] = "FAILED"
    update_derived_state()
    return statuses

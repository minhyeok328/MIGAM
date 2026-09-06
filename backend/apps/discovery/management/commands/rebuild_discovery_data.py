from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from backend.apps.catalog.models import Exhibition
from backend.apps.discovery.projection import rebuild_search_documents
from backend.data_pipeline.enrichment import backfill_source_evidence
from backend.data_pipeline.freshness.state import apply_time_based_freshness
from backend.data_pipeline.registry import SourceRegistry
from backend.data_pipeline.registry_state import sync_registry_state


class Command(BaseCommand):
    help = "Rebuild local derived data without claiming an official source recheck."

    @transaction.atomic
    def handle(self, *args, **options):
        registry = SourceRegistry.load(settings.REPOSITORY_ROOT / "sources.yaml")
        sync_registry_state(registry)
        now = timezone.now()
        today = timezone.localdate(now)
        active = Exhibition.objects.exclude(lifecycle__in=("CANCELED", "UNKNOWN"))
        active.filter(end_date__lt=today).update(lifecycle="ENDED")
        active.filter(start_date__gt=today).update(lifecycle="UPCOMING")
        active.filter(start_date__lte=today, end_date__gte=today).update(lifecycle="CURRENT")
        apply_time_based_freshness(Exhibition.objects.all(), now=now)
        changed = backfill_source_evidence(registry)
        projection = rebuild_search_documents()
        self.stdout.write(f"exhibitions={projection.exhibition_count} institutions={projection.institution_count} feature_snapshots={changed}; official verification timestamps preserved")

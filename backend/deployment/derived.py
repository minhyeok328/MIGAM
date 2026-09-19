"""Time-derived state on a private serving copy; never writes verification times."""

from django.db import transaction
from django.utils import timezone


@transaction.atomic
def update_derived_state():
    from backend.apps.catalog.models import Exhibition
    from backend.apps.discovery.projection import rebuild_search_documents
    from backend.data_pipeline.freshness.state import apply_time_based_freshness
    now = timezone.now()
    today = timezone.localdate(now)
    active = Exhibition.objects.exclude(lifecycle__in=("CANCELED", "UNKNOWN"))
    active.filter(end_date__lt=today).exclude(lifecycle="ENDED").update(lifecycle="ENDED")
    active.filter(start_date__gt=today).exclude(lifecycle="UPCOMING").update(lifecycle="UPCOMING")
    active.filter(start_date__lte=today, end_date__gte=today).exclude(lifecycle="CURRENT").update(lifecycle="CURRENT")
    apply_time_based_freshness(Exhibition.objects.all(), now=now)
    rebuild_search_documents()

from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from backend.apps.catalog.models import Exhibition
from backend.data_pipeline.freshness.schedule import refresh_schedule_for


def _render_time(value: datetime | None) -> str:
    return value.isoformat() if value is not None else "-"


class Command(BaseCommand):
    help = "Show the current exhibition refresh schedule without changing data."

    def handle(self, *args: object, **options: object) -> None:
        del args, options
        now = timezone.now()
        for exhibition in Exhibition.objects.order_by("id"):
            schedule = refresh_schedule_for(exhibition, now=now)
            self.stdout.write(
                " ".join(
                    (
                        f"id={exhibition.pk}",
                        f"lifecycle={exhibition.lifecycle}",
                        f"last_verified_at={exhibition.last_verified_at.isoformat()}",
                        f"next_refresh_at={_render_time(schedule.next_refresh_at)}",
                        f"stale_at={_render_time(schedule.stale_at)}",
                        f"due={'yes' if schedule.is_due else 'no'}",
                        f"freshness={schedule.freshness}",
                        f"reason={schedule.reason}",
                    )
                )
            )

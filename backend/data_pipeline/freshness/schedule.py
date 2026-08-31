from dataclasses import dataclass
from datetime import datetime, timedelta

from django.utils import timezone

from backend.apps.catalog.models import Exhibition


@dataclass(frozen=True, slots=True)
class RefreshSchedule:
    next_refresh_at: datetime | None
    stale_at: datetime | None
    is_due: bool
    freshness: str
    reason: str


def refresh_schedule_for(
    exhibition: Exhibition,
    *,
    now: datetime,
) -> RefreshSchedule:
    if exhibition.lifecycle not in {
        Exhibition.Lifecycle.CURRENT,
        Exhibition.Lifecycle.UPCOMING,
    }:
        reason = (
            "ENDED_NOT_PERIODIC"
            if exhibition.lifecycle == Exhibition.Lifecycle.ENDED
            else "LIFECYCLE_NOT_PERIODIC"
        )
        return RefreshSchedule(
            next_refresh_at=None,
            stale_at=None,
            is_due=False,
            freshness=exhibition.freshness,
            reason=reason,
        )

    local_today = timezone.localdate(now)
    is_near = (
        exhibition.lifecycle == Exhibition.Lifecycle.CURRENT
        or exhibition.start_date <= local_today + timedelta(days=7)
    )
    if is_near:
        refresh_after = timedelta(days=1)
        stale_after = timedelta(hours=48)
        reason = (
            "CURRENT_DAILY"
            if exhibition.lifecycle == Exhibition.Lifecycle.CURRENT
            else "UPCOMING_WITHIN_7_DAYS"
        )
    else:
        refresh_after = timedelta(days=3)
        stale_after = timedelta(days=3)
        reason = "UPCOMING_3_DAY"

    next_refresh_at = exhibition.last_verified_at + refresh_after
    stale_at = exhibition.last_verified_at + stale_after
    freshness = (
        Exhibition.Freshness.STALE
        if now > stale_at
        else Exhibition.Freshness.FRESH
    )
    if exhibition.freshness == Exhibition.Freshness.UNVERIFIED:
        freshness = Exhibition.Freshness.UNVERIFIED

    return RefreshSchedule(
        next_refresh_at=next_refresh_at,
        stale_at=stale_at,
        is_due=now >= next_refresh_at,
        freshness=freshness,
        reason=reason,
    )

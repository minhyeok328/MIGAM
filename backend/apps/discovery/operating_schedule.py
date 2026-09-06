"""Resolve official opening evidence without expanding every requested date."""

from dataclasses import dataclass
from datetime import date, datetime, time
from enum import StrEnum

from backend.apps.catalog.models import Exhibition, OperatingSchedule
from backend.apps.discovery.visit_conditions import _current_source_record_ids, _related_rows


class OpeningState(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class ResolvedOperatingSchedule:
    state: OpeningState
    first_open_date: date | None = None
    opens_at: time | None = None
    closes_at: time | None = None
    source_record_ids: tuple[int, ...] = ()
    verified_at: datetime | None = None


class OperatingScheduleResolver:
    def resolve(self, exhibition: Exhibition, start: date, end: date) -> ResolvedOperatingSchedule:
        if start > end:
            raise ValueError("Schedule request start must not exceed end.")
        first = max(start, exhibition.start_date).toordinal()
        last = min(end, exhibition.end_date).toordinal()
        if first > last:
            return ResolvedOperatingSchedule(OpeningState.UNKNOWN)

        current_ids = _current_source_record_ids(exhibition)
        rows = [
            row
            for target in (exhibition, exhibition.institution)
            for row in _related_rows(target, "operatingschedule_records")
            if row.source_record_id in current_ids
            and row.effective_from.toordinal() <= last
            and row.effective_to.toordinal() >= first
        ]
        boundaries = {first, last + 1}
        for row in rows:
            boundaries.add(max(first, row.effective_from.toordinal()))
            boundaries.add(min(last + 1, row.effective_to.toordinal() + 1))

        ordered_boundaries = sorted(boundaries)
        has_unknown = False
        for left, right in zip(ordered_boundaries, ordered_boundaries[1:]):
            active = [
                row for row in rows
                if row.effective_from.toordinal() <= left <= row.effective_to.toordinal()
            ]
            # The active rules stay constant here; all later weeks repeat these weekdays.
            for ordinal in range(left, min(right, left + 7)):
                result = _resolve_day(active, date.fromordinal(ordinal))
                if result.state == OpeningState.OPEN:
                    return result
                has_unknown |= result.state == OpeningState.UNKNOWN
        return ResolvedOperatingSchedule(
            OpeningState.UNKNOWN if has_unknown else OpeningState.CLOSED
        )


def _resolve_day(rows: list[OperatingSchedule], day: date) -> ResolvedOperatingSchedule:
    applicable = [
        row for row in rows
        if row.kind == OperatingSchedule.Kind.OVERRIDE
        or row.status == OperatingSchedule.Status.UNKNOWN
        or day.weekday() in row.weekdays
    ]
    if not applicable:
        return ResolvedOperatingSchedule(OpeningState.UNKNOWN)

    def precedence(row: OperatingSchedule) -> tuple[bool, bool]:
        return row.kind == OperatingSchedule.Kind.OVERRIDE, row.exhibition_id is not None

    priority = max(precedence(row) for row in applicable)
    selected = [row for row in applicable if precedence(row) == priority]
    if any(row.status == OperatingSchedule.Status.UNKNOWN for row in selected):
        return ResolvedOperatingSchedule(OpeningState.UNKNOWN)
    values = {(row.is_open, row.opens_at, row.closes_at) for row in selected}
    if len(values) != 1:
        return ResolvedOperatingSchedule(OpeningState.UNKNOWN)
    is_open, opens_at, closes_at = next(iter(values))
    if not is_open:
        return ResolvedOperatingSchedule(OpeningState.CLOSED)
    return ResolvedOperatingSchedule(
        state=OpeningState.OPEN,
        first_open_date=day,
        opens_at=opens_at,
        closes_at=closes_at,
        source_record_ids=tuple(sorted({row.source_record_id for row in selected})),
        verified_at=min(row.verified_at for row in selected),
    )

from dataclasses import dataclass
from datetime import date, datetime

from backend.data_pipeline.models import RawExhibitionRecord


@dataclass(frozen=True, slots=True)
class NormalizedExhibition:
    raw_record: RawExhibitionRecord
    title: str | None
    start_date: date | None
    end_date: date | None
    venue: str | None
    region_area: str | None
    region_district: str | None
    lifecycle: str
    official_url: str | None
    rule_version: str = "1.0.0"


def normalize_record(
    raw_record: RawExhibitionRecord,
    *,
    as_of: date,
) -> NormalizedExhibition:
    title = _clean(raw_record.title)
    start_date = _parse_date(raw_record.start_date)
    end_date = _parse_date(raw_record.end_date)
    return NormalizedExhibition(
        raw_record=raw_record,
        title=title,
        start_date=start_date,
        end_date=end_date,
        venue=_clean(raw_record.venue),
        region_area=_clean(raw_record.region_area),
        region_district=_clean(raw_record.region_district),
        lifecycle=_lifecycle(
            start_date,
            end_date,
            as_of=as_of,
            canceled=raw_record.canceled,
        ),
        official_url=_clean(raw_record.official_url),
    )


def _clean(value: object) -> str | None:
    cleaned = "" if value is None else str(value).strip()
    return cleaned or None


def _parse_date(value: object) -> date | None:
    cleaned = _clean(value)
    if cleaned is None:
        return None
    for date_format in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(cleaned, date_format).date()
        except ValueError:
            continue
    return None


def _lifecycle(
    start_date: date | None,
    end_date: date | None,
    *,
    as_of: date,
    canceled: bool,
) -> str:
    if canceled:
        return "CANCELED"
    if start_date is None or end_date is None or end_date < start_date:
        return "UNKNOWN"
    if as_of < start_date:
        return "UPCOMING"
    if as_of > end_date:
        return "ENDED"
    return "CURRENT"

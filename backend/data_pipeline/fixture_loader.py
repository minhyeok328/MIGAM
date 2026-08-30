import json
from pathlib import Path

from backend.data_pipeline.models import RawExhibitionRecord
from backend.data_pipeline.registry import SourceRegistry


def load_qualification_fixture(
    path: Path,
    registry: SourceRegistry,
) -> tuple[RawExhibitionRecord, ...]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        raise ValueError("qualification fixture must contain a records list")

    records: list[RawExhibitionRecord] = []
    for item in data["records"]:
        if not isinstance(item, dict):
            raise ValueError("qualification fixture records must be mappings")
        source_id = str(item["source_id"])
        source = registry.source(source_id)
        region = item.get("region")
        if not isinstance(region, dict):
            raise ValueError("qualification fixture record region must be a mapping")
        records.append(
            RawExhibitionRecord(
                source_id=source_id,
                institution_id=str(item["institution_id"]),
                source_record_id=str(item["source_record_id"]),
                source_owner=str(source["owner"]),
                title=_optional_string(item.get("title")),
                start_date=_optional_string(item.get("start_date")),
                end_date=_optional_string(item.get("end_date")),
                venue=_optional_string(item.get("venue")),
                region_area=_optional_string(region.get("area")),
                region_district=_optional_string(region.get("district")),
                official_url=_optional_string(item.get("official_url")),
                canceled=item.get("status_at_verification") == "CANCELED",
                raw=_allowed_fixture_payload(item, region),
            )
        )
    return tuple(records)


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _allowed_fixture_payload(
    item: dict[str, object],
    region: dict[str, object],
) -> dict[str, str | None]:
    return {
        "record_id": _optional_string(item.get("source_record_id")),
        "title": _optional_string(item.get("title")),
        "start_date": _optional_string(item.get("start_date")),
        "end_date": _optional_string(item.get("end_date")),
        "venue": _optional_string(item.get("venue")),
        "region_area": _optional_string(region.get("area")),
        "region_district": _optional_string(region.get("district")),
        "official_url": _optional_string(item.get("official_url")),
    }

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True, slots=True)
class RawExhibitionRecord:
    source_id: str
    institution_id: str
    source_record_id: str
    source_owner: str
    title: str | None
    start_date: str | None
    end_date: str | None
    venue: str | None
    region_area: str | None
    region_district: str | None
    official_url: str | None
    canceled: bool = False
    conflicts: frozenset[str] = field(default_factory=frozenset)
    raw: Mapping[str, str | None] = field(default_factory=dict)

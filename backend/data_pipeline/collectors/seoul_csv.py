import csv
from io import StringIO
from typing import Any, Mapping

from backend.data_pipeline.models import RawExhibitionRecord
from backend.data_pipeline.registry import SourceRegistry


class SourceContractError(ValueError):
    pass


def _clean(value: object) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _decode_csv(csv_content: bytes) -> str:
    try:
        return csv_content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return csv_content.decode("cp949", errors="replace")


def _resolved_columns(
    source: Mapping[str, Any],
    fieldnames: tuple[str, ...],
) -> tuple[dict[str, str], dict[str, str]]:
    fields = source["fields"]
    header_aliases = source.get("csv_headers", {})
    columns: dict[str, str] = {}
    source_columns: dict[str, str] = {}
    missing: list[str] = []
    for field_name, source_field in fields.items():
        candidates = (header_aliases.get(source_field), source_field)
        column = next(
            (candidate for candidate in candidates if candidate in fieldnames),
            None,
        )
        if column is None:
            missing.append(source_field)
            continue
        columns[field_name] = column
        source_columns[source_field] = column
    if missing:
        raise SourceContractError(
            f"missing source columns: {', '.join(sorted(missing))}"
        )
    return columns, source_columns


class SeoulCsvCollector:
    def __init__(self, registry: SourceRegistry, source_id: str) -> None:
        self.registry = registry
        self.source_id = source_id

    def collect(self, csv_content: str | bytes) -> list[RawExhibitionRecord]:
        source = self.registry.source(self.source_id)
        if source.get("kind") != "HTTPS_CSV_SHEET":
            raise ValueError(f"source is not a CSV Sheet: {self.source_id}")

        if isinstance(csv_content, bytes):
            csv_text = _decode_csv(csv_content)
        else:
            csv_text = csv_content.lstrip("\ufeff")

        fields = source["fields"]
        institutions = self.registry.institutions_for_source(self.source_id)
        reader = csv.DictReader(StringIO(csv_text))
        columns, source_columns = _resolved_columns(
            source,
            tuple(reader.fieldnames or ()),
        )

        records: list[RawExhibitionRecord] = []
        for row in reader:
            if not self._passes_source_filters(row, source, columns):
                continue
            institution = self._matching_institution(
                row,
                institutions,
                source_columns,
            )
            if institution is None:
                continue
            region = institution.get("region", {})
            selected_raw = {
                source_field: _clean(row.get(columns[field_name]))
                for field_name, source_field in fields.items()
            }
            records.append(
                RawExhibitionRecord(
                    source_id=self.source_id,
                    institution_id=institution["id"],
                    source_record_id=_clean(row.get(columns["record_id"])) or "",
                    source_owner=source["owner"],
                    title=_clean(row.get(columns["title"])),
                    start_date=_clean(row.get(columns["start_date"])),
                    end_date=_clean(row.get(columns["end_date"])),
                    venue=_clean(row.get(columns["venue"])),
                    region_area=_clean(region.get("area")),
                    region_district=_clean(region.get("district")),
                    official_url=_clean(row.get(columns["official_url"])),
                    raw=selected_raw,
                )
            )
        return records

    @staticmethod
    def _passes_source_filters(
        row: Mapping[str, Any],
        source: Mapping[str, Any],
        fields: Mapping[str, str],
    ) -> bool:
        filters = source.get("source_filter", {})
        genres = filters.get("genres")
        if genres and _clean(row.get(fields.get("genre", ""))) not in genres:
            return False
        venues = filters.get("venues")
        if venues and _clean(row.get(fields["venue"])) not in venues:
            return False
        return True

    @staticmethod
    def _matching_institution(
        row: Mapping[str, Any],
        institutions: tuple[Mapping[str, Any], ...],
        source_columns: Mapping[str, str],
    ) -> Mapping[str, Any] | None:
        for institution in institutions:
            filters = institution.get("source_filter", {})
            if all(
                _clean(row.get(source_columns.get(field, field))) == expected
                for field, expected in filters.items()
            ):
                return institution
        return None

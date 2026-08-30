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
        try:
            return csv_content.decode("cp949")
        except UnicodeDecodeError as error:
            raise SourceContractError(
                "CSV encoding must be UTF-8 (with optional BOM) or CP949"
            ) from error


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
        missing_columns = sorted(set(fields.values()) - set(reader.fieldnames or ()))
        if missing_columns:
            raise SourceContractError(
                f"missing source columns: {', '.join(missing_columns)}"
            )

        records: list[RawExhibitionRecord] = []
        for row in reader:
            if not self._passes_source_filters(row, source, fields):
                continue
            institution = self._matching_institution(row, institutions)
            if institution is None:
                continue
            region = institution.get("region", {})
            selected_raw = {
                column: _clean(row.get(column))
                for column in fields.values()
            }
            records.append(
                RawExhibitionRecord(
                    source_id=self.source_id,
                    institution_id=institution["id"],
                    source_record_id=_clean(row.get(fields["record_id"])) or "",
                    source_owner=source["owner"],
                    title=_clean(row.get(fields["title"])),
                    start_date=_clean(row.get(fields["start_date"])),
                    end_date=_clean(row.get(fields["end_date"])),
                    venue=_clean(row.get(fields["venue"])),
                    region_area=_clean(region.get("area")),
                    region_district=_clean(region.get("district")),
                    official_url=_clean(row.get(fields["official_url"])),
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
    ) -> Mapping[str, Any] | None:
        for institution in institutions:
            filters = institution.get("source_filter", {})
            if all(_clean(row.get(field)) == expected for field, expected in filters.items()):
                return institution
        return None

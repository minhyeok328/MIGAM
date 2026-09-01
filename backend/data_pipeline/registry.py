from pathlib import Path
from typing import Any, Mapping

import yaml


class SourceRegistry:
    def __init__(self, data: Mapping[str, Any]) -> None:
        self.data = data
        self._sources = {source["id"]: source for source in data.get("sources", [])}
        self._institutions = {
            institution["id"]: institution
            for institution in data.get("institution_allowlist", [])
        }

    @classmethod
    def load(cls, path: Path) -> "SourceRegistry":
        with path.open("r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
        if not isinstance(data, dict):
            raise ValueError("source registry must be a mapping")
        return cls(data)

    def source(self, source_id: str) -> Mapping[str, Any]:
        try:
            return self._sources[source_id]
        except KeyError as error:
            raise KeyError(f"unknown source: {source_id}") from error

    def institutions_for_source(self, source_id: str) -> tuple[Mapping[str, Any], ...]:
        return tuple(
            institution
            for institution in self._institutions.values()
            if institution.get("source_id") == source_id
        )

    def institution(self, institution_id: str) -> Mapping[str, Any]:
        try:
            return self._institutions[institution_id]
        except KeyError as error:
            raise KeyError(f"unknown institution: {institution_id}") from error

    @property
    def source_ids(self) -> tuple[str, ...]:
        return tuple(self._sources)

    @property
    def collection_issues(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(self.data.get("collection_issues", ()))

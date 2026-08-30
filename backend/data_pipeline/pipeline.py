from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from backend.data_pipeline.models import RawExhibitionRecord
from backend.data_pipeline.normalization import NormalizedExhibition, normalize_record
from backend.data_pipeline.quality import QualityResult, evaluate_core_quality
from backend.data_pipeline.registry import SourceRegistry


@dataclass(frozen=True, slots=True)
class ProcessedExhibition:
    normalized: NormalizedExhibition
    quality: QualityResult


def process_records(
    records: Iterable[RawExhibitionRecord],
    registry: SourceRegistry,
    *,
    as_of: date,
) -> tuple[ProcessedExhibition, ...]:
    processed: list[ProcessedExhibition] = []
    for raw_record in records:
        normalized = normalize_record(raw_record, as_of=as_of)
        processed.append(
            ProcessedExhibition(
                normalized=normalized,
                quality=evaluate_core_quality(normalized, registry),
            )
        )
    return tuple(processed)

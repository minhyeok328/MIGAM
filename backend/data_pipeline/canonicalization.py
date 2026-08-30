from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
import unicodedata

from django.db import transaction
from django.utils import timezone

from backend.apps.catalog.models import (
    DuplicateCandidate,
    Exhibition,
    ExhibitionSourceLink,
    FieldEvidence,
    Institution,
    SourceConflict,
)
from backend.apps.data_quality.models import ExhibitionCandidate
from backend.data_pipeline.registry import SourceRegistry


CANONICAL_FIELDS = (
    "title",
    "start_date",
    "end_date",
    "venue",
    "region_area",
    "region_district",
    "lifecycle",
    "official_url",
)


@dataclass(frozen=True, slots=True)
class CanonicalizationSummary:
    created_count: int
    matched_count: int
    skipped_count: int
    duplicate_candidate_count: int
    conflict_count: int


@transaction.atomic
def canonicalize_candidates(
    candidates: Iterable[ExhibitionCandidate],
    *,
    registry: SourceRegistry | None = None,
) -> CanonicalizationSummary:
    created_count = 0
    matched_count = 0
    skipped_count = 0
    duplicate_candidate_count = 0
    conflict_count = 0

    for candidate in candidates:
        if not _is_publishable(candidate):
            skipped_count += 1
            continue

        source_record = candidate.source_record
        source_link = (
            ExhibitionSourceLink.objects.select_for_update()
            .select_related("exhibition")
            .filter(
                source_id=source_record.source_id,
                source_record_id=source_record.source_record_id,
            )
            .first()
        )
        if source_link is not None:
            conflict_count += _merge_same_source_version(
                source_link.exhibition,
                candidate,
            )
            if source_link.latest_source_record_id != source_record.pk:
                source_link.latest_source_record = source_record
                source_link.save(update_fields=("latest_source_record", "updated_at"))
            matched_count += 1
            continue

        institution = _institution_for(candidate, registry)
        strong_match = _find_strong_match(candidate, institution)
        if strong_match is not None:
            conflict_count += _merge_additional_source(strong_match, candidate)
            _link_source(strong_match, candidate)
            matched_count += 1
            continue

        similar_exhibitions = _find_similar_exhibitions(candidate, institution)
        exhibition = _create_exhibition(candidate, institution)
        _link_source(exhibition, candidate)
        _record_initial_evidence(exhibition, candidate)
        created_count += 1

        for similar in similar_exhibitions:
            primary_id, related_id = sorted((similar.pk, exhibition.pk))
            _, created = DuplicateCandidate.objects.get_or_create(
                primary_exhibition_id=primary_id,
                related_exhibition_id=related_id,
                defaults={"reason": "SAME_TITLE_CORE_DIFFERENCE"},
            )
            duplicate_candidate_count += int(created)

    return CanonicalizationSummary(
        created_count=created_count,
        matched_count=matched_count,
        skipped_count=skipped_count,
        duplicate_candidate_count=duplicate_candidate_count,
        conflict_count=conflict_count,
    )


def _is_publishable(candidate: ExhibitionCandidate) -> bool:
    return (
        candidate.core_result == ExhibitionCandidate.CoreResult.PASS
        and candidate.eligibility == ExhibitionCandidate.Eligibility.VERIFIED
        and not candidate.quarantined
    )


def _institution_for(
    candidate: ExhibitionCandidate,
    registry: SourceRegistry | None,
) -> Institution:
    registry_id = candidate.source_record.institution_id
    metadata: Mapping[str, object] = {}
    if registry is not None:
        metadata = registry.institution(registry_id)

    defaults = {
        "name": str(metadata.get("name") or registry_id),
        "region_area": str(
            _nested_region(metadata, "area") or candidate.region_area or ""
        ),
        "region_district": str(
            _nested_region(metadata, "district") or candidate.region_district or ""
        ),
    }
    institution, created = Institution.objects.get_or_create(
        registry_id=registry_id,
        defaults=defaults,
    )
    if not created and registry is not None:
        changed_fields = [
            field
            for field, value in defaults.items()
            if getattr(institution, field) != value
        ]
        for field in changed_fields:
            setattr(institution, field, defaults[field])
        if changed_fields:
            institution.save(update_fields=(*changed_fields, "updated_at"))
    return institution


def _nested_region(metadata: Mapping[str, object], key: str) -> object:
    region = metadata.get("region", {})
    return region.get(key) if isinstance(region, dict) else None


def _find_strong_match(
    candidate: ExhibitionCandidate,
    institution: Institution,
) -> Exhibition | None:
    possible = Exhibition.objects.select_for_update().filter(
        institution=institution,
        start_date=candidate.start_date,
        end_date=candidate.end_date,
    )
    title_key = _comparison_text(candidate.title)
    venue_key = _comparison_text(candidate.venue)
    return next(
        (
            exhibition
            for exhibition in possible
            if _comparison_text(exhibition.title) == title_key
            and _comparison_text(exhibition.venue) == venue_key
        ),
        None,
    )


def _find_similar_exhibitions(
    candidate: ExhibitionCandidate,
    institution: Institution,
) -> tuple[Exhibition, ...]:
    title_key = _comparison_text(candidate.title)
    if not title_key:
        return ()
    return tuple(
        exhibition
        for exhibition in Exhibition.objects.filter(institution=institution)
        if _comparison_text(exhibition.title) == title_key
    )


def _comparison_text(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "".join(
        character
        for character in normalized
        if not character.isspace()
        and not unicodedata.category(character).startswith("P")
    )


def _create_exhibition(
    candidate: ExhibitionCandidate,
    institution: Institution,
) -> Exhibition:
    return Exhibition.objects.create(
        institution=institution,
        **{field: getattr(candidate, field) for field in CANONICAL_FIELDS},
        freshness=Exhibition.Freshness.FRESH,
        eligibility=Exhibition.Eligibility.VERIFIED,
    )


def _link_source(
    exhibition: Exhibition,
    candidate: ExhibitionCandidate,
) -> ExhibitionSourceLink:
    source_record = candidate.source_record
    return ExhibitionSourceLink.objects.create(
        exhibition=exhibition,
        source_id=source_record.source_id,
        source_record_id=source_record.source_record_id,
        latest_source_record=source_record,
    )


def _record_initial_evidence(
    exhibition: Exhibition,
    candidate: ExhibitionCandidate,
) -> None:
    for field_name in CANONICAL_FIELDS:
        _record_evidence(
            exhibition,
            candidate,
            field_name,
            adopted=True,
            decision_reason="INITIAL_VERIFIED_SOURCE",
        )


def _merge_same_source_version(
    exhibition: Exhibition,
    candidate: ExhibitionCandidate,
) -> int:
    changed_fields: list[str] = []
    conflict_count = 0
    for field_name in CANONICAL_FIELDS:
        current_value = getattr(exhibition, field_name)
        candidate_value = getattr(candidate, field_name)
        if current_value == candidate_value:
            _record_evidence(
                exhibition,
                candidate,
                field_name,
                adopted=True,
                decision_reason="REVERIFIED_SOURCE_VALUE",
            )
            continue

        other_source_support = FieldEvidence.objects.filter(
            exhibition=exhibition,
            field_name=field_name,
            adopted=True,
        ).exclude(
            source_record__source_id=candidate.source_record.source_id,
            source_record__source_record_id=candidate.source_record.source_record_id,
        )
        if other_source_support.exists():
            _record_evidence(
                exhibition,
                candidate,
                field_name,
                adopted=False,
                decision_reason="CONFLICT_PRESERVED",
            )
            conflict_count += _record_conflict(
                exhibition,
                candidate,
                field_name,
                current_value,
                candidate_value,
            )
            continue

        FieldEvidence.objects.filter(
            exhibition=exhibition,
            field_name=field_name,
            adopted=True,
        ).update(adopted=False)
        setattr(exhibition, field_name, candidate_value)
        changed_fields.append(field_name)
        _record_evidence(
            exhibition,
            candidate,
            field_name,
            adopted=True,
            decision_reason="SAME_SOURCE_UPDATE",
        )

    _finish_merge(exhibition, changed_fields, conflict_count)
    return conflict_count


def _merge_additional_source(
    exhibition: Exhibition,
    candidate: ExhibitionCandidate,
) -> int:
    conflict_count = 0
    for field_name in CANONICAL_FIELDS:
        current_value = getattr(exhibition, field_name)
        candidate_value = getattr(candidate, field_name)
        adopted = current_value == candidate_value
        _record_evidence(
            exhibition,
            candidate,
            field_name,
            adopted=adopted,
            decision_reason=(
                "STRONG_MATCH_SUPPORT" if adopted else "CONFLICT_PRESERVED"
            ),
        )
        if not adopted:
            conflict_count += _record_conflict(
                exhibition,
                candidate,
                field_name,
                current_value,
                candidate_value,
            )

    _finish_merge(exhibition, [], conflict_count)
    return conflict_count


def _finish_merge(
    exhibition: Exhibition,
    changed_fields: list[str],
    new_conflict_count: int,
) -> None:
    exhibition.last_verified_at = timezone.now()
    exhibition.freshness = Exhibition.Freshness.FRESH
    has_open_conflict = new_conflict_count > 0 or SourceConflict.objects.filter(
        exhibition=exhibition,
        status=SourceConflict.Status.OPEN,
    ).exists()
    exhibition.eligibility = (
        Exhibition.Eligibility.EXCLUDED
        if has_open_conflict
        else Exhibition.Eligibility.VERIFIED
    )
    exhibition.save(
        update_fields=(
            *changed_fields,
            "last_verified_at",
            "freshness",
            "eligibility",
            "updated_at",
        )
    )


def _record_evidence(
    exhibition: Exhibition,
    candidate: ExhibitionCandidate,
    field_name: str,
    *,
    adopted: bool,
    decision_reason: str,
) -> FieldEvidence:
    value = getattr(candidate, field_name)
    evidence, _ = FieldEvidence.objects.get_or_create(
        exhibition=exhibition,
        source_record=candidate.source_record,
        field_name=field_name,
        defaults={
            "candidate": candidate,
            "canonical_value": _serialized(value),
            "raw_value": candidate.source_record.payload.get(field_name),
            "adopted": adopted,
            "decision_reason": decision_reason,
        },
    )
    return evidence


def _record_conflict(
    exhibition: Exhibition,
    candidate: ExhibitionCandidate,
    field_name: str,
    current_value: object,
    candidate_value: object,
) -> int:
    _, created = SourceConflict.objects.get_or_create(
        exhibition=exhibition,
        field_name=field_name,
        candidate_source_record=candidate.source_record,
        defaults={
            "canonical_value": _serialized(current_value),
            "candidate_value": _serialized(candidate_value),
        },
    )
    return int(created)


def _serialized(value: object) -> str:
    if isinstance(value, date):
        return value.isoformat()
    return str(value)

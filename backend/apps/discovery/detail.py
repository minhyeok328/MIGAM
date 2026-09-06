"""Catalog detail reads using canonical visibility and shared visit resolution."""

from ipaddress import ip_address
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.db.models import Case, F, IntegerField, Prefetch, When, prefetch_related_objects
from django.utils import timezone

from backend.apps.catalog.models import (
    AccessibilityFact, Exhibition, Institution, OperatingSchedule, PriceOption,
    ReservationInfo, SensoryNotice, SourceConflict, VisitDuration,
)
from backend.apps.discovery.models import ContentFeatureAssertion
from backend.apps.discovery.operating_schedule import OperatingScheduleResolver, OpeningState
from backend.apps.discovery.presenters import _load_exhibitions, present_exhibition
from backend.apps.discovery.visit_conditions import (
    EvidenceState, VisitEvidenceResolver, _is_adult_standard_price_evidence,
    _related_rows, _select_precedence_rows,
)


_HTTPS_VALIDATOR = URLValidator(schemes=("https",))
_LIFECYCLES = ("CURRENT", "UPCOMING", "ENDED", "CANCELED")
_EVIDENCE_MODELS = (
    ("priceoption_records", PriceOption),
    ("reservationinfo_records", ReservationInfo),
    ("visitduration_records", VisitDuration),
    ("accessibilityfact_records", AccessibilityFact),
    ("sensorynotice_records", SensoryNotice),
    ("operatingschedule_records", OperatingSchedule),
)


def _safe_url(value: str | None) -> str | None:
    if not value or any(ord(character) <= 32 for character in value) or "\\" in value:
        return None
    try:
        _HTTPS_VALIDATOR(value)
        parsed = urlsplit(value)
        host = parsed.hostname
        if not host or parsed.username is not None or parsed.password is not None:
            return None
        if host == "localhost" or host.endswith(".localhost"):
            return None
        try:
            if not ip_address(host).is_global:
                return None
        except ValueError:
            pass
        return value
    except (ValidationError, ValueError):
        return None


def _visible_exhibitions():
    # Use live canonical gates rather than trusting an older search projection.
    # Institution health/lifecycle alone must not discard last-good canonical facts.
    return (
        Exhibition.objects.filter(
            eligibility=Exhibition.Eligibility.VERIFIED,
            freshness__in=(Exhibition.Freshness.FRESH, Exhibition.Freshness.STALE),
            lifecycle__in=_LIFECYCLES,
            end_date__gte=F("start_date"),
            source_links__latest_source_record__institution_id=F("institution__registry_id"),
            source_links__latest_source_record__source_id=F("source_links__source_id"),
            source_links__latest_source_record__source_record_id=F("source_links__source_record_id"),
        )
        .exclude(source_conflicts__status=SourceConflict.Status.OPEN)
        .exclude(source_links__latest_source_record__source_owner="")
        .distinct()
    )


def _has_displayable_core(exhibition: Exhibition) -> bool:
    return bool(
        all(value.strip() for value in (
            exhibition.title, exhibition.venue,
            exhibition.region_area, exhibition.region_district,
        ))
        and _safe_url(exhibition.official_url)
    )


def _prepare_exhibition(exhibition: Exhibition) -> None:
    exhibition.search_source_links = [
        link for link in exhibition.search_source_links
        if link.latest_source_record.institution_id == exhibition.institution.registry_id
        and link.latest_source_record.source_id == link.source_id
        and link.latest_source_record.source_record_id == link.source_record_id
        and link.latest_source_record.source_owner.strip()
    ]
    exhibition.recommendation_source_links = exhibition.search_source_links


def _safe_exhibition(exhibition: Exhibition) -> dict[str, object]:
    _prepare_exhibition(exhibition)
    result = present_exhibition(exhibition)
    media = result["media"]
    if media["status"] != "HIDDEN":
        page_url = _safe_url(media["page_url"])
        media_url = _safe_url(media["media_url"])
        if page_url is None:
            result["media"] = {"status": "HIDDEN", "media_url": None, "page_url": None, "credit_line": None}
        elif media["status"] == "INLINE" and media_url is None:
            result["media"] = {**media, "status": "LINK_ONLY", "media_url": None}
    return result


@transaction.atomic
def exhibition_detail(exhibition_id: int) -> dict[str, object] | None:
    visible = _visible_exhibitions().filter(pk=exhibition_id).first()
    if visible is None or not _has_displayable_core(visible):
        return None
    exhibition = _load_exhibitions((exhibition_id,))[exhibition_id]
    presented = _safe_exhibition(exhibition)
    prefetches = []
    for name, model in _EVIDENCE_MODELS:
        for prefix in ("", "institution__"):
            prefetches.append(Prefetch(
                f"{prefix}{name}", queryset=model.objects.select_related("source_record"),
                to_attr=f"recommendation_{name}",
            ))
    prefetch_related_objects([exhibition], *prefetches)
    current_ids = {link.latest_source_record_id for link in exhibition.search_source_links}
    resolved = VisitEvidenceResolver().resolve(exhibition)

    def rows(name: str, *, kind: str | None = None, adult_price: bool = False) -> list:
        def selected(target: object) -> list:
            return [row for row in _related_rows(target, name)
                    if (kind is None or row.kind == kind)
                    and (not adult_price or _is_adult_standard_price_evidence(row))]
        return _select_precedence_rows(selected(exhibition), selected(exhibition.institution), current_ids)

    price_rows = rows("priceoption_records", adult_price=True)
    reservation_rows = rows("reservationinfo_records")
    duration_rows = rows("visitduration_records")
    visit_information = {
        "price": {
            "state": resolved.price.state,
            "amount": float(resolved.price.amount) if resolved.price.amount is not None else None,
            "currency": resolved.price.currency, "is_free": resolved.price.is_free,
            "evidence": [_evidence(row) for row in price_rows],
        },
        "reservation": {
            "state": resolved.reservation.state,
            "reservation_type": resolved.reservation.reservation_type,
            "official_urls": sorted({url for row in reservation_rows if (url := _safe_url(row.official_url))})
            if resolved.reservation.state == EvidenceState.CONFIRMED else [],
            "guidance": _confirmed_text(resolved.reservation.state, reservation_rows, "guidance"),
            "evidence": [_evidence(row) for row in reservation_rows],
        },
        "duration": {
            "state": resolved.duration.state,
            "minimum_minutes": resolved.duration.minimum_minutes,
            "maximum_minutes": resolved.duration.maximum_minutes,
            "evidence": [_evidence(row) for row in duration_rows],
        },
        "accessibility": [
            _fact(kind, fact, rows("accessibilityfact_records", kind=kind))
            for kind, fact in resolved.accessibility.items()
        ],
        "sensory": [
            _fact(kind, fact, rows("sensorynotice_records", kind=kind))
            for kind, fact in resolved.sensory.items()
        ],
    }
    features = ContentFeatureAssertion.objects.filter(
        snapshot__exhibition=exhibition, snapshot__is_current=True,
        source_record_id__in=current_ids,
    ).select_related("source_record").order_by("axis", "value")
    return {
        "exhibition": presented,
        "visit_information": visit_information,
        "features": [{
            "axis": row.axis, "value": row.value, "evidence_kind": row.evidence_kind,
            "rule_version": row.rule_version or None, "source": _source(row.source_record),
        } for row in features],
        "operating_schedule": _schedule(exhibition, current_ids),
    }


def _source(record) -> dict[str, object]:
    return {
        "source_id": record.source_id, "source_record_id": record.source_record_id,
        "source_owner": record.source_owner, "last_seen_at": record.last_seen_at,
    }


def _evidence(row) -> dict[str, object]:
    return {
        "scope": "EXHIBITION" if row.exhibition_id is not None else "INSTITUTION",
        "verified_at": row.verified_at, "source": _source(row.source_record),
    }


def _confirmed_text(state: EvidenceState, rows: list, field: str) -> list[str]:
    if state != EvidenceState.CONFIRMED:
        return []
    return sorted({text for row in rows if (text := getattr(row, field).strip()[:2000])})


def _fact(kind: str, fact, rows: list) -> dict[str, object]:
    return {
        "kind": kind, "state": fact.state, "value": fact.value,
        "details": _confirmed_text(fact.state, rows, "details"),
        "evidence": [_evidence(row) for row in rows],
    }


def _schedule(exhibition: Exhibition, current_ids: set[int]) -> dict[str, object]:
    rows = [row for target in (exhibition, exhibition.institution)
            for row in _related_rows(target, "operatingschedule_records")
            if row.source_record_id in current_ids
            and row.effective_from <= exhibition.end_date
            and row.effective_to >= exhibition.start_date]
    state = OpeningState.UNKNOWN
    availability = None
    today = timezone.localdate()
    if exhibition.lifecycle in ("CURRENT", "UPCOMING") and today <= exhibition.end_date:
        resolved = OperatingScheduleResolver().resolve(exhibition, today, exhibition.end_date)
        state = resolved.state
        if state == OpeningState.OPEN:
            availability = {
                "first_open_date": resolved.first_open_date,
                "opens_at": resolved.opens_at.isoformat(timespec="seconds"),
                "closes_at": resolved.closes_at.isoformat(timespec="seconds"),
                "verified_at": resolved.verified_at,
            }
    return {
        "state": state, "visit_availability": availability,
        "rules": [{
            "status": row.status, "kind": row.kind,
            "effective_from": row.effective_from, "effective_to": row.effective_to,
            "weekdays": row.weekdays, "is_open": row.is_open,
            "opens_at": row.opens_at.isoformat(timespec="seconds") if row.opens_at else None,
            "closes_at": row.closes_at.isoformat(timespec="seconds") if row.closes_at else None,
            "rule_version": row.rule_version, "evidence": _evidence(row),
        } for row in rows],
    }


@transaction.atomic
def institution_detail(institution_id: int, *, page: int = 1, page_size: int = 24) -> dict[str, object] | None:
    institution = Institution.objects.filter(pk=institution_id).first()
    if institution is None:
        return None
    candidates = _visible_exhibitions().filter(institution=institution).annotate(
        lifecycle_order=Case(
            *(When(lifecycle=value, then=index) for index, value in enumerate(_LIFECYCLES)),
            output_field=IntegerField(),
        ),
    ).order_by("lifecycle_order", "-start_date", "title", "id")
    ids = [row.pk for row in candidates if _has_displayable_core(row)]
    if not ids:
        return None
    offset = (page - 1) * page_size
    selected = ids[offset:offset + page_size]
    exhibitions = _load_exhibitions(selected)
    return {
        "institution": {
            "type": "INSTITUTION", "id": institution.pk, "name": institution.name,
            "region": {"area": institution.region_area, "district": institution.region_district},
            "searchable_exhibition_count": len(ids),
        },
        "total": len(ids), "page": page, "page_size": page_size,
        "has_more": offset + len(selected) < len(ids),
        "exhibitions": [_safe_exhibition(exhibitions[identifier]) for identifier in selected],
    }

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import TypeVar

from backend.apps.catalog.models import (
    AccessibilityFact,
    Exhibition,
    PriceOption,
    ReservationInfo,
    SensoryNotice,
    VisitDuration,
)


class EvidenceState(StrEnum):
    CONFIRMED = "CONFIRMED"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True, slots=True)
class ResolvedPrice:
    state: EvidenceState
    amount: Decimal | None = None
    currency: str | None = None
    is_free: bool | None = None


@dataclass(frozen=True, slots=True)
class ResolvedReservation:
    state: EvidenceState
    reservation_type: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedDuration:
    state: EvidenceState
    minimum_minutes: int | None = None
    maximum_minutes: int | None = None


@dataclass(frozen=True, slots=True)
class ResolvedThreeStateFact:
    state: EvidenceState
    value: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedVisitEvidence:
    price: ResolvedPrice
    reservation: ResolvedReservation
    duration: ResolvedDuration
    accessibility: Mapping[str, ResolvedThreeStateFact]
    sensory: Mapping[str, ResolvedThreeStateFact]


_Row = TypeVar("_Row")
_Value = TypeVar("_Value")
_UNKNOWN = object()


class VisitEvidenceResolver:
    def resolve(self, exhibition: Exhibition) -> ResolvedVisitEvidence:
        current_source_record_ids = _current_source_record_ids(exhibition)
        institution = exhibition.institution

        exhibition_prices = [
            row
            for row in _related_rows(exhibition, "priceoption_records")
            if _is_adult_standard_price_evidence(row)
        ]
        institution_prices = [
            row
            for row in _related_rows(institution, "priceoption_records")
            if _is_adult_standard_price_evidence(row)
        ]
        price_rows = _select_precedence_rows(
            exhibition_prices,
            institution_prices,
            current_source_record_ids,
        )

        reservation_rows = _select_precedence_rows(
            _related_rows(exhibition, "reservationinfo_records"),
            _related_rows(institution, "reservationinfo_records"),
            current_source_record_ids,
        )
        duration_rows = _select_precedence_rows(
            _related_rows(exhibition, "visitduration_records"),
            _related_rows(institution, "visitduration_records"),
            current_source_record_ids,
        )

        accessibility = {
            kind: _resolve_fact(
                _select_precedence_rows(
                    [
                        row
                        for row in _related_rows(
                            exhibition,
                            "accessibilityfact_records",
                        )
                        if row.kind == kind
                    ],
                    [
                        row
                        for row in _related_rows(
                            institution,
                            "accessibilityfact_records",
                        )
                        if row.kind == kind
                    ],
                    current_source_record_ids,
                )
            )
            for kind in AccessibilityFact.Kind.values
        }
        sensory = {
            kind: _resolve_fact(
                _select_precedence_rows(
                    [
                        row
                        for row in _related_rows(
                            exhibition,
                            "sensorynotice_records",
                        )
                        if row.kind == kind
                    ],
                    [
                        row
                        for row in _related_rows(
                            institution,
                            "sensorynotice_records",
                        )
                        if row.kind == kind
                    ],
                    current_source_record_ids,
                )
            )
            for kind in SensoryNotice.Kind.values
        }

        return ResolvedVisitEvidence(
            price=_resolve_price(price_rows),
            reservation=_resolve_reservation(reservation_rows),
            duration=_resolve_duration(duration_rows),
            accessibility=accessibility,
            sensory=sensory,
        )


def _current_source_record_ids(exhibition: Exhibition) -> set[int]:
    prefetched = getattr(exhibition, "recommendation_source_links", None)
    if prefetched is not None:
        return {link.latest_source_record_id for link in prefetched}
    return set(
        exhibition.source_links.values_list("latest_source_record_id", flat=True)
    )


def _related_rows(target: object, related_name: str) -> list[object]:
    prefetched_name = f"recommendation_{related_name}"
    prefetched = getattr(target, prefetched_name, None)
    if prefetched is not None:
        return list(prefetched)
    manager = getattr(target, related_name)
    return list(manager.select_related("source_record").all())


def _select_precedence_rows(
    exhibition_rows: Iterable[_Row],
    institution_rows: Iterable[_Row],
    current_source_record_ids: set[int],
) -> list[_Row]:
    current_exhibition_rows = [
        row
        for row in exhibition_rows
        if row.source_record_id in current_source_record_ids
    ]
    if current_exhibition_rows:
        return current_exhibition_rows

    fallback_rows = list(institution_rows)
    if not fallback_rows:
        return []
    latest_verified_at = max(row.verified_at for row in fallback_rows)
    return [
        row for row in fallback_rows if row.verified_at == latest_verified_at
    ]


def _is_adult_standard_price_evidence(row: PriceOption) -> bool:
    return (
        row.status == PriceOption.Status.UNKNOWN
        or row.is_standard_adult_admission
    )


def _collapse_values(
    rows: Iterable[_Row],
    normalizer: Callable[[_Row], _Value | object],
) -> tuple[EvidenceState, _Value | None]:
    values = {normalizer(row) for row in rows}
    if not values or values == {_UNKNOWN}:
        return EvidenceState.UNKNOWN, None
    if _UNKNOWN in values or len(values) > 1:
        return EvidenceState.CONFLICT, None
    return EvidenceState.CONFIRMED, next(iter(values))


def _resolve_price(rows: Iterable[PriceOption]) -> ResolvedPrice:
    def normalize(
        row: PriceOption,
    ) -> tuple[bool, Decimal, str | None] | object:
        if row.status == PriceOption.Status.UNKNOWN:
            return _UNKNOWN
        if row.is_free:
            return True, Decimal("0"), None
        amount = row.amount_max if row.amount_max is not None else row.amount_min
        if amount is None:
            return _UNKNOWN
        return False, amount, row.currency

    state, value = _collapse_values(rows, normalize)
    if state != EvidenceState.CONFIRMED or value is None:
        return ResolvedPrice(state=state)
    is_free, amount, currency = value
    return ResolvedPrice(
        state=state,
        amount=amount,
        currency=currency,
        is_free=is_free,
    )


def _resolve_reservation(
    rows: Iterable[ReservationInfo],
) -> ResolvedReservation:
    state, value = _collapse_values(
        rows,
        lambda row: (
            _UNKNOWN
            if row.reservation_type == ReservationInfo.Type.UNKNOWN
            else row.reservation_type
        ),
    )
    return ResolvedReservation(
        state=state,
        reservation_type=value if isinstance(value, str) else None,
    )


def _resolve_duration(rows: Iterable[VisitDuration]) -> ResolvedDuration:
    state, value = _collapse_values(
        rows,
        lambda row: (
            _UNKNOWN
            if row.status == VisitDuration.Status.UNKNOWN
            else (row.minimum_minutes, row.maximum_minutes)
        ),
    )
    if state != EvidenceState.CONFIRMED or value is None:
        return ResolvedDuration(state=state)
    minimum_minutes, maximum_minutes = value
    return ResolvedDuration(
        state=state,
        minimum_minutes=minimum_minutes,
        maximum_minutes=maximum_minutes,
    )


def _resolve_fact(rows: Iterable[object]) -> ResolvedThreeStateFact:
    state, value = _collapse_values(
        rows,
        lambda row: (
            _UNKNOWN if row.state == row.State.UNKNOWN else row.state
        ),
    )
    return ResolvedThreeStateFact(
        state=state,
        value=value if isinstance(value, str) else None,
    )

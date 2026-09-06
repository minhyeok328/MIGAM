"""Deterministic optional evidence from the current approved source versions."""

from collections.abc import Iterable
from decimal import Decimal
from datetime import time
import re

from django.db import transaction

from backend.apps.catalog.models import Exhibition, OperatingSchedule, PriceOption
from backend.apps.discovery.features import FeatureAssertionInput, record_content_feature_snapshot
from backend.apps.discovery.models import ContentFeatureSnapshot
from backend.data_pipeline.registry import SourceRegistry


RULE_VERSION = "source-optional-1.0.0"
MEDIA = {
    "회화": "PAINTING", "조각": "SCULPTURE", "공예": "CRAFT",
    "사진": "PHOTOGRAPHY", "영상": "VIDEO", "사운드": "SOUND",
    "설치": "INSTALLATION", "퍼포먼스": "PERFORMANCE",
    "인터랙티브": "INTERACTIVE", "미디어아트": "MEDIA_ART",
    "디자인": "DESIGN", "건축": "ARCHITECTURE",
}


def price_fields(value: object) -> dict[str, object]:
    text = re.sub(r"\s+", "", str(value or ""))
    amount = None
    if text in {"무료", "무료관람", "무료입장"}:
        amount = Decimal(0)
    else:
        match = re.fullmatch(r"(?:(?:성인|일반)(?:기본권|관람료)?[:：]?)?(0|[1-9][0-9]{0,8}|[1-9][0-9]{0,2}(?:,[0-9]{3}){1,2})원", text)
        if match:
            amount = Decimal(match[1].replace(",", ""))
    if amount is None:
        return {"status": PriceOption.Status.UNKNOWN}
    return {
        "status": PriceOption.Status.CONFIRMED,
        "category": PriceOption.Category.STANDARD, "audience": "ADULT",
        "currency": "KRW", "amount_min": amount, "amount_max": amount,
        "is_free": amount == 0, "is_standard_adult_admission": True,
        "details": str(value),
    }


def schedule_fields(value: object) -> list[dict[str, object]]:
    text = re.sub(r"\s+", "", str(value or ""))
    hours = r"([0-9]{1,2}):([0-9]{2})[~～-]([0-9]{1,2}):([0-9]{2})"
    daily = re.fullmatch("매일" + hours, text)
    weekly = re.fullmatch(hours + r"\((?:매주)?([월화수목금토일])요일휴관\)", text)
    match = daily or weekly
    unknown = [{"status": "UNKNOWN", "kind": "REGULAR", "details": str(value or "")}]
    if not match:
        return unknown
    try:
        opens_at = time(int(match[1]), int(match[2]))
        closes_at = time(int(match[3]), int(match[4]))
    except ValueError:
        return unknown
    if opens_at >= closes_at:
        return unknown
    closed_day = "월화수목금토일".index(match[5]) if weekly else None
    rows = [{
        "status": "CONFIRMED", "kind": "REGULAR", "is_open": True,
        "weekdays": [day for day in range(7) if day != closed_day],
        "opens_at": opens_at, "closes_at": closes_at, "details": str(value),
    }]
    if closed_day is not None:
        rows.append({"status": "CONFIRMED", "kind": "REGULAR", "is_open": False, "weekdays": [closed_day], "details": str(value)})
    return rows


@transaction.atomic
def backfill_source_evidence(
    registry: SourceRegistry, *, exhibition_ids: Iterable[int] | None = None,
) -> int:
    exhibitions = Exhibition.objects.select_for_update().select_related("institution").prefetch_related("source_links__latest_source_record")
    if exhibition_ids is not None:
        exhibitions = exhibitions.filter(pk__in=exhibition_ids)
    count = 0
    for exhibition in exhibitions:
        assertions = {}
        handles_media = False
        for link in exhibition.source_links.all():
            if link.source_id not in registry.source_ids:
                continue
            source = registry.source(link.source_id)
            fields = source.get("optional_fields", {})
            record = link.latest_source_record
            if record.institution_id != exhibition.institution.registry_id:
                continue
            raw = record.payload.get("source_payload", {})
            if "operating_schedule" in fields and not OperatingSchedule.objects.filter(
                exhibition=exhibition, source_record=record, rule_version=RULE_VERSION,
            ).exists():
                for values in schedule_fields(raw.get(fields["operating_schedule"])):
                    OperatingSchedule.objects.create(
                        exhibition=exhibition, source_record=record,
                        effective_from=exhibition.start_date, effective_to=exhibition.end_date,
                        rule_version=RULE_VERSION, verified_at=record.last_seen_at, **values,
                    )
            OperatingSchedule.objects.filter(
                exhibition=exhibition, source_record=record, rule_version=RULE_VERSION,
                verified_at__lt=record.last_seen_at,
            ).update(verified_at=record.last_seen_at)
            if "price" in fields:
                values = price_fields(raw.get(fields["price"]))
                price, _ = PriceOption.objects.get_or_create(
                    exhibition=exhibition, source_record=record,
                    category=values.get("category", ""), audience=values.get("audience", ""),
                    defaults={**values, "verified_at": record.last_seen_at, "rule_version": RULE_VERSION},
                )
                if all(getattr(price, field) == value for field, value in values.items()):
                    price.verified_at = max(price.verified_at, record.last_seen_at)
                    price.rule_version = RULE_VERSION
                    price.save(update_fields=("verified_at", "rule_version"))
            if "media" in fields:
                handles_media = True
                for token in re.split(r"[,·/、]", str(raw.get(fields["media"]) or "")):
                    code = MEDIA.get(token.strip())
                    if code:
                        assertions.setdefault(code, FeatureAssertionInput(
                            axis="MEDIA_GROUP", value=code, evidence_kind="DERIVED",
                            source_record=record, rule_version=RULE_VERSION,
                        ))
        if handles_media:
            current = ContentFeatureSnapshot.objects.filter(exhibition=exhibition, is_current=True).first()
            combined = {(item.axis, item.value): item for item in assertions.values()}
            if current:
                for item in current.assertions.select_related("source_record"):
                    if item.rule_version != RULE_VERSION:
                        combined[(item.axis, item.value)] = FeatureAssertionInput(
                            axis=item.axis, value=item.value, evidence_kind=item.evidence_kind,
                            source_record=item.source_record, rule_version=item.rule_version,
                        )
            inputs = tuple(combined[key] for key in sorted(combined))
            keys = {(item.axis, item.value, item.source_record.pk, item.rule_version, item.evidence_kind) for item in inputs}
            existing = set(current.assertions.values_list("axis", "value", "source_record_id", "rule_version", "evidence_kind")) if current else None
            if current is None or existing != keys:
                record_content_feature_snapshot(exhibition=exhibition, assertions=inputs)
                count += 1
    return count

"""Fictional, opt-in records for an isolated TP-006 demonstration database."""

from datetime import timedelta
from decimal import Decimal
from hashlib import sha256

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from backend.apps.catalog.models import (
    AccessibilityFact, Exhibition, ExhibitionSourceLink, Institution,
    PriceOption, ReservationInfo, SensoryNotice, VisitDuration,
)
from backend.apps.discovery.features import FeatureAssertionInput, record_content_feature_snapshot
from backend.apps.discovery.projection import rebuild_search_documents
from backend.apps.sources.models import SourceRecord


@transaction.atomic
def seed_demo() -> None:
    if not getattr(settings, "MIGAM_DEMO_MODE", False):
        raise RuntimeError("Demo seeding requires explicit isolated demo mode.")
    if Institution.objects.exists() or Exhibition.objects.exists() or SourceRecord.objects.exists():
        raise RuntimeError("Demo seeding refuses a database containing existing records.")

    institutions = [
        Institution.objects.create(registry_id=f"fictional-{index}", name=name, region_area=area, region_district=district)
        for index, (name, area, district) in enumerate((
            ("미감 미술관 · 가상", "서울", "종로구"),
            ("여백 아트센터 · 가상", "경기", "수원시"),
            ("공간 사이 · 가상", "인천", "중구"),
        ))
    ]
    titles = (
        ("고요의 형태", "CALM", "PHOTOGRAPHY"),
        ("빛이 머무는 자리", "IMMERSIVE", "MOVING_IMAGE_DIGITAL"),
        ("선과 선 사이", "REFLECTIVE", "PAINTING"),
        ("소리, 보이지 않는 풍경", "CALM", "SOUND_PERFORMANCE"),
        ("도시의 작은 장면들", "LIVELY", "PHOTOGRAPHY"),
        ("낯선 감각의 방", "EXPERIMENTAL", "INSTALLATION"),
        ("움직임의 언어", "PARTICIPATORY", "SOUND_PERFORMANCE"),
        ("오래된 미래", "REFLECTIVE", "MOVING_IMAGE_DIGITAL"),
        ("지난 계절의 기록", "CALM", "PAINTING"),
        ("취소된 가상 전시", "LIVELY", "INSTALLATION"),
    )
    today = timezone.localdate()
    for index, (title, mood, media) in enumerate(titles):
        institution = institutions[index % len(institutions)]
        record_id = f"fictional-exhibition-{index}"
        source = SourceRecord.objects.create(
            source_id="fictional-demo-only", institution_id=institution.registry_id,
            source_record_id=record_id, source_owner=institution.name,
            payload={"fictional": True, "title": title, "mood": mood, "media": media},
            content_hash=sha256(record_id.encode()).hexdigest(),
        )
        lifecycle = Exhibition.Lifecycle.CURRENT
        start, end = today - timedelta(days=12 + index), today + timedelta(days=40 + index * 5)
        if index in (6, 7):
            lifecycle, start = Exhibition.Lifecycle.UPCOMING, today + timedelta(days=7 + index)
        elif index == 8:
            lifecycle, start, end = Exhibition.Lifecycle.ENDED, today - timedelta(days=90), today - timedelta(days=30)
        elif index == 9:
            lifecycle = Exhibition.Lifecycle.CANCELED
        exhibition = Exhibition.objects.create(
            institution=institution, title=title, start_date=start, end_date=end,
            venue=f"{institution.name} 전시장", region_area=institution.region_area,
            region_district=institution.region_district, lifecycle=lifecycle,
            official_url=f"https://example.com/fictional/{index}",
            freshness=Exhibition.Freshness.STALE if index == 5 else Exhibition.Freshness.FRESH,
            eligibility=Exhibition.Eligibility.VERIFIED,
        )
        ExhibitionSourceLink.objects.create(
            exhibition=exhibition, source_id=source.source_id,
            source_record_id=source.source_record_id, latest_source_record=source,
        )
        record_content_feature_snapshot(exhibition=exhibition, assertions=(
            FeatureAssertionInput(axis="MOOD", value=mood, evidence_kind="DIRECT", source_record=source),
            FeatureAssertionInput(axis="MEDIA_GROUP", value=media, evidence_kind="DIRECT", source_record=source),
        ))
        if index == 3:
            PriceOption.objects.create(exhibition=exhibition, source_record=source, status=PriceOption.Status.UNKNOWN)
        else:
            amount = Decimal(0 if index % 3 == 0 else 8000 + index * 1000)
            PriceOption.objects.create(
                exhibition=exhibition, source_record=source, status=PriceOption.Status.CONFIRMED,
                category=PriceOption.Category.STANDARD, audience="ADULT", currency="KRW",
                amount_min=amount, amount_max=amount, is_free=amount == 0, is_standard_adult_admission=True,
            )
        ReservationInfo.objects.create(
            exhibition=exhibition, source_record=source,
            reservation_type=ReservationInfo.Type.UNKNOWN if index == 3 else ReservationInfo.Type.NOT_REQUIRED,
        )
        VisitDuration.objects.create(
            exhibition=exhibition, source_record=source,
            status=VisitDuration.Status.OFFICIAL, minimum_minutes=30, maximum_minutes=60 + index * 10,
        )
        AccessibilityFact.objects.create(
            exhibition=exhibition, source_record=source, kind=AccessibilityFact.Kind.WHEELCHAIR_ACCESS,
            state=AccessibilityFact.State.CONFIRMED_POSITIVE if index % 2 == 0 else AccessibilityFact.State.UNKNOWN,
        )
        SensoryNotice.objects.create(
            exhibition=exhibition, source_record=source, kind=SensoryNotice.Kind.FLASHING_LIGHTS,
            state=SensoryNotice.State.CONFIRMED_NEGATIVE if index % 2 == 0 else SensoryNotice.State.UNKNOWN,
        )
    rebuild_search_documents()

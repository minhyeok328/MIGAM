"""Fictional, opt-in records for an isolated TP-006 demonstration database."""

from datetime import time, timedelta
from decimal import Decimal
from hashlib import sha256

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from backend.apps.catalog.models import (
    AccessibilityFact, Artwork, ArtworkFeatureAssertion, Exhibition, ExhibitionSourceLink, Institution,
    OperatingSchedule, PriceOption, ReservationInfo, SensoryNotice, VisitDuration,
)
from backend.apps.discovery.features import FeatureAssertionInput, record_content_feature_snapshot
from backend.apps.discovery.projection import rebuild_search_documents
from backend.apps.sources.models import SourceRecord


@transaction.atomic
def seed_demo() -> None:
    if not getattr(settings, "MIGAM_DEMO_MODE", False):
        raise RuntimeError("Demo seeding requires explicit isolated demo mode.")
    if Institution.objects.exists() or Exhibition.objects.exists() or SourceRecord.objects.exists() or Artwork.objects.exists():
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
        for weekdays, is_open in (([1, 2, 3, 4, 5, 6], True), ([0], False)):
            OperatingSchedule.objects.create(
                exhibition=exhibition, source_record=source,
                status=OperatingSchedule.Status.CONFIRMED, kind=OperatingSchedule.Kind.REGULAR,
                effective_from=start, effective_to=end, weekdays=weekdays, is_open=is_open,
                opens_at=time(10) if is_open else None, closes_at=time(18) if is_open else None,
                details="가상 데모 일정: 화~일 10:00~18:00, 월요일 휴관",
                rule_version="fictional-demo-v1",
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
    _seed_artworks(institutions)
    rebuild_search_documents()


def _seed_artworks(institutions: list[Institution]) -> None:
    """Private helper called only inside the guarded, atomic isolated demo seed."""
    for index, (title, creator, creator_id, year, medium, media, mood, institution_index) in enumerate((
        ("푸른 여백 · 가상", "가상 작가 하나", "fictional-creator-1", "2024", "캔버스에 유채", "PAINTING", "CALM", 0),
        ("겹친 계절 · 가상", "가상 작가 하나", "fictional-creator-1", "2025", "종이에 채색", "PAINTING", "REFLECTIVE", 1),
        ("오후의 기록 · 가상", "가상 작가 둘", "fictional-creator-2", "2023", "사진", "PHOTOGRAPHY", "CALM", 0),
        ("이름 없는 공간 · 가상", "작자 미상 · 가상", "", "제작연도 미상", "복합 재료", "INSTALLATION", "EXPERIMENTAL", 2),
    )):
        institution = institutions[institution_index]
        record_id = f"fictional-artwork-{index}"
        source = SourceRecord.objects.create(
            source_id="fictional-demo-only", institution_id=institution.registry_id,
            source_record_id=record_id, source_owner=institution.name,
            payload={"fictional": True, "title": title, "media": media, "mood": mood},
            content_hash=sha256(record_id.encode()).hexdigest(),
        )
        artwork = Artwork.objects.create(
            source_id=source.source_id, source_artwork_id=record_id, source_record=source,
            title=title, creator_name=creator, creator_official_id=creator_id,
            creator_state="KNOWN" if creator_id else "UNKNOWN", production_year=year, medium=medium,
            collection_institution=institution, culture_state="UNKNOWN",
            official_url=f"https://example.com/fictional/artworks/{index}",
            last_verified_at=source.last_seen_at, eligibility="DEMO", is_demo=True,
        )
        for axis, value in (("MEDIA_GROUP", media), ("MOOD", mood)):
            ArtworkFeatureAssertion.objects.create(artwork=artwork, source_record=source, axis=axis, value=value)

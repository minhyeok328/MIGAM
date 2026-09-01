from datetime import datetime
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from backend.apps.catalog.models import MediaAsset, MediaRights
from backend.apps.sources.models import SourceRecord


RIGHTS_VALUE_FIELDS = (
    "policy_status",
    "rights_holder",
    "license_name",
    "credit_line",
    "display_allowed",
    "copy_allowed",
    "cache_allowed",
    "transform_allowed",
    "hotlink_allowed",
)


@transaction.atomic
def record_media_rights(
    *,
    asset: MediaAsset,
    source_record: SourceRecord,
    policy_status: str,
    rights_holder: str = "",
    license_name: str = "",
    credit_line: str = "",
    display_allowed: bool = False,
    copy_allowed: bool = False,
    cache_allowed: bool = False,
    transform_allowed: bool = False,
    hotlink_allowed: bool = False,
    reviewed_at: datetime | None = None,
) -> MediaRights:
    locked_asset = MediaAsset.objects.select_for_update().get(pk=asset.pk)
    values: dict[str, Any] = {
        "policy_status": policy_status,
        "rights_holder": rights_holder,
        "license_name": license_name,
        "credit_line": credit_line,
        "display_allowed": display_allowed,
        "copy_allowed": copy_allowed,
        "cache_allowed": cache_allowed,
        "transform_allowed": transform_allowed,
        "hotlink_allowed": hotlink_allowed,
    }
    candidate = MediaRights(
        asset=locked_asset,
        source_record=source_record,
        reviewed_at=reviewed_at or timezone.now(),
        is_current=True,
        **values,
    )
    candidate.full_clean(validate_constraints=False)

    existing = MediaRights.objects.filter(
        asset=locked_asset,
        source_record=source_record,
    ).first()
    if existing is not None:
        changed_fields = [
            field_name
            for field_name in RIGHTS_VALUE_FIELDS
            if getattr(existing, field_name) != values[field_name]
        ]
        if changed_fields:
            raise ValidationError(
                {
                    "source_record": (
                        "Rights evidence is immutable for one SourceRecord version; "
                        f"changed fields: {', '.join(changed_fields)}."
                    )
                }
            )
        return existing

    MediaRights.objects.filter(asset=locked_asset, is_current=True).update(
        is_current=False
    )
    candidate.save(force_insert=True)
    return candidate

from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlparse

from backend.apps.catalog.models import MediaAsset, MediaRights


INLINE_IMAGE_ROLES = frozenset(
    {
        MediaAsset.Role.POSTER,
        MediaAsset.Role.SPACE_PHOTO,
        MediaAsset.Role.ARTWORK_IMAGE,
        MediaAsset.Role.PERSON_PHOTO,
        MediaAsset.Role.VIDEO_THUMBNAIL,
    }
)


class MediaPresentationStatus(StrEnum):
    INLINE = "INLINE"
    LINK_ONLY = "LINK_ONLY"
    HIDDEN = "HIDDEN"


@dataclass(frozen=True, slots=True)
class MediaPresentation:
    status: MediaPresentationStatus
    media_url: str | None = None
    page_url: str | None = None
    credit_line: str | None = None


def resolve_media_presentation(asset: MediaAsset) -> MediaPresentation:
    rights = asset.rights_history.filter(is_current=True).first()
    if rights is None:
        return MediaPresentation(status=MediaPresentationStatus.HIDDEN)

    if rights.policy_status in {
        MediaRights.PolicyStatus.RIGHTS_UNKNOWN,
        MediaRights.PolicyStatus.UNAVAILABLE_OR_WITHDRAWN,
    }:
        return MediaPresentation(status=MediaPresentationStatus.HIDDEN)

    page_url = _validated_https_url(asset.source_page_url)
    if page_url is None:
        return MediaPresentation(status=MediaPresentationStatus.HIDDEN)

    if rights.policy_status == MediaRights.PolicyStatus.LINK_ONLY:
        return MediaPresentation(
            status=MediaPresentationStatus.LINK_ONLY,
            page_url=page_url,
        )

    media_url = _validated_https_url(asset.origin_url)
    if (
        asset.media_type == MediaAsset.MediaType.IMAGE
        and asset.role in INLINE_IMAGE_ROLES
        and rights.display_allowed
        and rights.hotlink_allowed
        and media_url is not None
    ):
        return MediaPresentation(
            status=MediaPresentationStatus.INLINE,
            media_url=media_url,
            page_url=page_url,
            credit_line=rights.credit_line or None,
        )

    return MediaPresentation(
        status=MediaPresentationStatus.LINK_ONLY,
        page_url=page_url,
        credit_line=rights.credit_line or None,
    )


def _validated_https_url(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname:
        return None
    return value

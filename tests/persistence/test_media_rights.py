from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from backend.apps.catalog.media_access import (
    MediaPresentationStatus,
    resolve_media_presentation,
)
from backend.apps.catalog.models import Exhibition, Institution, MediaAsset, MediaRights
from backend.apps.catalog.rights import record_media_rights
from backend.apps.sources.models import SourceRecord


class MediaRightsTests(TestCase):
    def setUp(self) -> None:
        self.institution = Institution.objects.create(
            registry_id="institution-a",
            name="기관 A",
            region_area="서울",
            region_district="종로구",
        )
        self.exhibition = Exhibition.objects.create(
            institution=self.institution,
            title="이미지 권리 전시",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
            venue="기관 A 전시장",
            region_area="서울",
            region_district="종로구",
            lifecycle=Exhibition.Lifecycle.CURRENT,
            official_url="https://example.com/exhibitions/a",
        )
        self.asset_source = self._source_record("asset", "a")
        self.asset = MediaAsset(
            exhibition=self.exhibition,
            source_record=self.asset_source,
            media_type=MediaAsset.MediaType.IMAGE,
            role=MediaAsset.Role.POSTER,
            origin_url="https://cdn.example.com/poster.jpg",
            source_page_url="https://example.com/exhibitions/a",
        )
        self.asset.full_clean()
        self.asset.save()

    def _source_record(self, record_id: str, hash_char: str) -> SourceRecord:
        return SourceRecord.objects.create(
            source_id="official-a",
            institution_id=self.institution.registry_id,
            source_record_id=record_id,
            source_owner="기관 A",
            payload={"id": record_id},
            content_hash=hash_char * 64,
        )

    def test_missing_or_unknown_rights_never_expose_media_url(self) -> None:
        missing = resolve_media_presentation(self.asset)
        self.assertEqual(missing.status, MediaPresentationStatus.HIDDEN)
        self.assertIsNone(missing.media_url)

        record_media_rights(
            asset=self.asset,
            source_record=self._source_record("rights-unknown", "b"),
            policy_status=MediaRights.PolicyStatus.RIGHTS_UNKNOWN,
        )
        unknown = resolve_media_presentation(self.asset)

        self.assertEqual(unknown.status, MediaPresentationStatus.HIDDEN)
        self.assertIsNone(unknown.media_url)
        self.assertIsNone(unknown.page_url)

    def test_reuse_allowed_image_requires_display_and_hotlink_permissions(self) -> None:
        record_media_rights(
            asset=self.asset,
            source_record=self._source_record("rights-reuse", "c"),
            policy_status=MediaRights.PolicyStatus.REUSE_ALLOWED,
            rights_holder="기관 A",
            license_name="기관 A 웹 이미지 이용조건",
            credit_line="기관 A 제공",
            display_allowed=True,
            hotlink_allowed=True,
        )

        presentation = resolve_media_presentation(self.asset)

        self.assertEqual(presentation.status, MediaPresentationStatus.INLINE)
        self.assertEqual(presentation.media_url, self.asset.origin_url)
        self.assertEqual(presentation.credit_line, "기관 A 제공")

    def test_reuse_without_hotlink_falls_back_to_official_page(self) -> None:
        record_media_rights(
            asset=self.asset,
            source_record=self._source_record("rights-no-hotlink", "d"),
            policy_status=MediaRights.PolicyStatus.REUSE_ALLOWED,
            rights_holder="기관 A",
            license_name="기관 A 웹 이미지 이용조건",
            display_allowed=True,
            copy_allowed=True,
        )

        presentation = resolve_media_presentation(self.asset)

        self.assertEqual(presentation.status, MediaPresentationStatus.LINK_ONLY)
        self.assertIsNone(presentation.media_url)
        self.assertEqual(presentation.page_url, self.asset.source_page_url)

    def test_link_only_never_returns_origin_media_url(self) -> None:
        record_media_rights(
            asset=self.asset,
            source_record=self._source_record("rights-link", "e"),
            policy_status=MediaRights.PolicyStatus.LINK_ONLY,
        )

        presentation = resolve_media_presentation(self.asset)

        self.assertEqual(presentation.status, MediaPresentationStatus.LINK_ONLY)
        self.assertIsNone(presentation.media_url)
        self.assertEqual(presentation.page_url, self.asset.source_page_url)

    def test_new_current_rights_preserve_history_and_withdraw_inline_access(self) -> None:
        first = record_media_rights(
            asset=self.asset,
            source_record=self._source_record("rights-first", "f"),
            policy_status=MediaRights.PolicyStatus.REUSE_ALLOWED,
            rights_holder="기관 A",
            license_name="기관 A 웹 이미지 이용조건",
            display_allowed=True,
            hotlink_allowed=True,
        )
        withdrawn = record_media_rights(
            asset=self.asset,
            source_record=self._source_record("rights-withdrawn", "1"),
            policy_status=MediaRights.PolicyStatus.UNAVAILABLE_OR_WITHDRAWN,
        )

        first.refresh_from_db()
        presentation = resolve_media_presentation(self.asset)

        self.assertFalse(first.is_current)
        self.assertTrue(withdrawn.is_current)
        self.assertEqual(self.asset.rights_history.count(), 2)
        self.assertEqual(presentation.status, MediaPresentationStatus.HIDDEN)
        self.assertIsNone(presentation.media_url)

    def test_database_rejects_two_current_rights_rows_for_one_asset(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            MediaRights.objects.bulk_create(
                [
                    MediaRights(
                        asset=self.asset,
                        source_record=self._source_record("rights-current-a", "7"),
                        policy_status=MediaRights.PolicyStatus.LINK_ONLY,
                        is_current=True,
                    ),
                    MediaRights(
                        asset=self.asset,
                        source_record=self._source_record("rights-current-b", "8"),
                        policy_status=MediaRights.PolicyStatus.LINK_ONLY,
                        is_current=True,
                    ),
                ]
            )

    def test_same_source_rights_are_idempotent_and_immutable(self) -> None:
        source_record = self._source_record("rights-idempotent", "9")
        first = record_media_rights(
            asset=self.asset,
            source_record=source_record,
            policy_status=MediaRights.PolicyStatus.LINK_ONLY,
        )
        repeated = record_media_rights(
            asset=self.asset,
            source_record=source_record,
            policy_status=MediaRights.PolicyStatus.LINK_ONLY,
        )

        self.assertEqual(first.pk, repeated.pk)
        self.assertEqual(self.asset.rights_history.count(), 1)
        with self.assertRaises(ValidationError):
            record_media_rights(
                asset=self.asset,
                source_record=source_record,
                policy_status=MediaRights.PolicyStatus.RIGHTS_UNKNOWN,
            )

    def test_reprocessing_old_reuse_evidence_does_not_reverse_withdrawal(self) -> None:
        reuse_source = self._source_record("rights-old-reuse", "d")
        withdrawal_source = self._source_record("rights-new-withdrawal", "e")
        old_reuse = record_media_rights(
            asset=self.asset,
            source_record=reuse_source,
            policy_status=MediaRights.PolicyStatus.REUSE_ALLOWED,
            rights_holder="기관 A",
            license_name="기관 A 웹 이미지 이용조건",
            display_allowed=True,
            hotlink_allowed=True,
        )
        withdrawal = record_media_rights(
            asset=self.asset,
            source_record=withdrawal_source,
            policy_status=MediaRights.PolicyStatus.UNAVAILABLE_OR_WITHDRAWN,
        )

        repeated = record_media_rights(
            asset=self.asset,
            source_record=reuse_source,
            policy_status=MediaRights.PolicyStatus.REUSE_ALLOWED,
            rights_holder="기관 A",
            license_name="기관 A 웹 이미지 이용조건",
            display_allowed=True,
            hotlink_allowed=True,
        )

        old_reuse.refresh_from_db()
        withdrawal.refresh_from_db()
        presentation = resolve_media_presentation(self.asset)
        self.assertEqual(repeated.pk, old_reuse.pk)
        self.assertFalse(old_reuse.is_current)
        self.assertTrue(withdrawal.is_current)
        self.assertEqual(presentation.status, MediaPresentationStatus.HIDDEN)
        self.assertIsNone(presentation.media_url)

    def test_non_reuse_status_rejects_processing_permissions(self) -> None:
        with self.assertRaises(ValidationError):
            record_media_rights(
                asset=self.asset,
                source_record=self._source_record("rights-invalid", "2"),
                policy_status=MediaRights.PolicyStatus.RIGHTS_UNKNOWN,
                display_allowed=True,
            )

        self.assertFalse(self.asset.rights_history.exists())

    def test_reuse_status_requires_holder_license_and_explicit_permission(self) -> None:
        invalid = MediaRights(
            asset=self.asset,
            source_record=self._source_record("rights-incomplete", "3"),
            policy_status=MediaRights.PolicyStatus.REUSE_ALLOWED,
            is_current=True,
        )

        with self.assertRaises(ValidationError):
            invalid.full_clean()

    def test_audio_and_full_video_are_never_inline(self) -> None:
        audio = MediaAsset(
            exhibition=self.exhibition,
            source_record=self._source_record("audio-asset", "4"),
            media_type=MediaAsset.MediaType.AUDIO,
            role=MediaAsset.Role.AUDIO,
            origin_url="https://cdn.example.com/audio.mp3",
            source_page_url="https://example.com/exhibitions/a/audio",
        )
        audio.full_clean()
        audio.save()
        record_media_rights(
            asset=audio,
            source_record=self._source_record("audio-rights", "5"),
            policy_status=MediaRights.PolicyStatus.REUSE_ALLOWED,
            rights_holder="기관 A",
            license_name="기관 A 오디오 이용조건",
            display_allowed=True,
            hotlink_allowed=True,
        )
        video = MediaAsset(
            exhibition=self.exhibition,
            source_record=self._source_record("video-asset", "6"),
            media_type=MediaAsset.MediaType.VIDEO,
            role=MediaAsset.Role.FULL_VIDEO,
            origin_url="https://cdn.example.com/video.mp4",
            source_page_url="https://example.com/exhibitions/a/video",
        )
        video.save()
        record_media_rights(
            asset=video,
            source_record=self._source_record("video-rights", "7"),
            policy_status=MediaRights.PolicyStatus.REUSE_ALLOWED,
            rights_holder="기관 A",
            license_name="기관 A 영상 이용조건",
            display_allowed=True,
            hotlink_allowed=True,
        )

        for asset in (audio, video):
            with self.subTest(media_type=asset.media_type):
                presentation = resolve_media_presentation(asset)
                self.assertEqual(
                    presentation.status,
                    MediaPresentationStatus.LINK_ONLY,
                )
                self.assertIsNone(presentation.media_url)

    def test_media_asset_requires_matching_source_and_exactly_one_target(self) -> None:
        other_source = SourceRecord.objects.create(
            source_id="official-b",
            institution_id="institution-b",
            source_record_id="other-asset",
            source_owner="기관 B",
            payload={},
            content_hash="6" * 64,
        )
        wrong_source = MediaAsset(
            exhibition=self.exhibition,
            source_record=other_source,
            media_type=MediaAsset.MediaType.IMAGE,
            role=MediaAsset.Role.POSTER,
            origin_url="https://cdn.example.com/other.jpg",
            source_page_url="https://example.com/other",
        )
        two_targets = MediaAsset(
            exhibition=self.exhibition,
            institution=self.institution,
            source_record=self.asset_source,
            media_type=MediaAsset.MediaType.IMAGE,
            role=MediaAsset.Role.POSTER,
            origin_url="https://cdn.example.com/duplicate.jpg",
            source_page_url="https://example.com/exhibitions/a",
        )

        with self.assertRaises(ValidationError):
            wrong_source.full_clean()
        with self.assertRaises(ValidationError):
            two_targets.full_clean()
        with self.assertRaises(ValidationError):
            MediaAsset.objects.create(
                exhibition=self.exhibition,
                source_record=other_source,
                media_type=MediaAsset.MediaType.IMAGE,
                role=MediaAsset.Role.POSTER,
                origin_url="https://cdn.example.com/save-bypass.jpg",
                source_page_url="https://example.com/other",
            )

    def test_media_rights_save_requires_matching_source_institution(self) -> None:
        other_source = SourceRecord.objects.create(
            source_id="official-b",
            institution_id="institution-b",
            source_record_id="other-rights",
            source_owner="기관 B",
            payload={},
            content_hash="6" * 64,
        )

        with self.assertRaises(ValidationError):
            MediaRights.objects.create(
                asset=self.asset,
                source_record=other_source,
                policy_status=MediaRights.PolicyStatus.LINK_ONLY,
            )

    def test_media_urls_must_use_https(self) -> None:
        asset = MediaAsset(
            exhibition=self.exhibition,
            source_record=self.asset_source,
            media_type=MediaAsset.MediaType.IMAGE,
            role=MediaAsset.Role.POSTER,
            origin_url="http://cdn.example.com/poster.jpg",
            source_page_url="https://example.com/exhibitions/a",
        )

        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_read_gate_does_not_trust_an_unvalidated_non_https_origin(self) -> None:
        unsafe_asset = MediaAsset.objects.create(
            exhibition=self.exhibition,
            source_record=self._source_record("unsafe-origin", "0"),
            media_type=MediaAsset.MediaType.IMAGE,
            role=MediaAsset.Role.POSTER,
            origin_url="https://cdn.example.com/poster.jpg",
            source_page_url="https://example.com/exhibitions/a",
        )
        MediaAsset.objects.filter(pk=unsafe_asset.pk).update(
            origin_url="http://cdn.example.com/poster.jpg"
        )
        unsafe_asset.refresh_from_db()
        record_media_rights(
            asset=unsafe_asset,
            source_record=self._source_record("unsafe-origin-rights", "a"),
            policy_status=MediaRights.PolicyStatus.REUSE_ALLOWED,
            rights_holder="기관 A",
            license_name="기관 A 웹 이미지 이용조건",
            display_allowed=True,
            hotlink_allowed=True,
        )

        presentation = resolve_media_presentation(unsafe_asset)

        self.assertEqual(presentation.status, MediaPresentationStatus.LINK_ONLY)
        self.assertIsNone(presentation.media_url)
        self.assertEqual(presentation.page_url, unsafe_asset.source_page_url)

    def test_read_gate_hides_an_unvalidated_non_https_source_page(self) -> None:
        unsafe_asset = MediaAsset.objects.create(
            exhibition=self.exhibition,
            source_record=self._source_record("unsafe-page", "b"),
            media_type=MediaAsset.MediaType.IMAGE,
            role=MediaAsset.Role.POSTER,
            origin_url="https://cdn.example.com/poster.jpg",
            source_page_url="https://example.com/exhibitions/a",
        )
        MediaAsset.objects.filter(pk=unsafe_asset.pk).update(
            source_page_url="http://example.com/exhibitions/a"
        )
        unsafe_asset.refresh_from_db()
        record_media_rights(
            asset=unsafe_asset,
            source_record=self._source_record("unsafe-page-rights", "c"),
            policy_status=MediaRights.PolicyStatus.LINK_ONLY,
        )

        presentation = resolve_media_presentation(unsafe_asset)

        self.assertEqual(presentation.status, MediaPresentationStatus.HIDDEN)
        self.assertIsNone(presentation.media_url)
        self.assertIsNone(presentation.page_url)

    def test_read_gate_does_not_trust_an_unvalidated_video_role_as_image(self) -> None:
        mismatched_asset = MediaAsset.objects.create(
            exhibition=self.exhibition,
            source_record=self._source_record("mismatched-video", "f"),
            media_type=MediaAsset.MediaType.VIDEO,
            role=MediaAsset.Role.FULL_VIDEO,
            origin_url="https://cdn.example.com/video.mp4",
            source_page_url="https://example.com/exhibitions/a/video",
        )
        MediaAsset.objects.filter(pk=mismatched_asset.pk).update(
            media_type=MediaAsset.MediaType.IMAGE
        )
        mismatched_asset.refresh_from_db()
        record_media_rights(
            asset=mismatched_asset,
            source_record=self._source_record("mismatched-video-rights", "1"),
            policy_status=MediaRights.PolicyStatus.REUSE_ALLOWED,
            rights_holder="기관 A",
            license_name="기관 A 영상 이용조건",
            display_allowed=True,
            hotlink_allowed=True,
        )

        presentation = resolve_media_presentation(mismatched_asset)

        self.assertEqual(presentation.status, MediaPresentationStatus.LINK_ONLY)
        self.assertIsNone(presentation.media_url)
        self.assertEqual(presentation.page_url, mismatched_asset.source_page_url)

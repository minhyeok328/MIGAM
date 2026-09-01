from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, URLValidator
from django.db import models
from django.utils import timezone

from backend.apps.data_quality.models import ExhibitionCandidate
from backend.apps.sources.models import SourceRecord


HTTPS_URL_VALIDATOR = URLValidator(schemes=("https",))


class Institution(models.Model):
    registry_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=255)
    region_area = models.CharField(max_length=100, blank=True)
    region_district = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("registry_id",)


class Exhibition(models.Model):
    class Lifecycle(models.TextChoices):
        UPCOMING = "UPCOMING", "Upcoming"
        CURRENT = "CURRENT", "Current"
        ENDED = "ENDED", "Ended"
        CANCELED = "CANCELED", "Canceled"
        UNKNOWN = "UNKNOWN", "Unknown"

    class Freshness(models.TextChoices):
        FRESH = "FRESH", "Fresh"
        STALE = "STALE", "Stale"
        UNVERIFIED = "UNVERIFIED", "Unverified"

    class Eligibility(models.TextChoices):
        VERIFIED = "VERIFIED", "Verified"
        PARTIAL = "PARTIAL", "Partial"
        DISCOVERY_ONLY = "DISCOVERY_ONLY", "Discovery only"
        EXCLUDED = "EXCLUDED", "Excluded"

    institution = models.ForeignKey(
        Institution,
        on_delete=models.PROTECT,
        related_name="exhibitions",
    )
    title = models.CharField(max_length=500)
    start_date = models.DateField()
    end_date = models.DateField()
    venue = models.CharField(max_length=500)
    region_area = models.CharField(max_length=100)
    region_district = models.CharField(max_length=100)
    lifecycle = models.CharField(max_length=16, choices=Lifecycle.choices)
    official_url = models.URLField(max_length=2048)
    freshness = models.CharField(
        max_length=16,
        choices=Freshness.choices,
        default=Freshness.FRESH,
    )
    eligibility = models.CharField(
        max_length=20,
        choices=Eligibility.choices,
        default=Eligibility.VERIFIED,
    )
    last_verified_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-start_date", "title", "id")
        indexes = [
            models.Index(
                fields=("institution", "start_date", "end_date"),
                name="catalog_exhibition_match",
            )
        ]


class ExhibitionSourceLink(models.Model):
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.PROTECT,
        related_name="source_links",
    )
    source_id = models.CharField(max_length=128)
    source_record_id = models.CharField(max_length=255)
    latest_source_record = models.ForeignKey(
        SourceRecord,
        on_delete=models.PROTECT,
        related_name="canonical_links",
    )
    linked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("source_id", "source_record_id"),
                name="catalog_unique_source_identity",
            )
        ]


class VerificationRecord(models.Model):
    class Outcome(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.PROTECT,
        related_name="verification_records",
    )
    ingestion_run = models.ForeignKey(
        "sources.IngestionRun",
        on_delete=models.PROTECT,
        related_name="verification_records",
    )
    source_id = models.CharField(max_length=128, blank=True)
    source_record_id = models.CharField(max_length=255, blank=True)
    outcome = models.CharField(max_length=16, choices=Outcome.choices)
    checked_at = models.DateTimeField(default=timezone.now)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-checked_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("exhibition", "ingestion_run"),
                name="catalog_unique_exhibition_verification_run",
            )
        ]
        indexes = [
            models.Index(
                fields=("exhibition", "checked_at"),
                name="catalog_verification_lookup",
            )
        ]


class FieldEvidence(models.Model):
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.PROTECT,
        related_name="field_evidence",
    )
    candidate = models.ForeignKey(
        ExhibitionCandidate,
        on_delete=models.PROTECT,
        related_name="field_evidence",
    )
    source_record = models.ForeignKey(
        SourceRecord,
        on_delete=models.PROTECT,
        related_name="field_evidence",
    )
    field_name = models.CharField(max_length=64)
    canonical_value = models.TextField()
    raw_value = models.JSONField(null=True, blank=True)
    adopted = models.BooleanField(default=False)
    decision_reason = models.CharField(max_length=64)
    verified_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("exhibition", "source_record", "field_name"),
                name="catalog_unique_field_evidence",
            )
        ]
        indexes = [
            models.Index(
                fields=("exhibition", "field_name", "adopted"),
                name="catalog_evidence_lookup",
            )
        ]


class TargetedSourceEvidence(models.Model):
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.PROTECT,
        related_name="%(class)s_records",
        null=True,
        blank=True,
    )
    institution = models.ForeignKey(
        Institution,
        on_delete=models.PROTECT,
        related_name="%(class)s_records",
        null=True,
        blank=True,
    )
    source_record = models.ForeignKey(
        SourceRecord,
        on_delete=models.PROTECT,
        related_name="%(class)s_records",
    )
    verified_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def clean(self) -> None:
        super().clean()
        has_exhibition = self.exhibition_id is not None
        has_institution = self.institution_id is not None
        if has_exhibition == has_institution:
            raise ValidationError(
                "Exactly one of exhibition or institution must be set."
            )

        if not self.source_record_id:
            return
        if has_exhibition:
            target_registry_id = self.exhibition.institution.registry_id
        else:
            target_registry_id = self.institution.registry_id
        if self.source_record.institution_id != target_registry_id:
            raise ValidationError(
                {
                    "source_record": (
                        "SourceRecord institution must match the target institution."
                    )
                }
            )

    def save(self, *args: object, **kwargs: object) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class PriceOption(TargetedSourceEvidence):
    class Status(models.TextChoices):
        CONFIRMED = "CONFIRMED", "Confirmed"
        UNKNOWN = "UNKNOWN", "Unknown"

    class Category(models.TextChoices):
        STANDARD = "STANDARD", "Standard admission"
        DISCOUNT = "DISCOUNT", "Discount"
        PROGRAM = "PROGRAM", "Program"

    status = models.CharField(max_length=16, choices=Status.choices)
    category = models.CharField(
        max_length=16,
        choices=Category.choices,
        blank=True,
    )
    audience = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=3, blank=True)
    amount_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=(MinValueValidator(Decimal("0")),),
    )
    amount_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=(MinValueValidator(Decimal("0")),),
    )
    is_free = models.BooleanField(null=True, blank=True)
    is_standard_adult_admission = models.BooleanField(default=False)
    details = models.TextField(blank=True)

    class Meta:
        ordering = ("exhibition_id", "institution_id", "category", "audience", "id")
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(exhibition__isnull=False, institution__isnull=True)
                    | models.Q(exhibition__isnull=True, institution__isnull=False)
                ),
                name="catalog_price_target_xor",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status="CONFIRMED")
                    | models.Q(
                        status="UNKNOWN",
                        category="",
                        audience="",
                        currency="",
                        amount_min__isnull=True,
                        amount_max__isnull=True,
                        is_free__isnull=True,
                        is_standard_adult_admission=False,
                        details="",
                    )
                ),
                name="catalog_price_unknown_empty",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(amount_max__isnull=True)
                    | models.Q(
                        amount_min__isnull=False,
                        amount_max__gte=models.F("amount_min"),
                    )
                ),
                name="catalog_price_valid_range",
            ),
            models.UniqueConstraint(
                fields=("exhibition", "source_record", "category", "audience"),
                condition=models.Q(exhibition__isnull=False),
                name="catalog_price_source_exhibition",
            ),
            models.UniqueConstraint(
                fields=("institution", "source_record", "category", "audience"),
                condition=models.Q(institution__isnull=False),
                name="catalog_price_source_institution",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.status == self.Status.UNKNOWN:
            if any(
                (
                    self.category,
                    self.audience,
                    self.currency,
                    self.amount_min is not None,
                    self.amount_max is not None,
                    self.is_free is not None,
                    self.is_standard_adult_admission,
                    self.details,
                )
            ):
                errors["status"] = "UNKNOWN price must not carry inferred values."
        elif self.status == self.Status.CONFIRMED:
            if not self.category:
                errors["category"] = "Confirmed price requires a category."
            if self.is_free is None:
                errors["is_free"] = "Confirmed price requires an explicit free state."
            elif not self.is_free and self.amount_min is None:
                errors["amount_min"] = "Paid price requires a minimum amount."
            if self.is_free and any(
                value not in (None, Decimal("0"))
                for value in (self.amount_min, self.amount_max)
            ):
                errors["is_free"] = "Free admission cannot carry a non-zero amount."
            if (self.amount_min is not None or self.amount_max is not None) and not self.currency:
                errors["currency"] = "A priced amount requires a currency."
            if self.amount_max is not None and self.amount_min is None:
                errors["amount_min"] = "A maximum amount requires a minimum amount."
            if (
                self.amount_min is not None
                and self.amount_max is not None
                and self.amount_max < self.amount_min
            ):
                errors["amount_max"] = "Maximum amount cannot be below minimum amount."
            if self.is_standard_adult_admission and (
                self.category != self.Category.STANDARD or self.audience != "ADULT"
            ):
                errors["is_standard_adult_admission"] = (
                    "Adult representative price must be STANDARD with audience ADULT."
                )
        if errors:
            raise ValidationError(errors)


class ReservationInfo(TargetedSourceEvidence):
    class Type(models.TextChoices):
        NOT_REQUIRED = "NOT_REQUIRED", "Not required"
        REQUIRED = "REQUIRED", "Required"
        RECOMMENDED = "RECOMMENDED", "Recommended"
        TIMED_ENTRY = "TIMED_ENTRY", "Timed entry"
        ON_SITE = "ON_SITE", "On site"
        FIRST_COME = "FIRST_COME", "First come"
        PROGRAM_ONLY = "PROGRAM_ONLY", "Program only"
        UNKNOWN = "UNKNOWN", "Unknown"

    reservation_type = models.CharField(max_length=16, choices=Type.choices)
    official_url = models.URLField(
        max_length=2048,
        blank=True,
        validators=(HTTPS_URL_VALIDATOR,),
    )
    guidance = models.TextField(blank=True)

    class Meta:
        ordering = ("exhibition_id", "institution_id", "id")
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(exhibition__isnull=False, institution__isnull=True)
                    | models.Q(exhibition__isnull=True, institution__isnull=False)
                ),
                name="catalog_reservation_target_xor",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(reservation_type="UNKNOWN")
                    | models.Q(official_url="", guidance="")
                ),
                name="catalog_reservation_unknown_empty",
            ),
            models.UniqueConstraint(
                fields=("exhibition", "source_record"),
                condition=models.Q(exhibition__isnull=False),
                name="catalog_reservation_source_exhibition",
            ),
            models.UniqueConstraint(
                fields=("institution", "source_record"),
                condition=models.Q(institution__isnull=False),
                name="catalog_reservation_source_institution",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        if self.reservation_type == self.Type.UNKNOWN and (
            self.official_url or self.guidance
        ):
            raise ValidationError(
                {
                    "reservation_type": (
                        "UNKNOWN reservation must not carry inferred guidance or links."
                    )
                }
            )


class VisitDuration(TargetedSourceEvidence):
    class Status(models.TextChoices):
        OFFICIAL = "OFFICIAL", "Official"
        UNKNOWN = "UNKNOWN", "Unknown"

    status = models.CharField(max_length=16, choices=Status.choices)
    minimum_minutes = models.PositiveIntegerField(null=True, blank=True)
    maximum_minutes = models.PositiveIntegerField(null=True, blank=True)
    details = models.TextField(blank=True)

    class Meta:
        ordering = ("exhibition_id", "institution_id", "id")
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(exhibition__isnull=False, institution__isnull=True)
                    | models.Q(exhibition__isnull=True, institution__isnull=False)
                ),
                name="catalog_duration_target_xor",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status="OFFICIAL")
                    | models.Q(
                        status="UNKNOWN",
                        minimum_minutes__isnull=True,
                        maximum_minutes__isnull=True,
                        details="",
                    )
                ),
                name="catalog_duration_unknown_empty",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(maximum_minutes__isnull=True)
                    | models.Q(
                        minimum_minutes__isnull=False,
                        maximum_minutes__gte=models.F("minimum_minutes"),
                    )
                ),
                name="catalog_duration_valid_range",
            ),
            models.UniqueConstraint(
                fields=("exhibition", "source_record"),
                condition=models.Q(exhibition__isnull=False),
                name="catalog_duration_source_exhibition",
            ),
            models.UniqueConstraint(
                fields=("institution", "source_record"),
                condition=models.Q(institution__isnull=False),
                name="catalog_duration_source_institution",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.status == self.Status.UNKNOWN:
            if (
                self.minimum_minutes is not None
                or self.maximum_minutes is not None
                or self.details
            ):
                errors["status"] = "UNKNOWN duration must not carry inferred values."
        elif self.status == self.Status.OFFICIAL:
            if self.minimum_minutes is None or self.minimum_minutes <= 0:
                errors["minimum_minutes"] = (
                    "Official duration requires a positive minimum."
                )
            if self.maximum_minutes is not None and self.maximum_minutes <= 0:
                errors["maximum_minutes"] = "Maximum duration must be positive."
            if (
                self.minimum_minutes is not None
                and self.maximum_minutes is not None
                and self.maximum_minutes < self.minimum_minutes
            ):
                errors["maximum_minutes"] = (
                    "Maximum duration cannot be below minimum duration."
                )
        if errors:
            raise ValidationError(errors)


class ThreeStateFact(TargetedSourceEvidence):
    class State(models.TextChoices):
        CONFIRMED_POSITIVE = "CONFIRMED_POSITIVE", "Confirmed positive"
        CONFIRMED_NEGATIVE = "CONFIRMED_NEGATIVE", "Confirmed negative"
        UNKNOWN = "UNKNOWN", "Unknown"

    state = models.CharField(max_length=24, choices=State.choices)
    details = models.TextField(blank=True)

    class Meta:
        abstract = True

    def clean(self) -> None:
        super().clean()
        if self.state == self.State.UNKNOWN and self.details:
            raise ValidationError(
                {"state": "UNKNOWN fact must not carry a factual detail."}
            )


class AccessibilityFact(ThreeStateFact):
    class Kind(models.TextChoices):
        WHEELCHAIR_ACCESS = "WHEELCHAIR_ACCESS", "Wheelchair access"
        MOBILITY_ACCESS = "MOBILITY_ACCESS", "Mobility access"
        CAPTIONS = "CAPTIONS", "Captions"
        SIGN_LANGUAGE = "SIGN_LANGUAGE", "Sign language"
        AUDIO_DESCRIPTION = "AUDIO_DESCRIPTION", "Audio description"
        AGE_CONDITION = "AGE_CONDITION", "Age condition"

    kind = models.CharField(max_length=24, choices=Kind.choices)

    class Meta:
        ordering = ("exhibition_id", "institution_id", "kind", "id")
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(exhibition__isnull=False, institution__isnull=True)
                    | models.Q(exhibition__isnull=True, institution__isnull=False)
                ),
                name="catalog_access_target_xor",
            ),
            models.CheckConstraint(
                condition=(~models.Q(state="UNKNOWN") | models.Q(details="")),
                name="catalog_access_unknown_empty",
            ),
            models.UniqueConstraint(
                fields=("exhibition", "source_record", "kind"),
                condition=models.Q(exhibition__isnull=False),
                name="catalog_access_source_exhibition",
            ),
            models.UniqueConstraint(
                fields=("institution", "source_record", "kind"),
                condition=models.Q(institution__isnull=False),
                name="catalog_access_source_institution",
            ),
        ]


class SensoryNotice(ThreeStateFact):
    class Kind(models.TextChoices):
        LOUD_SOUND = "LOUD_SOUND", "Loud sound"
        SUDDEN_SOUND = "SUDDEN_SOUND", "Sudden sound"
        FLASHING_LIGHTS = "FLASHING_LIGHTS", "Flashing lights"
        DARK_SPACE = "DARK_SPACE", "Dark space"
        NARROW_OR_ENCLOSED_SPACE = (
            "NARROW_OR_ENCLOSED_SPACE",
            "Narrow or enclosed space",
        )

    kind = models.CharField(max_length=32, choices=Kind.choices)

    class Meta:
        ordering = ("exhibition_id", "institution_id", "kind", "id")
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(exhibition__isnull=False, institution__isnull=True)
                    | models.Q(exhibition__isnull=True, institution__isnull=False)
                ),
                name="catalog_sensory_target_xor",
            ),
            models.CheckConstraint(
                condition=(~models.Q(state="UNKNOWN") | models.Q(details="")),
                name="catalog_sensory_unknown_empty",
            ),
            models.UniqueConstraint(
                fields=("exhibition", "source_record", "kind"),
                condition=models.Q(exhibition__isnull=False),
                name="catalog_sensory_source_exhibition",
            ),
            models.UniqueConstraint(
                fields=("institution", "source_record", "kind"),
                condition=models.Q(institution__isnull=False),
                name="catalog_sensory_source_institution",
            ),
        ]


class MediaAsset(TargetedSourceEvidence):
    class MediaType(models.TextChoices):
        IMAGE = "IMAGE", "Image"
        AUDIO = "AUDIO", "Audio"
        VIDEO = "VIDEO", "Video"

    class Role(models.TextChoices):
        POSTER = "POSTER", "Poster"
        SPACE_PHOTO = "SPACE_PHOTO", "Space photo"
        ARTWORK_IMAGE = "ARTWORK_IMAGE", "Artwork image"
        PERSON_PHOTO = "PERSON_PHOTO", "Person photo"
        VIDEO_THUMBNAIL = "VIDEO_THUMBNAIL", "Video thumbnail"
        AUDIO = "AUDIO", "Audio"
        FULL_VIDEO = "FULL_VIDEO", "Full video"

    media_type = models.CharField(max_length=8, choices=MediaType.choices)
    role = models.CharField(max_length=24, choices=Role.choices)
    origin_url = models.URLField(
        max_length=2048,
        validators=(HTTPS_URL_VALIDATOR,),
    )
    source_page_url = models.URLField(
        max_length=2048,
        validators=(HTTPS_URL_VALIDATOR,),
    )

    class Meta:
        ordering = ("exhibition_id", "institution_id", "role", "id")
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(exhibition__isnull=False, institution__isnull=True)
                    | models.Q(exhibition__isnull=True, institution__isnull=False)
                ),
                name="catalog_media_target_xor",
            ),
            models.UniqueConstraint(
                fields=("source_record", "role", "origin_url"),
                name="catalog_media_source_role_url",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        image_roles = {
            self.Role.POSTER,
            self.Role.SPACE_PHOTO,
            self.Role.ARTWORK_IMAGE,
            self.Role.PERSON_PHOTO,
            self.Role.VIDEO_THUMBNAIL,
        }
        expected_type = {
            self.Role.AUDIO: self.MediaType.AUDIO,
            self.Role.FULL_VIDEO: self.MediaType.VIDEO,
        }.get(self.role, self.MediaType.IMAGE if self.role in image_roles else None)
        if expected_type is not None and self.media_type != expected_type:
            raise ValidationError(
                {"media_type": "Media type does not match the selected media role."}
            )


class MediaRights(models.Model):
    class PolicyStatus(models.TextChoices):
        REUSE_ALLOWED = "REUSE_ALLOWED", "Reuse allowed"
        LINK_ONLY = "LINK_ONLY", "Link only"
        RIGHTS_UNKNOWN = "RIGHTS_UNKNOWN", "Rights unknown"
        UNAVAILABLE_OR_WITHDRAWN = (
            "UNAVAILABLE_OR_WITHDRAWN",
            "Unavailable or withdrawn",
        )

    asset = models.ForeignKey(
        MediaAsset,
        on_delete=models.PROTECT,
        related_name="rights_history",
    )
    source_record = models.ForeignKey(
        SourceRecord,
        on_delete=models.PROTECT,
        related_name="media_rights_records",
    )
    policy_status = models.CharField(max_length=32, choices=PolicyStatus.choices)
    rights_holder = models.CharField(max_length=255, blank=True)
    license_name = models.CharField(max_length=255, blank=True)
    credit_line = models.TextField(blank=True)
    display_allowed = models.BooleanField(default=False)
    copy_allowed = models.BooleanField(default=False)
    cache_allowed = models.BooleanField(default=False)
    transform_allowed = models.BooleanField(default=False)
    hotlink_allowed = models.BooleanField(default=False)
    is_current = models.BooleanField(default=True)
    reviewed_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("asset_id", "-reviewed_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("asset", "source_record"),
                name="catalog_media_rights_evidence",
            ),
            models.UniqueConstraint(
                fields=("asset",),
                condition=models.Q(is_current=True),
                name="catalog_media_one_current_rights",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(policy_status="REUSE_ALLOWED")
                    | models.Q(
                        display_allowed=False,
                        copy_allowed=False,
                        cache_allowed=False,
                        transform_allowed=False,
                        hotlink_allowed=False,
                    )
                ),
                name="catalog_media_nonreuse_denied",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(policy_status="REUSE_ALLOWED")
                    | (
                        ~models.Q(rights_holder="")
                        & ~models.Q(license_name="")
                        & (
                            models.Q(display_allowed=True)
                            | models.Q(copy_allowed=True)
                            | models.Q(cache_allowed=True)
                            | models.Q(transform_allowed=True)
                            | models.Q(hotlink_allowed=True)
                        )
                    )
                ),
                name="catalog_media_reuse_evidence",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        if self.asset_id and self.source_record_id:
            if self.asset.exhibition_id is not None:
                target_registry_id = self.asset.exhibition.institution.registry_id
            else:
                target_registry_id = self.asset.institution.registry_id
            if self.source_record.institution_id != target_registry_id:
                raise ValidationError(
                    {
                        "source_record": (
                            "Rights evidence institution must match the media target."
                        )
                    }
                )

        processing_permissions = (
            self.display_allowed,
            self.copy_allowed,
            self.cache_allowed,
            self.transform_allowed,
            self.hotlink_allowed,
        )
        if self.policy_status == self.PolicyStatus.REUSE_ALLOWED:
            errors: dict[str, str] = {}
            if not self.rights_holder:
                errors["rights_holder"] = "Reuse requires a confirmed rights holder."
            if not self.license_name:
                errors["license_name"] = "Reuse requires a confirmed license or terms."
            if not any(processing_permissions):
                errors["policy_status"] = (
                    "Reuse requires at least one explicitly allowed processing action."
                )
            if errors:
                raise ValidationError(errors)
        elif any(processing_permissions):
            raise ValidationError(
                {
                    "policy_status": (
                        "Non-reuse rights states cannot grant media processing permissions."
                    )
                }
            )

    def save(self, *args: object, **kwargs: object) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class ChangeHistory(models.Model):
    class ChangeType(models.TextChoices):
        CREATED = "CREATED", "Created"
        FIELD_CHANGED = "FIELD_CHANGED", "Field changed"

    class MeaningfulType(models.TextChoices):
        NONE = "NONE", "None"
        NEW_EXHIBITION = "NEW_EXHIBITION", "New exhibition"
        END_DATE_CHANGED = "END_DATE_CHANGED", "End date changed"
        VENUE_CHANGED = "VENUE_CHANGED", "Venue changed"
        CANCELED = "CANCELED", "Canceled"

    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.PROTECT,
        related_name="change_history",
    )
    ingestion_run = models.ForeignKey(
        "sources.IngestionRun",
        on_delete=models.PROTECT,
        related_name="canonical_changes",
        null=True,
        blank=True,
    )
    candidate = models.ForeignKey(
        ExhibitionCandidate,
        on_delete=models.PROTECT,
        related_name="change_history",
    )
    source_record = models.ForeignKey(
        SourceRecord,
        on_delete=models.PROTECT,
        related_name="change_history",
    )
    change_type = models.CharField(max_length=32, choices=ChangeType.choices)
    field_name = models.CharField(max_length=64, blank=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    rule_version = models.CharField(max_length=32)
    meaningful_for_promotion = models.BooleanField(default=False)
    meaningful_type = models.CharField(
        max_length=32,
        choices=MeaningfulType.choices,
        default=MeaningfulType.NONE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "ingestion_run",
                    "exhibition",
                    "source_record",
                    "change_type",
                    "field_name",
                ),
                name="catalog_unique_canonical_change",
            )
        ]
        indexes = [
            models.Index(
                fields=("ingestion_run", "meaningful_for_promotion"),
                name="catalog_change_run_meaningful",
            )
        ]


class SourceConflict(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        RESOLVED = "RESOLVED", "Resolved"

    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.PROTECT,
        related_name="source_conflicts",
    )
    field_name = models.CharField(max_length=64)
    canonical_value = models.TextField()
    candidate_value = models.TextField()
    candidate_source_record = models.ForeignKey(
        SourceRecord,
        on_delete=models.PROTECT,
        related_name="source_conflicts",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
    )
    resolution_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("exhibition", "field_name", "candidate_source_record"),
                name="catalog_unique_source_conflict",
            )
        ]


class DuplicateCandidate(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        DISTINCT = "DISTINCT", "Distinct"
        MERGED = "MERGED", "Merged"

    primary_exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.PROTECT,
        related_name="duplicate_candidates_primary",
    )
    related_exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.PROTECT,
        related_name="duplicate_candidates_related",
    )
    reason = models.CharField(max_length=64)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
    )
    resolution_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("primary_exhibition", "related_exhibition"),
                name="catalog_unique_duplicate_pair",
            )
        ]

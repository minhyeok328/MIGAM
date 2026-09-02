from datetime import date
from hashlib import sha256
from importlib import import_module, util

from django.core.exceptions import ValidationError
from django.test import TestCase

from backend.apps.catalog.models import Exhibition, Institution
from backend.apps.sources.models import SourceRecord


class ContentFeatureSnapshotTests(TestCase):
    def setUp(self) -> None:
        self.institution = Institution.objects.create(
            registry_id="feature-institution",
            name="특성 미술관",
            region_area="서울",
            region_district="종로구",
        )
        self.exhibition = Exhibition.objects.create(
            institution=self.institution,
            title="근거 있는 특성 전시",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 10, 1),
            venue="특성 미술관 전시장",
            region_area="서울",
            region_district="종로구",
            lifecycle=Exhibition.Lifecycle.CURRENT,
            official_url="https://example.com/exhibitions/features",
            eligibility=Exhibition.Eligibility.VERIFIED,
        )
        self.source = self.create_source(
            institution_id=self.institution.registry_id,
            source_record_id="feature-source-1",
        )
        self.second_source = self.create_source(
            institution_id=self.institution.registry_id,
            source_record_id="feature-source-2",
        )
        self.other_source = self.create_source(
            institution_id="other-institution",
            source_record_id="feature-source-other",
        )

    def create_source(
        self,
        *,
        institution_id: str,
        source_record_id: str,
    ) -> SourceRecord:
        return SourceRecord.objects.create(
            source_id=f"official-{institution_id}",
            institution_id=institution_id,
            source_record_id=source_record_id,
            source_owner=institution_id,
            payload={"feature": source_record_id},
            content_hash=sha256(source_record_id.encode()).hexdigest(),
        )

    def feature(self) -> tuple[object, object]:
        self.assertIsNotNone(
            util.find_spec("backend.apps.discovery.features"),
            "content feature writer is missing",
        )
        features = import_module("backend.apps.discovery.features")
        models = import_module("backend.apps.discovery.models")
        self.assertTrue(hasattr(models, "ContentFeatureSnapshot"))
        self.assertTrue(hasattr(models, "ContentFeatureAssertion"))
        return features, models

    def assertion(
        self,
        features: object,
        *,
        axis: str = "MOOD",
        value: str = "CALM",
        evidence_kind: str = "DIRECT",
        source_record: SourceRecord | None = None,
        rule_version: str = "",
    ) -> object:
        return features.FeatureAssertionInput(
            axis=axis,
            value=value,
            evidence_kind=evidence_kind,
            source_record=source_record or self.source,
            rule_version=rule_version,
        )

    def test_new_snapshot_becomes_current_without_deleting_history(self) -> None:
        features, models = self.feature()
        first = features.record_content_feature_snapshot(
            exhibition=self.exhibition,
            assertions=(self.assertion(features),),
        )

        second = features.record_content_feature_snapshot(
            exhibition=self.exhibition,
            assertions=(
                self.assertion(
                    features,
                    axis="MEDIA_GROUP",
                    value="MOVING_IMAGE_DIGITAL",
                    source_record=self.second_source,
                ),
            ),
        )

        first.refresh_from_db()
        self.assertFalse(first.is_current)
        self.assertTrue(second.is_current)
        self.assertEqual(
            models.ContentFeatureSnapshot.objects.filter(
                exhibition=self.exhibition
            ).count(),
            2,
        )
        current = models.ContentFeatureSnapshot.objects.get(
            exhibition=self.exhibition,
            is_current=True,
        )
        self.assertEqual(current.pk, second.pk)
        self.assertEqual(current.schema_version, features.FEATURE_SCHEMA_VERSION)
        self.assertEqual(
            list(current.assertions.values_list("axis", "value")),
            [("MEDIA_GROUP", "MOVING_IMAGE_DIGITAL")],
        )

    def test_duplicate_axis_and_value_is_rejected(self) -> None:
        features, models = self.feature()

        with self.assertRaises(ValidationError):
            features.record_content_feature_snapshot(
                exhibition=self.exhibition,
                assertions=(
                    self.assertion(features),
                    self.assertion(
                        features,
                        source_record=self.second_source,
                    ),
                ),
            )

        self.assertEqual(models.ContentFeatureSnapshot.objects.count(), 0)

    def test_feature_value_requires_a_stable_uppercase_code(self) -> None:
        features, models = self.feature()

        with self.assertRaises(ValidationError):
            features.record_content_feature_snapshot(
                exhibition=self.exhibition,
                assertions=(
                    self.assertion(features, value="차분한 분위기"),
                ),
            )

        self.assertEqual(models.ContentFeatureSnapshot.objects.count(), 0)

    def test_derived_evidence_requires_rule_version(self) -> None:
        features, models = self.feature()

        for missing_version in ("", "   "):
            with self.subTest(rule_version=missing_version):
                with self.assertRaises(ValidationError):
                    features.record_content_feature_snapshot(
                        exhibition=self.exhibition,
                        assertions=(
                            self.assertion(
                                features,
                                evidence_kind="DERIVED",
                                rule_version=missing_version,
                            ),
                        ),
                    )

        snapshot = features.record_content_feature_snapshot(
            exhibition=self.exhibition,
            assertions=(
                self.assertion(
                    features,
                    evidence_kind="DERIVED",
                    rule_version="mood-rules-1.0.0",
                ),
            ),
        )
        self.assertEqual(models.ContentFeatureSnapshot.objects.count(), 1)
        self.assertEqual(
            snapshot.assertions.get().rule_version,
            "mood-rules-1.0.0",
        )

    def test_direct_evidence_rejects_a_rule_version(self) -> None:
        features, models = self.feature()

        with self.assertRaises(ValidationError):
            features.record_content_feature_snapshot(
                exhibition=self.exhibition,
                assertions=(
                    self.assertion(
                        features,
                        evidence_kind="DIRECT",
                        rule_version="unexpected-rule",
                    ),
                ),
            )

        self.assertEqual(models.ContentFeatureSnapshot.objects.count(), 0)

    def test_source_record_must_belong_to_the_exhibition_institution(self) -> None:
        features, models = self.feature()

        with self.assertRaises(ValidationError):
            features.record_content_feature_snapshot(
                exhibition=self.exhibition,
                assertions=(
                    self.assertion(
                        features,
                        source_record=self.other_source,
                    ),
                ),
            )

        self.assertEqual(models.ContentFeatureSnapshot.objects.count(), 0)

    def test_direct_model_save_cannot_bypass_evidence_validation(self) -> None:
        _, models = self.feature()
        snapshot = models.ContentFeatureSnapshot.objects.create(
            exhibition=self.exhibition,
            schema_version="1.0.0",
        )

        with self.assertRaises(ValidationError):
            models.ContentFeatureAssertion.objects.create(
                snapshot=snapshot,
                axis="MOOD",
                value="CALM",
                evidence_kind="DIRECT",
                source_record=self.other_source,
            )

        self.assertEqual(models.ContentFeatureAssertion.objects.count(), 0)

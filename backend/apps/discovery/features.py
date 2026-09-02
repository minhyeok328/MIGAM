from collections.abc import Iterable
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction

from backend.apps.catalog.models import Exhibition
from backend.apps.discovery.models import (
    ContentFeatureAssertion,
    ContentFeatureSnapshot,
)
from backend.apps.sources.models import SourceRecord


FEATURE_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class FeatureAssertionInput:
    axis: str
    value: str
    evidence_kind: str
    source_record: SourceRecord
    rule_version: str = ""


@transaction.atomic
def record_content_feature_snapshot(
    *,
    exhibition: Exhibition,
    assertions: Iterable[FeatureAssertionInput],
    schema_version: str = FEATURE_SCHEMA_VERSION,
) -> ContentFeatureSnapshot:
    assertion_inputs = tuple(assertions)
    feature_keys = [(item.axis, item.value) for item in assertion_inputs]
    if len(feature_keys) != len(set(feature_keys)):
        raise ValidationError(
            {"assertions": "A snapshot cannot contain duplicate features."}
        )

    current_snapshots = ContentFeatureSnapshot.objects.select_for_update().filter(
        exhibition=exhibition,
        is_current=True,
    )
    current_snapshots.update(is_current=False)

    snapshot = ContentFeatureSnapshot(
        exhibition=exhibition,
        schema_version=schema_version,
        is_current=True,
    )
    snapshot.full_clean()
    snapshot.save()

    for item in assertion_inputs:
        assertion = ContentFeatureAssertion(
            snapshot=snapshot,
            axis=item.axis,
            value=item.value,
            evidence_kind=item.evidence_kind,
            source_record=item.source_record,
            rule_version=item.rule_version,
        )
        assertion.full_clean()
        assertion.save()

    return snapshot

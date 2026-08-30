from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from backend.data_pipeline.normalization import NormalizedExhibition
from backend.data_pipeline.registry import SourceRegistry


@dataclass(frozen=True, slots=True)
class QualityIssue:
    code: str
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class QualityResult:
    core_result: str
    eligibility: str
    issues: tuple[QualityIssue, ...]
    quarantine: bool = False


def evaluate_core_quality(
    record: NormalizedExhibition,
    registry: SourceRegistry,
) -> QualityResult:
    issues: list[QualityIssue] = []
    raw = record.raw_record
    quarantine = False

    required_values = {
        "source_record_id": raw.source_record_id,
        "title": record.title,
        "start_date": record.start_date,
        "end_date": record.end_date,
        "venue": record.venue,
        "region_area": record.region_area,
        "region_district": record.region_district,
    }
    for field, value in required_values.items():
        if value is None or value == "":
            issues.append(
                QualityIssue("MISSING_CORE_FIELD", field, f"{field} is required")
            )

    if (
        record.start_date is not None
        and record.end_date is not None
        and record.end_date < record.start_date
    ):
        issues.append(
            QualityIssue("INVALID_DATE_ORDER", "end_date", "end date precedes start date")
        )

    if record.lifecycle not in {"UPCOMING", "CURRENT", "ENDED", "CANCELED"}:
        issues.append(
            QualityIssue("INVALID_LIFECYCLE", "lifecycle", "lifecycle is not verified")
        )

    try:
        source = registry.source(raw.source_id)
        institution = registry.institution(raw.institution_id)
    except KeyError:
        issues.append(
            QualityIssue("UNREGISTERED_SOURCE", "source_id", "source is not registered")
        )
    else:
        if institution.get("source_id") != raw.source_id:
            issues.append(
                QualityIssue(
                    "SOURCE_INSTITUTION_MISMATCH",
                    "institution_id",
                    "institution is not registered for source",
                )
            )
        if raw.source_owner != source.get("owner"):
            issues.append(
                QualityIssue(
                    "UNVERIFIED_SOURCE_OWNER",
                    "source_owner",
                    "source owner does not match registry",
                )
            )
        if not _official_url_matches(record, source, institution):
            issues.append(
                QualityIssue(
                    "INVALID_OFFICIAL_URL",
                    "official_url",
                    "official URL does not match the approved source contract",
                )
            )

    for field in sorted(raw.conflicts):
        issues.append(
            QualityIssue("UNRESOLVED_CONFLICT", field, "core field has a conflict")
        )

    for collection_issue in registry.collection_issues:
        if collection_issue.get("status") != "OPEN":
            continue
        if (
            collection_issue.get("source_id") == raw.source_id
            and collection_issue.get("institution_id") == raw.institution_id
            and str(collection_issue.get("source_record_id")) == raw.source_record_id
        ):
            issue_code = str(collection_issue.get("classification", "COLLECTION_ISSUE"))
            issue_field = str(collection_issue.get("field", "record"))
            issues.append(
                QualityIssue(
                    issue_code,
                    issue_field,
                    "record matches an open collection issue",
                )
            )
            quarantine = collection_issue.get("action") == "QUARANTINE_RECORD"

    passed = not issues
    return QualityResult(
        core_result="PASS" if passed else "FAIL",
        eligibility="VERIFIED" if passed else "EXCLUDED",
        issues=tuple(issues),
        quarantine=quarantine,
    )


def _official_url_matches(
    record: NormalizedExhibition,
    source: object,
    institution: object,
) -> bool:
    if not isinstance(source, dict) or not isinstance(institution, dict):
        return False
    if not record.official_url:
        return False
    parsed = urlparse(record.official_url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.path in {"", "/"}:
        return False

    source_filter = source.get("source_filter", {})
    institution_filter = institution.get("source_filter", {})
    expected_host = source_filter.get("official_url_host") or institution_filter.get(
        "official_url_host"
    )
    if expected_host and parsed.hostname != expected_host:
        return False
    expected_path = source_filter.get("official_url_path")
    if expected_path and parsed.path != expected_path:
        return False

    query = parse_qs(parsed.query)
    for key, expected in source_filter.get("official_url_query", {}).items():
        if key.endswith("_equals_field"):
            query_key = key.removesuffix("_equals_field")
            if query.get(query_key) != [record.raw_record.source_record_id]:
                return False
        elif query.get(key) != [str(expected)]:
            return False
    return True

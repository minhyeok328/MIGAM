"""Validate a deliberately reviewed JSON bundle; no network or canonical writes."""

import json
from pathlib import Path

from django.core.exceptions import ValidationError

from backend.apps.catalog.content import ENTRY_FIELDS, record_reviewed_content


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValidationError(f"Nonstandard JSON constant: {value}")


def load_reviewed_content(path):
    path = Path(path)
    if path.stat().st_size > 10 * 1024 * 1024:
        raise ValidationError("Reviewed content bundles must not exceed 10 MiB.")
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=_unique_object, parse_constant=_invalid_constant)


def import_reviewed_content(bundle, *, now=None, dry_run=False):
    if not isinstance(bundle, dict) or set(bundle) != {"schema_version", "entries"} or bundle["schema_version"] != "1.0":
        raise ValidationError("Expected a reviewed content bundle with schema_version 1.0 and entries.")
    entries = bundle["entries"]
    if not isinstance(entries, list) or not 1 <= len(entries) <= 1000:
        raise ValidationError("Expected between 1 and 1000 content entries.")
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != ENTRY_FIELDS:
            raise ValidationError("Reviewed content fields do not match schema_version 1.0.")
        if type(entry["exhibition_id"]) is not int or entry["exhibition_id"] <= 0:
            raise ValidationError("exhibition_id must be a positive integer.")
        for field in ENTRY_FIELDS - {"exhibition_id", "highlights", "visit_notes"}:
            if not isinstance(entry[field], str):
                raise ValidationError({field: "Expected a string."})
    return record_reviewed_content(entries, now=now, dry_run=dry_run)

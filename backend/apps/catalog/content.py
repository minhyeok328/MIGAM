"""Reviewed descriptions are optional snapshots, separate from canonical visit facts."""

from dataclasses import dataclass
from datetime import timedelta
from hashlib import sha256
from html import unescape
from ipaddress import ip_address
import json
import re
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Exhibition, ExhibitionContent, ExhibitionSourceLink
from backend.apps.sources.models import InstitutionAllowlistEntry


VISIT_NOTE_KINDS = ("PRICE", "HOURS", "RESERVATION", "AGE", "LOCATION")
ENTRY_FIELDS = frozenset({
    "exhibition_id", "source_id", "source_record_id", "source_record_hash", "title", "start_date", "end_date",
    "venue", "official_url", "introduction", "highlights", "visit_notes", "source_owner", "reviewed_at",
    "expires_at", "evidence_notes",
})
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_HTML = re.compile(r"<\s*(?:/?[a-zA-Z][^>]*|!.*?)[>]", re.DOTALL)


@dataclass(frozen=True)
class ContentImportResult:
    created: int
    unchanged: int


def _digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _plain_text(value, *, field, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValidationError({field: f"Expected nonempty text of at most {maximum} characters."})
    decoded = value
    for _ in range(3):
        decoded = unescape(decoded)
    if _HTML.search(decoded) or any(ord(char) < 32 and char not in "\n\t\r" for char in value):
        raise ValidationError({field: "Only plain text without HTML or control characters is allowed."})


def _validate_url(value):
    _plain_text(value, field="official_url", maximum=2048)
    URLValidator(schemes=("https",))(value)
    parsed = urlsplit(value)
    if (any(ord(char) <= 32 for char in value) or "\\" in value or parsed.username is not None
            or parsed.password is not None or not parsed.hostname or parsed.fragment):
        raise ValidationError({"official_url": "Expected an official HTTPS detail URL without credentials or fragments."})
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith(".localhost"):
        raise ValidationError({"official_url": "Local URLs are not official evidence."})
    try:
        address = ip_address(host)
    except ValueError:
        return
    if not address.is_global:
        raise ValidationError({"official_url": "Private URLs are not official evidence."})


def validate_content_values(snapshot):
    for field, maximum in (("introduction", 2000), ("source_owner", 255), ("evidence_notes", 2000)):
        _plain_text(getattr(snapshot, field), field=field, maximum=maximum)
    _validate_url(snapshot.official_url)
    if not isinstance(snapshot.highlights, list) or len(snapshot.highlights) > 3:
        raise ValidationError({"highlights": "Expected at most three highlights."})
    for text in snapshot.highlights:
        _plain_text(text, field="highlights", maximum=300)
    if not isinstance(snapshot.visit_notes, list) or len(snapshot.visit_notes) > len(VISIT_NOTE_KINDS):
        raise ValidationError({"visit_notes": "Expected a bounded list of official visit notes."})
    kinds = []
    for note in snapshot.visit_notes:
        if not isinstance(note, dict) or set(note) != {"kind", "text"} or note["kind"] not in VISIT_NOTE_KINDS:
            raise ValidationError({"visit_notes": "Each visit note needs a registered kind and text."})
        _plain_text(note["text"], field="visit_notes", maximum=500)
        kinds.append(note["kind"])
    if len(kinds) != len(set(kinds)):
        raise ValidationError({"visit_notes": "Duplicate visit note kinds are not allowed."})
    for field in ("source_record_hash", "canonical_fingerprint", "review_hash"):
        value = getattr(snapshot, field)
        if not isinstance(value, str) or not _HASH.fullmatch(value):
            raise ValidationError({field: "Expected a SHA-256 hex digest."})
    if not snapshot.reviewed_at or not snapshot.expires_at:
        raise ValidationError("Review and expiry timestamps are required.")
    if timezone.is_naive(snapshot.reviewed_at) or timezone.is_naive(snapshot.expires_at):
        raise ValidationError("Review and expiry timestamps must include a timezone.")
    if not timedelta() < snapshot.expires_at - snapshot.reviewed_at <= timedelta(days=30):
        raise ValidationError("Content validity must be positive and no longer than 30 days.")


def _identity(exhibition):
    return {
        "exhibition_id": exhibition.pk, "institution_id": exhibition.institution.registry_id,
        "title": exhibition.title, "start_date": exhibition.start_date.isoformat(),
        "end_date": exhibition.end_date.isoformat(), "venue": exhibition.venue,
        "official_url": exhibition.official_url,
    }


def canonical_fingerprint(exhibition, source_record):
    return _digest({
        **_identity(exhibition), "source_id": source_record.source_id,
        "source_record_id": source_record.source_record_id, "source_record_pk": source_record.pk,
        "source_record_hash": source_record.content_hash,
    })


def _timestamp(value, field):
    try:
        parsed = parse_datetime(value) if isinstance(value, str) else None
    except ValueError:
        parsed = None
    if parsed is None or timezone.is_naive(parsed):
        raise ValidationError({field: "Expected an ISO timestamp including its timezone."})
    return parsed


def _snapshot(entry, exhibition, now):
    identity = _identity(exhibition)
    if any(entry[field] != identity[field] for field in ("title", "start_date", "end_date", "venue", "official_url")):
        raise ValidationError("Reviewed identity does not match the current canonical exhibition.")
    link = ExhibitionSourceLink.objects.select_for_update().select_related("latest_source_record").filter(
        exhibition=exhibition, source_id=entry["source_id"], source_record_id=entry["source_record_id"],
    ).first()
    if link is None:
        raise ValidationError("Reviewed source is not linked to this exhibition.")
    source = link.latest_source_record
    if (source.source_id != link.source_id or source.source_record_id != link.source_record_id
            or source.institution_id != exhibition.institution.registry_id
            or source.content_hash != entry["source_record_hash"]):
        raise ValidationError("Reviewed source does not match the current source record.")
    if not InstitutionAllowlistEntry.objects.filter(
        registry_id=exhibition.institution.registry_id, source__registry_id=source.source_id,
    ).exists():
        raise ValidationError("The source and institution must be registered together.")
    if (exhibition.eligibility != Exhibition.Eligibility.VERIFIED
            or exhibition.freshness == Exhibition.Freshness.UNVERIFIED
            or exhibition.source_conflicts.filter(status="OPEN").exists()):
        raise ValidationError("Reviewed content requires a verified canonical exhibition without open core conflicts.")
    reviewed_at = _timestamp(entry["reviewed_at"], "reviewed_at")
    expires_at = _timestamp(entry["expires_at"], "expires_at")
    if reviewed_at > now:
        raise ValidationError({"reviewed_at": "A review cannot be dated in the future."})
    snapshot = ExhibitionContent(
        exhibition=exhibition, source_record=source, source_record_hash=source.content_hash,
        canonical_fingerprint=canonical_fingerprint(exhibition, source), review_hash=_digest({"schema_version": "1.0", **entry}),
        reviewed_at=reviewed_at, expires_at=expires_at,
        **{key: entry[key] for key in ("introduction", "highlights", "visit_notes", "official_url", "source_owner", "evidence_notes")},
    )
    snapshot.full_clean(validate_unique=False, validate_constraints=False)
    return snapshot


@transaction.atomic
def record_reviewed_content(entries, *, now=None, dry_run=False):
    now = now or timezone.now()
    identifiers = [entry["exhibition_id"] for entry in entries]
    if len(set(identifiers)) != len(identifiers):
        raise ValidationError("A bundle cannot contain duplicate exhibition IDs.")
    exhibitions = {
        row.pk: row for row in Exhibition.objects.select_for_update().select_related("institution").filter(pk__in=identifiers)
    }
    if set(exhibitions) != set(identifiers):
        raise ValidationError("A reviewed exhibition does not exist.")
    snapshots = [_snapshot(entry, exhibitions[entry["exhibition_id"]], now) for entry in entries]
    existing_hashes = set(ExhibitionContent.objects.filter(
        review_hash__in=[snapshot.review_hash for snapshot in snapshots],
    ).values_list("review_hash", flat=True))
    new_snapshots = [snapshot for snapshot in snapshots if snapshot.review_hash not in existing_hashes]
    if not dry_run:
        for snapshot in new_snapshots:
            snapshot.save()
    return ContentImportResult(created=len(new_snapshots), unchanged=len(snapshots) - len(new_snapshots))


def current_exhibition_content(exhibition, *, now=None):
    """Never revive an older review after the newest review loses its evidence gate."""
    now = now or timezone.now()
    snapshot = ExhibitionContent.objects.filter(exhibition=exhibition).select_related("source_record").first()
    if snapshot is None or snapshot.reviewed_at > now or snapshot.expires_at <= now:
        return None
    source = snapshot.source_record
    if (source.institution_id != exhibition.institution.registry_id
            or source.content_hash != snapshot.source_record_hash
            or snapshot.canonical_fingerprint != canonical_fingerprint(exhibition, source)
            or not ExhibitionSourceLink.objects.filter(
                exhibition=exhibition, source_id=source.source_id, source_record_id=source.source_record_id,
                latest_source_record=source,
            ).exists()):
        return None
    return {key: getattr(snapshot, key) for key in (
        "introduction", "highlights", "visit_notes", "official_url", "source_owner", "reviewed_at", "expires_at",
    )}

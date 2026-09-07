from copy import deepcopy
from datetime import date, timedelta
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from backend.apps.catalog.models import Exhibition, ExhibitionContent, ExhibitionSourceLink, Institution
from backend.apps.sources.models import InstitutionAllowlistEntry, Source, SourceRecord
from backend.data_pipeline.reviewed_content import import_reviewed_content


class ExhibitionContentTests(TestCase):
    def setUp(self):
        self.now = timezone.now().replace(microsecond=0)
        self.institution = Institution.objects.create(registry_id="content-museum", name="내용 미술관")
        self.registered_source = Source.objects.create(
            registry_id="content-source", name="공식 자료", owner="자료 제공처", kind="OFFICIAL_API",
        )
        InstitutionAllowlistEntry.objects.create(
            registry_id=self.institution.registry_id, source=self.registered_source,
            name=self.institution.name, lifecycle="PROVISIONAL", health="HEALTHY",
        )
        self.source = SourceRecord.objects.create(
            source_id=self.registered_source.registry_id, institution_id=self.institution.registry_id,
            source_record_id="ex-1", source_owner="자료 제공처", payload={"title": "전시"}, content_hash="a" * 64,
        )
        self.exhibition = Exhibition.objects.create(
            institution=self.institution, title="색과 형태", start_date=date(2026, 9, 1),
            end_date=date(2026, 10, 31), venue="내용 미술관 1실", region_area="서울", region_district="종로구",
            lifecycle="CURRENT", official_url="https://example.com/exhibitions/1",
        )
        self.link = ExhibitionSourceLink.objects.create(
            exhibition=self.exhibition, source_id=self.source.source_id,
            source_record_id=self.source.source_record_id, latest_source_record=self.source,
        )
        self.entry = {
            "exhibition_id": self.exhibition.pk, "source_id": self.source.source_id,
            "source_record_id": self.source.source_record_id, "source_record_hash": self.source.content_hash,
            "title": self.exhibition.title, "start_date": "2026-09-01", "end_date": "2026-10-31",
            "venue": self.exhibition.venue, "official_url": self.exhibition.official_url,
            "introduction": "회화와 드로잉을 통해 색과 형태의 변화를 살펴보는 전시입니다.",
            "highlights": ["회화와 드로잉을 함께 볼 수 있습니다."],
            "visit_notes": [{"kind": "HOURS", "text": "화요일부터 일요일까지 10:00~18:00 운영합니다."}],
            "source_owner": self.institution.name, "reviewed_at": (self.now - timedelta(minutes=1)).isoformat(),
            "expires_at": (self.now + timedelta(days=14)).isoformat(),
            "evidence_notes": "공식 상세의 작품 종류와 관람 시간 항목을 확인함.",
        }
        self.url = f"/api/internal/v1/exhibitions/{self.exhibition.pk}/"

    def bundle(self, *entries):
        return {"schema_version": "1.0", "entries": list(entries or (self.entry,))}

    def test_import_is_idempotent_preserves_core_and_returns_only_public_content(self):
        exhibition_before = Exhibition.objects.values().get(pk=self.exhibition.pk)
        source_before = SourceRecord.objects.values().get(pk=self.source.pk)
        first = import_reviewed_content(self.bundle(), now=self.now)
        second = import_reviewed_content(self.bundle(), now=self.now)
        self.assertEqual((first.created, first.unchanged), (1, 0))
        self.assertEqual((second.created, second.unchanged), (0, 1))
        self.assertEqual(ExhibitionContent.objects.count(), 1)
        self.assertEqual(Exhibition.objects.values().get(pk=self.exhibition.pk), exhibition_before)
        self.assertEqual(SourceRecord.objects.values().get(pk=self.source.pk), source_before)
        content = self.client.get(self.url).json()["content"]
        self.assertEqual(set(content), {
            "introduction", "highlights", "visit_notes", "official_url", "source_owner", "reviewed_at", "expires_at",
        })
        self.assertEqual(content["introduction"], self.entry["introduction"])
        self.assertEqual(content["visit_notes"], self.entry["visit_notes"])
        self.assertEqual(self.client.get(self.url).json()["visit_information"]["price"]["state"], "UNKNOWN")

    def test_absent_content_keeps_detail_available(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["content"])

    def test_whole_bundle_rejects_one_invalid_entry_and_duplicate_ids(self):
        bad = {**self.entry, "exhibition_id": self.exhibition.pk + 100}
        for entries in ((self.entry, bad), (self.entry, self.entry)):
            with self.subTest(entries=entries), self.assertRaises(ValidationError):
                import_reviewed_content(self.bundle(*entries), now=self.now)
            self.assertEqual(ExhibitionContent.objects.count(), 0)

    def test_current_identity_and_registered_institution_are_required(self):
        for changes in (
            {"title": "다른 제목"}, {"start_date": "2026-09-02"}, {"venue": "다른 장소"},
            {"official_url": "https://example.com/exhibitions/2"}, {"source_id": "unregistered"},
            {"source_record_id": "different-record"}, {"source_record_hash": "b" * 64},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                import_reviewed_content(self.bundle({**self.entry, **changes}), now=self.now)
        InstitutionAllowlistEntry.objects.all().delete()
        with self.assertRaises(ValidationError):
            import_reviewed_content(self.bundle(), now=self.now)
        self.assertEqual(ExhibitionContent.objects.count(), 0)

    def test_replaced_source_or_changed_core_hides_old_content(self):
        import_reviewed_content(self.bundle(), now=self.now)
        Exhibition.objects.filter(pk=self.exhibition.pk).update(venue="변경된 전시실")
        self.assertIsNone(self.client.get(self.url).json()["content"])
        Exhibition.objects.filter(pk=self.exhibition.pk).update(venue=self.exhibition.venue)
        replacement = SourceRecord.objects.create(
            source_id=self.source.source_id, institution_id=self.source.institution_id,
            source_record_id=self.source.source_record_id, source_owner=self.source.source_owner,
            payload={"title": "새 원본"}, content_hash="b" * 64,
        )
        ExhibitionSourceLink.objects.filter(pk=self.link.pk).update(latest_source_record=replacement)
        self.assertIsNone(self.client.get(self.url).json()["content"])
        self.assertEqual(ExhibitionContent.objects.count(), 1)

    def test_latest_review_is_used_and_expiry_does_not_revive_older_review(self):
        from backend.apps.catalog.content import current_exhibition_content

        import_reviewed_content(self.bundle(), now=self.now)
        new_entry = {**self.entry, "introduction": "전시 구성을 다시 확인한 소개입니다.",
                     "reviewed_at": self.now.isoformat(), "expires_at": (self.now + timedelta(days=1)).isoformat()}
        import_reviewed_content(self.bundle(new_entry), now=self.now)
        self.assertEqual(ExhibitionContent.objects.count(), 2)
        self.assertEqual(current_exhibition_content(self.exhibition, now=self.now)["introduction"], new_entry["introduction"])
        self.assertIsNone(current_exhibition_content(self.exhibition, now=self.now + timedelta(days=2)))

    def test_immutable_snapshots_reject_instance_and_queryset_mutation(self):
        import_reviewed_content(self.bundle(), now=self.now)
        snapshot = ExhibitionContent.objects.get()
        snapshot.introduction = "변조"
        operations = [
            snapshot.save, snapshot.delete,
            lambda: ExhibitionContent.objects.filter(pk=snapshot.pk).update(introduction="변조"),
            lambda: ExhibitionContent.objects.filter(pk=snapshot.pk).delete(),
        ]
        for operation in operations:
            with self.assertRaises(ValidationError):
                operation()
        self.assertEqual(ExhibitionContent.objects.get().introduction, self.entry["introduction"])

    def test_inserting_a_new_instance_with_an_existing_primary_key_cannot_overwrite(self):
        import_reviewed_content(self.bundle(), now=self.now)
        values = ExhibitionContent.objects.values().get()
        values["introduction"] = "기존 스냅샷 덮어쓰기"
        duplicate = ExhibitionContent(**values)
        with self.assertRaises(ValidationError):
            duplicate.save()
        self.assertEqual(ExhibitionContent.objects.get().introduction, self.entry["introduction"])

    def test_registry_source_for_another_institution_cannot_authorize_content(self):
        SourceRecord.objects.filter(pk=self.source.pk).update(institution_id="other-museum")
        with self.assertRaises(ValidationError):
            import_reviewed_content(self.bundle(), now=self.now)
        self.assertEqual(ExhibitionContent.objects.count(), 0)

    def test_malformed_or_unsafe_content_and_dates_are_rejected(self):
        cases = (
            {"introduction": ""}, {"introduction": "<script>alert(1)</script>"},
            {"introduction": "&lt;img src=x&gt;"}, {"introduction": "a" * 2001},
            {"highlights": ["a"] * 4}, {"highlights": ["<b>작품</b>"]},
            {"visit_notes": [{"kind": "UNREGISTERED", "text": "설명"}]},
            {"visit_notes": [{"kind": "PRICE", "text": "무료"}] * 2},
            {"visit_notes": [{"kind": "PRICE", "text": ""}]},
            {"reviewed_at": (self.now + timedelta(seconds=1)).isoformat()},
            {"reviewed_at": "2026-09-01T10:00:00"},
            {"expires_at": (self.now + timedelta(days=31)).isoformat()},
            {"expires_at": self.entry["reviewed_at"]}, {"evidence_notes": ""},
            {"official_url": "javascript:alert(1)"}, {"official_url": "https://user:pass@example.com/"},
            {"official_url": "https://127.0.0.1/private"}, {"unknown_field": "unexpected"},
        )
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                import_reviewed_content(self.bundle({**self.entry, **changes}), now=self.now)
        self.assertEqual(ExhibitionContent.objects.count(), 0)

    def test_invalid_bundle_shape_and_nonstandard_json_are_rejected(self):
        for bundle in ([], {}, {"schema_version": "2.0", "entries": [self.entry]},
                       {"schema_version": "1.0", "entries": []}):
            with self.subTest(bundle=bundle), self.assertRaises(ValidationError):
                import_reviewed_content(bundle, now=self.now)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "content.json"
            path.write_text('{"schema_version":"1.0","schema_version":"1.0","entries":[]}', encoding="utf-8")
            with self.assertRaises(CommandError):
                call_command("import_exhibition_content", file=str(path), stdout=StringIO())

    def test_command_dry_run_validates_without_writing_then_imports(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "content.json"
            path.write_text(json.dumps(deepcopy(self.bundle()), ensure_ascii=False), encoding="utf-8")
            output = StringIO()
            call_command("import_exhibition_content", file=str(path), dry_run=True, stdout=output)
            self.assertEqual(ExhibitionContent.objects.count(), 0)
            self.assertIn("created=1", output.getvalue())
            call_command("import_exhibition_content", file=str(path), stdout=StringIO())
            self.assertEqual(ExhibitionContent.objects.count(), 1)

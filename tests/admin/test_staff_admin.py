from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from backend.apps.catalog.models import Exhibition, Institution, SourceConflict
from backend.apps.sources.models import (
    CollectionIssue,
    IngestionRun,
    InstitutionAllowlistEntry,
    InstitutionQualificationRun,
    InstitutionRunResult,
    Source,
    SourceRecord,
)


class AdminBoundaryConfigurationTests(SimpleTestCase):
    def test_enables_django_admin_session_and_csrf_boundary(self):
        self.assertIn("django.contrib.admin", settings.INSTALLED_APPS)
        self.assertIn(
            "django.middleware.csrf.CsrfViewMiddleware", settings.MIDDLEWARE
        )

    def test_anonymous_data_status_redirects_to_admin_login(self):
        response = self.client.get("/admin/data-status/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/admin/login/?next=/admin/data-status/")


class StaffAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.operator = users.objects.create_user("operator", is_staff=True)
        cls.viewer = users.objects.create_user("viewer", is_staff=True)
        cls.user = users.objects.create_user("visitor")
        cls.inactive = users.objects.create_user("inactive", is_staff=True, is_active=False)
        cls.superuser = users.objects.create_superuser("admin", password="test-only-password")
        cls.source = Source.objects.create(
            registry_id="test-source", name="운영 테스트 출처", owner="테스트 기관",
            kind="HTTPS_CSV_SHEET", operation_status="PAUSED",
        )
        cls.entry = InstitutionAllowlistEntry.objects.create(
            registry_id="test-institution", source=cls.source, name="검증 기관",
            lifecycle="PROVISIONAL", health="DEGRADED",
            consecutive_final_failed_count=1,
            promotion_validation_started_at=timezone.now() - timedelta(days=15),
            priority_reverify_at=timezone.now(),
            lifecycle_change_reason="TEST_REVIEW", health_reasons=["FAILED_RUN"],
        )
        cls.institution = Institution.objects.create(
            registry_id=cls.entry.registry_id, name=cls.entry.name,
        )
        cls.exhibition = Exhibition.objects.create(
            institution=cls.institution, title="현재 전시", start_date=date(2026, 1, 1),
            end_date=date(2027, 1, 1), venue="테스트관", region_area="서울",
            region_district="중구", lifecycle="CURRENT", freshness="STALE",
            official_url="https://example.org/exhibition/1",
            last_verified_at=timezone.now() - timedelta(days=4),
        )
        Exhibition.objects.create(
            institution=cls.institution, title="종료 전시", start_date=date(2025, 1, 1),
            end_date=date(2025, 2, 1), venue="테스트관", region_area="서울",
            region_district="중구", lifecycle="ENDED", freshness="UNVERIFIED",
            official_url="https://example.org/exhibition/2",
            last_verified_at=timezone.now() - timedelta(days=500),
        )
        cls.record = SourceRecord.objects.create(
            source_id=cls.source.registry_id, institution_id=cls.entry.registry_id,
            source_record_id="test-1", source_owner="테스트 기관",
            payload={"private": "DO_NOT_RENDER_RAW_PAYLOAD"}, content_hash="a" * 64,
        )
        cls.conflict = SourceConflict.objects.create(
            exhibition=cls.exhibition, field_name="end_date", canonical_value="2027-01-01",
            candidate_value="2027-02-01", candidate_source_record=cls.record,
        )
        cls.issue = CollectionIssue.objects.create(
            registry_id="test-issue", source=cls.source, institution=cls.entry,
            classification="ACCESS_BLOCK", scope="ENTRY", action="STOP",
            scope_evidence="DO_NOT_RENDER_RAW_EVIDENCE",
        )
        cls.ingestion_run = IngestionRun.objects.create(
            command="sync_exhibitions", source_id=cls.source.registry_id, status="FAILED",
            error_message="DO_NOT_RENDER_RAW_ERROR",
        )

    def grant(self, user, *permissions):
        from django.contrib.auth.models import Permission

        user.user_permissions.add(*Permission.objects.filter(codename__in=permissions))

    def test_non_staff_and_inactive_staff_cannot_access_status(self):
        for user in (self.user, self.inactive):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.get("/admin/data-status/")
                self.assertEqual(response.status_code, 302)
                self.assertNotContains(response, self.source.name, status_code=302)

    def test_staff_without_model_permissions_is_forbidden(self):
        self.client.force_login(self.operator)
        self.assertEqual(self.client.get("/admin/data-status/").status_code, 403)

    def test_permission_filters_counts_rows_and_related_links(self):
        self.grant(self.viewer, "view_source")
        self.client.force_login(self.viewer)
        response = self.client.get("/admin/data-status/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.source.name)
        self.assertNotContains(response, self.entry.name)
        self.assertNotContains(response, self.exhibition.title)
        self.assertNotContains(response, "전체 전시")
        self.assertContains(response, reverse("admin:sources_source_change", args=[self.source.pk]))
        self.assertNotContains(response, reverse("admin:catalog_exhibition_changelist"))

    def test_source_only_staff_cannot_open_exhibition_admin(self):
        self.grant(self.viewer, "view_source")
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("admin:catalog_exhibition_change", args=[self.exhibition.pk]))
        self.assertEqual(response.status_code, 403)

    def test_related_evidence_links_follow_related_model_permissions(self):
        self.grant(self.viewer, "view_sourceconflict")
        self.client.force_login(self.viewer)
        url = reverse("admin:catalog_sourceconflict_change", args=[self.conflict.pk])
        exhibition_url = reverse("admin:catalog_exhibition_change", args=[self.exhibition.pk])
        record_url = reverse("admin:sources_sourcerecord_change", args=[self.record.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, exhibition_url)
        self.assertNotContains(response, record_url)
        self.grant(self.viewer, "view_exhibition", "view_sourcerecord")
        response = self.client.get(url)
        self.assertContains(response, exhibition_url)
        self.assertContains(response, record_url)

    def test_provisional_status_counts_distinct_success_days_after_last_failure(self):
        now = timezone.now()
        for offset, status in ((6, "SUCCESS"), (6, "SUCCESS"), (5, "FAILED"), (4, "SUCCESS"), (4, "SUCCESS"), (2, "SUCCESS")):
            finished_at = now - timedelta(days=offset)
            ingestion = IngestionRun.objects.create(command="sync_exhibitions", status=status)
            result = InstitutionRunResult.objects.create(
                ingestion_run=ingestion, institution=self.entry, status=status,
                lifecycle_before="PROVISIONAL", lifecycle_after="PROVISIONAL",
                health_before="HEALTHY", health_after="HEALTHY", finished_at=finished_at,
            )
            InstitutionQualificationRun.objects.create(
                institution_result=result, institution=self.entry, status=status,
                finished_at=finished_at, service_date=timezone.localdate(finished_at),
                source_operation_status="NORMAL", target_count=5,
            )
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/data-status/")
        self.assertContains(response, "마지막 실패 이후 성공 2개 날짜 · 주기 내 실패 1회")
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.lifecycle, "PROVISIONAL")

    def test_change_permission_allows_reading_but_never_direct_mutation(self):
        self.grant(self.viewer, "change_exhibition")
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get("/admin/data-status/").status_code, 200)
        url = reverse("admin:catalog_exhibition_change", args=[self.exhibition.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.post(url, {"title": "changed"}).status_code, 403)

    def test_current_status_and_due_schedule_use_database_records(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/data-status/")
        self.assertEqual(response.status_code, 200)
        metrics = {metric["key"]: metric["count"] for metric in response.context["metrics"]}
        self.assertEqual(metrics["exhibitions"], 2)
        self.assertEqual(metrics["current"], 1)
        self.assertEqual(metrics["ended"], 1)
        self.assertEqual(metrics["stale"], 1)
        self.assertEqual(metrics["unverified"], 1)
        self.assertEqual(metrics["due"], 1)
        self.assertEqual(metrics["conflicts"], 1)
        self.assertEqual(metrics["issues"], 1)
        self.assertEqual(metrics["failed_runs"], 1)
        self.assertContains(response, "PROVISIONAL")
        self.assertContains(response, "DEGRADED")
        self.assertContains(response, "PAUSED")
        self.assertContains(response, "TEST_REVIEW")
        for model, obj in (("sourceconflict", self.conflict),):
            self.assertContains(response, reverse(f"admin:catalog_{model}_change", args=[obj.pk]))
        self.assertContains(response, reverse("admin:sources_collectionissue_change", args=[self.issue.pk]))
        self.assertIn("no-store", response["Cache-Control"])
        self.assertNotContains(response, "DO_NOT_RENDER_RAW")

    def test_canonical_and_operating_state_admin_are_read_only_even_for_superuser(self):
        self.client.force_login(self.superuser)
        for model, obj in (("catalog_exhibition", self.exhibition), ("sources_source", self.source)):
            with self.subTest(model=model):
                url = reverse(f"admin:{model}_change", args=[obj.pk])
                self.assertEqual(self.client.get(url).status_code, 200)
                self.assertEqual(self.client.post(url, {"title": "tampered", "operation_status": "NORMAL"}).status_code, 403)
                self.assertEqual(self.client.get(reverse(f"admin:{model}_add")).status_code, 403)
                self.assertEqual(self.client.get(reverse(f"admin:{model}_delete", args=[obj.pk])).status_code, 403)
        self.exhibition.refresh_from_db()
        self.source.refresh_from_db()
        self.assertEqual(self.exhibition.title, "현재 전시")
        self.assertEqual(self.source.operation_status, "PAUSED")

    def test_raw_payload_and_errors_are_not_rendered_in_admin(self):
        self.client.force_login(self.superuser)
        for model, obj in (("sourcerecord", self.record), ("ingestionrun", self.ingestion_run)):
            with self.subTest(model=model):
                for suffix, args in (("changelist", []), ("change", [obj.pk])):
                    response = self.client.get(reverse(f"admin:sources_{model}_{suffix}", args=args))
                    self.assertEqual(response.status_code, 200)
                    self.assertNotContains(response, "DO_NOT_RENDER_RAW")

    def test_login_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post("/admin/login/", {"username": "admin", "password": "test-only-password"})
        self.assertEqual(response.status_code, 403)

    def test_status_is_get_only_and_requires_csrf_for_post(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.post("/admin/data-status/", {}).status_code, 405)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.superuser)
        self.assertEqual(client.post("/admin/data-status/", {}).status_code, 403)

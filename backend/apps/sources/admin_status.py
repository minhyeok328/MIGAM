from urllib.parse import urlencode

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from backend.apps.catalog.models import (
    ChangeHistory, DuplicateCandidate, Exhibition, MediaAsset, MediaRights, SourceConflict,
)
from backend.apps.data_quality.models import ExhibitionCandidate
from backend.data_pipeline.freshness.schedule import refresh_schedule_for
from backend.data_pipeline.registry import SourceRegistry

from .admin import can_view_model
from .models import (
    CollectionIssue, IngestionRun, InstitutionAllowlistEntry,
    InstitutionQualificationRun, InstitutionRunResult, PromotionEvidence, Source,
)


RECENT_LIMIT = 20


def _list_url(model, **filters):
    opts = model._meta
    url = reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")
    return f"{url}?{urlencode(filters)}" if filters else url


def _cell(value, url=None):
    return {"value": value if value not in (None, "") else "—", "url": url}


def _link(user, obj, label=None):
    if obj is None or not can_view_model(user, type(obj)):
        return _cell("—")
    opts = obj._meta
    return _cell(
        label or f"{opts.verbose_name} #{obj.pk}",
        reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[obj.pk]),
    )


def _qualification_summary(entry, now):
    if entry.promotion_validation_started_at is None:
        return "검증 시작 기록 없음"
    runs = list(entry.qualification_runs.filter(
        finished_at__gte=entry.promotion_validation_started_at
    ).order_by("finished_at", "id"))
    days = set()
    failed = 0
    for run in runs:
        if run.status == InstitutionQualificationRun.Status.FAILED:
            days.clear()
            failed += 1
        elif run.status == InstitutionQualificationRun.Status.SUCCESS:
            days.add(run.service_date)
    elapsed = max((timezone.localdate(now) - timezone.localdate(entry.promotion_validation_started_at)).days, 0)
    return f"{elapsed}일 경과 · 마지막 실패 이후 성공 {len(days)}개 날짜 · 주기 내 실패 {failed}회"


def _registry_qualifications():
    try:
        registry = SourceRegistry.load(settings.REPOSITORY_ROOT / "sources.yaml")
    except (OSError, ValueError):
        return {}
    return {
        entry["id"]: entry.get("qualification", {})
        for entry in registry.data.get("institution_allowlist", ())
    }


@require_GET
def data_status(request):
    """Called through AdminSite.admin_view: active staff, CSRF and no-cache."""
    user = request.user
    now = timezone.now()
    metrics = []
    tables = []

    def metric(key, label, model, queryset=None, **filters):
        if can_view_model(user, model):
            queryset = queryset if queryset is not None else model.objects.filter(**filters)
            metrics.append({"key": key, "label": label, "count": queryset.count(), "url": _list_url(model, **filters)})

    def table(title, model, columns, rows):
        tables.append({"title": title, "url": _list_url(model), "columns": columns, "rows": rows})

    if can_view_model(user, Exhibition):
        for key, label, filters in (
            ("exhibitions", "전체 전시", {}),
            ("current", "현재", {"lifecycle": "CURRENT"}),
            ("upcoming", "예정", {"lifecycle": "UPCOMING"}),
            ("ended", "종료", {"lifecycle": "ENDED"}),
            ("stale", "STALE", {"freshness": "STALE"}),
            ("unverified", "UNVERIFIED", {"freshness": "UNVERIFIED"}),
        ):
            metric(key, label, Exhibition, **filters)
        due = [exhibition for exhibition in Exhibition.objects.filter(
            lifecycle__in=("CURRENT", "UPCOMING")
        ) if refresh_schedule_for(exhibition, now=now).is_due]
        metrics.append({"key": "due", "label": "일정상 재확인 대상", "count": len(due), "url": "#due-exhibitions"})
        table("일정상 재확인 대상", Exhibition, ("전시", "마지막 확인", "저장 freshness", "다음 확인"), [
            [_link(user, exhibition, exhibition.title), _cell(exhibition.last_verified_at),
             _cell(exhibition.freshness), _cell(refresh_schedule_for(exhibition, now=now).next_refresh_at)]
            for exhibition in sorted(due, key=lambda item: item.last_verified_at)[:RECENT_LIMIT]
        ])
        tables[-1]["id"] = "due-exhibitions"

    if can_view_model(user, Source):
        table("Source 운영 상태", Source, ("출처", "운영 상태", "확인 시각"), [
            [_link(user, source, source.name), _cell(source.operation_status), _cell(source.updated_at)]
            for source in Source.objects.all()[:RECENT_LIMIT]
        ])

    if can_view_model(user, InstitutionAllowlistEntry):
        qualifications = _registry_qualifications()
        rows = []
        for entry in InstitutionAllowlistEntry.objects.select_related("source")[:RECENT_LIMIT]:
            qualification = qualifications.get(entry.registry_id, {})
            sample = (
                f"{qualification.get('result', '미확인')} · CORE_PASS "
                f"{qualification.get('core_pass', '미확인')}/{qualification.get('sample_count', '미확인')}"
                if qualification else "승인 registry 심사 기록 없음"
            )
            validation = (
                _qualification_summary(entry, now)
                if can_view_model(user, InstitutionQualificationRun) else "조회 권한 없음"
            )
            conflict_count = (
                SourceConflict.objects.filter(
                    exhibition__institution__registry_id=entry.registry_id, status="OPEN"
                ).count() if can_view_model(user, SourceConflict) else "조회 권한 없음"
            )
            last_result = (
                entry.run_results.order_by("-finished_at", "-id").first()
                if can_view_model(user, InstitutionRunResult) else None
            )
            rows.append([
                _link(user, entry, entry.name), _link(user, entry.source, entry.source.operation_status),
                _cell(entry.lifecycle), _cell(entry.health), _cell(entry.consecutive_final_failed_count),
                _cell(entry.priority_reverify_at), _cell(sample), _cell(entry.promotion_validation_started_at),
                _cell(validation), _cell(conflict_count),
                _link(user, last_result, f"{last_result.status} · {last_result.finished_at}" if last_result else None),
                _cell(f"{entry.lifecycle_change_reason or '—'} · {', '.join(entry.health_reasons) or '—'}"),
            ])
        table("기관 심사와 수집 건강 상태", InstitutionAllowlistEntry,
              ("기관", "Source", "Lifecycle", "Health", "연속 최종 실패", "우선 재검증", "등록 심사", "검증 시작", "검증 주기", "열린 충돌", "마지막 실행", "전이·저하 근거"), rows)

    if can_view_model(user, IngestionRun):
        metric("successful_runs", "수집 성공 누적", IngestionRun, status="SUCCESS")
        metric("failed_runs", "수집 실패 누적", IngestionRun, status="FAILED")
        table("최근 수집 실행", IngestionRun, ("실행", "Source ID", "결과", "수신 / 검증 / 격리", "시작", "종료"), [
            [_link(user, run, f"#{run.pk} {run.command}"), _cell(run.source_id), _cell(run.status),
             _cell(f"{run.received_count} / {run.verified_count} / {run.quarantined_count}"),
             _cell(run.started_at), _cell(run.finished_at)]
            for run in IngestionRun.objects.all()[:RECENT_LIMIT]
        ])

    if can_view_model(user, CollectionIssue):
        metric("issues", "열린 수집 문제", CollectionIssue, status="OPEN")
        table("열린 수집 문제", CollectionIssue, ("문제", "분류", "범위", "필드", "조치", "기관", "Source"), [
            [_link(user, issue, issue.registry_id), _cell(issue.classification), _cell(issue.scope),
             _cell(issue.field), _cell(issue.action), _link(user, issue.institution, issue.institution.name if issue.institution else None),
             _link(user, issue.source, issue.source.name)]
            for issue in CollectionIssue.objects.filter(status="OPEN").select_related("source", "institution").order_by("-updated_at")[:RECENT_LIMIT]
        ])

    if can_view_model(user, SourceConflict):
        metric("conflicts", "열린 출처 충돌", SourceConflict, status="OPEN")
        table("열린 출처 충돌", SourceConflict, ("충돌", "필드", "전시", "후보 근거", "발견"), [
            [_link(user, conflict), _cell(conflict.field_name), _link(user, conflict.exhibition, conflict.exhibition.title),
             _link(user, conflict.candidate_source_record), _cell(conflict.created_at)]
            for conflict in SourceConflict.objects.filter(status="OPEN").select_related("exhibition", "candidate_source_record").order_by("-created_at")[:RECENT_LIMIT]
        ])

    if can_view_model(user, DuplicateCandidate):
        metric("duplicates", "열린 중복 후보", DuplicateCandidate, status="OPEN")
        table("열린 중복 후보", DuplicateCandidate, ("후보", "사유", "기준 전시", "관련 전시"), [
            [_link(user, candidate), _cell(candidate.reason), _link(user, candidate.primary_exhibition, candidate.primary_exhibition.title),
             _link(user, candidate.related_exhibition, candidate.related_exhibition.title)]
            for candidate in DuplicateCandidate.objects.filter(status="OPEN").select_related("primary_exhibition", "related_exhibition").order_by("-created_at")[:RECENT_LIMIT]
        ])

    if can_view_model(user, ExhibitionCandidate):
        metric("quarantined", "격리된 후보", ExhibitionCandidate, quarantined=True)

    if can_view_model(user, MediaAsset) and can_view_model(user, MediaRights):
        known_rights = MediaRights.objects.filter(is_current=True).exclude(policy_status="RIGHTS_UNKNOWN")
        pending = MediaAsset.objects.exclude(pk__in=known_rights.values("asset_id"))
        metric("rights_pending", "권리 확인 필요 미디어", MediaAsset, queryset=pending)
        table("권리 확인 필요 미디어", MediaAsset, ("미디어", "역할", "유형", "출처 근거"), [
            [_link(user, asset), _cell(asset.role), _cell(asset.media_type), _link(user, asset.source_record)]
            for asset in pending.select_related("source_record").order_by("pk")[:RECENT_LIMIT]
        ])

    if can_view_model(user, ChangeHistory):
        table("승격에 유효한 의미 변경", ChangeHistory, ("변경", "전시 정본", "원본 근거", "필드", "변경 유형", "발생"), [
            [_link(user, change), _link(user, change.exhibition, change.exhibition.title),
             _link(user, change.source_record), _cell(change.field_name), _cell(change.meaningful_type), _cell(change.created_at)]
            for change in ChangeHistory.objects.filter(meaningful_for_promotion=True).select_related("exhibition", "source_record").order_by("-created_at")[:RECENT_LIMIT]
        ])

    if can_view_model(user, PromotionEvidence):
        table("확정된 ACTIVE 승격 증거", PromotionEvidence, ("증거", "기관", "마지막 자격 실행", "의미 변경", "승격 시각"), [
            [_link(user, evidence), _link(user, evidence.institution, evidence.institution.name),
             _link(user, evidence.last_qualification_run), _link(user, evidence.meaningful_change_history), _cell(evidence.promoted_at)]
            for evidence in PromotionEvidence.objects.select_related("institution", "last_qualification_run", "meaningful_change_history")[:RECENT_LIMIT]
        ])

    if not metrics and not tables:
        raise PermissionDenied
    context = {
        **admin.site.each_context(request), "title": "데이터 상태", "metrics": metrics,
        "tables": tables, "checked_at": now, "recent_limit": RECENT_LIMIT,
    }
    return render(request, "admin/data_status.html", context)

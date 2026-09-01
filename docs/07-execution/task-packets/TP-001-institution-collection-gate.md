---
title: "TP-001 기관 운영 상태와 수집 전 게이트"
status: APPROVED
version: "1.0.2"
last_updated: "2026-09-01"
authoritative_for:
  - "승인 Source와 기관 allowlist의 DB 운영 상태 부트스트랩"
  - "P0 변경 명령의 lifecycle·Source 상태·Critical 수집 전 차단"
  - "기관별 실행 결과와 기본 health·연속 실패 상태 갱신"
related_documents:
  - "../../00-governance/decision-register.md"
  - "../../02-data/data-model.md"
  - "../../02-data/data-pipeline.md"
  - "../../06-quality/acceptance-criteria.md"
  - "../../06-quality/test-plan.md"
  - "../implementation-readiness.md"
---

# TP-001 기관 운영 상태와 수집 전 게이트

## 목적과 승인 근거

- 지원하는 P0 과업: 승인 출처 데이터만 안전하게 수집·재확인하고 마지막 정상 정본을 보존한다.
- 승인 근거: 2026-09-01 사용자의 "다음 작업 진행" 지시와 `DEC-097`~`DEC-099`, `P0-FR-088`, `P0-FR-091`, `P0-FR-092`.
- 제품·엔지니어링 근거: Data Model 7~8절, Data Pipeline 2.2.4·2.3절, `AC-023`, `AC-026`, `AC-027`.

## 범위

### 포함

- `sources.yaml`의 승인 Source 3개, InstitutionAllowlistEntry 5개, CollectionIssue를 DB 운영 레코드로 멱등 부트스트랩한다.
- YAML은 최초 승인 상태의 부트스트랩이다. 이미 존재하는 DB Source 운영 상태, 기관 lifecycle·health·실패 수, CollectionIssue 해결 상태를 명령 재실행으로 덮어쓰지 않는다.
- 공용 수집 게이트는 InstitutionAllowlistEntry가 `PROVISIONAL` 또는 `ACTIVE`, Source가 `NORMAL`, 영향 scope에 미해결 Critical CollectionIssue가 없을 때만 통과시킨다.
- `DEGRADED` health는 수집을 막지 않는다.
- `ENTRY` Critical은 해당 기관만, `SOURCE` Critical은 연결 기관 전체를 차단한다.
- `sync_exhibitions`, `refresh_due_exhibitions`, `refresh_exhibition`은 네트워크·파일 수집과 IngestionRun 생성 전에 같은 게이트를 사용한다.
- 수집 전 게이트 통과 뒤 새 Critical이 열리는 경우를 막기 위해 InstitutionRunResult 성공 확정 직전에 영향 scope의 열린 Critical을 다시 검사한다. 발견 시 성공 확정을 거부하고 실행 변경을 롤백한 뒤 실패 결과 경로로 전환한다.
- 실제 실행 대상 InstitutionAllowlistEntry마다 InstitutionRunResult를 정확히 하나 기록한다.
- 정본·검증 결과·기관별 결과·health를 성공으로 확정하는 DB 변경은 한 트랜잭션으로 처리한다. 기관별 결과 확정이 실패하면 앞선 성공 변경을 롤백하고 실행을 `FAILED`로 남긴다.
- 최종 성공은 `ACTIVE` 실패 수를 0으로 초기화하고, 미해결 `STRUCTURAL_OPTIONAL`이 없으면 health를 `HEALTHY`로 복구한다.
- `ACTIVE` 첫 최종 실패는 `DEGRADED`와 실패 수 1, 중간 성공 없는 서로 다른 IngestionRun의 두 번째 실패는 `SUSPENDED`와 실패 수 2로 기록한다.
- 실패 결과 확정 시 영향 scope에 열린 Critical이 있으면 실패 수가 1이어도 `ACTIVE`를 즉시 `SUSPENDED`로 전환하고 전이 시각·시스템 주체·사유·이슈 근거를 저장한다.
- `PROVISIONAL` 최종 실패는 `DEGRADED`로 만들되 실패 수는 0으로 유지한다.
- 차단되거나 실패한 실행은 기존 SourceRecord·Canonical Exhibition·FieldEvidence를 삭제하거나 빈 값으로 덮어쓰지 않는다.

### 포함하지 않음

- `InstitutionQualificationRun`, `PromotionEvidence`, 14일·서로 다른 날짜 3회 성공을 이용한 `PROVISIONAL → ACTIVE` 자동 승격.
- 실행 중 새 Critical을 자동 분류하는 탐지기와 전체 `ChangeHistory` 감사 이력·UI.
- 수집기 요청을 기관별로 귀속하는 재시도 telemetry. 귀속 가능한 신호가 없는 이번 범위의 `retry_count`는 실제 0회로 오인되지 않도록 `null`로 둔다.
- `STRUCTURAL_OPTIONAL` 선택 필드의 실제 `UNKNOWN` 데이터 모델 확장.
- Django Admin 등록과 `/admin/data-status/` 화면.
- SearchService, OpenAPI, 추천, 프론트엔드.

### 변경 영역

- `backend/apps/sources/models.py`와 신규 migration.
- `backend/data_pipeline/registry_state.py`, `collection_gate.py`, `institution_runs.py`.
- 세 변경 관리 명령과 `backend/data_pipeline/freshness/execution.py`.
- `tests/persistence/`의 모델·게이트·명령·실행 결과 테스트.
- README, 문서 인덱스, Acceptance·Test·Traceability의 실제 구현 증거.

## 계약과 데이터

- 관련 도메인: `sources`, `data_quality`, `catalog`.
- 코드 소유 경계: 정본 운영 모델은 `backend/apps/sources/`, 수집 판정과 상태 전이는 `backend/data_pipeline/`.
- Source 운영 상태 값: `NORMAL`, `PAUSED`, `DISABLED`.
- Institution lifecycle: `CANDIDATE`, `PROVISIONAL`, `ACTIVE`, `SUSPENDED`.
- Institution health: `HEALTHY`, `DEGRADED`; lifecycle·Source 상태·DataEligibility와 독립이다.
- Critical 분류: `POLICY_BLOCK`, `ACCESS_BLOCK`, `STRUCTURAL_CRITICAL`.
- 비차단 분류: `STRUCTURAL_OPTIONAL`, `RECORD_EXCEPTION`.
- CollectionIssue scope: `ENTRY`, `SOURCE`; `ENTRY`에는 영향 기관이 필수다.
- `(ingestion_run, institution_allowlist_entry)`는 유일하다.
- 자동 lifecycle 전이는 `lifecycle_changed_at`, `lifecycle_changed_by = SYSTEM`, `lifecycle_change_reason`, `suspension_reason`으로 직접 근거를 남긴다.
- API·UI 계약 영향: 없음.
- 최소 품질·선택 정보·필수 조건 계약은 변경하지 않는다.
- 운영자 경계: 후속 staff 전용 Admin 작업에서 현재 모델을 연결하며 이번 패킷은 공개 편집기를 만들지 않는다.

## 개인정보·보안

- 사용자 계정·브라우저 저장·서버 프로필·개발 이벤트 계약 영향 없음.
- 추천 payload, 원문 검색어, 정확 좌표를 저장하지 않는다.
- 새 운영 레코드는 공식 출처 운영과 기관별 실행 결과만 보존한다.
- 외부 분석이나 신규 외부 전송을 추가하지 않는다.

## 외부 의존성과 안전한 저하

- 승인 Source와 필드·호출 제약은 `sources.yaml`, 표본은 `fixtures/source-qualification.json`을 따른다.
- 키 없는 fixture 경로가 모든 자동 테스트의 기본 경로다.
- 차단 판정은 외부 요청 전에 끝나야 한다.
- 수집 또는 결과 확정 실패 시 마지막 정상 원본·정본·검증 시각을 보존하고 IngestionRun과 InstitutionRunResult에 실패를 남긴다. 성공 확정 도중 실패한 DB 변경은 부분 커밋하지 않는다.
- `PROVISIONAL`과 `ACTIVE`는 같은 레코드 품질·권리·최신성·충돌 경로를 사용한다.
- `ACTIVE → SUSPENDED → PROVISIONAL` 복구 승인과 승격 증거 초기화는 후속 패킷으로 분리한다.

## 검증 증거

- 자동 테스트: Django TestCase로 registry 멱등성, 상태 보존, lifecycle·Source·ENTRY/SOURCE Critical 수집 전·성공 확정 전 게이트, `DEGRADED` 허용, 기관별 결과 유일성, `ACTIVE` 실패 사다리·Critical 즉시 중단과 전이 근거, `PROVISIONAL` counter 0을 검증한다.
- 명령 통합: 차단된 explicit source와 canonical ID가 수집·IngestionRun 전에 실패하고, 전체/due 실행은 차단 기관을 제외하며 공유 Source의 허용 기관은 계속 실행되는지 검증한다.
- 원자성 통합: 기관별 결과 확정을 강제로 실패시켜 sync 정본·후보와 refresh 성공 검증·검증 시각이 롤백되고 실패 실행·기관 결과만 남는지 검증한다.
- 회귀: 기존 수집·정본화·최신성 테스트 전체를 실행한다.
- 실행 명령: `uv run --project backend python backend/manage.py test tests --verbosity 1`.
- migration 확인: `uv run --project backend python backend/manage.py makemigrations --check --dry-run`.
- 문서 확인: `git diff --check`와 변경 문서의 핵심 참조를 확인한다.

## 의존성·결정

- 선행 작업: `OD-003` 승인 Source·기관·fixture, 정본화와 전시별 재확인 경로.
- 적용 결정: `OD-003 RESOLVED`, `DEC-097`~`DEC-099`.
- `OD-001`, `OD-002`, `OD-004`~`OD-007`은 이 로컬 내부 운영 slice를 차단하지 않는다.

## 완료 기준

- 세 변경 명령이 공용 게이트를 우회하지 않는다.
- 차단 판정 전에 외부 수집과 IngestionRun 생성이 0건이다.
- 수집 전 판정 직후 열린 Critical도 성공 정본·검증·기관 결과로 확정되지 않는다.
- 실행 대상 기관별 결과가 정확히 한 건이며 health·실패 수가 계약대로 갱신된다.
- 성공 확정 변경은 원자적이며 Critical 자동 중단의 시각·주체·사유·이슈 근거를 역추적할 수 있다.
- 기존 정상 정본 보존과 외부 키 없는 테스트 재현성이 유지된다.
- README와 품질 문서가 실제 코드·테스트 경로를 가리킨다.

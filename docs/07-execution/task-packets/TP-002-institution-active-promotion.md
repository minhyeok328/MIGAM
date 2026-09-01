---
title: "TP-002 기관 ACTIVE 승격 증거와 자동 전이"
status: APPROVED
version: "1.0.1"
last_updated: "2026-09-01"
authoritative_for:
  - "PROVISIONAL 기관의 승격 검증 실행과 QualificationRun 기록"
  - "Canonical ChangeHistory와 P0 의미 변경 증거"
  - "14일·서로 다른 3일 성공 기반 ACTIVE 자동 승격"
related_documents:
  - "../../00-governance/decision-register.md"
  - "../../01-product/prd-p0.md"
  - "../../02-data/data-source-policy.md"
  - "../../02-data/data-model.md"
  - "../../02-data/normalization-rules.md"
  - "../../02-data/data-pipeline.md"
  - "../../06-quality/acceptance-criteria.md"
  - "../../06-quality/test-plan.md"
  - "../implementation-readiness.md"
---

# TP-002 기관 ACTIVE 승격 증거와 자동 전이

## 목적과 승인 근거

- 지원하는 P0 과업: 승인 기관의 실제 수집·변경 처리 안정성을 검증해 고신뢰 `ACTIVE` 상태로 승격한다.
- 승인 근거: 2026-09-01 사용자의 후속 작업 진행 지시와 `DEC-098`, `P0-FR-091`, `AC-026`.
- 선행 구현: [`TP-001`](TP-001-institution-collection-gate.md)의 Source·기관 운영 상태, 공용 수집 게이트, InstitutionRunResult와 원자적 성공 확정.

## 범위

### 포함

- `sync_exhibitions --qualification`을 명시적인 기관 승격 검증 실행으로 추가한다. 일반 sync와 `refresh_due_exhibitions`·`refresh_exhibition`은 승격 성공일을 만들지 않는다.
- InstitutionAllowlistEntry에 승인 표본의 핵심 대상 수를 정적 등록 정보로 동기화한다. 현재 다섯 승인 기관은 `sources.yaml`의 `qualification.sample_count = 5`를 사용한다.
- 자격 실행의 실제 대상 `PROVISIONAL` 기관마다 InstitutionRunResult와 일대일인 InstitutionQualificationRun을 정확히 하나 기록한다. `ACTIVE` 실행에는 만들지 않는다.
- 자격 실행의 기관 결과는 최소 승인 표본 수만큼 핵심 대상을 수집·처리하고, 최종 미수집 핵심 대상이나 기관·템플릿 수준 핵심 데이터 미완성이 없어야 `SUCCESS`다. 승인된 단건 `RECORD_EXCEPTION`의 정상 격리는 실패로 세지 않지만, 승인 표본 수 자체가 부족하면 해당 기관 결과와 QualificationRun을 `FAILED`로 기록하고 IngestionRun도 `FAILED`로 끝낸다.
- InstitutionRunResult와 InstitutionQualificationRun은 `CORE_PASS + VERIFIED + 비격리` 대상 수, 승인된 `RECORD_EXCEPTION + QUARANTINE_RECORD` 수와 두 값을 합친 핵심 처리 완료 수를 보존한다. InstitutionQualificationRun은 여기에 `finished_at`, `Asia/Seoul` 서비스 날짜, 재시도 수의 측정 여부, 최종 미수집 핵심 대상 수, Critical 분류 수, Source 상태, 미해결 SourceConflict 수, 의미 변경 수와 실패 사유를 함께 보존한다.
- Canonical 신규 생성과 실제 필드 변경을 SourceRecord·ExhibitionCandidate 규칙 버전·IngestionRun·Canonical Exhibition에 연결한 ChangeHistory로 기록한다.
- 현재 Canonical 스키마에서 승격 의미 변경은 `NEW_EXHIBITION`, `END_DATE_CHANGED`, `VENUE_CHANGED`, `CANCELED`만 인정한다. title·start_date·region·일반 lifecycle·official_url 변화와 raw hash만의 변화는 감사 이력에는 남겨도 승격 근거가 아니다.
- `promotion_validation_started_at + 14일` 경과, 마지막 Qualification 실패 이후 `Asia/Seoul` 기준 서로 다른 날짜의 최종 성공 3일, 그 세 실행 중 의미 ChangeHistory 1건 이상을 요구한다. 같은 날짜 성공은 한 날짜만 센다.
- 승격 직전 마지막 Qualification 성공, Source `NORMAL`, 열린 Critical 0건, 해당 기관 Canonical의 미해결 SourceConflict 0건을 다시 확인한다.
- 모든 조건을 통과하면 선택한 QualificationRun 3건과 의미 ChangeHistory를 PromotionEvidence로 고정하고 lifecycle을 `ACTIVE`로 전이한다. 전이 시각·주체 `SYSTEM`·사유를 저장한다.
- 모델·정본 변경·기관 결과·QualificationRun·PromotionEvidence·lifecycle 전이는 기존 실행 성공 확정 트랜잭션 안에서 함께 커밋하거나 롤백한다.

### 포함하지 않음

- `SUSPENDED → PROVISIONAL` 운영자 복구 승인과 새 검증 시작 UI.
- CandidateAssessment·4/5 후보 심사 자동화.
- 수집기 요청의 기관별 retry telemetry. 측정할 수 없는 값은 `null`로 유지한다.
- 핵심 대상 페이지별 상세 실행 로그. 이번 패킷은 승인 표본 수와 기관별 최종 처리량으로 완전성을 판정한다.
- 현재 Canonical 모델에 없는 요금·예약·공식 설명 필드의 ChangeHistory와 의미 변경 판정.
- 전체 lifecycle·health ChangeHistory, Django Admin과 `/admin/data-status/` 화면.
- 배포 스케줄러, SearchService, OpenAPI, 추천, 프론트엔드.

## 계약과 데이터

- `IngestionRun.qualification_mode = true`인 `sync_exhibitions`만 승격 검증 실행이다.
- InstitutionQualificationRun은 InstitutionRunResult와 일대일이며 `PROVISIONAL` 결과에만 존재한다.
- 실패 이후 과거 성공 레코드는 삭제하지 않고, 승격 평가 시 마지막 `FAILED` 이후의 성공만 사용한다.
- 한 서비스 날짜에 성공이 여러 건이면 의미 변경이 있는 실행을 우선 대표로 선택하고, 없으면 가장 늦은 실행을 선택한다.
- PromotionEvidence는 한 승격 주기의 불변 승인 근거이며 선택한 서로 다른 세 서비스 날짜와 의미 변경을 연결한다.
- 열린 Critical은 `ENTRY`·`SOURCE` scope를 TP-001과 동일하게 판정한다.
- 미해결 SourceConflict는 해당 기관 Canonical Exhibition의 `OPEN` 레코드 전체를 veto로 사용한다.
- 단건 격리 완료는 같은 기관·Source·source_record_id에 연결된 열린 `RECORD_EXCEPTION`, `ENTRY` scope, `QUARANTINE_RECORD` 조치가 모두 일치할 때만 승인한다. 그 밖의 `CORE_FAIL`·`EXCLUDED`·격리 레코드는 핵심 처리 완료 수에 포함하지 않는다.

## 외부 의존성과 안전한 저하

- 자동 테스트와 기본 자격 검증은 승인 fixture를 사용하며 외부 API 키가 필요 없다.
- 자격 대상 수를 충족하지 못하면 기존 정상 정본을 삭제하지 않고 실행·기관·Qualification 실패 근거만 남긴다.
- Source 비정상·Critical·충돌·의미 증거 부재는 `PROVISIONAL`을 유지하며 조건을 자동 완화하지 않는다.

## 검증 증거

- ChangeHistory: 신규 전시와 실제 Canonical 변경만 생성되고 의미 allowlist·denylist가 구분되는지 검증한다.
- Qualification: 일반 실행과 `ACTIVE` 실행은 생성하지 않고, 자격 실행의 `PROVISIONAL` 기관에만 일대일 생성되는지 검증한다.
- 날짜: 14일 미만, 정확히 14일, UTC와 `Asia/Seoul` 날짜 경계, 같은 날짜 중복을 검증한다.
- 연속성: 중간 `FAILED`가 이전 성공을 무효화하고 이후 서로 다른 세 성공일만 선택되는지 검증한다.
- veto: 의미 변경 없음, Source 비정상, 열린 Critical, 미해결 SourceConflict가 승격을 막는지 검증한다.
- 통합: 키 없는 fixture 자격 실행 3회가 다섯 기관을 독립적으로 승격하고 증거를 보존하는지 검증한다.
- 회귀: 전체 Django 테스트, migration 일치, `git diff --check`를 확인한다.

## 완료 기준

- 자격 실행 외 경로가 승격 성공일이나 PromotionEvidence를 만들지 않는다.
- QualificationRun의 서로 다른 서울 날짜·마지막 실패 이후 연속성과 의미 변경 근거를 DB에서 역추적할 수 있다.
- 모든 veto를 통과한 기관만 `ACTIVE`가 되고 PromotionEvidence 없는 자동 승격은 0건이다.
- 실패·차단 시 마지막 정상 정본과 과거 감사 근거가 보존된다.

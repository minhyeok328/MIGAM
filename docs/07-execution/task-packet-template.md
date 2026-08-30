---
title: "미감 작업 패킷 템플릿"
status: DRAFT
version: "0.2.0"
last_updated: "2026-08-30"
authoritative_for:
  - "P0 구현 작업의 최소 명세 형식"
  - "작업별 범위·검증·의존성 기록 기준"
related_documents:
  - "../00-governance/decision-register.md"
  - "../01-product/project-brief.md"
  - "implementation-readiness.md"
  - "../05-engineering/system-architecture.md"
  - "../05-engineering/security-privacy.md"
  - "../05-engineering/api-guidelines.md"
---

# 미감 작업 패킷 템플릿

이 템플릿은 승인된 P0 작업을 구현 가능한 작은 단위로 기록하기 위한 형식이다. 작업 순서·일정·브랜치 전략은 이 문서에서 정하지 않으며 OD-007을 따른다.

```markdown
## 작업명

### 목적

- 지원하는 P0 사용자 과업:
- 제품·엔지니어링 근거 문서:

### 범위

- 포함:
- 포함하지 않음:
- 변경 예상 영역/파일:

### 계약과 데이터

- 관련 도메인: catalog / discovery / sources / data_quality / 해당 없음
- 코드 소유 경계: frontend / backend/apps / backend/data_pipeline / 해당 없음
- OpenAPI 또는 UI 계약 영향:
- 복합 UI primitive 전략: Radix 직접 / Radix 기반 shadcn/ui / 해당 없음
- Lucide 아이콘과 텍스트 상태·접근성 이름:
- 출처·확인 시점·권리·불확실성 표현:
- 전시 최소 품질 핵심 항목의 항목별 검증·격리:
- 요금·예약·예상 관람시간·접근성·감각 `UNKNOWN`과 추론 금지:
- 필수 조건(날짜·지역·예산·접근성·감각 안전) 영향:
- 예약·예상 관람시간의 required/preferred 모드와 `UNKNOWN` 처리:
- 운영자 경계와 Admin 레코드 연결: /admin/ / /admin/data-status/ / 해당 없음

### 개인정보·보안

- 브라우저 저장 영향과 버전/초기화:
- 서버 전송 데이터:
- 장기 보존하지 않을 값: 추천 payload / 원문 검색어 / 정확 좌표 / 해당 없음
- 계정·서버 프로필·외부 분석 없음 확인:
- 개발 이벤트 계약: 이벤트 이름·허용 속성 / 외부 전송·영속 0 / 운영 빌드 no-op / 해당 없음

### 외부 의존성과 안전한 저하

- MapProvider / SearchService / 출처 / 기타:
- 신규 출처 후보라면 최근 공식 전시 5건 사전 검토 근거:
- 표본별 `CORE_PASS`, 4/5 판정과 `PASS`·`HOLD` 심사 결과:
- 같은 필수 필드의 반복적·구조적 누락 검토:
- 정책·라이선스·robots·인증·CAPTCHA·호출 제한 검토:
- 현재·목표 lifecycle과 허용 전이: `CANDIDATE` / `PROVISIONAL` / `ACTIVE` / `SUSPENDED`
- 현재·목표 health, `ACTIVE` 연속 최종 실패 수와 우선 재검증: `HEALTHY` / `DEGRADED`
- `PROVISIONAL`·`ACTIVE`의 동일한 레코드 품질·권리·최신성·충돌 게이트와 정상 서비스 경로:
- `promotion_validation_started_at + 14일` 경과와 `InstitutionQualificationRun.finished_at`의 `Asia/Seoul` 기준 서로 다른 날짜 3회 연속 최종 `SUCCESS`·중간 `FAILED`:
- 요청 재시도와 최종 성공, 핵심 대상 페이지 최종 미수집·핵심 미완성 commit 실패, 선택 대상 저하·단건 격리 판정:
- 의미 있는 신규·변경 allowlist와 raw hash·페이지 외피 denylist:
- `SourceRecord → P0 승인 정규화 규칙과 버전 → Canonical Exhibition → ChangeHistory` 승격 근거:
- 마지막 실행 성공·Source 정상·구조적 누락·정책/접근 문제·미해결 구조 충돌 0건:
- `ACTIVE` 첫 최종 `FAILED`·중간 `SUCCESS`·서로 다른 실행 2회 연속 최종 `FAILED` 판정과 counter 변경:
- `POLICY_BLOCK` / `ACCESS_BLOCK` / `STRUCTURAL_CRITICAL` 즉시 중단 근거, 실행 중·실행 밖 결과 차이, `ENTRY` / `SOURCE` scope와 범위 확대 증거:
- `PROVISIONAL` 일반 실패의 health·QualificationRun·counter 0, 미해결 Critical 수집 전 차단과 승격 증거 초기화:
- `STRUCTURAL_OPTIONAL`의 `UNKNOWN + DEGRADED`, `RECORD_EXCEPTION` 단건 격리와 반복 패턴 재분류:
- `ACTIVE → SUSPENDED → PROVISIONAL` 사유·수정·재승인, 연속 실패 수 0, 새 검증 시작 시각과 검증 증거 초기화(필수):
- 키 없는 데모·테스트 대체 경로:
- 외부 실패·데이터 누락 시 사용자 표시:

### 검증 증거

- 자동 테스트:
- API/OpenAPI·Zod 경계 확인:
- 접근성 또는 수동 시나리오:
- 실행 명령과 결과:

### 의존성·결정

- 선행 작업:
- 적용 OD: OD-001 / OD-002 / OD-003 / OD-004 / OD-005 / OD-006 / OD-007 / 해당 없음
- 미해결 사항과 처리: 해당 OD를 참조한다.

### 완료 기준

- 사용자가 확인할 수 있는 결과:
- 제외 범위가 유지되었는지:
- 소유 문서 갱신 여부:
```

## 작성 규칙

- 각 패킷은 하나의 검증 가능한 결과를 목표로 하며, 구현 계획 전체를 복제하지 않는다.
- 확정되지 않은 결정은 일반적인 미결정 표기로 남기지 말고 OD-001~OD-007 중 해당 항목을 적는다.
- 데이터·검색·추천·지도·UI 변경은 최소 품질 핵심 항목, 기관 4/5·예외 보류, lifecycle·승격 증거·`PROVISIONAL` 서비스 적격성, 선택 정보 `UNKNOWN`, 필수 조건, 출처·권리·최신성, 개인정보 영향 중 해당 항목을 반드시 기록한다.
- 백엔드 작업은 `backend/apps/`와 `backend/data_pipeline/` 중 소유 위치를, 복합 UI 작업은 Radix 직접 사용과 Radix 기반 shadcn/ui 중 한 전략을 기록한다.
- 테스트는 외부 API 키 없이 실행 가능한 경로를 포함한다.
- 패킷 완료 전에 변경한 영역의 소유 문서를 먼저 갱신하고, 사용자 또는 다른 작업의 변경을 덮어쓰지 않는다.

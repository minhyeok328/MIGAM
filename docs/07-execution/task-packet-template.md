---
title: "미감 작업 패킷 템플릿"
status: DRAFT
version: "0.2.1"
last_updated: "2026-09-05"
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

이 템플릿은 승인된 P0 작업의 범위와 검증을 기록한다. 현재 브랜치·위임·변경 보존 규칙은 [AGENTS.md](../../AGENTS.md)를 우선하며, 별도 합의가 필요한 일정·리뷰 범위는 OD-007에 연결한다. 적용하지 않는 항목은 생략하거나 `해당 없음`으로 표시한다.

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
- 외부 정책·권리·호출 제한과 검토 근거:
- 해당 영역의 추가 확인 사항과 소유 문서 링크:
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

추가 확인 사항은 해당 작업에서만 아래 소유 문서의 조건과 증거를 기록한다. 공통 템플릿에 전체 도메인 규칙을 복제하지 않는다.

| 변경 영역 | 추가로 기록할 내용 | 기준 문서 |
| --- | --- | --- |
| 출처 온보딩 | 5건 표본·4/5 CORE_PASS·구조/정책 HOLD·허용 필드와 권리 | [출처 자격 심사](../02-data/source-qualification.md), [출처 정책](../02-data/data-source-policy.md) |
| 기관 운영·승격 | lifecycle·health·Critical scope·실패/복구·14일/3일자 성공·의미 변경 chain과 veto | [구현 준비도](implementation-readiness.md), [도메인 규칙](../01-product/domain-rules.md) |
| 수집·정규화 | 최소 품질·격리·UNKNOWN·정본 반영과 변경 이력 | [데이터 파이프라인](../02-data/data-pipeline.md), [정규화 규칙](../02-data/normalization-rules.md) |
| 검색·추천 API | 필수/선호·UNKNOWN·조건 보존·OpenAPI와 Zod 영향 | [추천 명세](../03-recommendation/recommendation-spec.md), [API 지침](../05-engineering/api-guidelines.md) |
| UI·운영 화면 | primitive·포커스·반응형·권리 대체·staff 접근 경계 | [UI 지침](../04-ux/ui-guidelines.md), [보안·개인정보](../05-engineering/security-privacy.md) |

- 각 패킷은 하나의 검증 가능한 결과를 목표로 하며, 구현 계획 전체를 복제하지 않는다.
- 확정되지 않은 결정은 일반적인 미결정 표기로 남기지 말고 OD-001~OD-007 중 해당 항목을 적는다.
- 데이터·검색·추천·지도·UI 변경은 최소 품질 핵심 항목, 기관 4/5·예외 보류, lifecycle·승격 증거·`PROVISIONAL` 서비스 적격성, 선택 정보 `UNKNOWN`, 필수 조건, 출처·권리·최신성, 개인정보 영향 중 해당 항목을 반드시 기록한다.
- 백엔드 작업은 `backend/apps/`와 `backend/data_pipeline/` 중 소유 위치를, 복합 UI 작업은 Radix 직접 사용과 Radix 기반 shadcn/ui 중 한 전략을 기록한다.
- 테스트는 외부 API 키 없이 실행 가능한 경로를 포함한다.
- 패킷 완료 전에 변경한 영역의 소유 문서를 먼저 갱신하고, 사용자 또는 다른 작업의 변경을 덮어쓰지 않는다.

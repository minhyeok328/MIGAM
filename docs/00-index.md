---
title: "미감 문서 인덱스"
status: DRAFT
version: "0.5.7"
last_updated: "2026-09-04"
authoritative_for:
  - "프로젝트 문서 목록과 읽기 순서"
  - "문서별 권한·상태·열린 결정 현황"
related_documents:
  - "./00-governance/document-policy.md"
  - "./00-governance/decision-register.md"
---

# 미감 문서 인덱스

## 1. 현재 문서 세트

문서별 상태와 버전은 front matter에 기록한다. Project Brief, Domain Rules, Source Qualification, Source Registry와 범위가 닫힌 `TP-001`~`TP-006`은 `APPROVED`이며, P0 PRD를 포함한 나머지 포괄 문서는 계속 `DRAFT`다. `APPROVED` 문서와 제품 책임자의 최신 승인 결정만 해당 권위 범위의 구현 기준이 될 수 있고, 실제 구현에는 범위를 직접 정의·검증하는 승인 작업 패킷이 필요하다.

| 영역 | 문서 | 권위 범위 | 상태 |
| --- | --- | --- | --- |
| 거버넌스 | [문서 관리 정책](00-governance/document-policy.md) | 상태·버전·권한·충돌·변경 규칙 | `DRAFT` |
| 거버넌스 | [결정 등록부](00-governance/decision-register.md) | 현재·폐기·열린 결정 추적 | `DRAFT` |
| 제품 | [Project Brief](01-product/project-brief.md) | 제품 정체성·사용자·단계 범위·비범위·성공 정의 | `APPROVED 1.0.1` |
| 제품 | [P0 PRD](01-product/prd-p0.md) | P0 사용자 기능·예외·요구사항 ID | `DRAFT` |
| 제품 | [Roadmap](01-product/roadmap.md) | P0 이후 후보 범위와 진입 조건 | `DRAFT` |
| 도메인 | [Domain Rules](01-product/domain-rules.md) | 용어·분류·상태·판정 불변식 | `APPROVED 1.0.1` |
| 데이터 | [Data Source Policy](02-data/data-source-policy.md) | 허용 출처·출처 우선순위·미디어 권리 | `DRAFT` |
| 데이터 | [Source Qualification](02-data/source-qualification.md) | OD-003 후보 기관 표본·출처 접근·권리 심사 증거 | `APPROVED` |
| 데이터 | [Source Registry](../sources.yaml) | 승인 Source 3개와 `PROVISIONAL` 기관 5곳의 실행 설정 | `APPROVED` |
| 데이터 | [Data Model](02-data/data-model.md) | 논리 엔티티·관계·제약·상태축 | `DRAFT` |
| 데이터 | [Data Pipeline](02-data/data-pipeline.md) | 수집·검증·병합·갱신 흐름 | `DRAFT` |
| 데이터 | [Normalization Rules](02-data/normalization-rules.md) | 원본에서 canonical 값으로의 변환 규칙 | `DRAFT` |
| 추천 | [Recommendation Spec](03-recommendation/recommendation-spec.md) | 후보·신호·필터·다양성·탐색·이유 | `DRAFT` |
| 추천 | [Recommendation Evaluation](03-recommendation/recommendation-evaluation.md) | 추천 평가셋·시나리오·통과 게이트 | `DRAFT` |
| UX | [User Flows](04-ux/user-flows.md) | 화면 간 사용자 흐름과 분기 | `DRAFT` |
| UX | [Screen Spec](04-ux/screen-spec.md) | 화면별 정보·행동·상태·반응형 요구 | `DRAFT` |
| UX | [UI Guidelines](04-ux/ui-guidelines.md) | 브랜드·시각 언어·공통 문구·접근성 표현 | `DRAFT` |
| UX | [Design Reference](04-ux/design-reference.md) | 화면·컴포넌트·상태·반응형의 검토용 시각 표본 | `DRAFT` |
| 기술 | [System Architecture](05-engineering/system-architecture.md) | 런타임·저장소·컴포넌트 경계 | `DRAFT` |
| 기술 | [Security & Privacy](05-engineering/security-privacy.md) | 개인정보·인증·로그·비밀값 원칙 | `DRAFT` |
| 기술 | [API Guidelines](05-engineering/api-guidelines.md) | 내부 API와 OpenAPI 계약 원칙 | `DRAFT` |
| 기술 계약 | [Internal OpenAPI v1](../openapi/internal-v1.yaml) | 전시·기관 검색과 조건 보존 추천 요청·응답·오류의 기계 계약 | `1.1.1` |
| 품질 | [Acceptance Criteria](06-quality/acceptance-criteria.md) | 요구사항별 관찰 가능한 합격 조건 | `DRAFT` |
| 품질 | [Test Plan](06-quality/test-plan.md) | 테스트 계층·환경·fixture·검증 범위 | `DRAFT` |
| 품질 | [Traceability Matrix](06-quality/traceability-matrix.md) | 요구사항·화면·API·테스트 연결 | `DRAFT` |
| 실행 | [Implementation Readiness](07-execution/implementation-readiness.md) | 구현 착수 게이트와 미결정 의존성 | `DRAFT` |
| 실행 | [Task Packet Template](07-execution/task-packet-template.md) | 작업 단위 명세 형식 | `DRAFT` |
| 실행 | [TP-001 기관 운영 상태와 수집 전 게이트](07-execution/task-packets/TP-001-institution-collection-gate.md) | Source·기관 상태 부트스트랩, 수집 전 게이트, 기관별 기본 실행 결과 | `APPROVED 1.0.3` |
| 실행 | [TP-002 기관 ACTIVE 승격 증거와 자동 전이](07-execution/task-packets/TP-002-institution-active-promotion.md) | 자격 실행, ChangeHistory, 14일·3일자 성공과 PromotionEvidence | `APPROVED 1.0.2` |
| 실행 | [TP-003 선택 관람 정보와 미디어 권리 모델](07-execution/task-packets/TP-003-visit-information-and-media-rights.md) | 선택 정보 UNKNOWN 정본, MediaAsset·MediaRights 이력과 안전한 노출 판정 | `APPROVED 1.0.1` |
| 실행 | [TP-004 내부 OpenAPI와 FTS5 검색](07-execution/task-packets/TP-004-internal-search-openapi.md) | 전시·기관 내부 검색 API, SearchDocument·SearchService·SQLite FTS5 | `APPROVED 1.0.1` |
| 실행 | [TP-005 조건 보존 설명형 추천](07-execution/task-packets/TP-005-explainable-recommendation.md) | ContentFeatureSnapshot, 하드 조건·UNKNOWN·점수·다양성·이유와 내부 추천 API | `APPROVED 1.0.1` |
| 실행 | [TP-006 프론트엔드 홈과 검색·추천 분리](07-execution/task-packets/TP-006-frontend-discovery.md) | API 없는 몰입형 홈 `/`, 검색·추천 `/discover`, 생성 타입·Zod, 조건 보존·권리 경계와 격리 데모 | `APPROVED 2.0.1` |
| 저장소 | [AGENTS.md](../AGENTS.md) | 저장소 작업·검증 규칙 | `APPROVED 1.1.0` |
| 저장소 | [README.md](../README.md) | 프로젝트 소개와 임시 UI/UX 안내 | 현재 상태 안내 |
| 저장소 | [Frontend README](../frontend/README.md) | 키 없는 데모·로컬 실행과 프론트 검증 명령 | 현재 실행 안내 |

## 2. 권장 읽기 순서

### 제품 방향을 검토할 때

1. Project Brief
2. P0 PRD
3. Domain Rules
4. Decision Register

### 데이터·추천을 설계할 때

1. Domain Rules
2. Data Source Policy
3. Source Qualification
4. Data Model
5. Normalization Rules
6. Data Pipeline
7. Recommendation Spec
8. Recommendation Evaluation

### 화면을 설계할 때

1. P0 PRD
2. Domain Rules
3. User Flows
4. Screen Spec
5. UI Guidelines
6. Design Reference

### 구현 준비를 검토할 때

1. System Architecture
2. Security & Privacy
3. API Guidelines
4. Acceptance Criteria
5. Test Plan
6. Traceability Matrix
7. Implementation Readiness
8. Task Packet Template
9. AGENTS.md

## 3. 문서 권한 흐름

```text
Project Brief
  → P0 PRD
    → Domain / Data Source Rules
      → Data / Recommendation Specifications
        → UX / Engineering Specifications
          → Acceptance / Test / Traceability
            → Implementation Readiness / Task Packets
```

하위 문서는 상위 문서의 결정을 구체화할 수 있지만 제품 범위나 비범위를 다시 정의할 수 없다. 충돌 시 [문서 관리 정책](00-governance/document-policy.md)에 따라 상위 문서와 결정 등록부를 먼저 갱신한다.

## 4. 열린 결정 현황

현재 열린 결정은 6개다.

| ID | 요약 | 승인 차단 범위 |
| --- | --- | --- |
| OD-001 | 공개·비영리·상업 이용 목적 | 출처·권리·공개 운영 |
| OD-002 | 저장소 공개와 문서·데모 데이터 재배포 | README·배포 자산 |
| OD-004 | 로고와 최종 폰트 | 최종 시각 시스템 |
| OD-005 | 외부 공개 API 여부 | 인증·할당량·외부 계약 |
| OD-006 | P1 호스팅·비용·관측성 | 공개 배포·운영 |
| OD-007 | 일정·브랜치·리뷰 방식 | 상세 구현계획·작업 배치 |

전체 질문과 영향 문서는 [결정 등록부](00-governance/decision-register.md) 9절을 기준으로 한다.

## 5. 아직 만들지 않는 문서와 파일

다음 산출물은 확정 정보나 승인된 상위 문서가 부족하므로 현재 세트에 포함하지 않는다.

- 상세·비교·staff 상태까지 포함하는 완전한 P0 OpenAPI: 각 후속 범위가 승인될 때 [`internal-v1.yaml`](../openapi/internal-v1.yaml)을 호환 확장
- TP-006 이후의 포괄 구현계획: 다음 범위와 완료 조건이 승인되기 전에 미리 만들지 않음
- 공개 운영 runbook: 로컬 실행은 Frontend README에 기록하며 공개 운영 환경이 결정된 뒤 별도 작성
- 배포·장애 대응 문서: OD-006과 실제 운영 환경 확정 후 작성

비어 있는 문서나 추측으로 채운 계약을 먼저 만들지 않는다.

## 6. 검토 순서

문서 검토는 다음 묶음으로 진행하는 것이 안전하다.

1. 제품·도메인: Project Brief, P0 PRD, Domain Rules
2. 데이터·추천: Data Source, Data Model, Pipeline, Normalization, Recommendation
3. 경험: User Flows, Screen Spec, UI Guidelines, Design Reference
4. 기술·보안: Architecture, Security & Privacy, API Guidelines
5. 품질·실행: Acceptance, Test, Traceability, Implementation Readiness

각 묶음이 승인되면 상태와 버전을 함께 갱신하고, 해당 문서를 참조하는 하위 문서를 다시 검토한다.

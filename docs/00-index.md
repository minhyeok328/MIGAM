---
title: "미감 문서 인덱스"
status: DRAFT
version: "0.5.17"
last_updated: "2026-09-17"
authoritative_for:
  - "프로젝트 문서 목록과 읽기 순서"
  - "문서별 권한·상태·열린 결정 현황"
related_documents:
  - "./00-governance/document-policy.md"
  - "./00-governance/decision-register.md"
---

# 미감 문서 인덱스

## 1. 현재 문서 세트

2026-09-17 사용자 승인으로 미사용 빵찾깅 앱을 미감으로 전환하고 무료 쿼터가 있는 기존 JavaScript 키를 일반 개발 환경에 연결한다. [TP-008](07-execution/task-packets/TP-008-p0-product-completion.md) `APPROVED 1.0.1`에 기록했으며, 키 없는 5180 실행·데모와 공개 배포 범위는 유지한다.

2026-09-07 DEC-119와 [TP-011](07-execution/task-packets/TP-011-exhibition-content.md) `APPROVED 1.0.0`은 현재·예정 전시의 실제 소개·볼거리·관람 안내와 상세 화면 보강을 승인한다. 현재 내부 API는 OpenAPI `1.6.0`이다. 17건 보강과 기존 데이터 보존, 화면 검증은 [TP-011 검증 기록](06-quality/tp-011-verification.md)을 따른다. TP-001~TP-011은 해당 범위에서 승인된 작업 패킷이다.

2026-09-07 최신 DEC-118과 [`TP-010`](07-execution/task-packets/TP-010-local-completion-and-browser-regression.md) `APPROVED 1.0.0`은 공개 배포를 제외한 로컬 프로젝트 마무리를 승인한다. 단일 origin 실제 DB 실행·별도 파일 복구·브라우저 회귀와 CI 설정의 실행 증거와 제한은 [TP-010 검증 기록](06-quality/tp-010-verification.md)을 따른다.

2026-09-07 [`TP-009`](07-execution/task-packets/TP-009-discovery-and-official-guidance.md) `APPROVED 1.0.0`이 초기 출시의 전시 기간 탐색·공식 관람 안내 연결을 승인한다. 전시 둘러보기는 유지하며, 포괄 P0의 방문 조건 자동 판정 범위와 구분한다. 당시 내부 계약은 OpenAPI `1.5.0`이며 후속 TP-011에서 확장했다.

문서별 상태와 버전은 front matter에 기록한다. Project Brief, Domain Rules, Source Qualification, Source Registry, 작품 조회 계약, 홈·탐색 분리 설계, Staff Operations, Local Delivery와 `TP-001`~`TP-011`은 `APPROVED`이며, P0 PRD를 포함한 나머지 포괄 문서는 계속 `DRAFT`다. `APPROVED`는 해당 범위의 구현 권한이며 전체 P0 완료 판정은 아니다. 실제 구현에는 범위를 직접 정의·검증하는 승인 작업 패킷과 제품 책임자의 최신 결정을 함께 적용한다.

2026-09-06 TP-008은 상세·관심·비교·취향·작품 경로, staff 운영과 키 없는 로컬 통합 실행을 진행 중이다. 지도는 사용자의 선택에 따라 외부 카카오맵 링크를 유지한다. 실제 작품 Source는 `HOLD`이며 가상 데모와 분리한다. 최신 완료·미검증 범위는 [구현 준비도](07-execution/implementation-readiness.md)와 [현재 구현 증거](06-quality/traceability-matrix.md#11-현재-구현-증거)를 따른다.

| 영역 | 문서 | 권위 범위 | 상태 |
| --- | --- | --- | --- |
| 거버넌스 | [문서 관리 정책](00-governance/document-policy.md) | 상태·버전·권한·충돌·변경 규칙 | `DRAFT` |
| 거버넌스 | [결정 등록부](00-governance/decision-register.md) | 현재·폐기·열린 결정 추적 | `DRAFT` |
| 제품 | [Project Brief](01-product/project-brief.md) | 제품 정체성·사용자·단계 범위·비범위·성공 정의 | `APPROVED 1.0.3` |
| 제품 | [P0 PRD](01-product/prd-p0.md) | P0 사용자 기능·예외·요구사항 ID | `DRAFT` |
| 제품 | [Roadmap](01-product/roadmap.md) | P0 이후 후보 범위와 진입 조건 | `DRAFT` |
| 도메인 | [Domain Rules](01-product/domain-rules.md) | 용어·분류·상태·판정 불변식 | `APPROVED 1.0.2` |
| 데이터 | [Data Source Policy](02-data/data-source-policy.md) | 허용 출처·출처 우선순위·미디어 권리 | `DRAFT` |
| 데이터 | [Source Qualification](02-data/source-qualification.md) | OD-003 후보 기관 표본·출처 접근·권리 심사 증거 | `APPROVED` |
| 데이터 | [Source Registry](../sources.yaml) | 승인 Source 3개와 `PROVISIONAL` 기관 9곳의 실행 설정 | `APPROVED` |
| 데이터 | [Data Model](02-data/data-model.md) | 논리 엔티티·관계·제약·상태축 | `DRAFT` |
| 데이터 | [작품 조회 계약](02-data/artwork-contract.md) | 작품 정본·목록·상세·근거 관계와 실제 Source 보류·가상 데모 경계 | `APPROVED 1.0.0` |
| 데이터 | [Data Pipeline](02-data/data-pipeline.md) | 수집·검증·병합·갱신 흐름 | `DRAFT` |
| 데이터 | [Normalization Rules](02-data/normalization-rules.md) | 원본에서 canonical 값으로의 변환 규칙 | `DRAFT` |
| 추천 | [Recommendation Spec](03-recommendation/recommendation-spec.md) | 후보·신호·필터·다양성·탐색·이유 | `DRAFT` |
| 추천 | [Recommendation Evaluation](03-recommendation/recommendation-evaluation.md) | 추천 평가셋·시나리오·통과 게이트 | `DRAFT` |
| UX | [User Flows](04-ux/user-flows.md) | 화면 간 사용자 흐름과 분기 | `DRAFT` |
| UX | [Screen Spec](04-ux/screen-spec.md) | 화면별 정보·행동·상태·반응형 요구 | `DRAFT` |
| UX | [홈·탐색 분리 설계](04-ux/home-design.md) | TP-006 홈 구성·미디어·공통 셸과 탐색 분리 | `APPROVED 1.0.6` |
| UX | [UI Guidelines](04-ux/ui-guidelines.md) | 브랜드·시각 언어·공통 문구·접근성 표현 | `DRAFT` |
| UX | [Design Reference](04-ux/design-reference.md) | 화면·컴포넌트·상태·반응형의 검토용 시각 표본 | `DRAFT` |
| 기술 | [System Architecture](05-engineering/system-architecture.md) | 런타임·저장소·컴포넌트 경계 | `DRAFT` |
| 기술 | [Security & Privacy](05-engineering/security-privacy.md) | 개인정보·인증·로그·비밀값 원칙 | `DRAFT` |
| 기술 | [API Guidelines](05-engineering/api-guidelines.md) | 내부 API와 OpenAPI 계약 원칙 | `DRAFT` |
| 기술 계약 | [Internal OpenAPI v1](../openapi/internal-v1.yaml) | 전시·기관·작품 조회, 검토한 전시 콘텐츠, 전시 기간과 공식 방문일을 구분한 추천 | `1.6.0` |
| 기술 | [Staff Operations](05-engineering/staff-operations.md) | staff 인증·권한별 운영 데이터 조회와 Admin 연결 | `APPROVED 1.0.0` |
| 기술 | [Local Delivery](05-engineering/local-delivery.md) | 실제 데이터·가상 데모 단일 origin 실행, 검토 콘텐츠 반영·별도 DB 복구와 브라우저 회귀 | `APPROVED 1.1.1` |
| 품질 | [Acceptance Criteria](06-quality/acceptance-criteria.md) | 요구사항별 관찰 가능한 합격 조건 | `DRAFT` |
| 품질 | [Test Plan](06-quality/test-plan.md) | 테스트 계층·환경·fixture·검증 범위 | `DRAFT` |
| 품질 | [TP-008 검증 기록](06-quality/tp-008-verification.md) | 273개 백엔드·80개 프론트 검사, 브라우저 연결과 실제 데이터 제약·잔여 작업 | `DRAFT 1.0.0` |
| 품질 | [지도 검색 검증](06-quality/map-search-verification.md) | 9개 기관의 공식 장소명·주소, 검색·선택·지도와 주소 fallback 검증 | `DRAFT 1.0.0` |
| 품질 | [TP-009 검증 기록](06-quality/tp-009-verification.md) | 전시 기간·공식 안내 연결의 128개 백엔드·78개 프론트 검사와 실제 브라우저 확인 | `DRAFT 1.0.0` |
| 품질 | [TP-010 검증 기록](06-quality/tp-010-verification.md) | 로컬 실행·실제 복구·23개 브라우저·290개 백엔드·78개 프론트 검사와 환경 제한 | `DRAFT 1.0.0` |
| 품질 | [TP-011 검증 기록](06-quality/tp-011-verification.md) | 실제 전시 17건 보강·기존 데이터 보존·상세 화면과 24개 브라우저 검사 | `DRAFT 1.0.0` |
| 품질 | [Traceability Matrix](06-quality/traceability-matrix.md) | 요구사항·화면·API·테스트 연결 | `DRAFT` |
| 실행 | [Implementation Readiness](07-execution/implementation-readiness.md) | 구현 착수 게이트와 미결정 의존성 | `DRAFT` |
| 실행 | [Task Packet Template](07-execution/task-packet-template.md) | 작업 단위 명세 형식 | `DRAFT` |
| 실행 | [TP-001 기관 운영 상태와 수집 전 게이트](07-execution/task-packets/TP-001-institution-collection-gate.md) | Source·기관 상태 부트스트랩, 수집 전 게이트, 기관별 기본 실행 결과 | `APPROVED 1.0.3` |
| 실행 | [TP-002 기관 ACTIVE 승격 증거와 자동 전이](07-execution/task-packets/TP-002-institution-active-promotion.md) | 자격 실행, ChangeHistory, 14일·3일자 성공과 PromotionEvidence | `APPROVED 1.0.3` |
| 실행 | [TP-003 선택 관람 정보와 미디어 권리 모델](07-execution/task-packets/TP-003-visit-information-and-media-rights.md) | 선택 정보 UNKNOWN 정본, MediaAsset·MediaRights 이력과 안전한 노출 판정 | `APPROVED 1.0.1` |
| 실행 | [TP-004 내부 OpenAPI와 FTS5 검색](07-execution/task-packets/TP-004-internal-search-openapi.md) | 전시·기관 내부 검색 API, SearchDocument·SearchService·SQLite FTS5 | `APPROVED 1.0.1` |
| 실행 | [TP-005 조건 보존 설명형 추천](07-execution/task-packets/TP-005-explainable-recommendation.md) | ContentFeatureSnapshot, 하드 조건·UNKNOWN·점수·다양성·이유와 내부 추천 API | `APPROVED 1.0.1` |
| 실행 | [TP-006 프론트엔드 홈과 검색·추천 분리](07-execution/task-packets/TP-006-frontend-discovery.md) | API 없는 몰입형 홈 `/`, 검색·추천 `/discover`, 생성 타입·Zod, 조건 보존·권리 경계와 격리 데모 | `APPROVED 2.2.2` |
| 실행 | [TP-007 실데이터 연결과 공식 관람 근거](07-execution/task-packets/TP-007-live-data-and-visit-evidence.md) | DB 보존·업그레이드, 실제 재확인 입력, 선택 필드 백필과 공식 운영일 추천 | `APPROVED 1.0.0` |
| 실행 | [TP-008 P0 제품 E2E 완성](07-execution/task-packets/TP-008-p0-product-completion.md) | 데이터 확대·상세·관심·비교·취향·작품·선택 지도 연동·staff·통합 검증 위임 | `APPROVED 1.0.1` |
| 실행 | [TP-009 전시 발견과 공식 관람 안내](07-execution/task-packets/TP-009-discovery-and-official-guidance.md) | 둘러보기 유지·전시 기간 탐색·초기 필터 정리·공식 안내 연결 | `APPROVED 1.0.0` |
| 실행 | [TP-010 로컬 마무리와 브라우저 회귀](07-execution/task-packets/TP-010-local-completion-and-browser-regression.md) | 공개 배포 제외·실제 로컬 실행·별도 DB 복원·격리 브라우저 검사와 CI | `APPROVED 1.0.0` |
| 실행 | [TP-011 실제 전시 콘텐츠](07-execution/task-packets/TP-011-exhibition-content.md) | 공식 소개·볼거리·관람 안내의 불변 검토 자료와 내용 중심 상세 화면 | `APPROVED 1.0.0` |
| 저장소 | [AGENTS.md](../AGENTS.md) | 저장소 작업·검증 규칙 | `APPROVED 1.1.0` |
| 저장소 | [README.md](../README.md) | 프로젝트 소개와 임시 UI/UX 안내 | 현재 상태 안내 |
| 저장소 | [Frontend README](../frontend/README.md) | 키 없는 데모·로컬 실행과 프론트 검증 명령 | 현재 실행 안내 |
| 자산 | [홈 미디어 안내](04-ux/assets/home/README.md) | 사용 중인 미디어, 제작 원본과 이전 시안의 위치·출처 | 자산 기록 |
| 자산 | [폰트 안내](../frontend/public/assets/fonts/README.md) | 마루 부리·SUIT 원본·굵기·라이선스 | 자산 기록 |

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
4. Data Model / 작품 조회 계약
5. Normalization Rules
6. Data Pipeline
7. Recommendation Spec
8. Recommendation Evaluation

### 화면을 설계할 때

1. P0 PRD
2. Domain Rules
3. User Flows
4. Screen Spec
5. 홈·탐색 분리 설계
6. UI Guidelines
7. Design Reference

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
| OD-004 | 워드마크·로고 형식(마루 부리·SUIT 폰트 확정) | 최종 브랜드 자산 |
| OD-005 | 외부 공개 API 여부 | 인증·할당량·외부 계약 |
| OD-006 | P1 호스팅·비용·관측성 | 공개 배포·운영 |
| OD-007 | 일정·브랜치·리뷰 방식 | 상세 구현계획·작업 배치 |

전체 질문과 영향 문서는 [결정 등록부](00-governance/decision-register.md) 9절을 기준으로 한다.

## 5. 아직 만들지 않는 문서와 파일

다음 산출물은 확정 정보나 승인된 상위 문서가 부족하므로 현재 세트에 포함하지 않는다.

- 미승인 작품 Source의 수집·정규화 계약과 외부 공개 API: 작품 조회 계약의 `SOURCE_PENDING` 경계를 유지하며 실제 출처 심사와 OD-005 결정 후 필요한 범위만 확장
- P1 이후의 포괄 구현계획: 다음 범위와 완료 조건이 승인되기 전에 미리 만들지 않음
- 공개 운영 runbook: 로컬 실행과 staff 조회는 Local Delivery·Staff Operations·Frontend README에 기록하며 공개 운영 환경이 결정된 뒤 별도 작성
- 배포·장애 대응 문서: OD-006과 실제 운영 환경 확정 후 작성

비어 있는 문서나 추측으로 채운 계약을 먼저 만들지 않는다.

전시·기관 상세와 작품 조회의 내부 OpenAPI는 이미 포함되어 있다. 관심·비교·취향 보존은 브라우저 상태이며 별도 서버 프로필 API를 만들지 않는다. staff 상태는 Django 세션·모델 권한으로 보호되는 HTML 화면이다.

## 6. 검토 순서

문서 검토는 다음 묶음으로 진행하는 것이 안전하다.

1. 제품·도메인: Project Brief, P0 PRD, Domain Rules
2. 데이터·추천: Data Source, Data Model, Pipeline, Normalization, Recommendation
3. 경험: User Flows, Screen Spec, UI Guidelines, Design Reference
4. 기술·보안: Architecture, Security & Privacy, API Guidelines
5. 품질·실행: Acceptance, Test, Traceability, Implementation Readiness

각 묶음이 승인되면 상태와 버전을 함께 갱신하고, 해당 문서를 참조하는 하위 문서를 다시 검토한다.

---
title: "미감 구현 준비도"
status: DRAFT
version: "0.3.6"
last_updated: "2026-09-05"
authoritative_for:
  - "P0 구현 착수 전 확인 항목"
  - "확정 결정과 미결정 의존성의 구분"
  - "구현 준비도 판단 기준"
related_documents:
  - "../00-governance/decision-register.md"
  - "../01-product/project-brief.md"
  - "../05-engineering/system-architecture.md"
  - "../05-engineering/security-privacy.md"
  - "../05-engineering/api-guidelines.md"
  - "task-packet-template.md"
---

# 미감 구현 준비도

## 현재 판단

P0의 방향·기술 경계·개인정보 금지 조건은 작업 단위로 분해할 준비가 되었다. 그러나 이 문서는 전체 구현 계획이나 일정표가 아니다. 실제 구현 착수는 각 작업 패킷이 관련 제품·엔지니어링 기준과 아래 입구 조건을 충족하는지 확인한 뒤에만 진행한다.

현재 승인된 구현 단위는 [`TP-001 기관 운영 상태와 수집 전 게이트`](task-packets/TP-001-institution-collection-gate.md), [`TP-002 기관 ACTIVE 승격 증거와 자동 전이`](task-packets/TP-002-institution-active-promotion.md), [`TP-003 선택 관람 정보와 미디어 권리 모델`](task-packets/TP-003-visit-information-and-media-rights.md), [`TP-004 내부 OpenAPI와 FTS5 검색`](task-packets/TP-004-internal-search-openapi.md), [`TP-005 조건 보존 설명형 추천`](task-packets/TP-005-explainable-recommendation.md), [`TP-006 프론트엔드 홈과 검색·추천 분리`](task-packets/TP-006-frontend-discovery.md)이다. 여섯 패킷은 Source·기관 운영 상태, 공용 게이트, 기관별 결과·health, 자격 실행의 ChangeHistory·QualificationRun·PromotionEvidence·`PROVISIONAL → ACTIVE` 자동 승격, 선택 정보·권리 정본, 전시·기관 내부 검색과 근거 있는 전시 추천, API 없는 브랜드 홈 `/`와 검색·추천 `/discover`, 키 없는 격리 데모까지 승인한다. 후보 심사 자동화·복구 승인·Admin·작품·작가·운영시간·지도·취향 테스트·상세·비교·관심 저장과 추천 특성의 외부 Source 자동 백필은 포함하지 않는다.

TP-006의 프론트 자동 테스트·빌드·백엔드 회귀·로컬 API 연결과 Chrome 1440px·390px의 홈·검색·필터 확인은 패킷의 날짜별 실행 증거에 기록한다. 실제 모바일 기기·200% 확대·스크린리더·다른 브라우저와 전체 P0 접근성·사용성 검수는 남아 있다. 이는 전체 P0 UX 승인이나 공개 배포 준비 완료를 뜻하지 않는다.

## 확정된 구현 기준

| 영역 | 확정 기준 |
| --- | --- |
| 저장소·실행 | monorepo, 네이티브 개발 우선, Docker 재현성, `backend/` 단일 `uv` 의존성 경계 |
| 웹 | React + TypeScript + Vite, Tailwind CSS, Radix 또는 shadcn/ui 기반 접근성 primitive, Lucide React, TanStack Query, Zustand |
| 서버·데이터 | `backend/apps/`의 Django + DRF, `backend/data_pipeline/`의 Python 처리 계층, SQLite P0 |
| 탐색 경계 | SQLite FTS5 뒤의 SearchService, Kakao 지도용 MapProvider |
| 추천 경계 | 일회성 RecommendationService 요청, 하드 조건 우선, ContentFeatureSnapshot 근거, 비영속 명시 신호와 정성 등급·이유 |
| 계약 | OpenAPI 정본, 생성 TypeScript, 경계 Zod 어댑터 |
| 도메인 | catalog, discovery, sources, data_quality |
| 운영자 | staff 전용 Django Admin CRUD와 읽기 요약·Admin 연결만 제공하는 `/admin/data-status/` |
| 데이터 갱신 | `uv run python manage.py …` 관리 명령, `refresh_due_exhibitions`를 호출하는 배포 스케줄러, 상시 worker·Celery 없음 |
| 전시 최소 품질 | 전시명·시작일·종료일·장소·지역·유효 상태·공식 상세 URL·공식 출처를 각각 확인하고, 요금·예약·예상 관람시간·접근성·감각 미확인은 `UNKNOWN`으로 보존하며 추론하지 않음 |
| 기관 allowlist | 최근 전시 5건 중 4건 이상 `CORE_PASS`, 구조적 반복 누락·정책·접근 제한 시 비율 무관 `HOLD`, lifecycle과 별도 `HEALTHY`·`DEGRADED`; `PROVISIONAL`도 합격 레코드 서비스 가능, `ACTIVE` 승격은 14일·3일자 성공·의미 변경, 운영 중단은 첫 실패 DEGRADED·연속 최종 실패 2회 또는 Critical, `PROVISIONAL` Critical은 해당 scope 수집·승격 차단, 선택 구조는 UNKNOWN·DEGRADED, 단건은 격리 |
| 개인정보 | 계정·서버 익명/장기 취향 프로필·외부 분석 없음, 개발 이벤트는 허용 계약의 비영속 어댑터이고 운영 빌드는 no-op |
| 재현성 | 데모 모드와 테스트는 외부 API 키 없이 실행 |

## 작업 착수 입구 조건

- 작업이 Project Brief의 P0 범위와 명시적 제외 범위에 연결되어 있다.
- 변경 대상, 소유 문서, API·데이터·UI 경계, 검증 방법이 작업 패킷에 적혀 있다.
- 백엔드 작업은 `backend/apps/`와 `backend/data_pipeline/` 중 소유 위치를 명시하고 파이프라인이 정본을 임의로 덮어쓰지 않게 한다.
- 복합 UI 작업은 Radix 직접 사용과 Radix 기반 shadcn/ui 중 사용할 primitive 전략을 기록하고 키보드·포커스 계약을 포함한다.
- 운영자 화면 작업은 staff 차단과 `/admin/data-status/`에서 Django Admin 레코드로 이어지는 경계를 검증한다.
- 개발 이벤트 작업은 이름·속성 allowlist, 외부 전송·영속 0, 운영 빌드 no-op을 검증한다.
- 필수 조건 미완화, 출처·권리·최신성, 계정 없는 경험, 로그 금지 원칙에 미치는 영향을 명시했다.
- 데이터 작업은 최소 품질 핵심 항목의 항목별 합격·격리와 선택 정보 `UNKNOWN` 처리를 명시하고, 사용자 필수 방문 조건의 `UNKNOWN`을 충족으로 처리하지 않는다.
- 출처 온보딩 작업은 5건 표본·`CORE_PASS` 수·예외 보류 근거, 네 lifecycle 상태와 전이, `PROVISIONAL`·`ACTIVE`의 동일한 레코드 서비스 게이트, 14일·`InstitutionQualificationRun.finished_at`의 `Asia/Seoul` 기준 서로 다른 날짜 3회 연속 최종 성공·중간 실패·재시도 판정, 의미 변경의 SourceRecord→승인 정규화 규칙과 버전→Canonical→ChangeHistory와 최종 Source·충돌 상태를 작업 패킷에 포함한다.
- 기관 운영 작업은 InstitutionRunResult의 서로 다른 실행 ID, `ACTIVE` health·연속 실패 수·우선 재검증, 실행 중·실행 밖 Critical 결과 차이, `PROVISIONAL`의 실패·Critical 차단과 승격 증거 초기화, Critical 세 분류와 `ENTRY`·`SOURCE` scope, 선택 구조 `UNKNOWN + DEGRADED`, 단건 격리와 DataEligibility 재계산을 작업 패킷에 포함한다.
- 외부 의존성이 있으면 키 없는 데모·테스트 대체 경로를 정했다.
- 모호한 제품·운영 결정은 임의 추정하지 않고 아래 OD 항목에 연결했다.

## 미결정 의존성

| 결정 | 구현에 미치는 영향 |
| --- | --- |
| OD-001 공개/상업 목적 | 공개 문구, 권리·운영 범위 |
| OD-002 저장소 공개/라이선스·데모 재배포 | 라이선스, fixture·이미지 배포 방식 |
| OD-003 P0 출처 allowlist | `RESOLVED`: 3개 Source·5개 기관, 출처별 허용 필드·호출 제약과 25건 자격 심사 픽스처 |
| OD-004 워드마크·로고 형식 | 폰트는 DEC-101로 확정해 라이선스·로딩·렌더링을 검증하며, 최종 로고 자산의 선택·시각 승인은 별도 |
| OD-005 외부 공개 API | 인증·할당량·공개 계약 여부 |
| OD-006 P1 호스팅·비용·관측성 | 배포, 보존, 운영 관측성 |
| OD-007 구현 일정·리뷰 | 현재 main 작업·위임 한도는 AGENTS.md를 따르며 추가 일정·검토 방식은 별도 합의 |

## 준비도 게이트

| 게이트 | 통과 기준 |
| --- | --- |
| 범위 | P0 사용자 과업을 직접 지원하고 제외 기능을 추가하지 않음 |
| 데이터 | 최소 품질 항목별 검증·격리, 기관 4/5·예외 보류, lifecycle·health·DataEligibility 독립성, `PROVISIONAL` 서비스 적격성과 Critical 수집 전 차단, 승격 증거, `ACTIVE` 첫/두 번째 최종 실패·Critical·선택 구조·단건 격리, CollectionIssue scope, 출처·권리·확인 시점, 선택 정보 `UNKNOWN`과 추론 금지 정의 |
| 개인정보 | 사용자 식별·장기 서버 프로필·금지 로그를 만들지 않음 |
| 계약 | OpenAPI, API 경계 검증, 실패·빈 결과 처리의 영향 확인 |
| 재현성 | 외부 키 없는 데모와 자동 테스트 경로 정의 |
| 검증 | 단위·통합·접근성·수동 확인 중 필요한 증거가 명시됨 |

OD-003의 실제 기관·출처 목록, 허용 필드와 호출 제약은 [`sources.yaml`](../../sources.yaml), 최근 전시 25건의 `5/5·4/5 CORE_PASS` 판정은 [`source-qualification.json`](../../fixtures/source-qualification.json)으로 확정됐다. OD-005는 외부 소비자 대상 API 작업의 선행 결정이다. OD-006과 OD-007은 P1 운영 또는 병합 일정 관련 작업의 선행 결정이다. 그 외 P0 내부 작업은 해당 결정과 충돌하지 않는 범위에서 바로 구현할 수 있다.

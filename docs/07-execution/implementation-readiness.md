---
title: "미감 구현 준비도"
status: DRAFT
version: "0.3.8"
last_updated: "2026-09-06"
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

초기 승인된 구현 단위는 [`TP-001 기관 운영 상태와 수집 전 게이트`](task-packets/TP-001-institution-collection-gate.md), [`TP-002 기관 ACTIVE 승격 증거와 자동 전이`](task-packets/TP-002-institution-active-promotion.md), [`TP-003 선택 관람 정보와 미디어 권리 모델`](task-packets/TP-003-visit-information-and-media-rights.md), [`TP-004 내부 OpenAPI와 FTS5 검색`](task-packets/TP-004-internal-search-openapi.md), [`TP-005 조건 보존 설명형 추천`](task-packets/TP-005-explainable-recommendation.md), [`TP-006 프론트엔드 홈과 검색·추천 분리`](task-packets/TP-006-frontend-discovery.md)이다. 여섯 패킷은 Source·기관 운영 상태, 공용 게이트, 기관별 결과·health, 자격 실행의 ChangeHistory·QualificationRun·PromotionEvidence·`PROVISIONAL → ACTIVE` 자동 승격, 선택 정보·권리 정본, 전시·기관 내부 검색과 근거 있는 전시 추천, API 없는 브랜드 홈 `/`와 검색·추천 `/discover`, 키 없는 격리 데모까지 승인했다. 후보 심사 자동화·복구 승인·Admin·작품·작가·운영시간·지도·취향 테스트·상세·비교·관심 저장과 추천 특성의 외부 Source 자동 백필은 이 여섯 패킷 당시의 제외 범위이며, 현재 범위는 다음 TP-007·TP-008을 함께 읽는다.

TP-006의 프론트 자동 테스트·빌드·백엔드 회귀·로컬 API 연결과 Chrome 1440px·390px의 홈·검색·필터 확인은 패킷의 날짜별 실행 증거에 기록한다. 실제 모바일 기기·200% 확대·스크린리더·다른 브라우저와 전체 P0 접근성·사용성 검수는 남아 있다. 이는 전체 P0 UX 승인이나 공개 배포 준비 완료를 뜻하지 않는다.

2026-09-06 승인된 [`TP-007 실데이터 연결과 공식 관람 근거`](task-packets/TP-007-live-data-and-visit-evidence.md)가 위 여섯 패킷에 추가된다. 기존 DB 백업·업그레이드, 실제 Source 재확인 입력, 제한된 가격·매체·운영일 백필, 휴관·임시 변경·UNKNOWN 판정과 추천 응답의 첫 개관일 표시를 포함한다. 운영일과 Source 자동 백필에 관한 앞 문단의 제외는 TP-007의 명시 범위에서 해제된다. 실제 데이터 확보와 외부 재확인 성공 여부는 패킷 실행 증거를 따른다. 전체 P0 및 공개 서비스 운영 준비는 여전히 미완료다.

2026-09-06 사용자의 E2E 위임으로 [`TP-008`](task-packets/TP-008-p0-product-completion.md)이 상세·관심·비교·취향·작품·지도·staff·재현 검증을 이어서 승인한다. 작품 조회, staff 운영과 로컬 실행의 세부 계약은 각각 [`artwork-contract.md`](../02-data/artwork-contract.md), [`staff-operations.md`](../05-engineering/staff-operations.md), [`local-delivery.md`](../05-engineering/local-delivery.md)의 `APPROVED` 범위를 따른다.

### 2026-09-06 TP-008 진행 상태

| 영역 | 구현·확인한 범위 | 남은 검증·의존성 |
| --- | --- | --- |
| 전시 데이터 | 추가 4개 기관의 표본 20/20 CORE_PASS와 일반 sync를 거쳐 총 9개 기관·758개 전시, 현재 17개·예정 1개 확인 | 공식 가격·운영일의 실제 누락은 UNKNOWN 유지. 기관 ACTIVE 승격이나 전체 관람 정보 확보 완료로 보지 않음 |
| 상세·개인 상태 | 전시·기관 상세 API/UI, 명시적 관심·최근 전시·최대 3개 비교, 텍스트 취향 선택과 추천 연결, 부분·전체 삭제 구현. 브라우저 연결·초기화·390px와 저장 실패 자동 테스트 확인 | 적응형 취향 세부 요구·실제 기기와 보조기술 검수는 남음 |
| 작품 | OpenAPI 1.4.0과 작품 목록·상세·근거 있는 유사 관계, 격리 데모 4개, 프론트 관심·추천 연결 검증 | 실제 Source OA-15321은 권리·안정 ID·공식 상세 URL 문제로 HOLD이며 일반 모드는 SOURCE_PENDING |
| 지도 | 사용자가 외부 카카오맵 장소 검색 링크 유지 선택 | 내장 지도는 비활성. 월렛 연결·과금·키 주입 없이 외부 링크 흐름 검증 |
| staff | 모델별 조회 권한, 읽기 전용 Admin·데이터 상태·근거 레코드 연결 구현 | 실제 운영자 계정 생성·공개 운영 설정은 이 자동 테스트의 완료 범위가 아님 |
| 재현 | 키 없는 5181 단일 origin 데모, 기존 DB 보존과 임시 DB 정리, 빈 사전 연결과 동시 요청 검증. 백엔드 273·프론트 80개, 계약·빌드·핵심 브라우저 흐름 통과 | CI 브라우저 회귀와 Docker 이미지 빌드·컨테이너 기동 미검증 |

최종 명령 결과·브라우저 확인 범위·데이터 커버리지와 다음 순서는 [TP-008 검증 기록](../06-quality/tp-008-verification.md)을 따른다.

위 결과는 해당 시점의 실행 증거다. 실제 모바일 기기, 스크린리더, 200% 확대·다른 브라우저를 포함한 전체 접근성 검수는 완료되지 않았다. 실제 작품 Source 승인과 공개 배포 승인은 별도이며, 전체 P0 완료·공개 서비스 준비 완료로 판정하지 않는다.

## 확정된 구현 기준

| 영역 | 확정 기준 |
| --- | --- |
| 저장소·실행 | monorepo, 네이티브 개발 우선, Docker 재현성, `backend/` 단일 `uv` 의존성 경계 |
| 웹 | React + TypeScript + Vite, Tailwind CSS, Radix 또는 shadcn/ui 기반 접근성 primitive, Lucide React, TanStack Query, Zustand |
| 서버·데이터 | `backend/apps/`의 Django + DRF, `backend/data_pipeline/`의 Python 처리 계층, SQLite P0 |
| 탐색 경계 | SQLite FTS5 뒤의 SearchService. 현 지도 흐름은 외부 카카오맵 링크이며 내장 MapProvider는 비활성 |
| 추천 경계 | 일회성 RecommendationService 요청, 하드 조건 우선, ContentFeatureSnapshot 근거, 비영속 명시 신호와 정성 등급·이유 |
| 계약 | OpenAPI 1.4.0 정본, 생성 TypeScript, 경계 Zod 어댑터. 일반 작품 SOURCE_PENDING·데모 분리 |
| 도메인 | catalog, discovery, sources, data_quality |
| 운영자 | staff·모델 권한으로 보호된 읽기 전용 운영 모델 Admin과 `/admin/data-status/`. 정본 변경은 기존 서비스·명령 경로 사용 |
| 데이터 갱신 | `uv run python manage.py …` 관리 명령, `refresh_due_exhibitions`를 호출하는 배포 스케줄러, 상시 worker·Celery 없음 |
| 전시 최소 품질 | 전시명·시작일·종료일·장소·지역·유효 상태·공식 상세 URL·공식 출처를 각각 확인하고, 요금·예약·예상 관람시간·접근성·감각 미확인은 `UNKNOWN`으로 보존하며 추론하지 않음 |
| 기관 allowlist | 최근 전시 5건 중 4건 이상 `CORE_PASS`, 구조적 반복 누락·정책·접근 제한 시 비율 무관 `HOLD`, lifecycle과 별도 `HEALTHY`·`DEGRADED`; `PROVISIONAL`도 합격 레코드 서비스 가능, `ACTIVE` 승격은 14일·3일자 성공·의미 변경, 운영 중단은 첫 실패 DEGRADED·연속 최종 실패 2회 또는 Critical, `PROVISIONAL` Critical은 해당 scope 수집·승격 차단, 선택 구조는 UNKNOWN·DEGRADED, 단건은 격리 |
| 개인정보 | 계정·서버 익명/장기 취향 프로필·외부 분석 없음, 개발 이벤트는 허용 계약의 비영속 어댑터이고 운영 빌드는 no-op |
| 재현성 | 데모 모드와 테스트는 외부 API 키 없이 실행. 단일 origin 5181은 일회성 DB를 사용하고 기존 DB·운영자 계정과 분리 |

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
| OD-003 P0 출처 allowlist | `RESOLVED`: 3개 Source·9개 기관, 초기 25건과 2026-09-06 확대 20건의 자격 심사 픽스처 |
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

OD-003의 실제 기관·출처 목록, 허용 필드와 호출 제약은 [`sources.yaml`](../../sources.yaml), 초기 전시 25건의 `5/5·4/5 CORE_PASS` 판정은 [`source-qualification.json`](../../fixtures/source-qualification.json), 추가 4개 기관 20건의 판정은 [`source-expansion-2026-09-06.json`](../../fixtures/source-expansion-2026-09-06.json)으로 확정됐다. 이는 작품 Source까지 승인한 것이 아니다. OD-005는 외부 소비자 대상 API 작업의 선행 결정이다. OD-006과 OD-007은 P1 운영 또는 병합 일정 관련 작업의 선행 결정이다. 그 외 P0 내부 작업은 해당 결정과 충돌하지 않는 범위에서 바로 구현할 수 있다.

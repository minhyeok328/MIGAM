---
title: "TP-004 내부 OpenAPI와 FTS5 검색"
status: APPROVED
version: "1.0.0"
last_updated: "2026-09-02"
authoritative_for:
  - "전시·기관 내부 검색 API v1 계약"
  - "SearchService 경계와 SQLite FTS5 구현"
  - "SearchDocument 파생본의 생성·검색 적격성"
related_documents:
  - "../../00-governance/decision-register.md"
  - "../../01-product/prd-p0.md"
  - "../../02-data/data-model.md"
  - "../../05-engineering/api-guidelines.md"
  - "../../05-engineering/system-architecture.md"
  - "../../06-quality/acceptance-criteria.md"
  - "../../06-quality/test-plan.md"
  - "../implementation-readiness.md"
---

# TP-004 내부 OpenAPI와 FTS5 검색

## 목적과 승인 근거

- 지원하는 P0 과업: 계정 없이 현재 정본 전시와 기관을 키워드·상태·지역으로 찾고 후속 추천·프론트엔드가 같은 내부 계약을 사용하게 한다.
- 승인 근거: 2026-09-02 사용자의 로컬 실행, 외부 API 키·`.env` 불필요, 전시·기관 우선 구현 결정과 즉시 진행 지시, `DEC-104`, `DEC-105`, `DEC-107`, `P0-FR-038`, `P0-FR-040`~`P0-FR-046`, `P0-FR-089`.
- 선행 구현: [`TP-001`](TP-001-institution-collection-gate.md)~[`TP-003`](TP-003-visit-information-and-media-rights.md)의 정본·적격성·출처·최신성·권리 모델.

## 범위

### 포함

- `backend/apps/discovery/`에 기술 독립적인 `SearchService` 인터페이스와 P0 `SQLiteFTS5SearchService` 구현을 둔다.
- 정본을 대체하지 않는 `SearchDocument` 파생 모델은 `EXHIBITION | INSTITUTION`, 정본 ID, 검색 제목·보조 제목·검색어, 상태·지역·날짜, 문서 버전을 보존한다.
- Django migration이 SQLite FTS5 외부 콘텐츠 가상 테이블과 insert·update·delete trigger를 만들며 reverse migration에서 안전하게 제거한다.
- 검색 파생본 재구축 서비스와 `rebuild_search_index` 관리 명령을 제공하고, 정상 정본화 성공 트랜잭션에서 파생본도 동기화한다.
- 전시는 `eligibility = VERIFIED`, `freshness != UNVERIFIED`, 공식 SourceRecord 연결이 있을 때만 검색 파생본에 포함한다. `STALE`은 검색 가능하지만 응답에 상태를 그대로 표시한다.
- 기관은 위 조건을 충족하는 전시를 하나 이상 가진 경우에만 검색 파생본에 포함한다.
- 내부 `GET /api/internal/v1/search/`는 `q`, `type = EXHIBITION | INSTITUTION | ALL`, 복수 `lifecycle`, `region_area`, `region_district`, `sort`, `page`, `page_size`를 허용한다.
- `q`가 없을 때 기본 `type`은 `EXHIBITION`, 전시 상태는 `CURRENT | UPCOMING`이다. `q`가 있으면 기본적으로 `CURRENT | UPCOMING | ENDED`를 찾고 `CANCELED`는 명시적 상태 필터에서만 찾는다.
- 정렬은 `RELEVANCE`, `LATEST_START`, `ENDING_SOON`, `UPCOMING_START`만 허용한다. 개인화·추천 점수는 사용하지 않는다.
- 첫 응답과 추가 응답은 기본 24개이며 `page_size` 상한도 24다. 응답은 `total`, `page`, `page_size`, `has_more`와 중복 없는 결과를 제공한다.
- 전시 검색 결과는 핵심 정본값, lifecycle·freshness·eligibility, 마지막 확인 시각, 공식 출처 근거와 권리 게이트를 통과한 미디어 표시 상태를 제공한다. 기관 결과는 정본 이름·지역과 검색 가능한 전시 수를 제공한다.
- OpenAPI 3.1 YAML을 네트워크 계약 정본으로 추가하고 실제 DRF 요청·응답과 열거형·필수값·오류 형식을 계약 테스트로 검증한다.
- 입력 오류는 `INVALID_SEARCH_QUERY` 코드와 한국어 메시지, 필드별 상세를 가진 `400` 응답으로 구분한다. 정상 0건은 `200`과 빈 results다.

### 포함하지 않음

- `Artwork`, `Creator`, 작품·소장품 검색과 독립 작가 탭. 해당 정본 모델이 생긴 후 OpenAPI 호환 확장으로 추가한다.
- 추천 점수·취향 입력·추천 이유와 `RECOMMENDATION` 정렬.
- 가격·예약·접근성·감각 등 TP-003 선택 정보 필터와 필수조건 판정.
- 전시·기관 상세 API, 비교 API, 지도·MapProvider, TypeScript 생성 클라이언트와 Zod 어댑터, React 프론트엔드.
- 외부 공개 API, 사용자 인증·계정·세션 프로필, 검색어 로그·분석.

## 계약과 데이터

- 관련 도메인: `catalog`, `discovery`.
- 코드 소유 경계: 정본은 `backend/apps/catalog/`, 검색 파생본·검색 서비스·내부 API는 `backend/apps/discovery/`, 정본화 성공 뒤 파생본 동기화 호출만 `backend/data_pipeline/`에 둔다.
- URL 버전은 `/api/internal/v1/`에 고정한다. 외부 공개 API로 간주하지 않는다.
- FTS5 SQL, MATCH 표현식, bm25 점수는 `SQLiteFTS5SearchService` 밖으로 노출하지 않는다.
- 검색어는 Unicode 문자·숫자 token의 안전한 prefix MATCH 표현으로 변환하고 SQL 값은 항상 parameter binding 한다. 검색 가능한 token이 없는 비어 있지 않은 입력은 `400`이다.
- 검색 결과 사실은 SearchDocument 스냅샷을 직접 응답하지 않고 정본 Exhibition·Institution에서 다시 읽는다.
- 공식 출처는 ExhibitionSourceLink의 최신 SourceRecord로 추적하며 raw payload는 응답하지 않는다.
- 미디어 URL은 TP-003 `resolve_media_presentation()` 결과만 사용한다. `HIDDEN`·`LINK_ONLY`에서 원본 media URL을 우회 노출하지 않는다.
- 생성 TypeScript와 Zod는 후속 프론트엔드 패킷에서 이 OpenAPI를 입력으로 만들고 수동 복제 타입을 만들지 않는다.

## 개인정보·보안

- 일반 사용자 계정·인증·서버 프로필·쿠키 기반 개인화는 추가하지 않는다.
- 원문 검색어를 DB, 파일, analytics, IngestionRun이나 개발 이벤트에 저장하지 않는다.
- 추천 payload와 정확 좌표를 받거나 보존하지 않는다.
- API는 읽기 전용이며 Source·CollectionIssue·기관 lifecycle·health 같은 staff 운영 정보를 노출하지 않는다.
- 외부 분석·원격 전송·새 네트워크 호출은 없다.

## 외부 의존성과 안전한 저하

- `djangorestframework >= 3.18, < 3.19`만 추가한다. 프로젝트의 Python 3.11+와 Django 5.2 경계 안에서 사용한다.
- DRF 내장 OpenAPI 생성기는 사용하지 않고 정본 YAML과 계약 테스트를 사용한다.
- SQLite FTS5를 사용할 수 없는 DB 연결은 자동 LIKE 검색으로 완화하지 않고 명시적인 검색 백엔드 오류로 실패한다.
- 외부 API 키와 `.env` 없이 migration, 인덱스 재구축, API 테스트가 모두 실행돼야 한다.
- 인덱스가 비어 있으면 정상 0건을 반환하고, 명령으로 정본에서 재구축할 수 있어야 한다.

## 검증 증거

- migration: FTS5 테이블·trigger 생성과 SearchDocument 변경 동기화를 검증한다.
- projection: 검색 적격 전시·기관만 생성하고 제목·기관·장소·지역 변경과 제외 전환을 재구축에 반영하는지 검증한다.
- service: 한국어 prefix 검색, 유형·상태·지역 필터, 네 정렬, 24개 상한, total·has_more·중복 방지와 안전한 특수문자 처리를 검증한다.
- API: 기본 무검색 현재·예정 목록, 키워드 종료 전시 포함, 명시적 취소 검색, 정상 0건, 잘못된 enum·page·page_size·검색어의 `400`을 검증한다.
- response: 정본·출처·최신성, `INLINE | LINK_ONLY | HIDDEN` 미디어 계약과 원본 URL 비노출을 검증한다.
- OpenAPI: YAML 파싱, path·query·enum·response 필수값과 실제 JSON 응답의 계약 일치를 검증한다.
- 회귀: 전체 Django 테스트, migration 일치, `git diff --check`를 확인한다.

## 완료 기준

- 호출자는 SQLite SQL 없이 `SearchService` 계약만 사용한다.
- 검색 가능한 전시·기관과 제외 대상의 경계를 자동 테스트로 재현한다.
- API가 24개 단위·총 결과·중복 없는 페이지와 기계 판별 오류를 OpenAPI대로 반환한다.
- 원문 검색어·운영자 상태·권리 미허용 media URL이 저장 또는 응답되지 않는다.
- 외부 API 키·`.env` 없이 로컬에서 전체 검증을 통과한다.

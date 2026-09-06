---
title: "미감 API 가이드라인"
status: DRAFT
version: "0.2.4"
last_updated: "2026-09-06"
authoritative_for:
  - "P0 내부 API 계약 원칙"
  - "OpenAPI와 생성 클라이언트 경계"
  - "추천·검색 데이터의 안전한 표현"
related_documents:
  - "../01-product/project-brief.md"
  - "system-architecture.md"
  - "security-privacy.md"
---

# 미감 API 가이드라인

## 적용 범위

P0 API는 내부 React 프론트엔드와 향후 P2 챗봇이 같은 제품 원칙으로 소비하는 계약이다. 인터넷에 공개된 개발자 API가 아니며, 외부 공개 API는 OD-005가 승인되기 전까지 설계·배포 범위에 넣지 않는다.

## 계약의 정본

- OpenAPI 명세가 HTTP 계약의 정본이다.
- TypeScript 클라이언트는 OpenAPI에서 생성한다. 수동 복제 타입과 생성 타입의 이중 정본을 만들지 않는다.
- 프론트엔드는 응답을 API 경계의 Zod 어댑터에서 검증·UI 모델로 변환한다. 검증 실패는 안전한 오류 상태로 처리하고 신뢰할 수 없는 데이터를 사실처럼 표시하지 않는다.
- 호환성을 깨는 변경은 새 버전 경로 또는 명시적 전환 계획이 필요하다. 구현 일정은 OD-007에서 결정한다.

## 리소스와 책임

`exhibitions`, `artworks`, `institutions`는 catalog 읽기 리소스이며, discovery는 조건 탐색·추천을 제공한다. 비교는 최대 3개 전시 상세를 읽는 브라우저 기능으로 서버 비교 목록을 저장하지 않는다. sources와 data_quality의 관리 기능은 staff 전용이며 일반 사용자 API에 노출하지 않는다.

API는 표시하는 핵심 사실마다 출처·마지막 확인 시점·불확실성 상태를 표현할 수 있어야 한다. 작품·기관 관계는 실제 전시 출품 또는 개최 사실로 추정하지 않는다.

## 요청 규칙

- 날짜, 지역, 최대 예산, 필수 접근성, 피해야 할 감각 자극은 별도 필드로 전달한다. 예약과 예상 관람시간은 값과 함께 `required` 또는 `preferred` 모드를 명시하고 서버가 누락된 모드를 추정하지 않게 한다.
- 필수 조건은 누락·미확인·불일치를 충족으로 바꾸지 않으며, 서버는 이를 몰래 완화하지 않는다.
- 취향·관심 신호는 클라이언트가 명시적으로 보낸 현재 요청의 입력일 뿐이다. 사용자 ID, 세션 기반 장기 프로필, 암묵적 행동 신호를 계약에 추가하지 않는다.
- 검색은 전시 중심 통합 검색을 지원하되, 원문 검색어를 장기 저장·분석하는 계약을 만들지 않는다.
- 페이지네이션·정렬·필터는 허용 목록과 상한을 명시해 과도한 조회와 모호한 기본값을 피한다.
- `TP-005` 추천은 `POST /api/internal/v1/recommendations/`에 일회성 JSON으로 전달한다. 요청 body를 URL·DB·파일·분석 이벤트·일반 로그에 복제하지 않고, 배열·문자열·결과 개수 상한을 OpenAPI와 서버 serializer에 함께 둔다.

## 응답 규칙

- 현재·예정 추천, 종료 전시 아카이브, 공식 취소 상태와 최신성·선택 정보의 `UNKNOWN`을 명확히 구분한다. 생명주기 `UNKNOWN`인 전시는 최소 품질 불합격이므로 일반 사용자 콘텐츠 응답에 포함하지 않는다.
- 추천 응답에는 실제 계산에 기여한 매체·분위기·경험 특성 기반의 설명 가능한 이유를 포함한다. 점수만으로 이유를 대체하지 않는다.
- 요금·예약·예상 관람시간·접근성·감각 정보는 확인된 값과 명시적 `UNKNOWN`을 구분한다. `UNKNOWN`을 긍정 값으로 바꾸거나 필수 방문 조건 충족으로 응답하지 않는다.
- 일반 사용자용 전시 응답은 전시명·시작일·종료일·장소·지역·유효 상태·전시 단위 공식 상세 URL·공식 출처가 확인된 최소 품질 레코드만 사용한다. 공식 상세 URL과 출처 근거는 서로 다른 계약 필드로 추적할 수 있어야 한다.
- 기관 lifecycle과 health는 사용자 응답의 단독 포함·제외 기준이 아니다. 정상 Source에 연결된 `PROVISIONAL`과 `ACTIVE`의 레코드는 `HEALTHY`·`DEGRADED`와 관계없이 같은 품질·권리·최신성·충돌 게이트로 포함하며, `CANDIDATE`·`SUSPENDED`에서 새로 수집·반영된 데이터는 포함하지 않는다. `SUSPENDED`나 Critical 확인만으로 마지막 정상 정본을 일괄 제외하지 않고 DataEligibility를 다시 계산하되, Critical 근거가 현재 핵심값의 신뢰를 훼손한 영향 레코드는 `EXCLUDED`다. lifecycle·health·연속 실패 수·CollectionIssue와 scope는 staff 전용 sources·data_quality 계약에 두고, 일반 사용자에게는 선택 필드 `UNKNOWN`·이미지 대체·최신성만 노출한다.
- 이미지 URL은 권리 상태가 확인된 경우에만 제공하며, 이미지 부재도 정상 응답으로 취급한다.
- 지도용 데이터는 필요한 화면에 최소화한다. 정확 좌표를 장기 로그에 보내거나 응답 기록으로 축적하지 않는다.
- 추천은 주요 추천과 비안전 선택 정보의 `needs_verification`을 별도 배열로 반환한다. 내부 점수·퍼센트는 반환하지 않고 알고리즘 버전, 정성 등급, 실제 기여 trace와 1~3개 이유만 제공한다.

## TP-008 조회 계약

현재 정본은 [OpenAPI 1.4.0](../../openapi/internal-v1.yaml)이다. 1.3.0에서 내부 전시·기관 상세 GET을 추가했고, 1.4.0은 작품 목록·상세를 호환 확장한다.

| 경로 | 응답 경계 |
| --- | --- |
| `GET /api/internal/v1/exhibitions/{id}/` | 현재 정본 게시 게이트·출처 재판정, 가격·예약·관람시간·접근성·감각의 `CONFIRMED / UNKNOWN / CONFLICT`, 현재 특성과 운영일 근거. 없는 ID와 비공개 ID는 동일한 404 |
| `GET /api/internal/v1/institutions/{id}/` | 기관 정보와 현재→예정→종료→취소 순의 안전한 전시 목록, 페이지당 최대 24개 |
| `GET /api/internal/v1/artworks/` | q 최대 100자, institution_id·media_group·page·page_size 허용. 페이지당 최대 24개, `availability=DEMO / SOURCE_PENDING` |
| `GET /api/internal/v1/artworks/{id}/` | 작품과 최대 6개 유사 작품, 현재 SourceRecord와 일치하는 특성. 숨긴 ID와 없는 ID는 동일한 404 |

작품의 최소 정본과 노출 권한은 [작품 조회 계약](../02-data/artwork-contract.md)을 따른다. 실제 작품 Source는 승인 전이므로 일반 모드는 빈 `SOURCE_PENDING` 목록과 상세 404를 반환한다. 행의 VERIFIED 값만으로 이 게이트를 열지 않는다. 가상 작품 4개는 명시적 데모 설정·가상 Source·DEMO 적격성이 일치하는 격리 DB에서만 노출한다. 미디어 권리가 없으므로 이미지 URL·크레딧은 null이고 media는 HIDDEN이다. 같은 제작자 관계는 동일 Source 안의 공식 제작자 ID로만 판정하며 이름·소장기관으로 국적·문화권·전시 출품을 추론하지 않는다. 공식 출품 관계는 `UNCONFIRMED`와 빈 목록으로 반환한다.

관심·취향·최근 전시는 브라우저에 한정하고 조회 API에 사용자 프로필을 추가하지 않는다. 관심 작품은 추천 시 API로 재확인한 현재 특성만 일회성 `preferred_features`로 연결하며 원문·응답·검색어를 영속 저장하지 않는다. 프론트는 생성 타입과 strict Zod로 검증하고 404를 재시도 가능한 연결 실패와 구분한다.

staff 화면은 [Staff Operations](staff-operations.md)의 별도 Django 세션·CSRF·모델 권한 경계를 따른다. 운영 모델 Admin은 읽기 전용이며 원본 payload·오류 원문을 노출하지 않는다. [5181 로컬 데모](local-delivery.md)는 운영자 계정과 실제 DB를 사용하지 않고 `/admin/`을 차단한다.

## 오류와 안전한 저하

오류는 기계 판별 가능한 코드와 사용자가 이해할 수 있는 한국어 메시지를 제공한다. 입력 오류, 결과 없음, 데이터 최신성·품질 문제, 외부 지도 비가용을 구분한다. 외부 API 키 또는 지도 SDK가 없어도 검색·상세·비교·데모 테스트가 실패해서는 안 된다.

2026-09-06 사용자 결정에 따라 현 지도 흐름은 외부 카카오맵 장소 검색 링크다. 기관명·지역만 링크에 사용하고 사용자 원문 검색어나 정확 좌표를 전달·저장하는 API를 만들지 않는다. 내장 지도 SDK는 비활성으로 유지하며 데모에서는 가상 기관을 실제 지도에 표시하지 않는다.

## 테스트 계약

TP-006에서 도입한 프론트 계약 검증을 TP-008에서도 유지한다. `npm run api:generate`로 OpenAPI 타입을 만들고 `npm run api:check`로 재현성을 검사한다. 생성 타입 기반 openapi-fetch 뒤에서 Zod가 응답·URL·이미지 상태를 검증한 후 UI 모델을 만든다. 브라우저 URL에 입력을 쓰지 않으며 네이티브 개발은 `/api` loopback 프록시, 5181 데모는 단일 origin을 사용한다. 가상 데모도 별도 알고리즘 없이 임시 SQLite의 실제 Django API를 호출한다.

OpenAPI 1.1.1은 관람시간 최소/최대 중 하나 이상을 요구하는 동작을 유지하되 `anyOf` 각 분기에 mode와 숫자 속성·추가 속성 금지를 완전하게 명시한다. required-only 분기가 생성 타입을 `unknown`으로 약화시키지 않도록 타입 검사에서 모드 오타·범위 없는 입력을 거부하는지 확인한다.

명세 검증, 생성 클라이언트, Zod 어댑터, 필수 조건 불변성, 추천 이유-계산 근거 일치를 함께 검증한다. 데모 fixture는 최소 품질 핵심 항목을 하나씩 누락한 전시, 선택 방문 정보의 `UNKNOWN`, 권리 미확인 이미지, 출처 충돌, 종료 전시, 사용자 응답에 포함되는 `PROVISIONAL`·`ACTIVE + DEGRADED` CORE_PASS와 제외되는 불합격·격리·`CANDIDATE`·`SUSPENDED` 신규 데이터 사례를 포함한다. 마지막 정상 정본은 기관 상태만으로 일괄 제외되지 않고 DataEligibility 재계산 결과를 따르는 사례도 둔다. staff 계약은 health·`ACTIVE` 실패 수·우선 재검증·CollectionIssue scope와 수집 전 차단을 검증한다.

## 미결정 연계

P0 출처 allowlist는 OD-003, 외부 공개 API 여부는 OD-005, P1 호스팅·관측성은 OD-006, 구현 일정·브랜치·리뷰는 OD-007을 따른다.

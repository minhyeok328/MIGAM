---
title: "미감 보안과 개인정보 원칙"
status: DRAFT
version: "0.2.0"
last_updated: "2026-08-30"
authoritative_for:
  - "P0 개인정보 최소화와 데이터 보존 경계"
  - "외부 연동과 비밀값 처리 원칙"
  - "보안 검증의 최소 기준"
related_documents:
  - "../00-governance/decision-register.md"
  - "../01-product/project-brief.md"
  - "system-architecture.md"
  - "api-guidelines.md"
---

# 미감 보안과 개인정보 원칙

## 기본 원칙

P0는 계정 없이 완결되어야 한다. 일반 사용자 계정·로그인·서버 익명 프로필·장기 취향 프로필을 만들거나 우회적으로 재구성하지 않는다. 외부 행동 분석 도구를 사용하지 않는다. 보안 설계는 데이터 최소화, 출처와 권리의 정직한 표현, 운영자 권한 분리를 기본으로 한다.

## 데이터 처리 경계

| 데이터 | 처리 위치 | 보존 원칙 |
| --- | --- | --- |
| 취향 테스트·관심 있음 | 브라우저 | 버전 있는 localStorage, 사용자 요청으로 부분·전체 초기화 |
| 추천 요청의 취향·관심 신호 | 요청 처리 중 | 응답 생성에만 사용, 서버 장기 프로필·추천 payload 로그 금지 |
| 조건 검색어 | 요청 처리 중 | 원문 검색어의 장기 로그 금지 |
| 지도 좌표 | 지도 표시·필요한 처리 중 | 정확 좌표의 장기 로그 금지 |
| 전시·기관·작품 및 출처 | 서버 SQLite | 출처·확인 시점·권리·품질 근거와 함께 보존 |
| 기관 lifecycle·health·승격·중단 근거와 운영자 조작 기록 | 서버 | 기관·Source·SourceRecord·Canonical·IngestionRun·InstitutionRunResult·CollectionIssue·ChangeHistory 식별자, 실행 날짜·최종 상태·재시도 수·연속 실패 수·문제 코드와 영향 범위·규칙 버전·상태 전이 근거 등 최소 운영·품질 감사 정보에 한정하고 원문 응답 body·사용자 행동 데이터와 결합 금지 |
| 개발 검증 이벤트 | 개발·테스트 어댑터 | 외부 전송·장기 저장 없음, 아래 허용 속성만 사용 |

서버 로그는 요청 식별·장기 사용자 추적을 위한 수단으로 사용하지 않는다. 오류 분석에 불가피한 로그도 추천 payload, 원문 검색어, 정확 좌표를 제외하고 최소 보존한다. 구체적 보존 기간과 공개 운영 관측성은 OD-006에서 결정한다.

## 브라우저 저장소

- 저장 키에는 스키마 버전을 포함하고, 저장하는 값과 초기화 범위를 UI에서 설명한다.
- 로컬 데이터는 인증 수단이나 사용자 식별자로 취급하지 않는다.
- 민감한 값, API 비밀값, 외부 서비스 토큰을 localStorage에 저장하지 않는다.
- 저장값이 손상되었거나 이전 버전과 호환되지 않으면 기능을 중단하지 않고 안전하게 폐기·초기화한다.

## 개발 검증 이벤트 계약

P0는 외부 Analytics SDK나 전송 대상을 두지 않는다. 다음 이름은 향후 제품 흐름 측정을 일관되게 설계하기 위한 의미 계약이며, P0에서는 개발·자동 테스트 어댑터로만 검증하고 영속 로그·외부 서비스·사용자 프로필에 보내지 않는다.

| 이벤트 | 허용하는 최소 속성 |
| --- | --- |
| `TASTE_TEST_STARTED` | 없음 |
| `TASTE_TEST_COMPLETED` | `answered_count`, `skipped_count` |
| `EXHIBITION_SEARCHED` | `result_count`, `has_date_filter`, `has_region_filter`, `has_taste_profile` |
| `EXHIBITION_VIEWED` | 없음 |
| `EXHIBITION_INTEREST_ADDED` | 없음 |
| `EXHIBITION_INTEREST_REMOVED` | 없음 |
| `ARTWORK_INTEREST_ADDED` | 없음 |
| `INSTITUTION_INTEREST_ADDED` | 없음 |
| `COMPARE_OPENED` | `comparison_count` |
| `MAP_OPENED` | 없음 |
| `OFFICIAL_LINK_CLICKED` | 없음 |
| `LOCAL_DATA_RESET` | 없음 |

- `없음`은 P0 계약에서 추가 payload를 허용하지 않는다는 뜻이다.
- `answered_count`, `skipped_count`, `result_count`는 0 이상의 정수이고 `comparison_count`는 1~3의 정수다. `has_date_filter`, `has_region_filter`, `has_taste_profile`은 boolean만 허용한다.
- 사용자·세션 식별자, 원문 검색어, 정확 좌표, 추천 요청 payload, 전시·작품·기관 식별자를 이벤트에 추가하지 않는다.
- 이벤트 발생은 취향 학습 신호가 아니며 추천 순위를 바꾸지 않는다.
- 개발·테스트 어댑터는 메모리 또는 명시적인 개발 콘솔에서만 계약을 확인한다. HTTP, `fetch`, XHR, beacon, 외부 SDK, 서버 DB, 파일, 쿠키, `localStorage`로 전송하거나 영속하지 않는다.
- 운영 빌드의 이벤트 어댑터는 아무 작업도 하지 않는 no-op이어야 하며, 이벤트 때문에 네트워크 요청이나 저장소 쓰기가 발생해서는 안 된다.
- 공개 운영에서 수집·보존·전송을 도입하려면 OD-006과 개인정보 검토를 먼저 해결하고 이 계약을 별도로 승인해야 한다.

## 인증·권한

- 공개 읽기 기능은 P0 내부 프론트엔드와 향후 P2 챗봇 소비를 위한 내부 계약이다. 외부 공개 API 제공은 OD-005가 승인될 때까지 범위 밖이다.
- Django Admin과 staff 운영 기능은 최소 권한 원칙으로 분리한다. 운영 계정·권한 부여·배포 환경의 자격 증명은 일반 사용자 흐름과 분리한다.
- 관리자 기능은 데이터 품질·출처 검토에 필요한 범위로 제한하며, 사용자 취향을 조회·수집하는 기능을 제공하지 않는다.
- `/admin/data-status/`를 포함한 품질 화면은 Django `is_staff` 또는 `is_superuser`만 접근할 수 있고, 일반 사용자 인증 경로로 재사용하지 않는다. 상태 화면은 읽기 요약과 관련 Django Admin 레코드 연결만 제공하며 별도의 공개 편집 API를 만들지 않는다.

## 비밀값과 외부 연동

- Kakao 지도 키 등 비밀 또는 환경별 값은 소스·테스트 데이터·문서 예시에 기록하지 않는다. 제공 방식과 허용 도메인은 배포 환경에서 제한한다.
- 키가 없을 때 MapProvider는 명시적 비가용 상태를 반환하고, 핵심 발견·비교 흐름은 계속 사용할 수 있어야 한다.
- 일반 동기화는 정상 Source에 연결된 `PROVISIONAL` 또는 `ACTIVE` 중 영향 scope의 미해결 Critical CollectionIssue가 없는 기관만 사용한다. `DEGRADED`만으로 이 경로를 막지 않으며 선택값은 `UNKNOWN`으로 낮춘다. `CANDIDATE`·`SUSPENDED`와 Critical 차단 범위는 신규 수집·정본·파생본 생성에 사용하지 않는다. 사용자 서비스는 별도의 레코드별 품질·권리·최신성·충돌 게이트를 따르며 기관 중단만으로 마지막 정상 정본을 일괄 제외하지 않는다. `POLICY_BLOCK`·`ACCESS_BLOCK`은 추가 자동 요청 전에 중단하고 어떤 상태에서도 약관, robots.txt, 접근 통제, CAPTCHA·로그인과 이미지 권리를 우회하지 않는다.
- 데모 모드와 자동화된 테스트는 외부 API 키·외부 네트워크 없이 동작한다.

## 입력·출력 보호

- API 입력은 서버에서 명시적으로 검증하고, 프론트엔드 Zod 검증은 보조 경계로만 사용한다.
- 검색어·URL·외부 출처 값은 표시 전에 컨텍스트별 이스케이프와 허용 형식을 적용한다.
- 외부 링크는 공식 출처로 확인된 URL만 사용하며, 이미지와 미디어는 권리가 확인된 값만 노출한다.
- 오류 응답은 내부 경로, 비밀값, 원천 데이터 전체를 노출하지 않는다.

## 검증 기준

- 계정·서버 프로필·외부 분석 SDK가 추가되지 않았음을 코드와 의존성에서 확인한다.
- 추천 payload, 원문 검색어, 정확 좌표가 장기 로그·분석 저장소·테스트 고정값에 남지 않는지 확인한다.
- 개발 검증 이벤트가 허용된 이름·타입·속성만 사용하고 네트워크·SDK·서버 DB·브라우저 저장소로 전송·영속되거나 취향 학습에 쓰이지 않는지 확인한다. 운영 빌드에서는 no-op임을 확인한다.
- 키 없는 데모·테스트 실행, `/admin/`과 `/admin/data-status/`의 비운영자 접근 차단, 입력 검증과 오류 비노출을 검증한다.
- 권리·출처·최신성 정보가 빠진 콘텐츠가 사실 또는 이미지로 노출되지 않는지 검증한다.
- 기관 lifecycle 증거가 사용자 행동 로그와 분리되고, `PROVISIONAL`·`ACTIVE`에 동일한 레코드 게이트를 적용하며, `CANDIDATE`·`SUSPENDED`의 신규 운영 데이터가 서비스에 유입되지 않는지 검증한다.
- 14일·`InstitutionQualificationRun.finished_at`의 `Asia/Seoul` 기준 서로 다른 날짜 3회 연속 최종 성공·중간 실패 0·의미 변경 이력·마지막 성공·Source 정상·미해결 구조 충돌 0의 승격 조건을 검증한다. 재시도 후 모든 핵심 대상 페이지를 처리한 최종 성공, 선택 대상 실패와 정상 단건 격리, 핵심 대상 최종 미수집 또는 핵심 미완성값 Canonical 반영으로 InstitutionRunResult가 최종 `FAILED`가 되는 경우를 구분하고, `PROVISIONAL` 실행에서만 InstitutionQualificationRun과 승격 연속성을 갱신한다.
- 첫 최종 실패·중간 성공·두 번째 연속 실패의 health·counter 전이와 Critical 즉시 중단을 검증한다. 실행 중 Critical만 실제 결과를 `FAILED`로 만들고 실행 밖 검토는 가상 실패를 만들지 않아야 한다. 선택 구조 문제에는 `UNKNOWN + DEGRADED`만 적용하고, 단건 격리는 기관 상태에 전파하지 않으며, CollectionIssue의 `ENTRY`·`SOURCE` 범위를 증거 없이 확대하거나 원문 응답·자격 증명·사용자 데이터를 보존하지 않는지 확인한다.

## 미결정 연계

공개·상업 목적은 OD-001, 저장소·라이선스·데모 재배포는 OD-002, P0 출처 allowlist는 OD-003, 외부 공개 API는 OD-005, P1 호스팅·비용·관측성은 OD-006을 따른다.

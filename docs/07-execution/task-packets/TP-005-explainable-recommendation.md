---
title: "TP-005 조건 보존 설명형 추천"
status: APPROVED
version: "1.0.0"
last_updated: "2026-09-02"
authoritative_for:
  - "P0 RecommendationService 후보·필터·점수·다양성·이유 계약"
  - "ContentFeatureSnapshot과 근거 assertion의 물리 모델"
  - "내부 추천 API v1 요청·응답 계약"
related_documents:
  - "../../00-governance/decision-register.md"
  - "../../01-product/domain-rules.md"
  - "../../01-product/prd-p0.md"
  - "../../02-data/data-model.md"
  - "../../03-recommendation/recommendation-spec.md"
  - "../../03-recommendation/recommendation-evaluation.md"
  - "../../05-engineering/api-guidelines.md"
  - "../../05-engineering/security-privacy.md"
  - "../../06-quality/acceptance-criteria.md"
  - "../../06-quality/test-plan.md"
  - "../implementation-readiness.md"
---

# TP-005 조건 보존 설명형 추천

## 목적과 승인 근거

- 지원하는 P0 과업: 계정 없이 현재 요청의 방문 조건과 명시적 취향 신호만 사용해, 실제로 갈 수 있는 현재·예정 전시를 근거와 함께 추천한다.
- 승인 근거: 2026-09-02 사용자의 `선택 정보·권리 → 내부 OpenAPI/검색 → 추천 → 프론트엔드` 순서와 TP-005 즉시 진행 지시, `DEC-043`~`DEC-053`, `DEC-096`, `DEC-107`, `DEC-110`, `DEC-112`, `P0-FR-032`~`P0-FR-037`, `P0-FR-047`~`P0-FR-052`.
- 선행 구현: [`TP-003`](TP-003-visit-information-and-media-rights.md)의 방문 정보·권리 정본과 [`TP-004`](TP-004-internal-search-openapi.md)의 내부 DRF/OpenAPI·정본 presenter 경계.

## 범위

### 포함

- `backend/apps/discovery/`에 기술 독립적인 `RecommendationService` 인터페이스와 P0 ORM 구현을 둔다. 서비스는 요청 검증, 후보 게이트, 하드 조건, 점수, 다양성, 연결된 탐색, 이유 생성을 순서대로 적용한다.
- 추천 후보는 `CURRENT | UPCOMING`, `eligibility = VERIFIED`, `freshness = FRESH | STALE`, 최신 공식 SourceRecord 연결, 미해결 SourceConflict 없음 조건을 모두 만족하는 Exhibition 정본에서만 시작한다.
- 지역은 시·도 전체 또는 시·군·구까지 정확히 비교하고, 날짜를 받은 경우 사용자 하루·기간과 전시 기간이 한 날 이상 겹쳐야 한다. 운영시간·휴관일 모델이 아직 없으므로 이번 판정은 전시 시작일·종료일과 취소 상태까지만 증명하며 특정 날짜의 개관·회차·잔여석을 주장하지 않는다.
- 일반 성인 기본권 최대 예산, 필수 접근성, 회피 감각, 필수 예약 유형, 필수 예상 관람시간을 하드 조건으로 처리한다. 확인된 불일치는 제외하고 `UNKNOWN`·근거 없음·상충값은 충족으로 바꾸지 않는다.
- 접근성 필수조건은 `CONFIRMED_POSITIVE`, 감각 회피는 해당 자극의 `CONFIRMED_NEGATIVE`만 통과한다. 두 안전 조건의 `UNKNOWN`은 별도 후보군으로도 우회하지 않는다.
- 가격·예약·관람시간의 `UNKNOWN`은 해당 값이 필수인 요청에서 주요 추천에 섞지 않는다. 다른 안전 조건과 알려진 조건을 통과한 경우에만 `needs_verification`으로 분리하고 이유 코드를 제공한다.
- 전시 범위 방문 근거는 해당 ExhibitionSourceLink의 최신 SourceRecord에 연결된 값을 우선한다. 그런 값이 없을 때만 기관 범위의 가장 최근 검증값을 사용한다. 같은 우선순위의 현재 값이 서로 다르면 `CONFLICT`로 구분하고 필터에서는 `UNKNOWN`과 같이 충족으로 바꾸지 않는다.
- `ContentFeatureSnapshot`은 Exhibition별 버전 이력을 보존하고 현재 snapshot을 최대 한 건만 허용한다. `ContentFeatureAssertion`은 `MEDIA_GROUP | MEDIA_DETAIL | THEME | MOOD | EXPERIENCE | SPACE_TYPE | EVENT_FORMAT`, 안정적인 특성 코드, `DIRECT | DERIVED`, SourceRecord, 파생 규칙 버전을 특성별로 보존한다.
- 직접 assertion은 공식 SourceRecord를, 파생 assertion은 공식 SourceRecord와 비어 있지 않은 승인 규칙 버전을 요구한다. SourceRecord 기관과 Exhibition 기관이 다르면 snapshot 입력을 거부한다.
- 명시적 `preferred_features`, 관심 전시의 현재 feature snapshot, 관심 기관, 선호 모드 예약·관람시간만 개인화 점수에 기여한다. 조회·검색·비교·지도·클릭·체류·최근 본 입력 필드는 계약에 두지 않는다.
- 콜드 스타트는 현재 관람 가능성, 최신성, 방문정보·특성 완성도와 기관·주요 매체 다양성을 사용한다. `STALE`은 제외하지 않되 동일 조건의 `FRESH`보다 낮게 둔다.
- 결과는 결정론적인 점수와 ID tie-break를 사용하되 내부 점수를 응답하지 않는다. `VERY_CLOSE | GOOD_MATCH | SOME_MATCH | GENERAL | EXPLORATION` 정성 등급만 제공한다.
- 대표 결과 기본 6개에서 후보가 충분하고 명시적 특성이 있을 때, 기존 선호와 한 특성이 겹치면서 다른 특성이 새로운 후보 한 건을 마지막 슬롯의 탐색형으로 선택할 수 있다. 연결 근거가 없으면 탐색형을 억지로 만들지 않는다.
- 다양성 재정렬은 비슷한 점수대에서 같은 기관과 주 매체 반복에 패널티를 주지만 하드 조건을 통과하지 않은 후보를 살리거나 같은 Exhibition을 중복하지 않는다.
- 추천 이유는 실제 양의 기여 trace에서만 만들고 결과마다 1~3개를 반환한다. 개인화 근거가 없으면 공식 최신성·방문조건처럼 실제 일반 점수 근거만 설명하고 개인화된 문구를 쓰지 않는다.
- 내부 `POST /api/internal/v1/recommendations/`와 OpenAPI 3.1 계약을 추가한다. 기본 6개, 최대 24개를 반환하며 정상 0건은 `200`, 입력 오류는 `INVALID_RECOMMENDATION_REQUEST` `400`이다.
- 추천 presenter는 TP-004의 정본·공식 출처·마지막 확인·미디어 권리 판정을 재사용한다. 권리 미허용 원본 URL과 raw SourceRecord payload는 반환하지 않는다.

### 포함하지 않음

- Artwork·Creator 정본, 작품·기관 특성 snapshot, 작품 관심 ID와 작가 기반 추천.
- 취향 테스트 문항·프로필 계산 UI와 브라우저 저장소. 이번 API는 프론트가 명시적으로 보낸 현재 `preferred_features`만 사용한다.
- OperatingSchedule·휴관일·임시 운영 변경, 실시간 회차·잔여석·매진·티켓 구매 가능 판정.
- 동행 구성의 구조화 연령 제한 판정, 경로·거리·현재 위치 좌표, MapProvider.
- 외부 수집기에서 분류 assertion을 자동 생성하는 정규화 규칙과 기존 전체 데이터의 snapshot 백필. 이번 패킷은 근거 있는 기록 경계와 추천 소비 경로를 구현한다.
- 추천 결과·요청·사용자별 점수의 DB 저장, 일반 사용자 계정·세션 프로필·행동 학습·외부 analytics.
- 추천 정렬을 기존 검색 GET 계약에 혼합하는 작업, 상세·비교 API, TypeScript 생성 클라이언트·Zod·React 프론트엔드.

## 요청 계약

- `region`은 선택값이며 `district`를 보내려면 `area`가 있어야 한다.
- `visit_dates`는 선택값이며 `start`와 `end`를 함께 보내고 `start <= end`여야 한다.
- `max_budget_krw`는 0 이상의 정수다. 무료는 0으로 표현한다.
- `required_accessibility`와 `avoided_sensory`는 정본 enum의 중복 없는 목록이다.
- `reservation`은 `mode = REQUIRED | PREFERRED`와 하나 이상의 허용 예약 유형을 가진다. `UNKNOWN`은 허용 유형으로 받을 수 없다.
- `duration`은 `mode = REQUIRED | PREFERRED`, 양의 `minimum_minutes` 또는 `maximum_minutes` 중 하나 이상을 가지며 둘 다 있으면 최소가 최대 이하이어야 한다. 필수 모드는 공식 전시 시간 범위가 요청 범위 안에 완전히 들어올 때만 통과한다.
- `preferred_features`는 중복 없는 `{axis, value}` 목록이며 `value`는 대문자 영숫자와 `_`, `-`, `:`만 사용하는 1~64자 안정 코드다.
- `liked_exhibition_ids`와 `liked_institution_ids`는 양의 정수 목록이고 존재하지 않거나 서비스 부적격인 ID를 오류나 음수 신호로 바꾸지 않는다. 종료된 관심 전시의 검증된 feature는 선호 근거로 사용할 수 있지만 종료 전시 자체는 후보가 아니다.
- `limit` 기본값은 6, 범위는 1~24다. 요청 전체 크기와 각 목록 길이는 serializer 상한으로 제한한다.

## 점수·다양성·이유 계약

- 알고리즘 버전은 `p0-recommendation-1.0.0`이다. 가중치와 등급 경계는 서버 구성 상수이며 OpenAPI의 수치 계약이 아니다.
- 기본 점수는 lifecycle, freshness, 확인된 선택 정보 수, feature 수로 만들고, 명시 선호 feature 일치, 관심 전시 feature 겹침, 관심 기관 일치, preferred 예약·시간 일치만 양의 개인화 기여로 추가한다.
- 누락된 soft feature와 선호 모드의 `UNKNOWN`은 0점 중립이다. 하드 조건과 같은 값이 점수에서 다시 후보 자격을 뒤집지는 않는다.
- 다양성은 선택된 결과의 기관·주 매체 반복 횟수만큼 결정론적 패널티를 적용한다. 원 점수 차이가 큰 후보를 무조건 뒤집지 않도록 패널티는 단일 명시 feature 일치 가중치보다 작게 둔다.
- 이유 trace는 `code`, 선택적 `feature = {axis, value}`, 사용자용 `text`를 가진다. feature 이유는 해당 assertion이 현재 snapshot에 있고 현재 계산에서 양의 점수에 기여한 경우에만 반환한다.
- 탐색 이유는 연결 특성과 새로운 특성을 모두 trace에 보존한다. 단순 무작위·인기도·확인되지 않은 접근성·감각·관람시간은 이유가 될 수 없다.

## 개인정보·보안

- 추천 요청은 처리 트랜잭션 안에서만 사용하고 DB·파일·개발 이벤트·일반 로그에 payload, ID 목록, 특성 목록을 저장하지 않는다.
- 사용자·세션·기기 식별자와 정확 좌표를 요청 계약에 추가하지 않는다.
- 오류 응답은 잘못된 필드만 표시하고 내부 SQL·경로·원천 payload를 포함하지 않는다.
- API는 읽기 전용이며 staff lifecycle·health·CollectionIssue를 반환하지 않는다.

## 외부 의존성과 안전한 저하

- 새 외부 패키지·API 키·`.env`·네트워크 호출은 없다.
- feature snapshot이 없으면 후보를 제외하지 않고 해당 축을 중립으로 둔다. 개인화 이유도 만들지 않는다.
- 후보 부족은 종료·취소·중복·미확인 안전 조건으로 채우지 않고 실제 개수만 반환한다.
- 가격·예약·시간 확인 필요 결과는 주요 추천과 별도 배열이며 접근성·감각 안전 미확인은 포함하지 않는다.

## 검증 증거

- feature model: 현재 snapshot 유일성, 이력 보존, axis/value 검증, 직접·파생 근거, SourceRecord 기관 일치를 검증한다.
- hard filters: lifecycle·eligibility·freshness·공식 출처·충돌, 지역·날짜, 예산, 접근성, 감각, required 예약·시간의 알려진 위반과 `UNKNOWN` 통과 0건을 검증한다.
- verification split: 가격·예약·시간 미확인만 별도 후보로 갈 수 있고 접근성·감각 미확인은 양쪽 모두에서 제외되는지 검증한다.
- scoring: 콜드 스타트, preferred feature, 관심 전시 feature, 관심 기관, preferred 예약·시간, soft `UNKNOWN` 중립과 결정적 결과를 검증한다.
- diversity/exploration: 중복 0, 기관·매체 반복 완화, 연결된 탐색 한 건 이하, 후보 부족 시 억지 채움 없음과 같은 입력의 같은 결과·이유를 검증한다.
- reason: 모든 feature 이유가 현재 assertion과 양의 contribution에 대응하고 1~3개이며 퍼센트·내부 점수가 응답에 없는지 검증한다.
- API/OpenAPI: 정상·0건·400, enum·날짜·범위·목록 상한, exact response shape, 정본 재조회, 공식 출처·권리 안전 미디어를 검증한다.
- privacy: 요청 전후 사용자·추천 결과 영속 모델이 생기지 않고 추천 payload 로그·외부 호출이 없는 구조를 확인한다.
- 회귀: 전체 Django 테스트, migration 일치, Django system check, OpenAPI YAML 파싱과 `git diff --check`를 확인한다.

## 완료 기준

- `RecommendationService`가 하드 조건을 점수보다 먼저 적용하고 필수조건의 `UNKNOWN`을 정상 추천으로 통과시키지 않는다.
- 같은 정본·요청·알고리즘 버전에서 결과 순서·등급·이유가 재현된다.
- 추천 이유가 실제 현재 feature 또는 일반 품질 기여와 일치하고 내부 점수·퍼센트를 노출하지 않는다.
- 공식 출처·권리·최신성·충돌 게이트를 우회하는 추천 결과가 없다.
- 외부 API 키·`.env` 없이 관련 테스트와 전체 회귀 검증을 통과한다.

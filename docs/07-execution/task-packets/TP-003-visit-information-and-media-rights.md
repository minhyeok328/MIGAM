---
title: "TP-003 선택 관람 정보와 미디어 권리 모델"
status: APPROVED
version: "1.0.0"
last_updated: "2026-09-01"
authoritative_for:
  - "요금·예약·예상 관람시간·접근성·감각 정보의 정본 저장 계약"
  - "MediaAsset·MediaRights의 권리 이력과 안전한 이미지 노출 판정"
  - "선택 정보 UNKNOWN과 확인된 부정값의 분리"
related_documents:
  - "../../00-governance/decision-register.md"
  - "../../01-product/domain-rules.md"
  - "../../01-product/prd-p0.md"
  - "../../02-data/data-source-policy.md"
  - "../../02-data/data-model.md"
  - "../../02-data/normalization-rules.md"
  - "../../05-engineering/system-architecture.md"
  - "../../06-quality/acceptance-criteria.md"
  - "../../06-quality/test-plan.md"
  - "../implementation-readiness.md"
---

# TP-003 선택 관람 정보와 미디어 권리 모델

## 목적과 승인 근거

- 지원하는 P0 과업: 전시의 요금·예약·예상 관람시간·접근성·감각 정보를 근거와 함께 비교하고, 권리가 확인된 이미지만 안전하게 표시할 수 있는 정본 기반을 만든다.
- 승인 근거: 2026-09-01 사용자의 `선택 정보·권리 모델 확장 → 내부 OpenAPI/검색 → 추천 → 프론트엔드` 순서 확인과 후속 작업 진행 지시, `DEC-064`, `DEC-065`, `DEC-086`, `DEC-087`, `P0-FR-032`~`P0-FR-036`, `P0-FR-055`~`P0-FR-057`, `P0-FR-089`, `AC-015`, `AC-024`.
- 선행 구현: [`TP-001`](TP-001-institution-collection-gate.md)의 SourceRecord·기관 수집 게이트와 [`TP-002`](TP-002-institution-active-promotion.md)의 Canonical·ChangeHistory 기반.

## 범위

### 포함

- `backend/apps/catalog/`에 `PriceOption`, `ReservationInfo`, `VisitDuration`, `AccessibilityFact`, `SensoryNotice` 정본 모델을 추가한다.
- 각 선택 정보는 Exhibition 또는 Institution 중 정확히 한 대상에 연결하고, 공식 근거인 SourceRecord와 확인 시각을 필수로 보존한다. SourceRecord의 기관 식별자와 대상 기관이 다르면 정본 입력으로 승인하지 않는다.
- 가격은 확인 상태, 대상, 기본권·할인·프로그램 구분, 통화, 최소·최대 금액과 무료 여부를 분리한다. `UNKNOWN`에는 금액·무료·대상·유형을 추론해 넣지 않는다.
- 예약은 `NOT_REQUIRED`, `REQUIRED`, `RECOMMENDED`, `TIMED_ENTRY`, `ON_SITE`, `FIRST_COME`, `PROGRAM_ONLY`, `UNKNOWN`을 그대로 보존하고 잔여석·매진·구매 가능 필드는 만들지 않는다.
- 예상 관람시간은 `OFFICIAL`과 `UNKNOWN`만 허용하고, 공식값은 최소·최대 분 단위 범위로 보존한다.
- 접근성·감각 항목은 `CONFIRMED_POSITIVE`, `CONFIRMED_NEGATIVE`, `UNKNOWN`을 구분한다. 안내 부재를 부정값으로 변환하지 않는다.
- `MediaAsset`은 현재 구현된 Exhibition 또는 Institution 중 정확히 한 대상, 미디어 종류·역할, 원본 위치·공식 원본 페이지와 SourceRecord를 보존한다. 포스터·공간·작품·인물·영상 썸네일은 별도 asset으로 유지한다.
- `MediaRights`는 asset별 권리 판정 이력을 누적하고 현재 판정을 한 건만 유지한다. 판정값은 `REUSE_ALLOWED`, `LINK_ONLY`, `RIGHTS_UNKNOWN`, `UNAVAILABLE_OR_WITHDRAWN`이다.
- 재사용 허용 판정도 표시·복제·캐시·변환·핫링크 허용 범위를 각각 명시한다. `LINK_ONLY`, `RIGHTS_UNKNOWN`, `UNAVAILABLE_OR_WITHDRAWN`은 미디어 URL을 브라우저 이미지 요청에 전달하지 않는다.
- 현재 `REUSE_ALLOWED`이며 이미지 표시와 핫링크가 모두 명시적으로 허용된 경우에만 원본 URL을 인라인 이미지 전달값으로 반환한다. `LINK_ONLY`는 공식 원본 페이지 링크만 반환하고 나머지는 텍스트 대체 상태로 반환한다.
- 모든 DB 제약과 도메인 판정은 외부 API 키 없는 Django 테스트로 검증한다.

### 포함하지 않음

- 운영시간·휴관일·임시 운영 변경의 `OperatingSchedule` 모델과 수집기 매핑.
- 승인 Source의 현재 허용 필드 밖 요금·미디어를 실제 외부 응답에서 새로 수집하거나 `sources.yaml` 범위를 넓히는 작업.
- 바이너리 다운로드·복제·캐시·썸네일 생성·재호스팅과 권리 철회 파생 파일 삭제 작업. 이번 패킷은 메타데이터·권리 이력과 노출 판정만 구현한다.
- Artwork·Creator 정본 모델과 그 대상 FK. 현재는 media role로 작품·인물 이미지를 독립 판정하고, 해당 정본 엔터티가 도입될 때 관계를 확장한다.
- 가격·예약 변경의 수집→정규화→Canonical 병합과 승격용 ChangeHistory 생성. 승인 Source 매핑이 있는 후속 데이터 패킷 전에는 의미 변경으로 만들지 않는다.
- 내부 OpenAPI, SearchService·FTS5, 추천, 프론트엔드, staff Admin과 `/admin/data-status/`.
- P0 `VisualEmbedding` 생성·저장·조회·점수 사용.

## 계약과 데이터

- 관련 도메인: `catalog`, `sources`.
- 코드 소유 경계: 정본 모델과 읽기 판정은 `backend/apps/catalog/`; 수집·정규화 경로는 이번 범위에서 변경하지 않는다.
- OpenAPI 또는 UI 계약 영향: 이번 패킷에서는 API를 노출하지 않는다. 후속 내부 OpenAPI는 이 정본 enum을 번역 없이 사용하고 `UNKNOWN`, 확인된 부정, 링크 전용, 숨김을 별도 상태로 제공해야 한다.
- 선택 정보는 핵심 `CORE_PASS`와 독립이다. 선택 정보가 전부 없거나 `UNKNOWN`이어도 기존 Exhibition의 최소 품질 적격성을 바꾸지 않는다.
- 사용자 필수 방문 조건에서는 모든 선택 정보의 `UNKNOWN`을 충족으로 판단하지 않는다. 이 필터 동작은 추천 패킷에서 구현하되 저장 모델이 부정값과 `UNKNOWN`을 합치지 않게 한다.
- source URL과 공식 링크는 HTTPS만 허용한다.
- TP-003 정본 모델의 일반 `save()`는 전체 도메인 검증을 수행한다. 선택 정보·MediaAsset·MediaRights에 `bulk_create()`나 검증을 우회한 직접 `update()`를 운영 쓰기 경로로 사용하지 않으며, MediaRights 현재 이력 전환은 검증된 `record_media_rights()` 서비스 안에서만 수행한다.
- MediaRights 이력은 덮어쓰지 않는다. 새 현재 판정을 기록할 때 이전 판정은 비현재로 전환하고, 현재 판정이 없거나 미확인·철회이면 인라인 표시를 거부한다.
- 이미 저장된 과거 SourceRecord를 재처리해도 그 권리 행을 다시 현재로 승격하지 않는다. 철회 뒤 재사용을 허용하려면 새 SourceRecord 버전의 새 권리 근거가 필요하다.
- P0에서 실제 음원·전체 영상은 권리 상태와 무관하게 인라인 재생·재호스팅 대상으로 반환하지 않는다.

## 개인정보·보안

- 브라우저 저장, 서버 사용자 프로필, 추천 payload, 원문 검색어, 정확 좌표와 사용자 행동 로그를 추가하지 않는다.
- 계정·익명 프로필·외부 분석·개발 이벤트 변경은 없다.
- 미디어 URL은 권리 판정 전 사용자 응답으로 전달하지 않으며 공개 URL이라는 사실만으로 표시 권한을 만들지 않는다.

## 외부 의존성과 안전한 저하

- 신규 외부 출처·API 키·네트워크 호출은 없다. 테스트는 로컬 SourceRecord와 정본 fixture만 사용한다.
- 선택 정보 누락은 명시적 `UNKNOWN`으로 기록할 수 있지만 기존 확인값을 빈 새 응답으로 덮어쓰지 않는다.
- 이미지 권리가 없거나 현재 권리가 미확인·철회·링크 전용이면 미디어 URL 없이 `HIDDEN` 또는 `LINK_ONLY` 판정을 반환하고 전시 자체는 검색·추천 적격성을 유지한다.
- `STRUCTURAL_OPTIONAL`의 기관 health·재검증 처리는 TP-001 계약을 유지하며, 이 패킷은 lifecycle·health를 새로 변경하지 않는다.

## 검증 증거

- 선택 정보 모델: 대상 XOR, SourceRecord 기관 일치, enum, `UNKNOWN` 값 비움, 금액·시간 범위와 HTTPS 링크 제약을 검증한다.
- 불확실성: 접근성·감각의 `CONFIRMED_NEGATIVE`와 `UNKNOWN`이 다른 값이고, 선택 정보 `UNKNOWN` 생성이 Exhibition의 기존 eligibility를 바꾸지 않는지 검증한다.
- 미디어 권리: asset별 현재 권리 한 건, 권리 이력 보존, 비재사용 상태의 처리 권한 금지, 권리자·라이선스 근거를 검증한다.
- 노출 게이트: `REUSE_ALLOWED + 이미지 표시 허용 + 핫링크 허용`만 인라인 URL을 반환하고 `LINK_ONLY`, `RIGHTS_UNKNOWN`, 철회, 권리 없음, 음원·전체 영상은 반환하지 않는지 검증한다.
- 회귀: 관련 Django 테스트, 전체 Django 테스트, migration 일치와 `git diff --check`를 확인한다.

## 의존성·결정

- OD-001·OD-002가 공개 배포의 최종 권리 범위를 결정하므로 이번 패킷은 외부 배포를 전제하지 않는다.
- OD-003의 승인 Source·허용 필드 범위를 바꾸지 않는다.
- OD-005 외부 공개 API 결정과 무관한 내부 정본 모델이다.
- OD-007 일정·병합 방식은 정하지 않고 현재 `main` 작업 규칙을 따른다.

## 완료 기준

- 다섯 선택 정보 모델이 공식 근거와 함께 `UNKNOWN`·확인된 값·확인된 부정을 손실 없이 저장한다.
- 미디어 asset과 권리 판정 이력을 분리해 보존하고 현재 권리가 하나뿐임을 DB가 보장한다.
- 권리 미확인·링크 전용·철회 미디어 URL이 인라인 전달값으로 노출되는 테스트가 0건이다.
- 이미지가 없어도 Exhibition의 핵심 정본과 최소 품질 적격성은 유지된다.
- OpenAPI·검색·추천·프론트엔드와 실제 외부 선택 정보 수집은 제외 범위로 남는다.

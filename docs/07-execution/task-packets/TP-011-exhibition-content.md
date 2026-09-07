---
title: "실제 전시 소개와 상세 화면 보강"
status: APPROVED
version: "1.0.0"
last_updated: "2026-09-07"
authoritative_for:
  - "공식 전시 페이지를 검토한 소개·볼거리·관람 안내의 저장과 표시"
  - "내용 중심 상세 화면과 미확인 항목의 단일 안내"
related_documents:
  - "../../02-data/data-model.md"
  - "../../02-data/data-source-policy.md"
  - "../../02-data/normalization-rules.md"
  - "../../04-ux/screen-spec.md"
---

# TP-011 실제 전시 소개와 상세 화면 보강

## 승인과 완료 조건

2026-09-07 사용자는 상세의 모든 항목이 ‘공식 안내에서 확인’인 문제를 지적하고 실제 소개·관람 정보를 채우는 방향에 ‘응 실제 전시 내용을 채우는 작업이 필요할 것 같아’라고 승인했다. 현재 검색되는 현재·예정 17건의 공식 상세를 검토하고 확보 가능한 내용을 실제 로컬 DB와 화면에 반영한다. 접근 실패·소개 미게시 등 확보하지 못한 항목은 별도로 기록한다. 배포·커밋·푸시는 포함하지 않는다.

## 데이터와 API 계약

- 기존 allowlist 정본에 연결된 **동일한 전시 공식 상세 URL**만 수동 검토한다. 새 기관 수집기·대량 HTML 크롤링을 추가하지 않는다. 공개 사실을 독자적인 짧은 문장으로 정리하며 원문 장문·이미지를 복제하지 않는다. 접근 제한은 우회하지 않는다.
- `ExhibitionContent`는 전시와 현재 채택된 `SourceRecord`에 연결한 불변 검토 스냅샷이다. `introduction`(최대 2000자), `highlights`(최대 3개, 각 300자), `visit_notes`(중복 없는 `PRICE | HOURS | RESERVATION | AGE | LOCATION` 코드와 각 500자 이내 `text`), `official_url`, `source_owner`, `reviewed_at`, `expires_at`, 정본 식별 fingerprint와 검토 자료 hash를 저장한다. 짧은 사실 메모를 포함한 입력 JSON을 저장소에 보존한다.
- 입력 JSON은 `schema_version: "1.0"`과 `entries`로 구성한다. 각 입력은 현재 정본의 Source 식별자·원본 ID·`source_record_hash`·공식 URL·제목·기간·장소와 대조한다. 미래 확인일·30일 초과 유효기간·잘못된 URL·빈 소개·HTML·미등록 안내 코드를 거부한다. 전체를 검증한 다음 원자적으로 반영하며 동일 입력은 중복 저장하지 않는다. 이전 스냅샷은 보존한다.
- 기존 core 데이터·확인 시각·SourceRecord·수집 health·승격 이력을 변경하지 않는다. 현재 SourceRecord 또는 정본 fingerprint가 바뀌거나 유효기간(검토 후 최대 30일)이 지난 콘텐츠는 API에서 제외한다. 내용이 없어도 기존 상세 조회는 유지한다.
- 상세 API에 nullable `content`를 추가한다. 내용이 있으면 `introduction`, `highlights`, `visit_notes`, `official_url`, `source_owner`, `reviewed_at`, `expires_at`을 반환한다. 원문 메모·내부 hash·fingerprint는 노출하지 않는다. 방문 안내 문구는 설명용이며 가격·예약·운영 일정의 확정값이나 추천 조건으로 승격시키지 않는다.

## 화면 계약

- 상세 전용 구성으로 기관·기간·장소, 소개, 볼거리, 관람 안내를 보여준다. 목록 카드의 중복 제목과 현재 상세로 가는 ‘상세 보기’를 제거한다.
- 확인한 안내 문구와 기존 확정 방문값을 우선 표시한다. 미확인 항목마다 링크를 반복하지 않고 하나의 공식 안내로 묶는다. 접근성·감각은 확인되거나 충돌한 정보만 노출하며 누락을 ‘미제공’으로 표현하지 않는다.
- 공식 페이지와 확인일을 내용 가까이에 표시한다. 가상 데모 표기와 외부 링크 차단, 이미지 권리 정책, 지도 외부 링크 결정을 유지한다.

## 구현 및 검증 계획

1. 백엔드 모델·migration, pipeline 입력 검증/catalog 저장 서비스, management command, 상세 API/OpenAPI. 잘못된 연결·유효기간·원본 교체·중복·실패 원자성 테스트를 먼저 작성한다.
2. 공식 페이지 17건을 검토해 출처·확인 시각·짧은 근거 메모를 포함한 JSON을 작성한다. 기존 DB 백업 후 migration/import하고 기존 ID·핵심값·원본 보존을 확인한다.
3. 생성 TypeScript·Zod와 상세 화면, 빈 콘텐츠·확정 정보·단일 링크·가상 모드 테스트를 맞춘다. 비교의 행 정렬·충돌 처리를 유지한다.
4. 백엔드/프론트 회귀, API 생성 검사·빌드, 실제 상세 데스크톱/390px 브라우저를 검증한다. 확보량과 제한은 검증 기록에 남긴다.

검토 입력은 [2026-09-07 전시 콘텐츠](../../../data/reviewed/exhibition-content-2026-09-07.json), 실행 결과와 남은 항목은 [TP-011 검증 기록](../../06-quality/tp-011-verification.md)을 따른다.

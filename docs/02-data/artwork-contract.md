---
title: "미감 작품 조회 계약"
status: APPROVED
version: "1.0.0"
last_updated: "2026-09-06"
authoritative_for:
  - "TP-008 작품 정본의 최소 메타데이터와 노출 경계"
  - "작품 조회·유사 작품·출품 관계·키 없는 가상 데모"
related_documents:
  - "../07-execution/task-packets/TP-008-p0-product-completion.md"
  - "./data-model.md"
  - "./data-source-policy.md"
  - "../../openapi/internal-v1.yaml"
---

# 작품 조회 계약

## 승인 범위와 실제 데이터 경계

사용자의 P0 E2E 구현 위임과 TP-008에 따라 작품 목록·상세·관심 연결을 위한 내부 조회 계약을 추가한다. 기존 전시 검색·추천 계약을 바꾸지 않는다. 현재 등록된 공식 Source에는 작품 수집 승인이 없다. OA-15321 후보의 6,406건은 공공누리 제4유형·제3자 권리, 안정적인 공식 작품 ID와 작품 단위 공식 상세 URL 부재로 HOLD 상태이며 실제 정본에 적재하지 않는다.

이번 구현의 일반 모드 목록은 `availability=SOURCE_PENDING`과 빈 결과를 반환하며 상세는 404다. 데이터베이스에 수동으로 VERIFIED를 써 넣더라도 일반 노출을 허용하지 않는다. 후속 공식 작품 Source 심사, 수집·정규화·정본 승인 경로, 권리와 최신성 게이트가 승인·구현되어야 일반 노출을 열 수 있다. 작품 수를 늘리기 위해 가상 작품이나 출처 불명 레코드를 실제 데이터에 섞지 않는다.

`MIGAM_DEMO_MODE`가 명시적으로 켜진 격리 DB에만 가상 작품 4개를 만든다. 제목·작가·소장기관에 가상임을 표시하고 source와 공식 링크는 `fictional-demo-only` 및 example.com의 가상 경로를 사용한다. 이는 실제 기관·작품의 공식 정보가 아니다. 데모 표시, `is_demo=true`, `eligibility=DEMO`, 가상 SourceRecord의 증거가 모두 일치할 때만 데모 API로 노출한다. 데모 설정을 끄면 같은 행의 목록·상세·유사 작품도 즉시 숨긴다. 기존 DB에는 seed를 실행하지 않는다.

## 최소 정본과 근거

Artwork는 Source 단위 공식 작품 ID, 제목, 제작자 표시와 공식 제작자 ID(없으면 null), 제작자 `KNOWN | UNKNOWN`, 제작연도 원문 표현, 매체 원문, 소장기관, 현재 SourceRecord, HTTPS 작품 상세 URL, 마지막 검증 시각, `UNVERIFIED | VERIFIED | EXCLUDED | DEMO`, 가상 여부를 보존한다. 신규 행의 기본 적격성은 UNVERIFIED다. 공식 작자 미상은 UNKNOWN과 명시적 표시로 보존하며 빈 값·누락과 구분한다. 문화권은 `CONFIRMED | UNKNOWN`, 공식 표현과 한국 작품 여부(boolean 또는 null)를 분리한다. 이름·소장기관·문자열만 보고 한국 작품 여부를 추론하지 않는다.

SourceRecord의 기관과 소장기관이 일치해야 하며 작품 ID는 같은 Source 안에서 고유하다. 원본 payload를 API로 반환하지 않는다. 실제 정본 갱신은 수집 승인 후 별도 파이프라인에서 다뤄야 하며 API는 GET 전용이다. API 요청·검색어·관심을 서버 모델로 저장하지 않는다.

작품 특성은 현재 작품 SourceRecord와 일치하는 서버 검증 assertion만 반환한다. 이번 범위는 기존 MEDIA_GROUP·MOOD의 승인 코드와 DIRECT 근거에 한정한다. 제목에서 분위기를 추정하거나 클라이언트가 전송한 값을 작품 사실로 저장하지 않는다. 데모 특성의 근거 역시 가상임을 표시한 SourceRecord다. 후속 파생 규칙은 승인 버전·직접 증거 계약을 확장한 뒤 추가한다.

## 목록·상세와 관계

- `GET /api/internal/v1/artworks/`: q 최대 100자, institution_id, media_group, page 1 이상, page_size 1~24. 제목·제작자·소장기관의 메타데이터 검색이며 검색어를 보존하지 않는다. 안정적인 작품 ID 순서로 페이지를 나눈다. 알려지지 않은 매체 코드·반복 조건·지원하지 않는 조건은 400이다.
- `GET /api/internal/v1/artworks/{id}/`: 노출 가능한 작품과 최대 6개 유사 작품을 반환한다. 없거나 숨겨진 작품은 동일한 404다.
- 같은 제작자는 같은 Source 안에서 일치하는 공식 제작자 ID가 있을 때만 확인한다. 이름이 같은 사실만으로 합치지 않는다. 같은 소장기관은 기관 정본 ID가 같을 때만 관계 이유가 된다. 데모 관계도 데모 목록 안에서만 계산한다.
- 공식 출품 관계의 증거 모델·수집이 없으므로 `exhibition_links={state:UNCONFIRMED,exhibitions:[]}`를 반환한다. 같은 작가·소장기관·제목이 전시와 겹쳐도 출품 전시를 생성하지 않는다.
- 이미지 권리 승인이 없으므로 모든 작품의 media는 `HIDDEN`, URL·페이지 URL·크레딧은 null이다. 이미지나 원문을 다운로드하거나 외부 미확인 이미지 요청을 보내지 않는다.

정확한 필드·오류 계약은 OpenAPI 1.4.0이 정본이다. 이 계약은 작품 데이터 확보 완료나 일반 공개 운영 승인을 뜻하지 않는다.

## 브라우저 연결

`/artworks`와 `/artworks/{id}`는 검색·상세·관심 저장·유사 작품 이동을 제공한다. 일반 모드의 수집 준비 상태는 검색 결과 없음과 구분하고, 가상 모드의 이미지 없는 작품은 텍스트로 표시한다. 관심 작품 ID만 기존 로컬 v1 저장소에 추가하며 이전 데이터에 artworks가 없으면 빈 배열로 읽어 전시·기관·취향을 보존한다. 추천을 요청할 때 관심 작품을 API에서 재확인한 현재 특성만 기존 preferred_features로 전달한다. 불러오지 못한 작품은 제외하고 사용자에게 알리며, 검색어·작품 원문·이미지·특성 응답은 영속 저장하지 않는다. 명시한 방문 조건은 계속 우선한다.

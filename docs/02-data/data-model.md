---
title: "미감(美感) Data Model"
status: DRAFT
version: "0.2.0"
last_updated: "2026-08-30"
authoritative_for:
  - "공식 전시 데이터의 개념 엔터티와 관계"
  - "원본·정규화값·출처 증거·검증 이력의 분리"
  - "검색·추천용 파생 데이터의 경계"
  - "서버 데이터와 브라우저 로컬 사용자 데이터의 경계"
related_documents:
  - "../00-governance/decision-register.md"
  - "../01-product/project-brief.md"
  - "../01-product/domain-rules.md"
  - "../01-product/prd-p0.md"
  - "./data-source-policy.md"
  - "./data-pipeline.md"
  - "./normalization-rules.md"
  - "../03-recommendation/recommendation-spec.md"
---

# 미감(美感) Data Model

## 1. 문서 목적과 권위 경계

이 문서는 P0가 다루는 공식 전시 데이터의 개념 모델을 정한다. 엔터티의 의미, 소유 관계, 필수 불변식과 출처 추적 경계를 정의하지만 특정 데이터베이스, 테이블명, 컬럼 타입, 색인, API 응답 형식은 정하지 않는다.

도메인 값의 의미는 `domain-rules.md`, 출처 자격과 권리는 `data-source-policy.md`, 원본값 변환은 `normalization-rules.md`, 처리 순서는 `data-pipeline.md`가 기준이다.

## 2. 모델 경계

서버 데이터 모델의 주체는 공식 전시 생태계와 운영 증거다. 일반 사용자 계정이나 서버 개인 프로필은 P0 서버 모델에 포함하지 않는다.

| 영역 | 서버에 유지 | 브라우저에만 유지 |
| --- | --- | --- |
| 공식 콘텐츠 | 전시·작품·기관·제작자·분류·방문정보 | 해당 없음 |
| 출처 운영 | 원본 레코드, 증거, 권리, 검증·충돌·동기화 이력 | 해당 없음 |
| 검색·추천 준비 | 콘텐츠 검색 문서, 버전이 있는 콘텐츠 특성 스냅샷 | 해당 없음 |
| 사용자 취향 | 개인별 레코드 없음 | 최신 취향 테스트 결과와 취향 요약 |
| 관심·최근 기록 | 개인별 레코드 없음 | 전시·작품·기관 하트, 최근 본 전시 |
| 일시 상태 | 장기 저장 없음 | 비교 목록, 검색 조건, 테스트 단계, 요청 중 현재 위치 |

추천 요청이 현재 브라우저의 취향·관심 신호를 일시적으로 전달할 수는 있지만, 이를 서버 개인 프로필이나 장기 행동 로그로 변환하지 않는다.

## 3. 핵심 정본 엔터티

### 3.1 Exhibition

추천·검색·비교·방문 판단의 주 객체다. 한 전시는 공식적으로 확인된 개최 단위를 나타내며 정본 식별자와 함께 전시명, 시작일, 종료일, 개최 장소, 행정 지역, 유효한 생명주기 상태, 전시 단위 공식 상세 URL, 공식 출처 근거를 각각 가져야 최소 품질에 합격한다. 다음 상태축은 서로 분리한다.

- 생명주기 `ExhibitionLifecycle`: `UPCOMING`, `CURRENT`, `ENDED`, `CANCELED`, `UNKNOWN`
- 최신성 `FreshnessStatus`: `FRESH`, `STALE`, `UNVERIFIED`
- 노출 적격성 `DataEligibility`: `VERIFIED`, `PARTIAL`, `DISCOVERY_ONLY`, `EXCLUDED`

같은 제목이라도 장소·기간·가격·예약 조건이 다른 순회전이나 재개최는 별도 Exhibition이다. 공식 근거가 있을 때만 같은 시리즈 관계를 둘 수 있다.

#### 최소 품질 게이트 판정

최소 품질 판정은 별도 콘텐츠 엔터티가 아니라 Exhibition과 FieldEvidence, Source의 현재 상태에서 계산하는 품질 결과다. 모든 핵심 항목이 유효한 결과를 `CORE_PASS`로 기록한다. 하나라도 없거나 무효·미확인·해결되지 않은 충돌이면 `CORE_PASS`가 아니며 정상 검색·추천 파생본을 만들지 않는다. 생명주기 `ENDED`와 `CANCELED`는 유효한 사실 상태이므로 `CORE_PASS`일 수 있지만 현재 추천에는 들어가지 않는다.

요금, 예약, 관람시간, 접근성, 감각 정보는 핵심 게이트 밖의 선택 방문 정보다. 이 값들의 `UNKNOWN`은 게이트 합격을 막지 않으며, 해당 값을 요구하는 추천 요청이 들어왔을 때 후보 충족 여부를 별도로 제한한다.

### 3.2 Institution

전시를 운영·주최하거나 작품을 소장하는 공식 기관 또는 공간이다. 공식 명칭과 별칭, 공간 유형, 행정구역과 주소, 위치, 공식 홈페이지, 운영·접근성 정보를 가질 수 있다. 운영 기관, 개최 장소, 주최 기관, 소장 기관 역할은 관계에서 구분한다.

행정구역 관계는 대한민국 전역의 시·도와 시·군·구를 수용한다. 이는 모든 지역 데이터의 완전성을 뜻하지 않으며, P0 품질 검증은 서울·경기·인천을 우선한다.

### 3.3 Artwork

공식 소장품 또는 공식 출품 근거가 있는 개별 작품이다. 작품명, 제작자, 제작시기, 매체·재질, 문화권, 소장기관, 이미지 권리와 출처를 가질 수 있다. Artwork가 없는 Exhibition도 유효하다.

### 3.4 Creator

작가·제작자·참여 주체의 공식 식별 단위다. 이름과 공식 별칭을 관리할 수 있지만 P0의 독립 탐색 주 객체는 아니다. 동명이인 합치기는 공식 식별 근거 없이 수행하지 않는다.

## 4. 관계 엔터티

### 4.1 ExhibitionInstitution

Exhibition과 Institution 사이의 역할을 표현한다. 개최 장소, 운영, 주최, 주관 등 공식적으로 확인된 역할을 구분하며 한 관계를 다른 역할로 추정하지 않는다.

### 4.2 ExhibitionArtwork

공식 출품 목록 또는 동등한 공식 근거가 있을 때만 생성한다. 관계 자체가 출처 증거를 가져야 하며, 같은 작가 또는 소장기관이라는 이유만으로 생성해서는 안 된다.

### 4.3 ArtworkCreator와 ExhibitionCreator

작품 제작 관계와 전시 참여 관계를 분리한다. 전시 참여 사실은 특정 작품 출품을 의미하지 않는다.

### 4.4 SeriesRelation

순회·재개최 등 서로 다른 전시 인스턴스의 공식 연속성을 표현한다. 공식 시리즈 근거가 없으면 제목 유사도만으로 생성하지 않는다.

## 5. 방문 판단 정보

방문 정보는 Exhibition 또는 실제 개최 Institution에 연결하고, 값마다 출처·확인 시각을 추적한다.

| 개념 | 모델 경계 |
| --- | --- |
| OperatingSchedule | 정규 운영시간, 휴관 규칙, 임시 변경을 구분 |
| PriceOption | 대상, 금액 또는 범위, 무료 여부, 기본권·할인·프로그램 구분과 `UNKNOWN` 근거 상태 |
| ReservationInfo | 예약 유형 또는 `UNKNOWN`, 공식 링크, 안내 문구; 잔여석·매진 상태는 포함하지 않음 |
| VisitDuration | 기관이 직접 안내한 공식값과 `UNKNOWN`을 구분 |
| AccessibilityFact | 휠체어 접근, 이동, 자막, 수어, 오디오 설명, 연령 조건의 긍정·부정·`UNKNOWN` 상태 |
| SensoryNotice | 큰·갑작스러운 소리, 섬광, 어두움, 좁거나 밀폐된 공간의 존재·부재·`UNKNOWN` 상태 |

접근성과 감각 정보는 `지원·존재`, `미지원·부재`, `미확인`을 합치지 않는다. 미확인은 부정값이 아니다.

요금, 예약, 관람시간, 접근성, 감각 정보는 값의 부재만으로 의미를 추측하지 않도록 근거 상태에 `UNKNOWN`을 명시할 수 있어야 한다. 물리 저장 방식이 null과 상태 필드를 조합하더라도 API·도메인 경계에서는 `UNKNOWN`과 확인된 부정·해당 없음·수집 실패를 구분한다.

## 6. 분류와 설명 데이터

### TaxonomyTerm

공간 유형, 행사 형식, 매체 그룹·세부 매체, 주제, 분위기, 감상 방식처럼 승인된 분류값을 나타낸다. 서로 다른 축은 하나의 범용 태그로 합치지 않는다.

### ClassificationAssertion

정본 객체와 TaxonomyTerm의 연결이다. 직접 근거, 승인 규칙으로 파생, 미확인을 구분하고 근거 출처 또는 규칙 버전을 가진다. 분류가 없다는 사실을 비선호나 부정 특성으로 해석하지 않는다.

### StructuredSummary

공식 텍스트에서 사실 범위만 구조화한 서비스 설명이다. 공식 원문과 구분하고 사용한 원본과 변환 규칙을 추적한다. 자유 생성한 작품 해설이나 의도 추정은 모델에 포함하지 않는다.

## 7. 출처·권리·증거 모델

### InstitutionCandidateAssessment, CandidateSampleReview, InstitutionAllowlistEntry

`InstitutionCandidateAssessment`는 `CANDIDATE` 단계의 allowlist 사전 심사를 보존한다. 최근 전시 5건의 `CandidateSampleReview`, `CORE_PASS` 건수, 표본 밖 추가 페이지·출처 템플릿·필드 매핑·이전 수집 이력까지 포함한 같은 필수 필드의 반복적·구조적 누락 근거, 정책·접근 제한 검토, `PASS` 또는 `HOLD` 결과와 사유, 검토자와 시각을 추적한다. `HOLD`는 lifecycle 상태가 아니라 `CANDIDATE`에서 다음 상태로 진행하지 않는 심사 결과다.

`InstitutionAllowlistEntry`는 후보 심사, 기관과 실제 수집에 사용할 공식 Source 묶음을 연결하는 온보딩·allowlist 기록이다. 상태는 `CANDIDATE`, `PROVISIONAL`, `ACTIVE`, `SUSPENDED`이며 허용 전이는 `CANDIDATE → PROVISIONAL → ACTIVE → SUSPENDED → PROVISIONAL`이다. 심사를 통과해야 `CANDIDATE`에서 `PROVISIONAL`로 진행한다. `PROVISIONAL`과 `ACTIVE`는 모두 레코드별 최소 품질·권리·최신성·충돌 게이트를 통과한 데이터를 정본·검색·추천·일반 사용자 서비스에 사용할 수 있다. `ACTIVE`는 게시 권한의 단독 조건이 아니라 실제 신규·변경 처리까지 검증한 높은 기관 신뢰 상태다.

`InstitutionAllowlistEntry`는 lifecycle·Source 운영 상태와 별도의 `health = HEALTHY | DEGRADED`, `health_changed_at`, 복수 `health_reasons`, `consecutive_final_failed_count`, `priority_reverify_at`, `priority_reverify_reason`을 가진다. `health`는 수집 가능한 `PROVISIONAL`과 `ACTIVE` 모두의 운영 신호지만, 연속 최종 실패 수와 2회 자동 중단 사다리는 `ACTIVE`에서만 계산한다. `PROVISIONAL`의 최종 실패는 health와 승격 검증에 반영하되 이 수치를 올리지 않는다. `ACTIVE`의 첫 최종 실패는 실패 수 1과 `DEGRADED`, 중간 성공 없는 서로 다른 IngestionRun의 두 번째 최종 실패는 `SUSPENDED` 전이 근거다. 최종 성공은 실패 수를 0으로 초기화하되 미해결 `STRUCTURAL_OPTIONAL`이 있으면 health는 `DEGRADED`로 남는다.

또한 `promotion_validation_started_at`, 상태 변경 시각·사유·검토자, `SUSPENDED` 근거와 복구 승인을 추적한다. 미해결 Critical CollectionIssue는 별도 lifecycle 값을 만들지 않고 해당 영향 범위의 수집 적격성을 차단한다. `SUSPENDED → PROVISIONAL` 때 연속 최종 실패 수를 0으로 초기화하고 이전 승격 기간과 연속 성공을 재사용하지 않으며 새 검증 시작 시각부터 계산한다. 모든 lifecycle·health 변경과 승인 근거는 ChangeHistory에 남긴다.

### Source

승인 검토 대상인 공식 API, 데이터 파일, 웹페이지 또는 공지를 나타낸다. 책임 주체, 접근 방식, 이용조건·라이선스, 허용 필드, 정상·일시 중단·사용 중지의 운영 상태와 정책 검토를 연결하며 InstitutionAllowlistEntry가 허용한 기관·출처 범위 안에서만 사용한다. `CANDIDATE`·`PROVISIONAL`·`ACTIVE`·`SUSPENDED`는 Source 자체가 아니라 InstitutionAllowlistEntry의 상태다. 하나의 Source가 여러 기관에 공유되더라도 기관별 lifecycle과 Source 운영 상태를 함께 판정한다.

### SourceRecord

한 번의 수집에서 받은 원본 단위다. 출처의 원본 식별자, 원본 내용 또는 허용된 보존 표현, 수집 시각, 원본 갱신 시각, 해시와 처리 상태를 가진다. 재수집 실패가 기존 SourceRecord를 빈 값으로 바꾸지 않는다.

### FieldEvidence

정본 객체의 특정 값과 그 값을 지지하거나 반박하는 SourceRecord를 연결한다. 채택 여부, 원본값, 확인 시각과 판정 근거를 추적해 필드 단위 출처 표시와 충돌 검토를 가능하게 한다.

### MediaAsset와 MediaRights

이미지·음원·영상의 원본 위치와 표현 대상을 기록하고, 권리자·라이선스·필수 크레딧·허용 처리·확인 시각을 분리한다. 권리 미확인 또는 철회 상태는 콘텐츠 메타데이터의 존재 여부와 무관하게 표시 적격성을 제한한다.

### VisualEmbedding (P1 개념)

`VisualEmbedding`은 P1에서만 권리 허용 이미지를 이용한 작품 시각 유사성 확장을 위해 둘 수 있는 개념 엔터티다. `object_id`, `model_name`, `model_version`, `embedding`, `generated_at`, `source_media_id`를 가진다. `source_media_id`는 재사용이 허용된 `MediaAsset`만 가리킬 수 있으며, 권리 철회·변경 시 해당 임베딩은 사용 중지할 수 있어야 한다. P0에서는 `VisualEmbedding`을 생성·저장·읽거나 점수에 사용하지 않는다.

## 8. 품질과 운영 이력

| 개념 | 역할 |
| --- | --- |
| VerificationRecord | 어떤 공식 근거를 언제 재확인했고 어떤 결과였는지 기록 |
| SourceConflict | 동일 의미의 원본값이 충돌한 상태, 영향 필드와 검토 결과 기록 |
| DuplicateCandidate | 자동 합치기에 충분하지 않은 중복 의심 객체를 검토 대상으로 유지 |
| IngestionRun | 명령 종류·출처 또는 정본 전시 범위·due 선택 근거, 요청별 재시도 수, 핵심·선택 target별 최종 결과와 실행 최종 `SUCCESS`·`FAILED`를 기록한다. 공유 Source 실행은 기관별 lifecycle, 성공·실패·건너뜀·처리량과 실행 중 발견한 `SourceConflict`를 따로 추적한다. 핵심 대상 페이지가 최종 미수집되거나 핵심 미완성 데이터가 Canonical에 반영되거나 실행 중 Critical이 확인된 기관이 하나라도 있으면 실행을 최종 `FAILED`로 고정한다. 선택 target 실패와 정상 단건 격리만 있으면 `SUCCESS`일 수 있다. |
| InstitutionRunResult | 한 IngestionRun 안의 InstitutionAllowlistEntry별 결과다. `(ingestion_run_id, institution_allowlist_entry_id)`는 유일하며 최종 `SUCCESS`·`FAILED`, 핵심·선택 대상별 최종 결과, 재시도 수, 수집 문제 분류, 격리 레코드, health·연속 실패 수의 변경 전후를 기록한다. 같은 실행의 여러 HTTP 재시도는 연속 실패 수를 한 번만 갱신한다. 실행 중 Critical이 확인되면 영향 기관 결과는 `FAILED`다. 실행 밖 검토로 발견된 Critical을 위해 가상 결과를 만들지 않는다. |
| InstitutionQualificationRun | `PROVISIONAL` 기관의 승격 검증 실행만 InstitutionRunResult와 IngestionRun에 연결하고 `finished_at`, `finished_at`을 `Asia/Seoul` 달력일로 환산한 서비스 기준 날짜, 최종 상태, 재시도 수, 최종 미수집 핵심 페이지, 구조적 핵심 필드 누락, 정책·접근 문제, 실행 종료 시 Source 운영 상태, 미해결 구조 충돌 수와 의미 있는 변경 근거를 기록한다. 한 실행 안에 여러 `PROVISIONAL` 기관 결과가 있으면 기관별로 별도 생성한다. 핵심 대상 페이지가 최종 미수집되거나 해당 기관의 핵심 미완성 데이터가 Canonical에 반영되거나 실행 중 Critical이 확인되면 최종 `FAILED`로 고정하고 승격 연속 성공을 초기화한다. `ACTIVE` 런타임 결과에는 생성하거나 과거 승격 증거를 다시 쓰지 않는다. |
| CollectionIssue | `POLICY_BLOCK`, `ACCESS_BLOCK`, `STRUCTURAL_CRITICAL`, `STRUCTURAL_OPTIONAL`, `RECORD_EXCEPTION`과 영향 Source·기관·target·field·record, `scope = ENTRY | SOURCE`, 범위 확대 근거, 최초·마지막 확인 시각, 해결 상태와 근거를 기록한다. Critical은 기관·템플릿 범위 근거를, 단건 격리는 패턴이 아님을 추적한다. 미해결 Critical은 해당 scope의 수집 전 차단 게이트다. |
| PromotionEvidence | 최초 검증 시작 시각, 서로 다른 날짜의 연속 `SUCCESS` 3건, 중간 `FAILED` 0건, 최소 1건의 의미 있는 ChangeHistory 연결과 승격 시점의 최종 조건을 묶어 `ACTIVE` 승인 근거로 보존한다. |
| ChangeHistory | Canonical 값·상태·권리 판정과 InstitutionAllowlistEntry lifecycle·health·연속 실패 수의 변경 전후, SourceRecord·정규화 규칙 버전·검토자와 근거를 추적한다. 신규 Canonical 생성도 생성 이력으로 기록한다. |

운영 이력은 사용자 행동 분석 로그가 아니다. 콘텐츠 정확성과 출처 운영을 감사하기 위한 데이터만 포함한다.

## 9. 검색·추천용 파생 모델

### SearchDocument

정본 전시·작품·기관에서 만든 검색용 표현이다. 제목, 별칭, 작가명, 기관명, 분류, 지역과 상태를 포함할 수 있으며 원본 객체와 생성 버전을 가리킨다. SearchDocument가 정본을 대신하지 않는다.

### ContentFeatureSnapshot

추천에 사용할 승인된 콘텐츠 특성의 버전 있는 스냅샷이다. P0에서는 매체·주제·분위기·감상 방식·방문 조건과 근거 상태만 담을 수 있다. 추천 알고리즘과 가중치는 이 모델이 아니라 추천 명세가 정하며, P0는 시각 임베딩을 이 스냅샷에 넣지 않는다.

### RecommendationRequestContext

지역·날짜·필수조건·선호와 현재 브라우저가 제공한 취향·하트 신호를 한 요청에서만 결합하는 일시 문맥이다. 개인 식별자, 서버 개인 프로필 또는 장기 저장 엔터티가 아니다.

## 10. 브라우저 로컬 데이터 계약

브라우저에는 다음 논리 묶음만 유지한다.

- 스키마 버전
- 최신 취향 테스트의 명시적 선택과 계산된 취향 요약
- 전시·작품·기관의 하트 식별자
- 최대 10~20개의 최근 본 전시 식별자와 최소 재방문 정보

최신 테스트는 이전 테스트 기반 취향을 대체하고 하트는 사용자가 해제할 때까지 유지한다. 조회·클릭·검색·비교·스크롤·체류시간·최근 본 기록은 장기 취향 신호 모델이 아니다. 브라우저 로컬 데이터의 물리 키와 직렬화 형식은 구현 문서가 정한다.

## 11. 모델 불변식

1. Exhibition은 제품의 추천·방문 판단 주 객체이고 Artwork는 보조 탐색 객체다.
2. `ExhibitionLifecycle`·`FreshnessStatus`·`DataEligibility`는 서로 독립된 값이다.
3. 정본 핵심 값과 분류는 출처 증거 또는 승인된 파생 규칙을 추적할 수 있어야 한다.
4. 원본, 정본, 검색·추천 파생본과 운영 이력을 같은 레코드로 합치지 않는다.
5. 미확인과 부정, 수집 실패와 사실 삭제, 하트 해제와 비선호를 구분한다.
6. P0 서버 모델에 일반 사용자 계정, 익명 개인 프로필, 사용자 컬렉션, 암묵 행동 학습 이벤트를 추가하지 않는다.
7. 데모 레코드와 미디어도 출처·권리·재배포 판단을 추적한다.
8. P0는 `VisualEmbedding`을 생성·저장·읽거나 추천 점수에 사용하지 않는다.
9. Exhibition의 최소 품질 게이트와 게이트 밖 선택 방문 정보의 완전성은 별도 축이며, 선택 정보의 `UNKNOWN`을 추론값 또는 필수 방문 조건 충족으로 바꾸지 않는다.
10. `PROVISIONAL`과 `ACTIVE` InstitutionAllowlistEntry의 레코드는 동일한 최소 품질·권리·최신성·충돌 게이트를 통과하면 정본·검색·추천 파생본과 일반 사용자 서비스에 사용할 수 있다. `CANDIDATE`와 `SUSPENDED`는 신규 정본·파생본 생성 자격이 없다.
11. `ACTIVE`는 기관 수집기의 변경 처리 안정성을 나타내는 신뢰 상태이며 레코드별 게이트를 우회하지 않는다. `PROVISIONAL`이라는 이유만으로 합격 레코드를 배제하거나 `ACTIVE`라는 이유만으로 불합격 레코드를 노출하지 않는다.
12. 원본 해시·수집 시각·페이지 외피 변화만으로 의미 있는 변경을 만들 수 없다. 승격에 쓰는 변경은 SourceRecord, 승인 정규화 규칙 버전, Canonical 반영과 ChangeHistory를 모두 연결해야 한다.
13. InstitutionAllowlistEntry health는 lifecycle·Source 운영 상태·레코드 `DataEligibility`를 대체하지 않는다. `DEGRADED`나 `SUSPENDED`만으로 마지막 정상 정본을 일괄 `EXCLUDED`로 바꾸거나 Source를 사용 중지하지 않는다. 기존 핵심값 자체가 신뢰 불가하다는 Critical 근거가 있는 영향 레코드만 즉시 `EXCLUDED`로 격리하고 나머지는 근거·최신성·권리·충돌 규칙으로 다시 계산한다.
14. `STRUCTURAL_OPTIONAL`은 선택 필드를 `UNKNOWN`으로 만들고 기관 health를 `DEGRADED`로 하지만 InstitutionRunResult를 `FAILED`로 만들거나 연속 실패 수를 올리지 않는다. `RECORD_EXCEPTION`은 레코드만 격리하고 기관 health·lifecycle을 바꾸지 않는다.
15. `ACTIVE`의 연속 최종 실패 수는 서로 다른 IngestionRun ID의 InstitutionRunResult만 세며 중간 `SUCCESS`가 있으면 0으로 초기화한다. Critical 사유는 이 수치를 기다리지 않는다.
16. 미해결 Critical CollectionIssue는 `PROVISIONAL`·`ACTIVE`의 해당 scope를 수집 전에 차단한다. 기관 범위가 기본이며 Source 전체 근거가 있을 때만 연결 기관 전체와 Source 운영 상태로 전파한다.
17. `PROVISIONAL`의 InstitutionRunResult가 최종 `FAILED`이면 health와 InstitutionQualificationRun의 승격 연속성만 갱신하고 `ACTIVE`용 연속 최종 실패 수는 0으로 유지한다. `ACTIVE` 런타임 결과는 InstitutionQualificationRun이나 과거 PromotionEvidence를 생성·변경하지 않는다.

## 12. 열린 결정 등록부 참조

| 결정 ID | 모델에 미치는 영향 |
| --- | --- |
| OD-002 | 공개 저장소와 데모 재배포 범위에 따라 배포 가능한 SourceRecord·MediaAsset 표현을 제한한다. |
| OD-003 | 실제 기관 allowlist와 Source별 원본 식별자·허용 필드·호출 제약 매핑을 확정한다. 승격과 health·중단 증거 구조는 확정됐다. |
| OD-005 | 외부 공개 API를 제공할 경우 내부 모델과 외부 계약의 분리·노출 범위를 별도로 결정한다. |

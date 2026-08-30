---
title: "미감(美感) Data Pipeline"
status: DRAFT
version: "0.2.0"
last_updated: "2026-08-30"
authoritative_for:
  - "공식 출처에서 정본·검색·추천 데이터로 이어지는 처리 단계"
  - "증분 수집·재시도·충돌·중복·실패 복구 원칙"
  - "전시 상태별 재확인 주기와 최신성 판정 운영"
  - "P0 데모 모드와 후속 동기화 모드의 경계"
related_documents:
  - "../00-governance/decision-register.md"
  - "../01-product/project-brief.md"
  - "../01-product/domain-rules.md"
  - "../01-product/roadmap.md"
  - "./data-source-policy.md"
  - "./data-model.md"
  - "./normalization-rules.md"
  - "../03-recommendation/recommendation-spec.md"
---

# 미감(美感) Data Pipeline

## 1. 문서 목적과 권위 경계

이 문서는 승인된 공식 출처가 원본 증거, 정규화된 정본, 검색·추천 입력으로 바뀌는 논리 흐름과 운영 불변식을 정한다. P0의 동기화·재확인 관리 명령 계약과 배포 스케줄러의 호출 경계까지 정하지만, 특정 작업 큐 또는 배포 서비스 제공자는 정하지 않는다.

출처 허용 여부는 `data-source-policy.md`, 값의 변환은 `normalization-rules.md`, 결과 개념은 `data-model.md`, 상태 의미는 `domain-rules.md`가 기준이다.

## 2. 두 실행 모드

### 2.1 P0 데모 모드

외부 API 키와 실시간 네트워크 없이 승인된 대표 데모 데이터로 전체 탐색·추천 흐름을 재현한다. 데모 데이터는 운영과 같은 검증·정규화·권리 기준을 통과한 고정 스냅샷이며, 실패 없는 특별 정본으로 취급하지 않는다.

### 2.2 동기화 모드

`PROVISIONAL` 또는 `ACTIVE` InstitutionAllowlistEntry와 운영 상태가 정상인 Source가 함께 허용한 기관 범위를 수집해 변경분을 사용자 정본에 반영한다. 두 상태 모두 레코드별 최소 품질·권리·최신성·충돌 게이트를 동일하게 적용하며, `ACTIVE`는 게시 권한이 아니라 실제 변경 처리 안정성까지 검증한 높은 기관 신뢰 상태다. 후보 기관은 `data-source-policy.md`의 최근 5건 중 4건 이상 `CORE_PASS`, 구조적 반복 누락 없음, 반복 수집·재확인을 막는 정책·접근 제한 없음 조건을 통과한 뒤 `PROVISIONAL`이 된다. P0에서는 개발·운영자가 로컬에서 반복 실행할 수 있어야 하며, 배포 환경에서는 같은 재확인 경로를 스케줄러가 호출할 수 있어야 한다. Celery나 상시 worker는 P0에 두지 않는다. 공개 운영 단계의 호스팅·비용·관측성은 P1 게이트와 OD-006에서 결정한다.

#### 2.2.1 allowlist 온보딩 흐름

```text
후보 기관 최근 전시 5건 검토
  → 4건 미만 CORE_PASS: HOLD 심사 기록, allowlist 미등록, 심사 종료
  → 4건 이상 CORE_PASS
      → 구조적 필드 누락 또는 반복 수집을 막는 정책·접근 제한: HOLD 심사 기록, allowlist 미등록, 심사 종료
      → 보류 사유 없음: CANDIDATE에서 PROVISIONAL로 전이
          → 레코드별 게이트 통과 데이터를 정상 서비스에 사용
          → 최초 승격 검증 시작
          → 최소 14일 + 서로 다른 날짜 3회 연속 SUCCESS + 중간 FAILED 0
          → 최소 1회 의미 있는 신규·변경을 Canonical과 ChangeHistory까지 반영
          → 마지막 SUCCESS + Source 정상 + 미해결 구조 충돌 0
          → ACTIVE 승격
          → Critical 확인: PROVISIONAL 유지 + DEGRADED + 해당 scope 수집·승격 차단

ACTIVE
  → 첫 최종 FAILED: ACTIVE + DEGRADED + 우선 재검증
  → 중간 SUCCESS 없는 서로 다른 실행 2회 연속 최종 FAILED: SUSPENDED
  → POLICY_BLOCK / ACCESS_BLOCK / STRUCTURAL_CRITICAL: 즉시 SUSPENDED
  → STRUCTURAL_OPTIONAL: ACTIVE + DEGRADED, 선택값 UNKNOWN
  → RECORD_EXCEPTION: 해당 레코드만 격리, 기관 상태 유지
  → 문제 수정·승인: PROVISIONAL로 전이하고 승격 검증을 처음부터 다시 시작
```

`HOLD`는 `CANDIDATE` 심사 결과이지 lifecycle 상태가 아니다. `CANDIDATE`와 `SUSPENDED`는 신규 운영 수집·정본 반영·파생본 생성 대상이 아니다. `SUSPENDED` 전환만으로 마지막 정상 정본을 삭제하지 않고 최신성·권리·충돌 정책에 따라 기존 노출을 재평가한다.

#### 2.2.2 승격 검증 실행

승격 검증은 `PROVISIONAL` 기관에만 생성하는 InstitutionQualificationRun 단위로 판정한다. `ACTIVE` 런타임 실행은 InstitutionQualificationRun이나 과거 PromotionEvidence를 생성·변경하지 않는다.

- `promotion_validation_started_at + 14일`이 지나야 한다.
- `InstitutionQualificationRun.finished_at`을 `Asia/Seoul` 달력일로 환산한 날짜가 서로 다른 최종 `SUCCESS` 3건만 센다. 같은 날짜의 반복 성공은 한 날짜로만 계산한다.
- 첫 성공부터 세 번째 성공 사이에 해당 기관 범위의 최종 `FAILED`가 하나라도 있으면 연속 성공을 초기화한다.
- 요청 단계의 일시 오류와 `request_retry_count > 0`은 허용한다. 허용 재시도 안에서 모든 핵심 대상 페이지를 처리하고 실행이 최종 `SUCCESS`이면 성공이다.
- 핵심 대상 페이지를 끝내 수집하지 못하거나 해당 기관의 InstitutionRunResult가 최종 `FAILED`이면 실패다. 핵심 데이터가 미완성인 레코드는 격리해야 하며 이를 Canonical에 반영했거나 실행 중 Critical이 확인된 경우 해당 `PROVISIONAL` 기관의 InstitutionRunResult·InstitutionQualificationRun을 최종 `FAILED`로 기록하고 승격 연속 성공을 초기화한다. 공유 IngestionRun 전체가 다른 기관 때문에 `FAILED`여도 해당 기관의 결과가 `SUCCESS`라면 QualificationRun을 실패로 바꾸지 않는다. 선택 대상·필드 실패와 정상 격리된 단건 예외는 아래 운영 health 규칙으로 분리한다.
- 세 성공 실행 동안 구조적 핵심 필드 누락, 정책·robots·약관 문제, CAPTCHA·로그인 요구와 지속 접근 차단이 0건이어야 한다.
- 승격 직전 마지막 실행이 `SUCCESS`이고 대상 Source가 정상이며 미해결 구조적 `SourceConflict`가 0건이어야 한다.

#### 2.2.3 의미 있는 신규·변경 증거

세 성공 실행 중 하나 이상은 다음 경로를 끝까지 완료해야 한다.

```text
SourceRecord 신규·변경
  → 승인 규칙 버전으로 정규화
  → 의미 필드 신규·변경
  → Canonical Exhibition 생성·갱신
  → ChangeHistory 기록
```

P0에서는 새 전시, 종료일 변경·연장, 요금 변경, 장소 변경, 예약 방식 변경, 전시 취소, 공식 설명에서 P0 승인·버전 고정 정규화 규칙이 만든 Canonical 필드 변경만 인정한다. 전시명·시작일·지역·일반 상태 전이를 포함한 목록 밖 변화는 별도 결정과 규칙 버전 승인이 있기 전까지 승격 증거가 아니며 취소만 상태 변경 유형의 예외다. footer·배너, tracking parameter, HTML whitespace·필드 순서, 수집 시각, 재시도 횟수와 정규화 결과가 같은 hash 변화도 인정하지 않는다. 원본 hash가 바뀌어도 Canonical 의미 필드와 ChangeHistory가 바뀌지 않으면 승격 증거가 아니다.

#### 2.2.4 운영 health·실패 연속성·Critical 처리

모든 변경 명령은 공유 IngestionRun 안에서도 실제 실행 대상으로 확정된 InstitutionAllowlistEntry마다 InstitutionRunResult를 정확히 하나 만든다. `PROVISIONAL`과 `ACTIVE` 모두 health를 갱신하지만, 연속 최종 실패 수와 2회 자동 중단 사다리는 `ACTIVE`에만 적용하고 `PROVISIONAL`에서는 0으로 유지한다. 이 기관별 결과의 서로 다른 IngestionRun ID 카운터는 승격의 `Asia/Seoul` 기준 서로 다른 성공 날짜 3회와 별개다.

- 재시도 후 핵심 대상을 모두 처리한 최종 `SUCCESS`는 `ACTIVE` 실패 수를 0으로 초기화한다. lifecycle과 관계없이 미해결 `STRUCTURAL_OPTIONAL`·Critical이 없으면 health를 `HEALTHY`, 있으면 `DEGRADED`로 계산한다.
- 첫 최종 `FAILED`는 `ACTIVE`를 유지하고 health를 `DEGRADED`, 실패 수를 1로 만든 뒤 허용 호출 제한·backoff 안의 최우선 재검증 대상으로 올린다.
- 중간 `SUCCESS` 없이 다음의 서로 다른 IngestionRun에서 다시 최종 `FAILED`이면 실패 수 2와 함께 `SUSPENDED`로 전환한다.
- `POLICY_BLOCK`, `ACCESS_BLOCK`, `STRUCTURAL_CRITICAL`은 카운터를 기다리지 않고 영향 범위의 추가 요청과 정본 반영을 중단한다. 실행 중 확인되면 영향 기관의 InstitutionRunResult와 이를 포함한 IngestionRun을 최종 `FAILED`로 만들고, `ACTIVE`는 실패 수를 0→1 또는 1→2로 올린 뒤 즉시 `SUSPENDED`, `PROVISIONAL`은 health를 `DEGRADED`로 두며 연결된 InstitutionQualificationRun을 `FAILED`로 만들어 승격 연속 성공을 초기화한다. 실행 밖 검토로 확인되면 가상 실행·결과·실패 수를 만들지 않고 CollectionIssue와 lifecycle·수집 게이트만 갱신한다. 접근 통제를 우회하지 않는다.
- `STRUCTURAL_OPTIONAL`은 실행을 `SUCCESS`로 끝낼 수 있으며 선택값을 `UNKNOWN` 또는 미디어 대체로 두고 lifecycle을 유지한 채 health만 `DEGRADED`로 만든다. `ACTIVE` 실패 수는 증가하지 않는다.
- 가져와 파싱한 단일 `RECORD_EXCEPTION`은 정본·파생본·승격 의미 변경에서 제외해 격리하고, 기관 health·실패 수·lifecycle은 유지한다. 반복 패턴이면 Critical 재분류 대상으로 올린다.

미해결 Critical CollectionIssue는 lifecycle 값을 추가하지 않고 해당 scope의 수집 전 차단 게이트가 된다. 하나의 Source가 여러 기관을 반환하면 scope 기본값은 `ENTRY`이고 Critical·health·실패 수를 영향 기관별로 판정한다. 정책·robots·접근·구조 문제가 Source 전체에 적용된다는 근거가 있을 때만 `SOURCE`로 넓혀 Source 운영 상태와 연결된 다른 기관 범위까지 중단한다.

### 2.3 P0 관리 명령과 스케줄러 계약

P0의 동기화·재확인 실행은 다음 명령 계약을 사용한다.

```text
uv run python manage.py sync_exhibitions
uv run python manage.py refresh_due_exhibitions
uv run python manage.py sync_exhibitions --source=<source_key>
uv run python manage.py refresh_exhibition --id=<canonical_id>
uv run python manage.py show_refresh_schedule
```

- 인자 없는 `sync_exhibitions`는 `PROVISIONAL` 또는 `ACTIVE` InstitutionAllowlistEntry, 정상 Source, 영향 scope의 미해결 Critical CollectionIssue 0건을 모두 충족한 기관 범위를 증분 동기화한다. `--source=<source_key>`도 이 수집 전 게이트를 통과한 연결 기관이 하나 이상일 때만 시작한다. 알 수 없거나 미등록·일시 중단·사용 중지인 Source, `CANDIDATE`·`SUSPENDED`, 미해결 Critical 영향 범위는 네트워크 수집 전에 거부한다. `DEGRADED` health만으로 실행을 막지 않으며 우선 재검증 근거로 사용한다. 허용된 공유 Source가 반환한 각 레코드는 연결된 기관 lifecycle과 CollectionIssue scope를 다시 판정하고, `PROVISIONAL`과 `ACTIVE` 모두 같은 레코드 게이트와 정상 게시 경로를 사용한다.
- `refresh_due_exhibitions`는 상태·시작일·마지막 성공 공식 확인 시각과 출처별 허용 호출 조건으로 재확인 대상을 계산하고, 그 대상만 같은 수집·정규화·품질 흐름으로 처리한다.
- `refresh_exhibition --id=<canonical_id>`는 운영자가 지정한 정본 전시의 공식 근거를 즉시 재확인하되, 연결 기관이 `PROVISIONAL` 또는 `ACTIVE`이고 Source가 정상이며 미해결 Critical 영향 범위 밖일 때만 사용한다. `CANDIDATE`·`SUSPENDED`, 미해결 Critical 또는 미등록·일시 중단·사용 중지 Source를 ID 지정으로 우회하지 않는다.
- `show_refresh_schedule`은 현재 시점의 due 대상과 다음 재확인 근거를 읽기 전용으로 보여준다.
- 모든 변경 명령은 실행 범위, due 선택 근거, 요청 재시도, 페이지별 최종 결과, 출처·기관별 성공·실패·건너뜀, 실행 중 발견한 충돌과 연결된 `SourceConflict`를 `IngestionRun`에 남긴다. 실패는 마지막 정상 원본·정본을 삭제하거나 빈 값으로 덮어쓰지 않는다.
- 배포 스케줄러는 `PROVISIONAL` 또는 `ACTIVE` InstitutionAllowlistEntry와 정상 Source가 함께 허용한 대상에 대해 `refresh_due_exhibitions`를 호출한다. 스케줄러가 수집기·정본을 별도 경로로 직접 변경해서는 안 된다.

변경 명령과 스케줄러는 대상 선택 뒤 수집·정규화·품질·권리·정본 병합·파생본 생성 서비스를 공유한다. `PROVISIONAL`과 `ACTIVE`는 동일한 레코드 게이트를 통과하고 InstitutionRunResult·health를 기관별로 기록한다. `PROVISIONAL`은 InstitutionQualificationRun과 승격 증거를, `ACTIVE`는 연속 최종 실패 수를 별도로 갱신한다. `show_refresh_schedule`은 같은 due 선택기, 우선 재검증과 승격 검증 진행 상태를 읽기 전용으로 사용한다.

### 2.4 P0 처리 우선순위

현재·예정 전시와 `2023-01-01` 이후 전시를 우선 수집·재검증한다. 더 오래된 공식 데이터는 안정적으로 확보할 수 있을 때 종료 전시 아카이브로 보존하며, 연도만으로 정상 레코드를 삭제하지 않는다. 지역은 서울·경기·인천의 품질 검증을 우선하되 파이프라인과 정본은 전국 행정구역을 수용한다.

## 3. 처리 흐름

```text
승인 출처 등록부
  → 출처별 수집
  → 원본 레코드 보존
  → 구조·필수값 검증
  → 이용조건·미디어 권리 게이트
  → 정규화와 분류 근거 생성
  → 중복 탐지·정본 매칭
  → 필드별 증거 병합과 충돌 기록
  → 생명주기·최신성·노출 적격성 계산
  → 검색 문서·추천 특성 스냅샷 생성
  → 품질 검증과 운영 검토
```

출처별 수집기는 원본 레코드까지만 책임지고 정본을 직접 덮어쓰지 않는다. 이후 단계는 앞 단계의 성공·버전·근거를 확인할 수 있어야 한다.

## 4. 수집과 원본 보존

1. 일반 동기화는 `PROVISIONAL` 또는 `ACTIVE` InstitutionAllowlistEntry, 정상 Source, 영향 scope의 미해결 Critical CollectionIssue 0건을 모두 충족한 기관 범위만 실행한다. `CANDIDATE`·`SUSPENDED`와 Critical 차단 범위는 실행하지 않는다.
2. 출처의 호출 제한, 이용조건, 로봇 정책을 준수한다.
3. 원본 식별자, 출처 갱신 시각, 수집 시각과 내용 해시는 재처리·원본 변화 탐지에 사용한다. 내용 해시 변화만으로 의미 있는 Canonical 변경 또는 승격 증거를 만들지 않는다.
4. 같은 입력을 다시 처리해도 정본과 관계가 중복 생성되지 않아야 한다.
5. 부분 실행 실패 후 성공한 범위를 다시 만들지 않고 안전하게 이어갈 수 있어야 한다.
6. 원본 삭제·404·빈 응답·파싱 실패를 실제 행사 취소나 사실 삭제로 변환하지 않는다.
7. 마지막 정상 원본과 정본은 보존하고 실패·재시도 이력을 별도로 남긴다.

접근 통제를 우회하거나 승인되지 않은 대체 출처로 자동 전환하지 않는다.

## 5. 검증과 권리 게이트

원본은 최소 구조와 공식 식별 근거를 검사한다. 전시 한 건은 전시명, 시작일, 종료일, 장소, 지역, `UNKNOWN`이 아닌 유효 상태, 전시 단위 공식 상세 URL, 공식 출처가 각각 확인되어야 최소 품질에 합격한다. 하나라도 없거나 무효·충돌이면 정본 병합 전에 격리하고 정상 검색·추천 정본으로 승격하지 않는다.

요금, 예약, 관람시간, 접근성, 감각 정보는 최소 품질 게이트에 포함하지 않는다. 이 값의 근거가 없으면 `UNKNOWN`으로 명시해 보존하고, 다른 출처의 무관한 값·유사 전시·평균값으로 채우지 않는다.

미디어는 메타데이터와 별도로 권리 상태를 확인한다. 권리 미확인 미디어가 제외되어도 전시 메타데이터가 유효하면 텍스트 중심 결과는 유지할 수 있다. 반대로 공개된 이미지가 있다는 사실만으로 해당 전시의 사실 신뢰도를 높이지 않는다.

## 6. 정규화와 정본 매칭

정규화 단계는 원본 표현을 보존한 채 날짜, 지역, 가격, 예약, 매체·주제·분위기, 접근성·감각 정보를 승인된 도메인 값으로 변환한다. 선택 방문 정보의 근거가 부족하면 `UNKNOWN`으로 남기고, 핵심 게이트 필드는 `UNKNOWN`으로 합격시키지 않는다.

### 6.1 동일 객체의 강한 근거

- 같은 출처의 안정된 공식 식별자
- 공식적으로 선언된 상호 참조 식별자
- 동일 개최 기관·정규화 제목·장소·기간이 모두 일치하는 높은 확신 조합

### 6.2 자동 합치지 않는 경우

- 제목만 같음
- 작가나 소장기관만 같음
- 기간·장소가 다른 순회전 또는 재개최
- 동명이인 제작자
- 유사하지만 핵심값이 충돌하는 기관·작품

확신이 충분하지 않으면 별도 정본 후보를 유지하고 `DuplicateCandidate`로 운영 검토에 보낸다. 잘못 합친 이력이 확인되면 출처 증거를 잃지 않고 분리할 수 있어야 한다.

## 7. 필드 병합과 충돌

정본 병합은 필드별로 수행한다. 출처 정책의 책임 주체와 우선순위를 적용하되, 기존값·후보값·각 확인 시각과 채택 근거를 모두 보존한다.

- 더 최신이라는 이유만으로 책임 주체가 다른 값을 무조건 채택하지 않는다.
- 공식 취소·기간 변경·임시 휴관은 우선 재검증 대상으로 다룬다.
- 자동 판정이 불가능한 핵심 충돌은 `SourceConflict`로 기록한다.
- 최소 품질 핵심 항목의 해결되지 않은 충돌은 `EXCLUDED`로 판정해 사용자 검색·추천 파생본을 만들지 않는다. 게이트 밖 방문 정보 충돌은 해당 조건의 충족을 막고 추가 확인 대상으로 둘 수 있다.
- 충돌 해결 후에도 어떤 원본을 왜 채택했는지 감사할 수 있어야 한다.

## 8. ExhibitionLifecycle·FreshnessStatus·DataEligibility

전시 생명주기, 최신성, 노출 적격성은 정본 병합 후 각각 `ExhibitionLifecycle`, `FreshnessStatus`, `DataEligibility`로 독립 계산한다.

### 8.1 재확인 주기

| 전시 범위 | 목표 재확인 주기 |
| --- | --- |
| 현재 진행 중 | 매일; 마지막 성공 공식 확인 48시간 이내 유지 |
| 시작일까지 7일 이하인 예정 전시 | 매일; 마지막 성공 공식 확인 48시간 이내 유지 |
| 그 밖의 예정 전시 | 3일마다 |
| 종료 전시 | 정기 재확인 없음; 정정·권리 요청·충돌 때 재확인 |

이 표는 정본 전시의 최신성 목표다. 실제 출처별 호출 시각은 승인된 출처의 호출 제한·공식 갱신 특성·마지막 성공 시각을 함께 고려해 계산하며, 구체 출처 설정은 OD-003 이후 확정한다. 출처 제약 때문에 목표 시각 안에 공식 확인을 마치지 못하면 주기를 임의로 늘리지 않고 해당 정본을 `STALE`로 전환한다.

취소 공지, 임시 휴관, 핵심 필드 충돌, 첫 최종 실패와 미해결 `STRUCTURAL_OPTIONAL`은 주기와 무관하게 우선 재확인 대상으로 올리되 출처 호출 제한과 backoff는 지킨다.

### 8.2 최신성 판정

- 현재 또는 7일 이내 시작 전시는 마지막 성공 공식 확인이 48시간 이내일 때만 `FRESH`로 판단한다.
- 다른 예정 전시는 마지막 성공 공식 확인이 정해진 3일 재확인 범위 안에 있을 때만 `FRESH`로 판단한다.
- 기한을 넘겼지만 마지막 공식값이 남아 있으면 오래됨으로 표시한다.
- 최소 품질 핵심 항목의 마지막 검증 근거는 남아 있지만 공식 페이지가 일시적으로 소실되거나 반복 재확인에 실패해 최신 방문 가능성을 신뢰하기 어려우면 `UNVERIFIED`로 전환할 수 있다.
- 최소 품질 핵심 항목 자체가 누락·무효·충돌 상태가 되면 `UNVERIFIED` 제한 검색으로 우회하지 않고 `EXCLUDED`로 격리한다.

수집 실패 한 번만으로 생명주기를 종료·취소로 바꾸지 않는다. 최신성 저하와 실제 행사 상태 변경을 구분한다.

### 8.3 DataEligibility 갱신

공식성, 최소 품질 핵심 필드, 권리, 최신성, 충돌을 종합해 검증·일부 확인·발견 전용·제외 상태를 갱신한다. 최소 품질에 합격한 뒤 요금·예약·관람시간·접근성·감각 정보만 `UNKNOWN`인 레코드는 그 이유로 삭제하지 않는다. 다만 사용자의 필수 방문 조건에 필요한 값이 `UNKNOWN`이면 추천 단계에서 충족 후보로 통과시키지 않는다.

기관 lifecycle·health·Source 운영 상태는 DataEligibility 값을 직접 대입하는 축이 아니다. `SUSPENDED`나 Critical 확인만으로 마지막 정상 정본을 일괄 `EXCLUDED`로 만들지 않고 각 레코드의 근거와 최신성을 다시 계산한다. 다만 Critical 근거가 현재 정본의 핵심값 자체를 신뢰할 수 없음을 보여주는 영향 레코드는 즉시 `EXCLUDED`로 격리한다.

## 9. 검색·추천 파생 데이터

정본과 상태 계산이 완료된 버전에서 검색 문서와 콘텐츠 특성 스냅샷을 만든다.

- 검색 문서는 제목·별칭·작가·기관·지역·분류·전시 상태를 정본에서 파생한다.
- P0 추천 특성은 승인된 매체·주제·분위기·감상 방식·방문 조건과 근거 상태만 사용한다. 이미지 임베딩을 생성·저장·읽거나 점수에 사용하지 않는다.
- 파생본은 생성 버전과 정본 버전을 가리켜야 한다.
- 정본이나 권리 상태가 바뀌면 영향받는 파생본을 다시 만들거나 노출에서 제외한다.
- 추천 가중치와 개인화 계산은 이 파이프라인이 아니라 추천 명세가 정한다.

## 10. 실패 복구와 재처리

1. 단계별 실패는 실행 전체를 사실 삭제로 만들지 않는다.
2. 재시도는 출처 제한을 준수하고 영구 실패와 일시 실패를 구분한다. 개별 요청 실패가 허용 재시도 안에서 회복되고 모든 핵심 대상 처리가 끝나면 IngestionRun은 `SUCCESS`일 수 있다.
3. 핵심 대상 페이지가 최종 미수집이거나 파싱·정규화·정본 반영의 핵심 단계가 끝나지 않으면 IngestionRun과 영향받은 기관의 InstitutionRunResult는 최종 `FAILED`다. 영향 기관이 `PROVISIONAL`인 승격 검증 실행일 때만 연결된 InstitutionQualificationRun도 `FAILED`로 기록하고 승격 연속 성공을 초기화한다. `ACTIVE` 런타임 실패는 InstitutionQualificationRun이나 과거 PromotionEvidence를 만들거나 다시 쓰지 않는다. 선택 대상만 최종 실패하면 `STRUCTURAL_OPTIONAL`로 기록하고 실행은 `SUCCESS`일 수 있다.
4. 최소 품질 불합격 레코드는 격리하고 정본에 반영하지 않는다. 가져온 단일 레코드를 정상 격리하면 `RECORD_EXCEPTION`이며 실행 전체 실패가 아니다. 반면 핵심 데이터가 미완성인 값을 Canonical에 반영한 경우에는 IngestionRun과 영향받은 InstitutionRunResult를 최종 `FAILED`로 기록하고, `PROVISIONAL` 승격 검증 실행에서만 InstitutionQualificationRun 실패와 승격 연속 성공 초기화를 적용한다. 이는 별도 데이터 품질 결함으로도 남긴다.
5. 같은 원본과 규칙 버전의 재처리는 같은 정규화 결과를 만들어야 한다.
6. 정규화 규칙이 바뀌면 원본에서 파생 결과만 다시 만들 수 있어야 한다.
7. 권리 철회 시 표시·파생 미디어를 우선 중단하되 관련 운영 감사 기록은 남긴다.
8. 실패 상태에서도 마지막 검증 데이터와 데모 데이터로 P0 핵심 탐색을 재현할 수 있어야 한다.
9. `ACTIVE` 기관의 첫 최종 `FAILED`는 `DEGRADED`, 중간 성공 없는 서로 다른 실행 2회 연속 최종 `FAILED`는 `SUSPENDED`다. Critical 사유는 즉시 중단하고, 선택 구조 문제·단건 예외는 각각 `DEGRADED + UNKNOWN`·레코드 격리로 제한한다. 수정·재승인 후 `PROVISIONAL`로 돌아가 14일·연속 성공·의미 변경 검증을 처음부터 다시 시작한다.

## 11. 품질 게이트와 운영 검토

파이프라인 결과는 다음을 자동 또는 운영 검토로 확인한다.

- 전시명, 시작일, 종료일, 장소, 지역, 유효 상태, 공식 상세 URL, 공식 출처가 모두 확인된 최소 품질 합격과 불합격 격리
- 요금·예약·관람시간·접근성·감각 정보의 근거 없는 추론 금지와 명시적 `UNKNOWN` 보존
- 날짜 역전, 잘못된 행정구역, 음수 가격 등 구조 오류
- 생명주기·최신성·노출 적격성의 독립성
- 권리 미확인 미디어의 표시·데모 포함 여부
- 중복 후보와 사실상 동일한 추천 결과
- 핵심 출처 충돌과 반복 수집 실패
- 현재·예정 전시의 재확인 기한 초과와 `refresh_due_exhibitions`의 due 선택 근거
- 정본과 검색·추천 파생본의 버전 불일치
- 기관별 최근 5건 `CORE_PASS` 수와 구조적 반복 누락·정책·접근 제한 보류 여부
- 기관별 `CANDIDATE`·`PROVISIONAL`·`ACTIVE`·`SUSPENDED` 상태와 전이 사유
- 기관별 `HEALTHY`·`DEGRADED`, 연속 최종 실패 수, 우선 재검증 근거와 Critical·선택 구조·단건 예외 분류
- `PROVISIONAL`·`ACTIVE` 레코드의 동일한 서비스 품질 게이트 적용 여부
- 최초 검증 시작 후 14일, 서로 다른 날짜의 연속 `SUCCESS` 3건, 중간 `FAILED` 0건과 요청 재시도·최종 실행 상태
- 의미 있는 신규·변경의 SourceRecord·정규화·Canonical·ChangeHistory 연결과 raw hash·페이지 외피 변화의 제외
- 승격 시 마지막 `SUCCESS`, Source 정상, 구조적 핵심 필드 누락·정책·접근 문제·미해결 구조 충돌 0건

운영자는 일반 사용자 영역과 분리된 품질 관리 수단에서 이 항목과 최근 `IngestionRun`의 실행 범위를 확인할 수 있어야 한다. 화면과 알림 체계는 후속 UX·운영 문서가 정한다.

## 12. 열린 결정 등록부 참조

| 결정 ID | 파이프라인에 미치는 영향 |
| --- | --- |
| OD-001 | 공개·상업 목적에 따라 수집·보존·표시 전 단계의 법적 검토 강도가 달라진다. |
| OD-002 | 데모 스냅샷과 원본 표현을 저장소에 포함·재배포할 수 있는 범위를 확정한다. |
| OD-003 | 4/5 판정, lifecycle, 승격과 health·중단 기준은 확정됐다. 실제 수집기 대상과 출처별 호출 제한·필드 매핑을 확정한다. |
| OD-006 | P1의 호스팅, 비용 한도와 관측성 운영을 확정한다. P0의 재확인 스케줄러 호출 계약은 이 결정과 별개로 적용한다. |
| OD-007 | 구현 일정·브랜치·리뷰 방식은 파이프라인 의미가 아니라 실행 계획에서 확정한다. |

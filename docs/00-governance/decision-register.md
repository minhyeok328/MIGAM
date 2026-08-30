---
title: "미감 결정 등록부"
status: DRAFT
version: "0.4.0"
last_updated: "2026-08-30"
authoritative_for:
  - "기획 대화에서 확정·폐기·미확정된 결정의 추적"
  - "후반 결정이 대체한 초기안 기록"
related_documents:
  - "./document-policy.md"
  - "../01-product/project-brief.md"
  - "../02-data/source-qualification.md"
---

# 미감 결정 등록부

## 1. 사용법

이 등록부는 전체 기획 대화의 결정을 주제별로 묶어 추적한다. 한 항목이 대화의 질문 하나와 반드시 일치하지는 않는다. 같은 주제를 여러 번 논의했으면 **가장 나중에 명시적으로 확정된 결정**을 `CURRENT`로 기록하고, 이전 안은 `SUPERSEDED`로 남긴다.

- `CURRENT`: 현재 문서가 따라야 하는 결정
- `SUPERSEDED`: 후반 결정으로 폐기된 안
- `OPEN`: 사용자 결정이나 외부 검증이 더 필요한 항목
- `RESOLVED`: 열린 결정이 해소되어 소유 문서에 반영된 상태

## 2. 현재 제품 결정

| ID | 결정 | 소유 문서 |
| --- | --- | --- |
| DEC-001 | 서비스명은 `미감 / 美感 / MIGAM`이며 감각에서 시작하는 발견을 뜻한다. | Project Brief |
| DEC-002 | 메인 슬로건은 `당신의 감각으로, 전시를 발견하다.`이고 보조 문구는 `아는 만큼 보는 대신, 좋아하는 것부터 시작해보세요.`다. | Project Brief, UI Guidelines |
| DEC-003 | 미감은 전시 중심의 대한민국 우선 비회원 큐레이션 서비스다. | Project Brief |
| DEC-004 | 핵심 사용자는 취향에 맞는 전시를 고르기 어려운 일반 관람자이며, 동행 조건을 고려하는 문화 외출 사용자가 보조 사용자다. | Project Brief, P0 PRD |
| DEC-005 | 제품 성공 흐름은 `발견 → 이해 → 판단`이다. | Project Brief, P0 PRD |
| DEC-006 | 홈의 동등한 진입 경로는 `내 취향부터 알아보기`와 `지금 갈 전시 찾기`다. | P0 PRD, User Flows |
| DEC-007 | 데이터 구조는 전국을 수용하되 P0 품질 검증은 서울·경기·인천을 우선한다. | Project Brief, Data Model |
| DEC-008 | 전시는 주 객체이고 작품·소장품과 기관은 취향·맥락 탐색을 돕는 보조 객체다. | Domain Rules, Data Model |
| DEC-009 | 현재·예정 전시는 추천 대상이며 종료 전시는 검색·상세·관심·비교 가능한 아카이브와 취향 근거로 남긴다. | Domain Rules, Recommendation Spec |
| DEC-010 | 일반 사용자 회원가입·로그인·서버 익명 프로필·장기 서버 취향 프로필을 두지 않는다. | P0 PRD, Security & Privacy |
| DEC-011 | 일정·동선·교통·식당·카페·캘린더 계획과 티켓 예매·결제는 제품 범위가 아니다. | Project Brief, P0 PRD |
| DEC-012 | P2 챗봇은 동일한 공식 데이터·필수 조건·출처·권리 정책 위에서만 동작한다. | Roadmap, System Architecture |

## 3. 탐색·검색·관심 결정

| ID | 결정 | 소유 문서 |
| --- | --- | --- |
| DEC-020 | 통합 검색은 전시, 작품·소장품, 기관을 다루며 P0에 독립 작가 탭·상세는 없다. | P0 PRD, User Flows |
| DEC-021 | 검색어가 없을 때 기본 목록은 현재·예정 전시이며 `현재 관람 가능 → 사용자 조건·취향 적합 → 종료 임박 → 예정 시작 임박 → 데이터 품질·정보 완성도` 순으로 우선한다. 검색어가 있으면 종료 전시도 포함하되 관련성 판단 안에서 현재 전시를 우선한다. | P0 PRD, Domain Rules |
| DEC-022 | 키워드 검색은 관련도순이 기본이고 개인화는 보조 신호이며 `추천순`에서 더 강하게 반영한다. 사용자 정렬은 `관련도순`, `추천순`, `최신 시작일순`, `종료 임박순`, `예정 시작일순`이며 현재 상태 필터에 의미가 없는 정렬은 비활성화하거나 전환 사실을 알린다. | P0 PRD, Recommendation Spec, Screen Spec |
| DEC-023 | 목록은 최초 24개를 보여주고 `더 보기`마다 24개를 추가한다. 조건은 URL에 보존하고 중복을 허용하지 않는다. | P0 PRD, Screen Spec |
| DEC-024 | 결과가 0건이어도 필수 조건을 몰래 완화하지 않고, 사용자가 선택할 수 있는 선호 완화만 제안한다. | P0 PRD, Recommendation Spec |
| DEC-025 | 접근성·감각 필수조건은 0건 완화 제안 대상에서도 제외한다. | Domain Rules, Recommendation Spec |
| DEC-026 | `관심 있음`은 전시·작품·기관 저장과 긍정 취향 신호를 겸한다. | P0 PRD, Recommendation Spec |
| DEC-027 | 관심 해제는 긍정 신호 제거일 뿐 부정 평가가 아니다. | Recommendation Spec |
| DEC-028 | 사용자 지정 컬렉션·폴더·공유는 없고 관심 목록은 전시·작품·기관으로 자동 분류한다. | P0 PRD, Screen Spec |
| DEC-029 | 비교는 전시 최대 3개이며 일정표나 순위를 자동 결정하지 않는다. | P0 PRD, Screen Spec |
| DEC-030 | 지도는 선택형 보조 보기이고 목록이 기본이다. 경로 안내는 제공하지 않는다. | P0 PRD, User Flows |

## 4. 취향·추천 결정

| ID | 결정 | 소유 문서 |
| --- | --- | --- |
| DEC-040 | 취향 테스트는 기본 약 8문항, 필요 시 4~6문항을 추가하는 적응형 구조다. | P0 PRD, Recommendation Spec |
| DEC-041 | 테스트는 복수 선택·상황 쌍·매체 선택을 혼합하고 `둘 다`, `잘 모르겠어요`, `건너뛰기`를 허용한다. | P0 PRD, Screen Spec |
| DEC-042 | 테스트 이미지는 재사용 권리가 확인된 실제 자료와 경험 시나리오를 혼합하며 P0에서 오디오·비디오를 직접 재생하지 않는다. | Data Source Policy, Screen Spec |
| DEC-043 | 취향 테스트와 명시적 `관심 있음`만 장기 취향 신호로 사용한다. | Recommendation Spec |
| DEC-044 | 조회·검색·비교·지도·공식 링크 클릭·체류시간은 취향 신호가 아니다. | Recommendation Spec, Security & Privacy |
| DEC-045 | 지역·날짜와 사용자가 지정한 최대 예산·필수 접근성·회피 감각 조건은 하드 필터다. 예약·예상 관람시간도 사용자가 필수 방문 조건으로 명시하면 하드 필터로 처리한다. | Domain Rules, Recommendation Spec |
| DEC-046 | 동행 관계, 분위기, 매체는 소프트 선호다. 예상 관람시간과 예약은 선호로 선택한 경우에만 소프트 선호로 처리한다. | Domain Rules, Recommendation Spec |
| DEC-047 | 추천은 하드 필터, 콘텐츠 유사도, 문맥 보정, 다양성 재정렬, 연결된 탐색 순으로 구성한다. | Recommendation Spec |
| DEC-048 | 대표 추천 약 6개 중 1개는 기존 취향과 한 축 이상 연결된 탐색형 후보를 지향한다. | Recommendation Spec, Evaluation |
| DEC-049 | 사용자에게 적합도 퍼센트를 보여주지 않고 정성 등급과 실제 이유를 보여준다. | Recommendation Spec, UI Guidelines |
| DEC-050 | 카드에는 핵심 이유 1개, 상세에는 최대 3개를 보여주며 실제 계산 기여와 일치해야 한다. | Recommendation Spec, Screen Spec |
| DEC-051 | 취향 데이터가 없으면 품질·다양성 중심 일반 추천을 제공하고 명시적 신호가 쌓일수록 개인화를 강화한다. | Recommendation Spec |
| DEC-052 | 작품 유사성은 P0에서 공식 메타데이터만 사용한다. P1의 `VisualEmbedding`은 권리 허용 미디어와 원본·모델·버전·생성 시점을 추적하는 개념 후보이며 P0에서는 생성·저장·조회·점수 사용하지 않는다. | Data Model, Recommendation Spec, Roadmap |
| DEC-053 | 주제·분위기는 공식 태그와 명시적 규칙에 근거하며 P0에서 자유롭게 추론해 채우지 않는다. 여섯 분위기 태그는 고정된 짧은 사용자 설명과 함께 제공한다. | Domain Rules, Normalization Rules, UI Guidelines |

## 5. 방문 조건과 도메인 결정

| ID | 결정 | 소유 문서 |
| --- | --- | --- |
| DEC-060 | 날짜는 하루 또는 사용자가 직접 지정한 기간만 받으며 빠른 날짜 프리셋은 두지 않는다. | P0 PRD, Domain Rules |
| DEC-061 | 기간 검색은 실제 관람 가능한 날이 하나 이상 겹치면 포함하고, 알려진 휴관일을 적용한다. | Domain Rules |
| DEC-062 | 위치는 시·도→시·군·구 수동 선택이 기본이며 현재 위치는 사용자 동작 후 일시적으로만 사용한다. | P0 PRD, Security & Privacy |
| DEC-063 | 예산 필터는 일반 성인 1인 기본 관람권을 기준으로 한다. | Domain Rules |
| DEC-064 | 상세에는 공식적으로 확인된 주요 가격을 구조화하되 임의 최저가 대표화와 동행자 총액 계산은 하지 않는다. | Domain Rules, Screen Spec |
| DEC-065 | 예약 필요·권장·시간 지정·현장·선착순·프로그램 전용·미확인을 구분하되 실시간 잔여석은 다루지 않는다. | Domain Rules |
| DEC-066 | 예상 관람시간은 공식적으로 확인된 값과 `UNKNOWN`을 구분한다. 공식값이 없을 때 작품 수·영상 길이·유사 전시로 서비스 추정값을 만들지 않는다. | Domain Rules, Normalization Rules |
| DEC-067 | 접근성·감각 정보의 미확인은 `지원 안 함`이 아니라 `확인 필요`다. 사용자가 필수로 지정하면 주요 추천에서 제외한다. | Domain Rules, Screen Spec |
| DEC-068 | 공간 유형과 행사 형식은 별도 분류 축으로 유지한다. 행사 형식의 공식 근거가 없으면 제목·공간 유형·유사 매체로 추론하지 않고 `형식 미확인`으로 표시한다. | Domain Rules, Data Model, Normalization Rules |
| DEC-069 | 같은 작가·기관이라는 이유만으로 작품을 실제 출품작이라고 추정하지 않는다. | Domain Rules, Data Model |

## 6. 데이터·권리 결정

| ID | 결정 | 소유 문서 |
| --- | --- | --- |
| DEC-080 | 공식 API·공공 데이터가 우선이며 허용된 공식 기관 페이지와 공식 보도·공지로 보완한다. | Data Source Policy |
| DEC-081 | 블로그·커뮤니티·리뷰·타 플랫폼 복제·공식 SNS만 있는 행사·접근 통제 우회는 정규 출처로 사용하지 않는다. | Data Source Policy |
| DEC-082 | 운영정보는 기관 공식 페이지, 표준 ID·코드·주소·좌표는 공식 API를 우선한다. | Data Source Policy, Normalization Rules |
| DEC-083 | 원본·표시값·필드별 출처·확인 시각·변경 이력을 보존한다. | Data Model, Data Pipeline |
| DEC-084 | 출처 충돌은 별도 상태로 관리하고 방문 핵심 정보가 해결되지 않으면 개인화 추천에서 제외한다. | Domain Rules, Data Pipeline |
| DEC-085 | 중복 자동 병합은 공식 동일 ID 또는 강한 기간·기관·정규화 제목 근거가 있을 때만 수행한다. 순회전은 별도 레코드로 연결한다. | Normalization Rules |
| DEC-086 | 포스터·공간·작품·인물·영상 썸네일의 권리를 별도로 판단하고 재사용 허용 자료만 화면·테스트에 사용한다. | Data Source Policy |
| DEC-087 | 권리 미확인 자료는 복제·캐시·핫링크하지 않고 텍스트 대체 표현을 사용한다. | Data Source Policy, UI Guidelines |
| DEC-088 | 이미지 부재만으로 전시를 검색·추천에서 제외하지 않는다. | Data Source Policy, Recommendation Spec |
| DEC-089 | 현재 및 7일 이내 예정 전시는 매일, 그 이후 예정 전시는 3일 간격을 기본 재확인 대상으로 두고 종료 전시는 일상 재수집하지 않는다. 출처별 허용 호출 조건과 마지막 성공 시각을 함께 계산하며, P0 수동 실행과 배포 스케줄러는 같은 Django 관리 명령 계약을 사용하고 상시 worker·Celery를 두지 않는다. | Data Pipeline, System Architecture |
| DEC-090 | 수집 실패만으로 기존 데이터를 삭제하지 않으며 최신성·검증 상태로 안전하게 노출을 낮춘다. | Data Pipeline |
| DEC-091 | P0 품질 우선 범위는 2023-01-01 이후 및 현재·예정 전시다. 더 오래된 공식 데이터는 안정적으로 얻을 수 있을 때 보존한다. | Data Source Policy, Data Pipeline |
| DEC-092 | 대표 데모 데이터는 전시 300~500, 작품 500~1,000, 기관 약 100 규모와 주요 예외 상황을 목표로 한다. | Test Plan |
| DEC-093 | `CURRENT`와 시작까지 7일 이내인 `UPCOMING`은 마지막 공식 성공 확인이 48시간 이내일 때만 `FRESH`이며, 그 밖의 `UPCOMING`은 3일 재확인 기한을 적용한다. | Domain Rules, Data Pipeline |
| DEC-094 | P0 기관·출처 allowlist는 데이터 품질과 반복 가능한 확보 가능성을 공동 최우선 기준으로 선정한다. 두 기준을 통과한 후보 사이에서는 지역·기관 유형·콘텐츠 다양성을 보조 기준으로 사용한다. | Data Source Policy, Data Pipeline |
| DEC-095 | OD-003의 최종 기관 allowlist를 정하기 전에 후보 기관마다 공식 출처의 최근 전시 5건을 수동 표본 검토해 전시명·시작일·종료일·장소·지역·유효 상태·공식 상세 URL·공식 출처의 완전성, 최신성, 반복 수집 가능성을 기록한다. | Data Source Policy, Implementation Readiness |
| DEC-096 | 전시 데이터의 최소 품질 합격에는 전시명, 시작일, 종료일, 장소, 지역, `UNKNOWN`이 아닌 유효한 전시 상태, 공식 상세 URL, 공식 출처 확인이 모두 필요하다. 요금·예약·예상 관람시간·접근성·감각 정보는 이 게이트 밖에서 미확인 시 `UNKNOWN`으로 관리하고 추론하지 않으며, 사용자가 해당 정보를 필수 방문 조건으로 지정하면 `UNKNOWN`은 조건을 충족하지 않는다. | Project Brief, Domain Rules, Data Source Policy, Data Model, Data Pipeline, Normalization Rules, Recommendation Spec |
| DEC-097 | 후보 기관의 최근 전시 5건 중 최소 4건이 `CORE_PASS`여야 allowlist 후보 심사를 통과한다. 같은 필수 필드의 반복적·구조적 누락 또는 정책·접근 제한 문제가 확인되면 비율과 무관하게 등록을 보류한다. 심사 통과 기관은 먼저 `PROVISIONAL`로 등록하고 실제 수집 안정성을 추가 검증한 뒤에만 `ACTIVE`로 승격한다. | P0 PRD, Roadmap, Data Source Policy, Data Model, Data Pipeline, System Architecture, Acceptance Criteria, Test Plan, Traceability Matrix, Implementation Readiness |
| DEC-098 | 기관 온보딩 lifecycle은 `CANDIDATE → PROVISIONAL → ACTIVE → SUSPENDED → PROVISIONAL`이다. `PROVISIONAL`도 레코드별 최소 품질·권리·최신성·충돌 게이트를 통과한 데이터는 정상 서비스에 사용할 수 있으며, `ACTIVE`는 최초 검증 시작 후 최소 14일이 지나고 `InstitutionQualificationRun.finished_at`을 `Asia/Seoul`로 환산한 서로 다른 날짜의 최종 성공 실행 3회가 중간 `FAILED` 없이 연속되며 그중 1회 이상 승인된 의미 있는 신규·변경 전시가 `SourceRecord → 정규화 → Canonical Exhibition → ChangeHistory`까지 반영된 고신뢰 상태다. P0 의미 변경은 새 전시, 종료일 변경·연장, 요금·장소·예약 방식 변경, 전시 취소, 공식 설명에서 승인·버전 고정 정규화 규칙이 만든 Canonical 필드 변경만 인정하며 페이지 외피·raw hash만의 변화는 인정하지 않는다. 세 실행의 치명적 수집 실패·구조적 핵심 필드 누락·정책·robots·약관 문제·CAPTCHA·로그인 요구·지속 접근 차단은 모두 0건이어야 하며, 승격 순간에는 마지막 실행 성공·Source 정상·미해결 구조 충돌 0건을 다시 확인한다. 요청 재시도 후 최종 성공은 성공으로 인정하지만 핵심 대상 페이지 최종 미수집이나 미완성 핵심 데이터의 Canonical 반영은 최종 `FAILED`다. `ACTIVE` 운영 실패와 중단 판정은 `DEC-099`를 따르며, 중단 사유를 수정한 뒤 `PROVISIONAL`에서 검증을 처음부터 다시 시작한다. | P0 PRD, Roadmap, Data Source Policy, Data Model, Data Pipeline, Normalization Rules, Recommendation Spec, System Architecture, API Guidelines, Security & Privacy, Acceptance Criteria, Test Plan, Traceability Matrix, Implementation Readiness |
| DEC-099 | InstitutionAllowlistEntry의 수집 `health = HEALTHY \| DEGRADED`는 lifecycle과 Source 운영 상태에서 분리한다. `ACTIVE` 기관의 허용 재시도를 모두 소진한 기관별 최종 `FAILED` 1회는 lifecycle을 유지한 채 `DEGRADED`, 연속 실패 수 1, 출처 호출 제한·backoff 안의 최우선 재검증으로 처리한다. 중간 기관별 최종 `SUCCESS` 없이 서로 다른 IngestionRun ID에 속한 해당 기관의 InstitutionRunResult 2개가 연속 `FAILED`이면 `SUSPENDED`로 전환하며, 기관별 최종 `SUCCESS`는 실패 수를 0으로 초기화하고 미해결 선택 필드 구조 문제가 없을 때 `HEALTHY`로 복구한다. `POLICY_BLOCK`은 약관상 자동 수집 불허 또는 중대한 변경의 미해결 불명확성, robots 대상 경로 금지이고, `ACCESS_BLOCK`은 CAPTCHA·로그인 필수·한 실행 안의 반복 403/bot 차단·접근 통제 우회 필요이며, `STRUCTURAL_CRITICAL`은 최소 품질 핵심 필드의 기관·템플릿 수준 안정적 추출 불가, 핵심 오값 대량 생성 위험, 목록과 상세의 신뢰 가능한 연결 상실이다. 이 Critical 사유는 실패 횟수와 관계없이 `ACTIVE → SUSPENDED`다. 실행 중 확인된 Critical은 영향 기관의 InstitutionRunResult를 최종 `FAILED`로 기록하고 `ACTIVE` 실패 수를 기존 0에서 1 또는 1에서 2로 올리되 중단 판정은 수치를 기다리지 않는다. `PROVISIONAL`에서는 lifecycle을 임의 전이하지 않고 미해결 Critical CollectionIssue를 수집 전 차단 게이트로 사용하며, 실행 중 확인됐다면 InstitutionQualificationRun도 `FAILED`로 기록해 승격 연속 성공을 초기화한다. 실행 밖 검토로 발견한 Critical은 가상 실패 실행이나 실패 수를 만들지 않는다. 모든 Critical의 영향 범위는 기관 단위가 기본이며 Source 전체 근거가 있을 때만 공유 Source 전체로 넓힌다. 요금·예약·관람시간·접근성·감각·미디어 같은 선택 필드 구조 문제는 값을 `UNKNOWN`으로 두고 `DEGRADED`를 유지하며 실행 실패 수를 올리지 않는다. 가져온 단일 전시의 예외는 해당 레코드만 격리하고 기관 health·lifecycle을 바꾸지 않되, 반복·기관 수준 패턴이면 `STRUCTURAL_CRITICAL`로 재분류한다. | Project Brief, P0 PRD, Roadmap, Domain Rules, Data Source Policy, Data Model, Data Pipeline, Normalization Rules, Recommendation Spec, System Architecture, API Guidelines, Security & Privacy, Acceptance Criteria, Test Plan, Traceability Matrix, Implementation Readiness |

## 7. UX·기술·품질 결정

| ID | 결정 | 소유 문서 |
| --- | --- | --- |
| DEC-100 | 반응형 한국어 웹이며 제한된 공식 영문 제목만 보조 표시한다. 다국어 UI는 P0에서 제외한다. | UI Guidelines |
| DEC-101 | 디자인은 따뜻한 중성색, Serif 제목과 Sans UI, 얇은 선, 넓은 여백, 절제된 모션을 사용한다. | UI Guidelines |
| DEC-102 | 이미지가 없는 카드도 정보 위계가 떨어지지 않는 편집형 텍스트 카드로 제공한다. | UI Guidelines, Screen Spec |
| DEC-103 | 웹 접근성은 키보드·포커스·대체텍스트·텍스트 상태·대비·모션 감소·확대·터치 사용을 포함한다. | UI Guidelines, Acceptance Criteria |
| DEC-104 | P0 기술은 React·TypeScript·Vite, Django·DRF, Python 파이프라인, SQLite, Kakao 지도 조합이다. | System Architecture |
| DEC-105 | 검색과 지도는 각각 SearchService와 MapProvider 경계로 교체 가능하게 만든다. P0 검색은 SQLite FTS5다. | System Architecture |
| DEC-106 | 서버 상태는 TanStack Query, 클라이언트 상태는 Zustand, 지속 개인 데이터는 버전 있는 브라우저 저장소가 담당한다. | System Architecture |
| DEC-107 | OpenAPI를 네트워크 계약 기준으로 삼고 생성 타입과 경계 검증을 사용한다. | API Guidelines |
| DEC-108 | 프론트는 npm, 백엔드는 uv를 사용하며 네이티브 실행과 재현 가능한 컨테이너 실행을 지원한다. | System Architecture |
| DEC-109 | 일반 사용자 인증은 없고 운영자만 Django staff/superuser 인증을 사용한다. | Security & Privacy |
| DEC-110 | 외부 사용자 행동 분석 도구를 사용하지 않고 원문 검색어·정확 좌표·추천 취향 payload를 장기 로그에 남기지 않는다. | Security & Privacy |
| DEC-111 | 데이터·추천·API·프론트·E2E·접근성·주요 브라우저 검증을 계층별로 수행한다. | Test Plan |
| DEC-112 | 필수조건 위반, 종료·검증불가 오추천, 중복, 이유 불일치, 권리 미확인 이미지 노출은 0건이어야 한다. | Acceptance Criteria, Recommendation Evaluation |
| DEC-113 | 단일 monorepo에서 정본 도메인·API·운영 기능은 `backend/apps/`, 수집·정규화·중복·권리·최신성·품질 처리는 `backend/data_pipeline/`에 둔다. 데이터 파이프라인은 정본을 임의로 직접 덮어쓰지 않는다. | System Architecture, Implementation Readiness |
| DEC-114 | 프론트 UI는 Tailwind CSS, Radix UI primitive 직접 사용 또는 Radix 기반 shadcn/ui 컴포넌트, Lucide React로 구현한다. 같은 역할의 primitive 전략은 작업 단위에서 하나로 정하고 미감 시각 지침으로 스타일링한다. | System Architecture, UI Guidelines |
| DEC-115 | `/admin/`은 staff 운영자용 Django Admin CRUD이고 `/admin/data-status/`는 품질 현황을 요약해 관련 Admin 레코드로 연결하는 staff 전용 최소 대시보드다. | System Architecture, Security & Privacy, Acceptance Criteria |
| DEC-116 | P0 행동 이벤트 계약은 개발·테스트 어댑터에서 허용된 이름과 최소 속성만 검증한다. 외부 전송·영속 저장·사용자 식별·취향 학습은 하지 않고 운영 빌드에서는 아무 작업도 하지 않는다. | P0 PRD, Security & Privacy, Test Plan |

## 8. 폐기된 초기 결정

| ID | 상태 | 폐기된 안 | 대체 결정 |
| --- | --- | --- | --- |
| SUP-001 | `SUPERSEDED` | 소프트웨어 의존성 위험 분석을 프로젝트 도메인으로 선택 | DEC-003 |
| SUP-002 | `SUPERSEDED` | 식물 관리 서비스를 우선 도메인으로 선택 | DEC-003 |
| SUP-003 | `SUPERSEDED` | 작품·소장품 추천이 P0의 중심 | DEC-008 |
| SUP-004 | `SUPERSEDED` | 익명 서버 프로필과 쿠키 기반 개인화 | DEC-010 |
| SUP-005 | `SUPERSEDED` | P1 회원가입·OAuth·익명 데이터 계정 병합 | DEC-010 |
| SUP-006 | `SUPERSEDED` | 조회·검색·체류시간을 취향 신호로 사용 | DEC-043, DEC-044 |
| SUP-007 | `SUPERSEDED` | `봤어요`, `관심 없음`, 별도 취향 버튼, 부정 학습 | DEC-026, DEC-027 |
| SUP-008 | `SUPERSEDED` | 사용자 컬렉션·폴더·공유 | DEC-028 |
| SUP-009 | `SUPERSEDED` | 자동 일정·동선 계획을 후속 기본 기능으로 확장 | DEC-011 |
| SUP-010 | `SUPERSEDED` | 지도와 접근성 정보를 P1로 미룸 | DEC-030, DEC-067, DEC-103 |
| SUP-011 | `SUPERSEDED` | 현재·예정 전시만 제공하고 종료 전시 검색을 제외 | DEC-009, DEC-021 |
| SUP-012 | `SUPERSEDED` | 공식 예상 관람시간이 없을 때 객관 근거를 조합해 `미감 추정` 참고 범위를 제공 | DEC-066, DEC-096 |
| SUP-013 | `SUPERSEDED` | `PROVISIONAL` 기관은 원본·검증 이력만 만들고 정본·검색·추천·사용자 서비스에 사용할 수 없음 | DEC-098 |

## 9. 열린 결정

| ID | 상태 | 결정이 필요한 내용 | 영향 문서 |
| --- | --- | --- | --- |
| OD-001 | `OPEN` | P0를 개인 로컬 포트폴리오로만 사용할지, 비영리 공개 또는 향후 상업 공개까지 고려할지 | Data Source Policy, Security & Privacy |
| OD-002 | `OPEN` | Git 저장소 공개 여부와 MIT 코드 라이선스 외에 문서·데모 데이터 재배포 조건을 어떻게 둘지 | README, Data Source Policy |
| OD-003 | `RESOLVED` | 세종문화회관 본관 전시공간·서울시립 서서울미술관·서울시립 사진미술관·수원시립미술관 행궁 본관·국립민속박물관 서울 본관과 공식 Source 3개를 P0 allowlist로 확정 | P0 PRD, Roadmap, Data Source Policy, Data Model, Data Pipeline, System Architecture, Acceptance Criteria, Test Plan, Traceability Matrix, Implementation Readiness |
| OD-004 | `OPEN` | 타이포그래피형 워드마크와 별도 로고 중 무엇을 채택하고 Serif·Sans 최종 폰트를 무엇으로 할지 | UI Guidelines |
| OD-005 | `OPEN` | P0 API를 내부 소비 전용으로 유지할지 제3자 공개 API까지 제공할지 | API Guidelines, Security & Privacy |
| OD-006 | `OPEN` | P1 호스팅 대상, 월 비용 한도, 도메인, 오류 모니터링과 최소 분석 허용 범위 | Roadmap, System Architecture |
| OD-007 | `OPEN` | 구현 마감일, 동시 작업 에이전트 수, 브랜치·리뷰·병합 방식 | Implementation Readiness |

열린 결정은 현재 초안 작성을 막지 않지만 관련 문서를 `APPROVED`로 올리기 전에 해결해야 한다.

`OD-003`의 `2026-08-30` 검증 결과와 보류 근거는 [P0 Source Qualification](../02-data/source-qualification.md)에, 실행 설정은 [`sources.yaml`](../../sources.yaml)에, 25개 표본은 [고정 fixture](../../fixtures/source-qualification.json)에 기록한다. 세종문화회관 본관 전시공간·서울시립 서서울미술관·서울시립 사진미술관·수원시립미술관 행궁 본관은 `5/5`, 국립민속박물관 서울 본관은 `4/5`로 승인했다. 서울 열린데이터광장 기반 3곳은 공공누리 제1유형 공식 HTTPS CSV Sheet, 경기·국립박물관 두 곳은 이용허락 제한 없는 문화정보 HTTPS API를 사용하며 이미지·장문 설명은 제외한다. 다섯 곳의 첫 lifecycle은 `PROVISIONAL`이다. 서울 HTTP Open API는 HTTPS 미지원으로 정식 키를 사용하지 않으며, MMCA 서울·서울공예박물관·대한민국역사박물관·예술의전당 제7전시실·서울역사박물관 등 보류 후보는 `HOLD`로 남긴다.

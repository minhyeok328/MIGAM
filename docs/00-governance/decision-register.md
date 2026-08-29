---
title: "미감 결정 등록부"
status: DRAFT
version: "0.1.0"
last_updated: "2026-08-29"
authoritative_for:
  - "기획 대화에서 확정·폐기·미확정된 결정의 추적"
  - "후반 결정이 대체한 초기안 기록"
related_documents:
  - "./document-policy.md"
  - "../01-product/project-brief.md"
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
| DEC-021 | 검색어가 없을 때 기본 목록은 현재·예정 전시이고, 검색어가 있으면 종료 전시도 포함하되 현재 전시를 우선한다. | P0 PRD, Domain Rules |
| DEC-022 | 관련도 정렬을 기본으로 하고 개인화는 보조 신호이며 `추천순`에서 더 강하게 반영한다. | P0 PRD, Recommendation Spec |
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
| DEC-045 | 지역·날짜와 사용자가 지정한 최대 예산·필수 접근성·회피 감각 조건은 하드 필터다. | Domain Rules, Recommendation Spec |
| DEC-046 | 동행 관계, 분위기, 매체, 관람시간, 예약 선호는 소프트 선호다. | Domain Rules, Recommendation Spec |
| DEC-047 | 추천은 하드 필터, 콘텐츠 유사도, 문맥 보정, 다양성 재정렬, 연결된 탐색 순으로 구성한다. | Recommendation Spec |
| DEC-048 | 대표 추천 약 6개 중 1개는 기존 취향과 한 축 이상 연결된 탐색형 후보를 지향한다. | Recommendation Spec, Evaluation |
| DEC-049 | 사용자에게 적합도 퍼센트를 보여주지 않고 정성 등급과 실제 이유를 보여준다. | Recommendation Spec, UI Guidelines |
| DEC-050 | 카드에는 핵심 이유 1개, 상세에는 최대 3개를 보여주며 실제 계산 기여와 일치해야 한다. | Recommendation Spec, Screen Spec |
| DEC-051 | 취향 데이터가 없으면 품질·다양성 중심 일반 추천을 제공하고 명시적 신호가 쌓일수록 개인화를 강화한다. | Recommendation Spec |
| DEC-052 | 작품 유사성은 P0에서 공식 메타데이터를 사용하며 이미지 임베딩은 권리가 허용되는 후속 후보로 남긴다. | Recommendation Spec, Roadmap |
| DEC-053 | 주제·분위기는 공식 태그와 명시적 규칙에 근거하며 P0에서 LLM이 자유롭게 해석해 채우지 않는다. | Domain Rules, Normalization Rules |

## 5. 방문 조건과 도메인 결정

| ID | 결정 | 소유 문서 |
| --- | --- | --- |
| DEC-060 | 날짜는 하루 또는 사용자가 직접 지정한 기간만 받으며 빠른 날짜 프리셋은 두지 않는다. | P0 PRD, Domain Rules |
| DEC-061 | 기간 검색은 실제 관람 가능한 날이 하나 이상 겹치면 포함하고, 알려진 휴관일을 적용한다. | Domain Rules |
| DEC-062 | 위치는 시·도→시·군·구 수동 선택이 기본이며 현재 위치는 사용자 동작 후 일시적으로만 사용한다. | P0 PRD, Security & Privacy |
| DEC-063 | 예산 필터는 일반 성인 1인 기본 관람권을 기준으로 한다. | Domain Rules |
| DEC-064 | 상세에는 공식적으로 확인된 주요 가격을 구조화하되 임의 최저가 대표화와 동행자 총액 계산은 하지 않는다. | Domain Rules, Screen Spec |
| DEC-065 | 예약 필요·권장·시간 지정·현장·선착순·프로그램 전용·미확인을 구분하되 실시간 잔여석은 다루지 않는다. | Domain Rules |
| DEC-066 | 예상 관람시간은 공식·근거 있는 추정·미확인을 구분하고 추정은 범위와 라벨을 함께 표시한다. | Domain Rules |
| DEC-067 | 접근성·감각 정보의 미확인은 `지원 안 함`이 아니라 `확인 필요`다. 사용자가 필수로 지정하면 주요 추천에서 제외한다. | Domain Rules, Screen Spec |
| DEC-068 | 공간 유형과 행사 형식은 별도 분류 축으로 유지한다. | Domain Rules, Data Model |
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
| DEC-089 | 현재 및 7일 이내 전시는 매일, 그 이후 예정 전시는 3일 간격을 기본 재확인 후보로 두고 종료 전시는 일상 재수집하지 않는다. | Data Pipeline |
| DEC-090 | 수집 실패만으로 기존 데이터를 삭제하지 않으며 최신성·검증 상태로 안전하게 노출을 낮춘다. | Data Pipeline |
| DEC-091 | P0 품질 우선 범위는 2023-01-01 이후 및 현재·예정 전시다. 더 오래된 공식 데이터는 안정적으로 얻을 수 있을 때 보존한다. | Data Source Policy, Data Pipeline |
| DEC-092 | 대표 데모 데이터는 전시 300~500, 작품 500~1,000, 기관 약 100 규모와 주요 예외 상황을 목표로 한다. | Test Plan |

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

## 9. 열린 결정

| ID | 상태 | 결정이 필요한 내용 | 영향 문서 |
| --- | --- | --- | --- |
| OD-001 | `OPEN` | P0를 개인 로컬 포트폴리오로만 사용할지, 비영리 공개 또는 향후 상업 공개까지 고려할지 | Data Source Policy, Security & Privacy |
| OD-002 | `OPEN` | Git 저장소 공개 여부와 MIT 코드 라이선스 외에 문서·데모 데이터 재배포 조건을 어떻게 둘지 | README, Data Source Policy |
| OD-003 | `OPEN` | 공공 API와 함께 P0에 포함할 수도권 공식 기관 5~10곳의 최종 allowlist | Data Source Policy, Data Pipeline |
| OD-004 | `OPEN` | 타이포그래피형 워드마크와 별도 로고 중 무엇을 채택하고 Serif·Sans 최종 폰트를 무엇으로 할지 | UI Guidelines |
| OD-005 | `OPEN` | P0 API를 내부 소비 전용으로 유지할지 제3자 공개 API까지 제공할지 | API Guidelines, Security & Privacy |
| OD-006 | `OPEN` | P1 호스팅 대상, 월 비용 한도, 도메인, 오류 모니터링과 최소 분석 허용 범위 | Roadmap, System Architecture |
| OD-007 | `OPEN` | 구현 마감일, 동시 작업 에이전트 수, 브랜치·리뷰·병합 방식 | Implementation Readiness |

열린 결정은 현재 초안 작성을 막지 않지만 관련 문서를 `APPROVED`로 올리기 전에 해결해야 한다.

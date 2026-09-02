# 미감(美感 / MIGAM)

> 당신의 감각으로, 전시를 발견하다.

미감은 사용자의 시각·청각·공간·상호작용 취향과 실제 관람 조건을 바탕으로 국내 전시를 발견하고 이해·비교하도록 돕는 대한민국 우선 큐레이션 서비스입니다.

## 현재 상태

이 저장소는 현재 **P0 데이터 신뢰·내부 검색 구현 단계**입니다. Project Brief와 Domain Rules, Source Qualification, Source Registry, [`TP-001 기관 운영 상태와 수집 전 게이트`](docs/07-execution/task-packets/TP-001-institution-collection-gate.md), [`TP-002 기관 ACTIVE 승격 증거와 자동 전이`](docs/07-execution/task-packets/TP-002-institution-active-promotion.md), [`TP-003 선택 관람 정보와 미디어 권리 모델`](docs/07-execution/task-packets/TP-003-visit-information-and-media-rights.md), [`TP-004 내부 OpenAPI와 FTS5 검색`](docs/07-execution/task-packets/TP-004-internal-search-openapi.md)이 승인됐고 나머지 P0 PRD·추천·UX·기술·품질 문서는 계속 검토 중입니다.

- Django 기반으로 승인 Source 3개·기관 5곳의 수집, 최소 품질 검사·격리, 원본·후보 보존, 정본 병합·충돌 증거, 전시 최신성 재확인이 구현돼 있습니다.
- Source·기관 운영 상태와 CollectionIssue를 DB에 멱등 부트스트랩하고, `PROVISIONAL`·`ACTIVE` + 정상 Source + 미해결 Critical 없음 조건을 세 변경 명령이 수집 전과 성공 확정 직전에 공통으로 검사합니다.
- 기관별 실행 결과와 `ACTIVE` 첫 실패 `DEGRADED`·두 번째 실패 또는 Critical 즉시 `SUSPENDED`, 전이 근거, `PROVISIONAL` 실패 counter 0, 성공 복구와 성공 확정의 원자성이 구현돼 있습니다.
- `sync_exhibitions --qualification`은 승인 표본 처리 결과와 Canonical ChangeHistory를 기관별 QualificationRun에 묶고, 14일·서로 다른 서울 날짜 3회 연속 성공·의미 변경·최종 veto를 통과한 기관만 PromotionEvidence와 함께 `ACTIVE`로 승격합니다.
- TP-003은 요금·예약·예상 관람시간·접근성·감각 정보의 `UNKNOWN` 정본과 미디어 권리 이력·안전한 이미지 노출 판정을 구현합니다.
- TP-004는 전시·기관 `SearchService`, SQLite FTS5 파생 인덱스, `/api/internal/v1/search/`와 [`OpenAPI 3.1 계약`](openapi/internal-v1.yaml)을 구현합니다. 정본화 성공 시 인덱스가 자동 갱신되며 `uv run --project backend python backend/manage.py rebuild_search_index`로 전체 재구축할 수 있습니다.
- 자동 테스트는 외부 API 키 없이 `uv run --project backend python backend/manage.py test tests --verbosity 1`로 실행합니다.
- 아직 작품·작가 정본과 검색, 추천, staff Admin 상태 화면, React 프론트엔드는 구현되지 않았습니다.
- 후속 구현도 해당 범위를 직접 정의·검증하는 승인 작업 패킷이 필요합니다.
- 열린 결정은 [결정 등록부](docs/00-governance/decision-register.md)에 기록합니다.
- 전체 문서와 권한은 [문서 인덱스](docs/00-index.md)에서 확인할 수 있습니다.

## 제품 범위 요약

- `내 취향부터 알아보기`와 `지금 갈 전시 찾기`의 두 진입 경로
- 현재·예정 전시 추천과 종료 전시 아카이브
- 전시 중심 탐색, 작품·소장품과 기관 보조 탐색
- 취향 테스트와 명시적 관심만 사용하는 설명 가능한 개인화
- 지역·날짜·예산·접근성·감각 안전 조건을 지키는 추천
- 관심 저장, 최대 3개 비교, 선택형 지도, 공식 페이지 연결
- 공식 출처·최신성·불확실성·미디어 권리 표시
- 계정 없이 브라우저에 저장하고 사용자가 초기화하는 개인화

회원가입, 티켓 예매·결제, 일정·동선 계획, 커뮤니티, 암묵적 행동 추적은 현재 범위에 포함하지 않습니다.

## 문서 읽기 순서

1. [Project Brief](docs/01-product/project-brief.md)
2. [P0 PRD](docs/01-product/prd-p0.md)
3. [Domain Rules](docs/01-product/domain-rules.md)
4. 데이터·추천·UX 명세
5. 기술·보안 명세
6. 합격 기준·테스트·추적성 문서
7. 구현 준비도와 작업 패킷 양식

자세한 경로와 각 문서의 권한은 [문서 인덱스](docs/00-index.md)를 기준으로 합니다.

## 기여와 변경

- 문서를 변경하기 전에 [문서 관리 정책](docs/00-governance/document-policy.md)과 [AGENTS.md](AGENTS.md)를 확인합니다.
- 하위 문서에서 제품 범위나 도메인 규칙을 임의로 바꾸지 않습니다.
- `DRAFT`의 열린 결정을 구현 기본값으로 추측하지 않습니다.
- 사용자 변경과 관련 없는 파일을 덮어쓰거나 정리하지 않습니다.

## 라이선스와 데이터 권리

저장소의 코드는 [MIT License](LICENSE)를 따릅니다. 문서, 데모 데이터, 외부 전시 데이터와 미디어의 재배포 조건은 코드 라이선스와 별개이며 `OD-001`, `OD-002`, `OD-003` 결정 및 각 원출처의 약관·권리를 따라야 합니다.

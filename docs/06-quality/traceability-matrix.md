---
title: "미감 P0 요구사항 추적성 매트릭스"
status: DRAFT
version: "0.3.4"
last_updated: "2026-09-03"
authoritative_for:
  - "P0 요구사항과 결정·화면·합격 기준·테스트의 연결"
  - "요구사항 누락과 고아 테스트의 식별"
  - "P0 비범위 회귀 방지 추적"
related_documents:
  - "../00-governance/decision-register.md"
  - "../01-product/prd-p0.md"
  - "../04-ux/user-flows.md"
  - "../04-ux/screen-spec.md"
  - "./acceptance-criteria.md"
  - "./test-plan.md"
---

# 미감 P0 요구사항 추적성 매트릭스

## 1. 사용법

이 문서는 `prd-p0.md`의 실제 `P0-FR-*`, `P0-NFR-*`, `P0-OUT-*`를 기준으로 다음 연결을 추적한다.

```text
제품 결정(DEC) → 기능 요구사항(FR) → 화면(UX) → 합격 기준(AC) → 테스트(TEST)
```

- 범위 표기 `P0-FR-001~006`은 시작과 끝을 포함한 모든 요구사항을 뜻한다. `P0-NFR-*`와 `P0-OUT-*`도 같은 규칙을 사용한다.
- 한 요구사항이 여러 계층에서 검증되면 관련 `TEST-###`를 모두 연결한다.
- 운영자 영역처럼 일반 사용자 화면 ID가 없는 요구사항은 `해당 없음`으로 명시한다.
- PRD 요구사항을 추가·변경할 때 같은 변경에서 이 매트릭스와 연결된 합격 기준·테스트를 갱신한다.
- 구현된 범위는 실제 존재하는 테스트 파일과 승인 작업 패킷을 아래 구현 증거에 연결한다. 문서상 계획만 있고 코드가 없는 범위는 구현 완료로 표시하지 않는다.

## 2. 공통 상태·홈

| 요구사항 ID | 기능 요약 | 결정 | 화면 | 합격 기준 | 테스트 |
| --- | --- | --- | --- | --- | --- |
| `P0-FR-001` | 계정·로그인 없는 P0 핵심 기능 | `DEC-010` | `UX-001`~`UX-013` | `AC-001` | `TEST-016`, `TEST-017`, `TEST-035` |
| `P0-FR-002` | 취향·관심·최근 본 전시의 브라우저 유지 | `DEC-010`, `DEC-026` | `UX-002`, `UX-003`, `UX-009`, `UX-013` | `AC-011`, `AC-014` | `TEST-013`, `TEST-020`~`TEST-022`, `TEST-026` |
| `P0-FR-003~004` | 서버 개인 프로필·장기 암묵 신호 금지 | `DEC-010`, `DEC-043`, `DEC-044`, `DEC-110` | `UX-002`, `UX-009`, `UX-011`, `UX-013` | `AC-011`, `AC-014` | `TEST-008`, `TEST-026` |
| `P0-FR-005` | 브라우저 저장 버전·손상 회복 | `DEC-106` | `UX-012` | `AC-014`, `AC-018` | `TEST-013` |
| `P0-FR-006` | 동등한 두 진입 경로 | `DEC-006` | `UX-001` | `AC-001` | `TEST-016`, `TEST-017` |
| `P0-FR-007~008` | 비개인화 기본값과 점진적 개인화 | `DEC-051` | `UX-001` | `AC-008` | `TEST-008`, `TEST-009`, `TEST-016` |
| `P0-FR-009` | 추천 6개·다양성·연결된 탐색 | `DEC-048`, `DEC-051` | `UX-001` | `AC-008` | `TEST-009`, `TEST-016` |
| `P0-FR-010~011` | 전시 소식·매체별 탐색 | `DEC-009`, `DEC-051` | `UX-001`, `UX-004` | `AC-008` | `TEST-014`, `TEST-016`, `TEST-018` |

## 3. 취향 테스트와 결과

| 요구사항 ID | 기능 요약 | 결정 | 화면 | 합격 기준 | 테스트 |
| --- | --- | --- | --- | --- | --- |
| `P0-FR-012~014` | 적응형 문항·혼합 응답·유보 | `DEC-040`, `DEC-041` | `UX-002` | `AC-002` | `TEST-016`, `TEST-032`, `TEST-033` |
| `P0-FR-015~016` | 권리 확인 자료·오디오/영상 비재생 | `DEC-042`, `DEC-086`, `DEC-087` | `UX-002` | `AC-002`, `AC-015` | `TEST-005`, `TEST-016`, `TEST-027` |
| `P0-FR-017` | 기본 단계 이후 결과 보기 | `DEC-040`, `DEC-041` | `UX-002` | `AC-002` | `TEST-016` |
| `P0-FR-018~019` | 정성 결과·실제 근거 | `DEC-049`, `DEC-050` | `UX-003` | `AC-003` | `TEST-008`, `TEST-009`, `TEST-016` |
| `P0-FR-020` | 취향 후보와 방문 추천 구분 | `DEC-045`, `DEC-051` | `UX-003`, `UX-004` | `AC-003` | `TEST-016`, `TEST-017` |
| `P0-FR-021` | 최신 재테스트·관심 유지 | `DEC-026`, `DEC-043` | `UX-002`, `UX-003`, `UX-012` | `AC-003`, `AC-014` | `TEST-008`, `TEST-013`, `TEST-016` |

## 4. 조건 기반 전시 찾기

| 요구사항 ID | 기능 요약 | 결정 | 화면 | 합격 기준 | 테스트 |
| --- | --- | --- | --- | --- | --- |
| `P0-FR-022~025` | 지역·날짜 입력과 위치 opt-in | `DEC-060`, `DEC-062` | `UX-004` | `AC-004` | `TEST-011`, `TEST-017`, `TEST-024` |
| `P0-FR-026` | 기간 겹침·휴관·취소 판정 | `DEC-061` | `UX-004`, `UX-006` | `AC-004` | `TEST-001`, `TEST-002`, `TEST-011`, `TEST-017` |
| `P0-FR-027` | 성인 1인 기본권 예산 | `DEC-063` | `UX-004`, `UX-006` | `AC-004`, `AC-009` | `TEST-001`, `TEST-012`, `TEST-017` |
| `P0-FR-028~031` | 동행·분위기·매체·공간·행사 형식·상세 조건과 예약·예상 관람시간 모드 | `DEC-045`, `DEC-046`, `DEC-053`, `DEC-067`, `DEC-068`, `DEC-096` | `UX-004` | `AC-004`, `AC-005`, `AC-024` | `TEST-001`, `TEST-006`, `TEST-007`, `TEST-017`, `TEST-040` |
| `P0-FR-032~034` | 하드 필터·선호 분리·자동 완화 금지 | `DEC-045`, `DEC-046`, `DEC-096` | `UX-004` | `AC-005`, `AC-006`, `AC-024` | `TEST-006`, `TEST-007`, `TEST-017`, `TEST-040` |
| `P0-FR-035~037` | 조건별 미확인 정보 처리 | `DEC-024`, `DEC-025`, `DEC-067`, `DEC-068`, `DEC-096` | `UX-004`, `UX-006` | `AC-005`, `AC-006`, `AC-024` | `TEST-006`, `TEST-007`, `TEST-012`, `TEST-017`, `TEST-040` |

## 5. 검색·추천

| 요구사항 ID | 기능 요약 | 결정 | 화면 | 합격 기준 | 테스트 |
| --- | --- | --- | --- | --- | --- |
| `P0-FR-038~039` | 통합검색 유형과 작가명 검색 | `DEC-020` | `UX-005`, `UX-007`, `UX-008` | `AC-007` | `TEST-011`, `TEST-018` |
| `P0-FR-040~042` | 기본 상태·키워드 전체 상태·관련도·상태별 정렬 | `DEC-021`, `DEC-022` | `UX-004`, `UX-005` | `AC-007` | `TEST-009`, `TEST-011`, `TEST-018`, `TEST-023` |
| `P0-FR-043~045` | 필터·URL 복원·24개 더 보기 | `DEC-023` | `UX-004` | `AC-007`, `AC-018` | `TEST-011`, `TEST-014`, `TEST-018`, `TEST-026` |
| `P0-FR-046` | 0건 사용자 주도 완화 | `DEC-024`, `DEC-025` | `UX-004` | `AC-006` | `TEST-011`, `TEST-014`, `TEST-017` |
| `P0-FR-047~048` | 비개인화 기본값·점진적 개인화 | `DEC-051` | `UX-001`, `UX-003`, `UX-004` | `AC-008` | `TEST-008`, `TEST-009`, `TEST-016`, `TEST-017` |
| `P0-FR-049~050` | 정성 등급·실제 이유 수 | `DEC-049`, `DEC-050` | `UX-001`, `UX-003`, `UX-006` | `AC-008` | `TEST-009`, `TEST-012`, `TEST-016` |
| `P0-FR-051~052` | 중복·과집중 제한과 이유 일치 | `DEC-047`, `DEC-048`, `DEC-050` | `UX-001`, `UX-004`, `UX-006` | `AC-008` | `TEST-009`, `TEST-012`, `TEST-016` |

## 6. 상세 화면

| 요구사항 ID | 기능 요약 | 결정 | 화면 | 합격 기준 | 테스트 |
| --- | --- | --- | --- | --- | --- |
| `P0-FR-053~054` | 전시 핵심·방문·출처 정보 | `DEC-050`, `DEC-064`, `DEC-065`, `DEC-066`, `DEC-067`, `DEC-096` | `UX-006` | `AC-009`, `AC-024` | `TEST-012`, `TEST-018`, `TEST-040` |
| `P0-FR-055~057` | 가격·예약 상세와 금지된 추정 | `DEC-063`, `DEC-064`, `DEC-065` | `UX-006` | `AC-009` | `TEST-001`, `TEST-012`, `TEST-018` |
| `P0-FR-058`, `P0-FR-060` | 공식 설명 구분·출품 관계 확인 | `DEC-053`, `DEC-069` | `UX-006`, `UX-007` | `AC-009`, `AC-010` | `TEST-004`, `TEST-012`, `TEST-018` |
| `P0-FR-059` | 종료 전시 상세·현재 대안 | `DEC-009`, `DEC-090` | `UX-006` | `AC-009`, `AC-016` | `TEST-002`, `TEST-015`, `TEST-023` |
| `P0-FR-061~063` | 작품 정보·메타데이터 유사 탐색 | `DEC-008`, `DEC-052`, `DEC-069` | `UX-007` | `AC-010`, `AC-022` | `TEST-005`, `TEST-012`, `TEST-021`, `TEST-037` |
| `P0-FR-064~065` | 기관 방문 정보·근거 있는 전시 집계 | `DEC-008` | `UX-008` | `AC-010` | `TEST-012`, `TEST-022` |

## 7. 관심·최근·비교·지도

| 요구사항 ID | 기능 요약 | 결정 | 화면 | 합격 기준 | 테스트 |
| --- | --- | --- | --- | --- | --- |
| `P0-FR-066~067` | 하나의 관심 행동·긍정 신호 | `DEC-026`, `DEC-027`, `DEC-043` | `UX-006`~`UX-009` | `AC-011` | `TEST-008`, `TEST-013`, `TEST-020`~`TEST-022` |
| `P0-FR-068~069` | 시스템 자동 분류·사용자 컬렉션 제외 | `DEC-028` | `UX-009` | `AC-011` | `TEST-014`, `TEST-020`~`TEST-022` |
| `P0-FR-070~071` | 전시만 최근 기록·추천 중립 | `DEC-044` | `UX-013` | `AC-011` | `TEST-008`, `TEST-013`, `TEST-026` |
| `P0-FR-072~074` | 최대 3개·종료·미확인 구분 | `DEC-029` | `UX-010` | `AC-012` | `TEST-014`, `TEST-019`, `TEST-032`, `TEST-033` |
| `P0-FR-075~077` | 선택형 지도·동일 필터·핀 정보 | `DEC-030` | `UX-004`, `UX-011` | `AC-013` | `TEST-024`, `TEST-036` |
| `P0-FR-078~079` | 경로 기능 제외·위치 비저장 | `DEC-011`, `DEC-030`, `DEC-062` | `UX-011` | `AC-013`, `AC-014` | `TEST-024`, `TEST-026`, `TEST-036` |

## 8. 데이터 제어·접근성·운영·회복성

| 요구사항 ID | 기능 요약 | 결정 | 화면 | 합격 기준 | 테스트 |
| --- | --- | --- | --- | --- | --- |
| `P0-FR-080~081` | 부분·전체 초기화와 확인 | `DEC-010`, `DEC-106` | `UX-012` | `AC-014` | `TEST-013`, `TEST-025` |
| `P0-FR-082~084` | 브라우저 저장·위치·개발 전용 비전송 이벤트 안내 | `DEC-010`, `DEC-062`, `DEC-110`, `DEC-116` | `UX-012` | `AC-014` | `TEST-013`, `TEST-025`, `TEST-026`, `TEST-038` |
| `P0-NFR-001~004` | 키보드·포커스·텍스트 상태·대비·모션·확대 | `DEC-103`, `DEC-114` | `UX-001`~`UX-013` | `AC-018`, `AC-020` | `TEST-014`, `TEST-031`~`TEST-034` |
| `P0-NFR-005` | 최신 주요 데스크톱·모바일 브라우저 | `DEC-111` | `UX-001`~`UX-013` | `AC-020` | `TEST-028`~`TEST-030` |
| `P0-FR-085` | staff 전용 `/admin/data-status/` 품질 영역 | `DEC-109`, `DEC-115` | 해당 없음: 운영자 영역 | `AC-021` | `TEST-010`, `TEST-035` |
| `P0-FR-086` | 상태·충돌·중복·권리·수집 품질·allowlist lifecycle·health·승격·중단 증거와 Admin drill-through | `DEC-083`, `DEC-084`, `DEC-085`, `DEC-086`, `DEC-090`, `DEC-097`~`DEC-099`, `DEC-115` | 해당 없음: 운영자 영역 | `AC-017`, `AC-021`, `AC-025`~`AC-027` | `TEST-001`~`TEST-005`, `TEST-035`, `TEST-041`~`TEST-043` |
| `P0-FR-087` | 운영자 인증과 일반 사용자 계정의 분리 | `DEC-010`, `DEC-109` | 해당 없음: 운영자 영역 | `AC-021` | `TEST-010`, `TEST-035` |
| `P0-FR-088` | 수동·배포 동기화의 동일 실행 경로, 우선 재검증과 기관별 lifecycle·health 증거 집계 | `DEC-089`, `DEC-093`, `DEC-098`, `DEC-099`, `DEC-113` | 해당 없음: 운영자 영역 | `AC-023`, `AC-026`, `AC-027` | `TEST-002`, `TEST-039`, `TEST-042`, `TEST-043` |
| `P0-FR-089` | 전시 최소 품질 핵심 항목과 선택 정보 `UNKNOWN` | `DEC-096` | `UX-004`, `UX-006` | `AC-017`, `AC-024` | `TEST-006`, `TEST-007`, `TEST-040` |
| `P0-FR-090` | 기관 후보 4/5 CORE_PASS·구조/정책 예외·`HOLD`·첫 `PROVISIONAL` | `DEC-094`, `DEC-095`, `DEC-096`, `DEC-097` | 해당 없음: 운영자 영역 | `AC-021`, `AC-025` | `TEST-035`, `TEST-041` |
| `P0-FR-091` | 기관 lifecycle·PROVISIONAL 서비스 적격성·14일/3회/의미 변경 `ACTIVE` 승격 | `DEC-083`, `DEC-090`, `DEC-097`~`DEC-099` | 해당 없음: 운영자 영역 | `AC-021`, `AC-023`, `AC-026`, `AC-027` | `TEST-035`, `TEST-039`, `TEST-042`, `TEST-043` |
| `P0-FR-092` | 기관 health·첫/두 번째 최종 실패·Critical 즉시 중단·선택 구조 저하·단건 격리 | `DEC-090`, `DEC-096`, `DEC-099` | 해당 없음: 운영자 영역 | `AC-021`, `AC-023`, `AC-024`, `AC-027` | `TEST-035`, `TEST-039`, `TEST-040`, `TEST-043` |
| `P0-NFR-006` | 출처 실패 시 마지막 검증값·데모 회복 | `DEC-090`, `DEC-093` | `UX-001`, `UX-004`~`UX-008` | `AC-016`, `AC-023` | `TEST-002`, `TEST-004`, `TEST-015`, `TEST-036`, `TEST-039` |
| `P0-NFR-007` | 이미지 없음·실패의 텍스트형 대체 | `DEC-087`, `DEC-102` | `UX-001`, `UX-003`~`UX-009`, `UX-013` | `AC-015` | `TEST-005`, `TEST-015`, `TEST-027` |
| `P0-NFR-008` | 오래된 정보·충돌의 안전한 노출 | `DEC-084`, `DEC-090`, `DEC-093` | `UX-004`, `UX-006` | `AC-016`, `AC-017`, `AC-023` | `TEST-002`, `TEST-004`, `TEST-015`, `TEST-023`, `TEST-039` |
| `P0-NFR-009` | 데이터가 적은 지역의 투명한 안내 | `DEC-007` | `UX-004` | `AC-016` | `TEST-011`, `TEST-015`, `TEST-017` |

### 횡단 합격 기준 역추적

| 합격 기준 | 추적 요구사항 | 화면 | 테스트 |
| --- | --- | --- | --- |
| `AC-019` 대표 E2E 흐름 | `P0-FR-006`, `P0-FR-012`, `P0-FR-022`, `P0-FR-038`, `P0-FR-066`, `P0-FR-072`, `P0-FR-075`, `P0-FR-080`, `P0-NFR-007` | `UX-001`~`UX-013` | `TEST-016`~`TEST-029` |

## 9. 대표 E2E 역추적

| 테스트 | 사용자 성과 | 핵심 화면 | 핵심 합격 기준 |
| --- | --- | --- | --- |
| `TEST-016` | 취향에서 전시 발견 | `UX-001`~`UX-003` | `AC-001`~`AC-003`, `AC-008` |
| `TEST-017` | 조건에서 방문 후보 발견 | `UX-001`, `UX-004` | `AC-004`~`AC-006` |
| `TEST-018` | 검색 결과 이해 | `UX-004`~`UX-006` | `AC-007`, `AC-009` |
| `TEST-019` | 전시 비교 판단 | `UX-010` | `AC-012` |
| `TEST-020`~`TEST-022` | 전시·작품·기관 관심 관리 | `UX-006`~`UX-009` | `AC-010`, `AC-011` |
| `TEST-023` | 현재·예정·종료 구분 | `UX-004`~`UX-006` | `AC-007`, `AC-009`, `AC-016` |
| `TEST-024` | 같은 결과의 지도 확인 | `UX-004`, `UX-011` | `AC-013` |
| `TEST-025`~`TEST-026` | 로컬 데이터 통제·유지 | `UX-002`, `UX-003`, `UX-009`, `UX-012`, `UX-013` | `AC-003`, `AC-011`, `AC-014` |
| `TEST-027` | 권리 없는 이미지에서도 탐색 | 이미지 카드가 있는 모든 화면 | `AC-015` |

## 10. 비범위 회귀 방지

| 금지된 초기안 | 현재 근거 | 검증 연결 |
| --- | --- | --- |
| 일반 사용자 계정·익명 서버 프로필·기기 동기화 | `P0-FR-001`, `P0-FR-003`, `P0-OUT-001`, `DEC-010` | `AC-001`, `AC-014`, `AC-022`, `TEST-016`, `TEST-026`, `TEST-035`, `TEST-037` |
| `봤어요`·`싫어요`·암묵 행동 기반 취향 | `P0-FR-066~067`, `P0-FR-071`, `P0-OUT-002`, `DEC-043`, `DEC-044` | `AC-011`, `AC-022`, `TEST-008`, `TEST-037` |
| 사용자 컬렉션·메모·공유·커뮤니티 | `P0-FR-069`, `P0-OUT-003`, `DEC-028` | `AC-011`, `AC-022`, `TEST-014`, `TEST-020`~`TEST-022`, `TEST-037` |
| 티켓·결제·예약 대행·잔여석·총액 계산 | `P0-FR-057`, `P0-OUT-004`, `DEC-011`, `DEC-064`, `DEC-065` | `AC-009`, `AC-022`, `TEST-012`, `TEST-018`, `TEST-037` |
| 일정·방문 순서·경로·교통·식당·카페 계획 | `P0-FR-078`, `P0-OUT-005`, `DEC-011`, `DEC-030` | `AC-012`, `AC-013`, `AC-022`, `TEST-019`, `TEST-024`, `TEST-037` |
| 네이티브·PWA·오프라인·푸시·백그라운드 위치 | `P0-OUT-006` | `AC-013`, `AC-020`, `AC-022`, `TEST-028`~`TEST-030`, `TEST-037` |
| 다국어·작가 독립 탐색·임베딩 생성·저장·읽기·점수 사용·근거 없는 LLM 해설 | `P0-FR-039`, `P0-FR-058`, `P0-FR-063`, `P0-OUT-007`, `DEC-052` | `AC-007`, `AC-009`, `AC-010`, `AC-022`, `TEST-011`, `TEST-012`, `TEST-021`, `TEST-037` |
| 권리·접근 통제가 불명확한 미디어 수집·표시 | `P0-FR-015`, `P0-NFR-007`, `P0-OUT-008` | `AC-015`, `AC-022`, `TEST-005`, `TEST-027`, `TEST-037` |

## 11. 현재 구현 증거

| 요구사항 | 작업 패킷 | 실제 테스트 파일 | 상태 |
| --- | --- | --- | --- |
| `P0-FR-015`, `P0-NFR-007` 미디어 권리·대체 | [`TP-003`](../07-execution/task-packets/TP-003-visit-information-and-media-rights.md), [`TP-006`](../07-execution/task-packets/TP-006-frontend-discovery.md) | `tests/persistence/test_media_rights.py`, `frontend/src/shared/api/client.test.ts`, `frontend/src/app/App.test.tsx` | `PARTIAL`: 저장·API 경계·발견 카드의 안전한 이미지·텍스트 대체 구현, 상세·취향 테스트·실제 브라우저 검수는 미구현 |
| `P0-FR-032`~`P0-FR-036`, `P0-FR-055`~`P0-FR-057`, `P0-FR-089` 선택 관람 정보 | [`TP-003`](../07-execution/task-packets/TP-003-visit-information-and-media-rights.md) | `tests/persistence/test_visit_information.py` | `PARTIAL`: 요금·예약·예상 관람시간·접근성·감각의 근거·`UNKNOWN`·확인된 부정 저장 구현, 승인 Source 수집 매핑·API·추천 필수조건 판정은 미구현 |
| `P0-FR-088` 수집 전 게이트와 기관별 실행 결과 | [`TP-001`](../07-execution/task-packets/TP-001-institution-collection-gate.md), [`TP-002`](../07-execution/task-packets/TP-002-institution-active-promotion.md) | `tests/persistence/test_registry_state.py`, `test_collection_gate.py`, `test_sync_command.py`, `test_refresh_commands.py`, `test_institution_qualification.py` | `PARTIAL`: 로컬 세 변경 명령·자격 모드·성공 확정 전 Critical 재검사·원자성 구현, 배포 스케줄러·승격 진행 표시는 미구현 |
| `P0-FR-091` lifecycle 서비스 적격성 | [`TP-001`](../07-execution/task-packets/TP-001-institution-collection-gate.md), [`TP-002`](../07-execution/task-packets/TP-002-institution-active-promotion.md) | `tests/persistence/test_collection_gate.py`, `test_institution_runs.py`, `test_change_history.py`, `test_institution_qualification.py`, `test_sync_command.py` | `PARTIAL`: 수집 자격, `ACTIVE` 실패·Critical 중단, 14일·서로 다른 서울 날짜 3회·의미 변경·최종 veto·PromotionEvidence 승격 구현, `SUSPENDED → PROVISIONAL` 복구 승인과 상태 화면은 미구현 |
| `P0-FR-092` health·Critical scope·격리 | [`TP-001`](../07-execution/task-packets/TP-001-institution-collection-gate.md), [`TP-003`](../07-execution/task-packets/TP-003-visit-information-and-media-rights.md) | `tests/persistence/test_collection_gate.py`, `test_institution_runs.py`, `test_refresh_commands.py`, `test_visit_information.py` | `PARTIAL`: 기본 health·ENTRY/SOURCE 사전 차단·열린 Critical 결과와 선택값 `UNKNOWN` 정본 구현, 실행 중 자동 분류·기관별 재시도 telemetry·수집기 선택값 변환은 미구현 |

TP-006의 추가 구현 증거:

| 요구사항 | 실제 테스트 파일 | 상태 |
| --- | --- | --- |
| `P0-FR-022`~`P0-FR-037`, `P0-FR-046`, `P0-FR-049`~`P0-FR-050` 조건·미확인·이유 | `frontend/src/features/discovery/forms.test.ts`, `frontend/src/app/App.test.tsx`, `tests/discovery/test_demo_api.py` | `PARTIAL`: 방문 입력·안전·모드·0건·적용 조건 표시·추천 이유 구현, 휴관일·위치·나머지 선호 축과 전체 홈은 제외 |
| `P0-FR-038`, `P0-FR-040`~`P0-FR-045` 검색·추가 로딩 | `frontend/src/app/App.test.tsx`, `frontend/src/shared/api/client.test.ts` | `PARTIAL`: 전시·기관 검색·상태·정렬·페이지 교체/추가·경합/오류 회복 구현, 작품·상세와 URL/새로고침 복원은 제외 |
| `P0-FR-003`~`P0-FR-004`, `P0-NFR-001`~`P0-NFR-004` 개인정보·포커스·상태 | `frontend/src/app/App.test.tsx`, `frontend/src/test/dev-log.test.ts` | `PARTIAL`: 입력 비영속·안전 로그·조건 보존·텍스트 상태·ESC 포커스 복귀 검증, 실제 브라우저·확대·스크린리더 검수는 미실행 |

현재 Django 실행 명령은 `uv run --project backend python backend/manage.py test tests --verbosity 1`, 프론트는 `frontend`의 `npm test`·`npm run api:check`·`npm run build`다. TP-006의 원문 입력 비영속 계약을 우선하며 포괄 문서의 URL 복원 요구 전체 완료로 판정하지 않는다.

## 12. 변경 통제

- 요구사항이 삭제되면 연결된 AC·TEST가 다른 요구사항을 검증하는지 확인하고 고아 항목을 제거하거나 재연결한다.
- 요구사항이 추가되면 최소 하나의 `AC-###`와 하나의 검증 방법을 연결한다.
- 화면이 바뀌어도 도메인 불변식과 무관용 기준을 약화하지 않는다.
- 테스트 구현 후 실제 테스트 파일 경로를 연결할 때는 존재 여부와 해당 요구사항 검증 내용을 함께 확인한다.
- 매트릭스에 연결되지 않은 P0 요구사항이나 요구사항에 연결되지 않은 필수 테스트가 있으면 문서 세트를 승인하지 않는다.

## 13. 열린 결정

- `OD-003`: `RESOLVED`. `DEC-094`~`DEC-099`의 출처 계약은 [`sources.yaml`](../../sources.yaml)과 [`source-qualification.json`](../../fixtures/source-qualification.json)으로 추적하며, 계약 테스트는 3개 Source·5개 기관·24개 `PASS`·1개 격리를 기준으로 한다.
- `OD-004`: 최종 워드마크·폰트 확정 후 해당 자산의 라이선스·로딩·렌더링 검증을 `P0-NFR-004`, `AC-020`, `TEST-030`·`TEST-034` 연결에 포함한다.

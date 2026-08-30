---
title: "미감 시스템 아키텍처"
status: DRAFT
version: "0.2.0"
last_updated: "2026-08-30"
authoritative_for:
  - "P0 시스템 경계와 런타임 구성"
  - "저장소 구조와 기술 선택"
  - "도메인 및 외부 연동 추상화"
related_documents:
  - "../00-governance/decision-register.md"
  - "../01-product/project-brief.md"
  - "../02-data/data-pipeline.md"
  - "../04-ux/ui-guidelines.md"
  - "security-privacy.md"
  - "api-guidelines.md"
  - "../07-execution/implementation-readiness.md"
---

# 미감 시스템 아키텍처

## 목적과 범위

이 문서는 P0의 기술 경계와 교체 가능한 구성 요소를 정한다. 화면·DB 세부 스키마·엔드포인트별 구현 순서와 배포 설계는 다루지 않는다. 상위 제품 원칙과 충돌하면 `docs/01-product/project-brief.md`가 우선한다.

## 기준 구조

단일 저장소(monorepo)에 다음 실행 단위를 둔다.

| 단위 | 기술 | 책임 |
| --- | --- | --- |
| `frontend/` | React, TypeScript, Vite | 한국어 웹 UI, 브라우저 내 취향·관심 상태, 내부 API 소비 |
| `backend/apps/` | Django, Django REST Framework | 전시·작품·기관 조회, 추천·검색 조율, 운영자 전용 관리 |
| `backend/data_pipeline/` | Python, Django 관리 명령 | 허용된 출처 수집, 정규화, 검증, 적재 후보 생성 |
| SQLite | SQLite P0 | 운영 데이터와 검색 인덱스의 단일 로컬 저장소 |

개발은 각 단위를 네이티브로 실행하는 것을 기본으로 하며, 동일 구성을 재현하는 Docker 구성을 제공한다. Docker는 로컬 개발의 필수 전제가 아니다.

## 저장소와 의존성 규약

- 프론트엔드는 `npm`과 `package-lock.json`을 사용한다.
- `backend/`의 Django 앱과 데이터 파이프라인은 `pyproject.toml`, `uv`, `uv.lock`을 사용한다.
- Python 의존성은 백엔드와 파이프라인의 실제 경계를 해치지 않는 범위에서 관리한다. 수집 실행이 웹 요청 경로에 포함되어서는 안 된다.
- Django 관리 명령은 `backend/` 의존성 경계에서 `uv run python manage.py …` 형식으로 실행한다. 수동 실행과 배포 스케줄러는 같은 명령 구현을 사용한다.
- P0에는 Celery나 별도의 상시 실행 worker를 두지 않는다. 배포 스케줄러는 정해진 시각에 due 대상 재확인 명령만 호출한다.
- 문서·예제·테스트는 외부 API 키 없이 동작해야 한다.

## 프론트엔드 경계

프론트엔드는 다음 구조를 따른다.

```
frontend/src/
  app/       앱 초기화, 라우팅, 공급자
  pages/     화면 단위 조합
  features/  취향 테스트, 관심, 비교, 조건 탐색 등 사용자 기능
  entities/  전시·작품·기관 표시와 도메인 표현
  shared/    공용 UI, API 클라이언트, 유틸리티, 타입
```

- 스타일 구현은 Tailwind CSS를 사용한다.
- Dialog, Sheet·Drawer, Popover, Select, Tabs, Tooltip, Accordion, Checkbox 같은 복합 상호작용은 Radix UI primitives를 직접 사용하거나 이를 기반으로 생성한 shadcn/ui 컴포넌트를 사용한다.
- 같은 역할의 primitive를 화면마다 서로 다른 방식으로 중복 도입하지 않는다. 작업 패킷은 해당 기능에서 직접 Radix를 사용할지 shadcn/ui 기반 컴포넌트를 사용할지 기록한다.
- 아이콘은 Lucide React를 사용하되 상태와 행동을 아이콘만으로 전달하지 않는다.
- primitive의 기본 시각 테마를 제품 디자인으로 간주하지 않는다. `ui-guidelines.md`의 색상·타이포그래피·여백·형태 규칙으로 스타일링하고 접근성 의미와 포커스 동작은 유지한다.
- TanStack Query는 서버 상태(조회 결과, 갱신, 오류)를 담당한다.
- Zustand는 화면 상태처럼 브라우저 안에서만 의미 있는 클라이언트 상태를 담당한다.
- 취향 테스트 결과와 `관심 있음`은 버전이 명시된 browser `localStorage`에 저장한다. 마이그레이션 실패 시 안전하게 초기화할 수 있어야 하며, 부분·전체 삭제를 지원한다.
- OpenAPI를 정본 계약으로 삼아 TypeScript 클라이언트를 생성한다. 생성 타입을 UI에 그대로 흘려보내지 않고, API 경계에서 Zod 어댑터로 검증·변환한다.

## 백엔드 경계

백엔드는 웹 도메인과 수집 처리 과정을 물리적으로 분리한다.

```text
backend/
  apps/
    catalog/
    discovery/
    sources/
    data_quality/
  data_pipeline/
    collectors/
    normalizers/
    deduplication/
    rights/
    freshness/
    quality/
```

`backend/apps/`는 사용자 API와 운영자 기능이 사용하는 정본 도메인을 담당하고, `backend/data_pipeline/`은 `SourceRecord → 검증·정규화·병합 → 정본 후보` 처리만 담당한다. 수집기는 정본 모델을 임의로 직접 덮어쓰지 않는다.

`backend/apps/`는 다음 도메인을 중심으로 구성한다.

| 도메인 | 책임 |
| --- | --- |
| `catalog` | 전시·작품·기관, 방문 정보, 출처·권리·확인 시점의 정본 데이터 |
| `discovery` | 조건 검증, 추천 후보·이유, 비교에 필요한 읽기 모델 |
| `sources` | 원천 레코드, InstitutionAllowlistEntry의 lifecycle과 `HEALTHY`·`DEGRADED` health·`ACTIVE` 연속 최종 실패 수, Source 운영 상태·출처 정책, InstitutionRunResult·CollectionIssue의 `ENTRY`·`SOURCE` scope·적재 이력과 승격 증거 연결 |
| `data_quality` | 중복·충돌·누락·최신성·DataEligibility 판정, 기관별 14일·연속 성공·의미 변경 자격, health·우선 재검증·Critical 수집 전 차단/선택 구조/단건 격리 판정과 운영자 검토 상태 |

Django Admin과 품질 상태 화면은 staff 운영자만 사용한다.

- `/admin/`은 Django Admin의 정본 CRUD와 개별 검토를 제공한다.
- `/admin/data-status/`는 전체·현재·예정·종료 건수, `STALE`, `UNVERIFIED`, 출처 충돌, 중복 후보, 권리 확인 필요 미디어, 최근 수집 성공·실패와 재확인 대상, 기관별 최근 5건 `CORE_PASS`, `PASS`·`HOLD` 심사 결과와 구조적 누락·정책·접근 제한 사유, 네 lifecycle과 `HEALTHY`·`DEGRADED`, 연속 최종 실패 수·우선 재검증, Critical·선택 구조·단건 격리 사유를 요약한다. `PROVISIONAL`에는 검증 시작일·경과일, 서로 다른 날짜의 연속 성공, 중간 실패, 마지막 실행, 의미 변경의 SourceRecord→Canonical→ChangeHistory 근거, Source 운영 상태와 미해결 구조 충돌 수도 보여준다.
- 상태 화면은 별도의 복잡한 편집기를 만들지 않고 관련 Django Admin 레코드로 이동해 검토하게 한다.
- 두 경로 모두 Django `is_staff` 또는 `is_superuser` 인증을 요구하며 일반 사용자 API와 분리한다.

일반 사용자 계정, 공개 운영 콘솔, 사용자 프로필 저장 기능은 만들지 않는다. 데이터 수집과 품질 검토는 이 경계를 통해 추적 가능해야 한다.

### 데이터 파이프라인 실행 계약

P0의 관리 명령 표면은 다음과 같다. 각 명령의 대상 선택, 실패 보존, 실행 이력 규칙은 `data-pipeline.md`가 정본이다.

| 목적 | 명령 |
| --- | --- |
| 전체 허용 출처 동기화 | `uv run python manage.py sync_exhibitions` |
| 현재 시각에 재확인이 필요한 대상 실행 | `uv run python manage.py refresh_due_exhibitions` |
| 한 출처 범위 동기화 | `uv run python manage.py sync_exhibitions --source=<source_key>` |
| 한 정본 전시 재확인 | `uv run python manage.py refresh_exhibition --id=<canonical_id>` |
| 대상별 다음 재확인 시각 확인 | `uv run python manage.py show_refresh_schedule` |

배포 스케줄러는 `refresh_due_exhibitions`를 호출한다. 별도 경로에서 정본을 수정하거나 due 판정을 다시 구현하지 않는다.

인자 없는 전체 동기화와 배포 스케줄러는 `PROVISIONAL` 또는 `ACTIVE` InstitutionAllowlistEntry, 정상 Source, 영향 scope의 미해결 Critical CollectionIssue 0건을 모두 충족한 기관 범위를 처리한다. 명시적 `--source` 실행도 같은 조건을 요구하고, 미등록·일시 중단·사용 중지 Source나 `CANDIDATE`·`SUSPENDED`·Critical 차단 범위는 수집 전에 거부한다. 허용된 공유 Source 안에서는 기관 lifecycle과 CollectionIssue scope를 따로 판정하며 Source 전체 근거가 있을 때만 연결 기관 전체로 차단을 넓힌다. `PROVISIONAL`과 `ACTIVE`는 모두 동일한 레코드별 품질·권리·최신성·충돌 게이트를 통과한 뒤 정본·검색·추천·사용자 서비스 경로로 진행하며, lifecycle 자격 증거만 별도로 누적한다.

`show_refresh_schedule`은 due 대상과 함께 기관별 승격 검증 시작일, `InstitutionQualificationRun.finished_at`을 `Asia/Seoul` 달력일로 환산한 서로 다른 날짜의 연속 최종 성공, health·`ACTIVE` 연속 최종 실패 수, 첫 실패와 선택 구조 문제의 우선 재검증, 미해결 Critical 차단 scope, 의미 변경 근거와 최종 상태 조건을 읽기 전용으로 보여준다. 첫 최종 `FAILED`는 `ACTIVE + DEGRADED`, 중간 성공 없는 서로 다른 IngestionRun 2회 연속 최종 `FAILED`는 `SUSPENDED`다. `POLICY_BLOCK`·`ACCESS_BLOCK`·`STRUCTURAL_CRITICAL`은 즉시 중단하며 실행 중 발견된 경우에만 해당 InstitutionRunResult를 `FAILED`로 기록한다. `PROVISIONAL`은 lifecycle을 유지하되 미해결 Critical로 수집·승격을 차단하고, `STRUCTURAL_OPTIONAL`·`RECORD_EXCEPTION`은 각각 `UNKNOWN + DEGRADED`·단건 격리로 제한한다. 수정·승인 후 `PROVISIONAL`에서 검증을 처음부터 다시 시작한다.

## 검색·지도·추천 경계

- 검색은 `SearchService` 뒤에 둔다. P0 구현은 SQLite FTS5이며, 호출자와 API는 FTS5 세부사항에 의존하지 않는다.
- 지도는 `MapProvider` 추상화 뒤에 둔다. P0의 Kakao 지도 연동은 해당 구현체이며, 지도 키·SDK 부재 시에도 목록·비교·테스트가 작동해야 한다.
- 추천은 서버가 콘텐츠와 명시적 요청 조건을 일회성으로 평가해 반환한다. 브라우저에 있는 취향·관심 신호를 요청에 포함할 수 있으나, 서버가 일반 사용자별 장기 프로필로 저장하지 않는다.
- 정확 좌표는 지도 표시 또는 필요한 순간의 요청 처리 외 장기 로그로 보존하지 않는다.

## 데이터 흐름과 안전한 저하

`공식·허용 출처 → backend/data_pipeline → sources/data_quality 검토 → catalog → discovery/search API → frontend`가 기본 흐름이다. 출처 충돌, 최신성 초과, 필수 방문 조건 누락, 이미지 권리 미확인은 긍정 사실이나 주요 추천에 사용하지 않는다. 데모 데이터는 같은 적재·표현 계약을 따르며 외부 키 없이 대표 흐름과 예외를 재현한다.

## 미결정 연계

- 공개·상업 목적: OD-001
- 저장소 공개, 라이선스, 데모 재배포: OD-002
- P0 출처 allowlist: OD-003
- 로고와 최종 폰트: OD-004
- 외부 공개 API 여부: OD-005
- P1 호스팅·비용·관측성: OD-006
- 구현 일정·브랜치·리뷰: OD-007

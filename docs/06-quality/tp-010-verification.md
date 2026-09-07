---
title: "TP-010 로컬 실행·복구·브라우저 회귀 검증"
status: DRAFT
version: "1.0.0"
last_updated: "2026-09-07"
authoritative_for:
  - "로컬 프로젝트 마무리 범위의 실행 증거와 검증 제한"
related_documents:
  - "../07-execution/task-packets/TP-010-local-completion-and-browser-regression.md"
  - "../05-engineering/local-delivery.md"
  - "./test-plan.md"
---

# TP-010 로컬 마무리 검증

사용자의 DEC-118에 따라 공개 배포를 제외하고 로컬 실행·복구·반복 검증을 마무리했다. 2026-09-07 Windows, main의 기존 TP-009 변경을 보존한 상태에서 Python 3.11, Node 24, Playwright 1.63.0으로 실행했다. 호스팅·도메인·Docker 설치·유료 지도·정기 수집·공개 운영자 계정은 이 작업의 완료 조건이 아니다.

## 실행 결과

| 검사 | 실제 결과 |
| --- | --- |
| backend `manage.py test tests --verbosity 1` | 290개 통과, 29.731초, Django 문제 0개 |
| backend `makemigrations --check --dry-run` | 변경 없음 |
| frontend `npm test` | 12개 파일 78개 통과 |
| frontend `npm run api:check` | OpenAPI 1.5.0 생성 타입 일치 |
| frontend `npm run build` | TypeScript·Vite 빌드 통과. 타입 검사에 E2E와 Playwright 설정도 포함 |
| frontend `npm run format:check` | 통과. 마지막 E2E 사례 추가 후 해당 파일도 포맷·빌드 타입 검사를 통과 |
| frontend `npm run test:e2e` | 23개 통과, 25.3초. Chromium 7개·390px Chromium 7개·WebKit 7개·공식 안내 fixture 2개 |
| 실제 `run_local.py --smoke-test --port 0` | 새 local-data 빌드, 홈·직접 경로·health·실제 검색 API·종료 성공 |
| 실제 백업 복구와 별도 DB 기동 | 전시 758개·기관 9개의 백업을 임시 파일로 복원하고 준비·health·API·종료 확인. 원본 DB와 백업 SHA-256 불변 |
| 설정·문서 검사 | workflow YAML 트리거·권한·검사 명령, manifest/lock 일치, 상대 문서 참조와 `git diff --check` 확인 |

브라우저 회귀는 다음 사용자 동작을 검사한다.

- 홈의 API 비호출과 전시 둘러보기 진입
- 미제출 검색어를 필터가 전송하지 않는 동작과 빈 결과의 조건 유지
- 전시 기간 추천 요청, 숨은 방문 조건 미전송과 개관일 미추정
- 상세 직접 새로고침, 관심 저장 유지, 비교·초기화·ESC 포커스 복귀
- API 503 후 입력을 보존한 재시도
- 가상 전시의 허구 공식 링크 미노출
- 명시적으로 저장한 취향의 새로고침 유지와 추천 반영
- 실제 UI 모드에서 미확인 상세·비교의 공식 링크와 별도 탭·referrer 차단

기본 21개 흐름은 `run_local_demo.py`의 실제 Django API와 임시 가상 DB를 사용한다. 공식 안내 2개는 명시적인 가상 응답으로 UI 계약만 검사하며 실제 기관 사이트의 접속이나 최신성을 검증했다고 보지 않는다. 모든 브라우저 컨텍스트는 새로 만들고 외부 요청을 차단한다. 홈·검색·추천·상세·비교·취향 화면의 가로 넘침을 검사한다.

## 로컬 실행과 데이터 보존

`scripts/run_local.py`는 기본 5180에서 기존 DB를 `mode=ro`로 사용한다. 빈 DB 생성·가상 seed·migration·원본 재확인을 하지 않는다. 시작 시 migration·무결성·시간에 따른 파생 상태를 확인하고 필요하면 명시적인 `prepare_local_data.py` 실행을 안내한다. 장시간 실행/날짜 변경은 정지→준비→재시작 절차를 따른다.

새 Python 테스트 11개는 손상 백업·기존 출력 덮어쓰기 거부, WAL 복원, 미적용 migration·만료 상태 거부, 잘못된 상속 환경·우발적인 DB 쓰기 거부, 원본 데이터 보존, 실제 검색·상세·추천 POST, 직접 SPA 경로·관리 화면 차단, SIGINT·SIGTERM 처리와 임시 파일 정리를 검사했다. Windows 프로세스의 강제 종료와 Python 신호 처리의 차이는 테스트에서 stdin을 통해 신호 핸들러를 호출해 구분했다.

실제 복구 검증은 `data/incoming/backups/db-20260907T065435Z-4991489b.sqlite3`를 임시 디렉터리의 새 DB로 복원했다. 복원 직후 전시 758개의 ID·공식 확인 시각을 원본 백업과 대조했다. 복원 DB에만 준비 명령을 적용해 날짜 파생 상태를 갱신하고 웹·API smoke를 실행했다. 임시 복원 DB와 그 준비 백업은 종료 후 제거했으며 실제 `backend/db.sqlite3`와 선택한 원본 백업의 바이트는 변경하지 않았다.

최종 실제 실행기를 기본 5180에 켠 뒤 In-app 브라우저에서 홈→전시 둘러보기로 이동해 실제 전시 17개와 공식 상세 링크를 확인했다. 5173·8000 개발 서버와 분리된 실행이며 사용자가 확인할 수 있도록 5180 실행기를 유지했다.

## CI와 환경 제한

`.github/workflows/local-regression.yml`은 main push·PR·수동 실행 시 잠금 의존성 설치, 백엔드 전체 검사, 프론트 검사·빌드·계약·형식, 모든 엔진 E2E를 수행한다. GitHub token은 contents read 권한이며 배포 단계나 실제 비밀값이 없다. 실패한 가상 테스트 보고서·trace·스크린샷만 7일 보관한다. 현재는 설정과 로컬 실행만 검증했으며 **커밋·푸시·원격 Actions 실행은 수행하지 않았다.**

Firefox를 포함한 첫 전체 실행은 Chromium·모바일·WebKit·공식 안내 20개가 통과하고 Firefox 6개가 브라우저 시작 전에 실패했다. 오류는 `browserType.launch: spawn UNKNOWN`이었다. 해당 Firefox 155 실행 파일의 `--headless --version`도 Windows side-by-side 오류로 실패했고, 일치하는 Windows 이벤트는 `mozglue` 종속 어셈블리를 찾지 못했다고 기록했다. 시스템 구성·벤더 실행 파일은 수정하지 않았다. 이후 취향 사례를 추가한 기본 23개는 모두 통과했다. Firefox 프로젝트의 현재 7개는 이 환경에서 미검증이며 Linux CI도 아직 실행하지 않았다.

초기 검사에서는 Vite의 예약어 `local` 대신 `local-data` 빌드 모드를 사용하도록 수정했다. 제한된 실행 환경에서 Windows 테스트 자식 프로세스 종료가 막힌 경우에는 명령과 포트를 대조한 검사 전용 서버만 정리하고 프로세스 실행 권한이 있는 환경에서 재실행했다. 기존 개발 서버나 실데이터 저장소를 테스트 대상으로 재사용하지 않았다.

실제 모바일 기기·스크린리더·200% 확대의 전체 수동 접근성 검수, Firefox 실행 환경 해결은 별도다. 자동 viewport 검사는 실제 기기나 전체 접근성 인증을 대신하지 않는다. 실제 작품 Source·관람 정보 커버리지·적응형 취향 등 포괄 P0 잔여 기능도 이번 로컬 완료에 포함하지 않는다.

## 실행 안내와 참고

일상 실행은 루트에서 `.\backend\.venv\Scripts\python.exe -X utf8 scripts/run_local.py`, 기본 자동 브라우저 검사는 frontend에서 `npm run test:e2e`다. 최초 설치·정지·복구·데모 경계는 [로컬 실행 안내](../05-engineering/local-delivery.md)에 정리했다.

브라우저 엔진·webServer·CI 설정은 [Playwright CI 문서](https://playwright.dev/docs/ci)와 [webServer 문서](https://playwright.dev/docs/test-webserver)를 참고했다. 고정 uv 설정은 [setup-uv 공식 사용법](https://github.com/astral-sh/setup-uv)에 따라 구성했다. Playwright는 개발 의존성으로만 추가했고 Node 20 이상 요구가 저장소의 Node 24.15 이상 조건과 호환됨을 확인했다. 설치 시 npm audit 결과는 취약점 0개였으며 운영 번들에는 테스트 러너가 포함되지 않는다.

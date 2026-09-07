---
title: "로컬 통합 실행과 복구"
status: APPROVED
version: "1.1.1"
last_updated: "2026-09-07"
authoritative_for:
  - "TP-008 가상 데이터 웹·API 통합 실행과 Docker 재현"
  - "TP-010 실제 데이터 로컬 실행·별도 파일 복구·브라우저 회귀"
related_documents:
  - "../07-execution/task-packets/TP-008-p0-product-completion.md"
  - "security-privacy.md"
  - "system-architecture.md"
---

# 로컬 통합 실행과 복구

## 2026-09-07 로컬 완료 범위

사용자는 공개 배포를 제외하고 로컬 프로젝트로 마무리하기로 했다. [TP-010](../07-execution/task-packets/TP-010-local-completion-and-browser-regression.md)에 따라 실제 데이터의 단일 origin 실행과 별도 파일 복구, 가상 DB를 이용한 브라우저 회귀를 제공한다. 실제 모드 실행은 기존 DB만 사용하고 가상 seed를 호출하지 않는다. 미적용 migration은 백업 후 준비 명령으로 안내한다. 복구는 무결성이 확인된 백업을 존재하지 않는 새 출력 DB에만 수행하며 원본과 기존 출력 파일을 덮어쓰지 않는다. 테스트는 운영체제 임시 DB·브라우저 컨텍스트로 격리하며 외부 사이트·키·사용자 저장소에 의존하지 않는다. 아래 Docker 및 공개 운영 항목은 선택적인 향후 범위이며 로컬 완료의 선행 조건이 아니다.

## 실제 로컬 데이터 실행

의존성 최초 준비 후 저장소 루트에서 한 명령으로 실제 웹·API를 연다. Python 3.11 이상, Node.js 24.15 이상과 uv가 필요하며 의존성은 잠금 파일을 따른다.

```powershell
uv sync --project backend --locked
npm ci --prefix frontend
.\backend\.venv\Scripts\python.exe -X utf8 scripts/run_local.py
```

`http://127.0.0.1:5180/`에서 열고 터미널의 Ctrl+C로 종료한다. 기존 5173·8000 개발 서버와 독립적이다. 기본 DB는 `backend/db.sqlite3`이며 `--database <기존 DB 경로>`로 선택한다. DB가 없는 새 checkout에서는 아래 가상 데모를 사용하거나 백업을 복원한다. 이 실행기는 데이터 수집·계정 생성·가상 seed·migration을 자동 수행하지 않는다.

실행 시 무결성·migration·날짜에 따른 전시 상태·최신성·검색 날짜를 읽기 검사한다. 준비가 필요하다는 안내가 나오면 서버를 정지한 뒤 다음 명령을 실행하고 다시 시작한다.

```powershell
.\backend\.venv\Scripts\python.exe -X utf8 scripts/prepare_local_data.py
.\backend\.venv\Scripts\python.exe -X utf8 scripts/run_local.py
```

별도 DB를 사용한다면 두 명령에 같은 `--database`를 지정한다. 준비 명령은 `data/incoming/backups/`에 무결성이 확인된 백업을 만든 뒤 migration과 파생 데이터를 갱신한다. 원본 수집·공식 재확인 시각을 갱신하지 않으므로 오래된 공식 정보는 계속 재확인 필요 상태다. 장시간 실행하거나 날짜가 바뀐 경우에도 정지→준비→재시작한다. 실제 Source 갱신은 승인된 최신 입력으로 별도 수행하며, 외부 데이터 없이 항상 같은 흐름을 시연하려면 가상 데모를 사용한다.

서비스 실행 중 SQLite는 `mode=ro`로 열어 우발적인 쓰기를 거부한다. 정적 자산은 `.env`와 상속된 키를 읽지 않는 `local-data` 모드로 임시 빌드하며 기존 `frontend/dist`를 덮어쓰지 않는다. `/admin/`·숨김 파일·경로 밖 자산은 차단하고 요청 로그는 남기지 않는다. 관심·취향은 현재 브라우저 origin에 저장되므로 5173과 5180의 저장 목록은 별개다. DB 백업에는 브라우저의 관심·취향이 들어 있지 않다.

```powershell
.\backend\.venv\Scripts\python.exe -X utf8 scripts/run_local.py --smoke-test --port 0
```

이 명령은 임의의 빈 포트에서 홈·직접 경로·`/healthz`·검색 API를 확인하고 종료한다. 실제 모드 health는 `{"status":"ok","mode":"local-data"}`다. `--port 5184`처럼 다른 loopback 포트를 선택할 수 있다. `--dist`는 명시적으로 준비한 `local-data` 빌드가 있을 때만 사용한다. 기본 명령은 매번 새 빌드를 만들어 현재 코드를 반영한다.

## 검토한 전시 콘텐츠 반영

[TP-011](../07-execution/task-packets/TP-011-exhibition-content.md)의 소개·볼거리·관람 안내는 공식 상세를 검토한 JSON으로 추가한다. 현재 DB에는 [2026-09-07 입력](../../data/reviewed/exhibition-content-2026-09-07.json) 17건이 반영돼 있다. 다른 DB에 적용하거나 새로운 검토 자료를 반영할 때는 실행 중인 서버를 정지하고 위 준비 명령으로 백업·migration을 마친 뒤 입력을 먼저 검증한다.

```powershell
.\backend\.venv\Scripts\python.exe -X utf8 backend/manage.py import_exhibition_content --file data/reviewed/exhibition-content-2026-09-07.json --dry-run
.\backend\.venv\Scripts\python.exe -X utf8 backend/manage.py import_exhibition_content --file data/reviewed/exhibition-content-2026-09-07.json
.\backend\.venv\Scripts\python.exe -X utf8 scripts/run_local.py
```

위 import 명령의 기본 대상은 `backend/db.sqlite3`다. 다른 DB에는 동일한 경로를 `MIGAM_DB_PATH`로 지정하고 준비·검증·반영의 대상을 맞춘다. 입력의 전시·원본 ID와 hash가 대상 DB에 일치해야 하며, 검증 오류가 있으면 전체 입력을 반영하지 않는다. 같은 자료를 반복 반영해도 중복 생성하지 않는다. 기존 스냅샷을 수정하지 않고 새 검토 자료를 추가한다. 유효기간은 검토 후 최대 30일이며 원본·정본 식별 변경 또는 만료 후에는 소개를 노출하지 않는다. 공식 페이지를 다시 확인한 뒤 새 자료를 작성하며 날짜만 바꿔 연장하지 않는다. 확보량과 검증 결과는 [TP-011 검증 기록](../06-quality/tp-011-verification.md)을 따른다.

## 백업을 별도 파일로 복구

먼저 실행 중인 실제 API·수집·준비 명령을 정지한다. 사용할 백업 파일을 직접 선택하고, 이미 존재하는 `data/incoming/` 폴더 안의 새 파일명으로 복구한다. 아래 `<선택한 백업>`은 실제 백업 경로로 바꾼다.

```powershell
.\backend\.venv\Scripts\python.exe -X utf8 scripts/restore_local_data.py --backup "<선택한 백업>" --output data/incoming/restored.sqlite3
.\backend\.venv\Scripts\python.exe -X utf8 scripts/prepare_local_data.py --database data/incoming/restored.sqlite3
.\backend\.venv\Scripts\python.exe -X utf8 scripts/run_local.py --database data/incoming/restored.sqlite3 --smoke-test --port 0
.\backend\.venv\Scripts\python.exe -X utf8 scripts/run_local.py --database data/incoming/restored.sqlite3
```

복구 도구는 백업과 복원 DB의 무결성을 확인하고 SQLite backup API로 커밋된 WAL도 포함한다. 기존 출력 파일·백업 자신을 덮어쓰지 않으며 게시 직전 같은 파일명이 생겨도 실패한다. 원본 `backend/db.sqlite3`는 그대로 남으므로 원래 실행 명령으로 돌아갈 수 있다. 출력 폴더는 먼저 존재해야 하며 NTFS 등 하드링크를 지원하는 로컬 파일시스템을 사용한다. 네트워크·비지원 파일시스템에서는 원본을 바꾸지 않고 실패한다.

## 브라우저 자동 회귀

최초 한 번 테스트 브라우저를 설치한 뒤 반복 실행한다. 이 명령은 실제 5173·8000·5180 서버를 사용하지 않는다.

```powershell
cd frontend
npx playwright install chromium webkit
npm run test:e2e
```

기본 검사는 데스크톱 Chromium·390px Chromium·WebKit에서 홈→검색→기간 추천→상세·관심·비교·초기화·취향 저장을 실행한다. 5182는 임시 가상 DB와 실제 API, 5183은 외부 호출을 차단한 공식 링크 fixture용 UI다. 두 포트가 사용 중이면 실패하며 기존 서버를 재사용하지 않는다. 각 사례는 새 브라우저 컨텍스트로 격리한다. 종료 시 테스트 프로세스를 정리한다. Windows의 강제 프로세스 종료나 중단으로 남은 `migam-local-demo-*` 임시 디렉터리는 재사용하지 않는다.

`npm run test:e2e:install`은 Firefox까지 설치하고 `npm run test:e2e:all`은 전체 엔진을 실행한다. GitHub Actions도 같은 전체 명령을 사용하며 서비스 공개 단계가 없다. 현재 Windows의 Firefox 실행 제한과 실제 검사 결과는 [TP-010 검증 기록](../06-quality/tp-010-verification.md)에 기록한다. 실패 HTML 보고서는 `output/playwright/report/index.html`, trace·스크린샷은 `output/playwright/results/`에 생기며 Git에서 제외한다. 원격 CI 성공 여부는 push 후 Actions 실행으로 따로 확인한다.

## 가상 데모 실행 경계

이 구성은 가상 전시로 P0 화면과 실제 Django API를 함께 확인하는 로컬 검토 환경이다. 실행 때마다 운영체제 임시 디렉터리에 SQLite를 만들고 migrate·데모 적재를 수행한다. 종료할 때 연결과 서버를 닫고 임시 DB를 제거한다. `backend/db.sqlite3`, 기존 `MIGAM_DB_PATH`, 수집 자료, 운영자 계정을 사용하지 않는다. 브라우저의 데모 취향·관심 저장 영역은 실제 데이터 모드와 분리하며 삭제는 화면의 내 데이터 관리에서 수행한다.

네이티브 실행과 Docker 모두 Python 표준 WSGI 서버로 정적 데모 빌드와 내부 API를 같은 origin에서 제공한다. `/admin/`은 이 실행기에서 열지 않는다. staff 운영은 [별도 운영 절차](staff-operations.md)를 따른다. 요청 경로·검색어·추천 본문은 access log로 출력하거나 저장하지 않는다. 앱과 API는 실행 중 외부 키를 요구하지 않는다. 의존성과 이미지의 최초 다운로드에는 네트워크가 필요하다.

## 가상 데모 네이티브 실행

저장소 루트에서 Python 3.11 이상, Node.js 24.15 이상과 잠금 파일 기준 의존성을 준비한다.

```powershell
uv sync --project backend --locked
npm ci --prefix frontend
.\backend\.venv\Scripts\python.exe -X utf8 scripts/run_local_demo.py
```

macOS/Linux에서는 마지막 명령의 Python 경로만 `backend/.venv/bin/python`으로 바꾼다. 실행기는 TypeScript 검사 후 `demo` 모드로 별도 임시 디렉터리에 빌드한다. 기존 `frontend/dist`는 덮어쓰지 않는다. 데모 빌드는 `.env` 파일을 읽지 않으며 상속된 `VITE_*` 값도 제거한다. 키 유무와 무관하게 가상 지도 경로를 사용한다.

준비 완료 후 `http://127.0.0.1:5181/`을 연다. 기존 개발용 5173·8000 포트는 사용하지 않는다. 포트가 사용 중이면 `--port 5182`로 바꾼다. 기본 바인딩은 loopback이다. Ctrl+C는 서버와 DB를 함께 종료한다. 강제 프로세스 종료나 정전 때 남은 `migam-local-demo-*` 임시 디렉터리는 다음 실행에 재사용하지 않는다.

```powershell
.\backend\.venv\Scripts\python.exe -X utf8 scripts/run_local_demo.py --smoke-test --port 0
```

이 명령은 임의의 비어 있는 포트에서 웹·health·검색 API를 확인한 뒤 종료한다. `--dist <directory>`는 이미 `demo` 모드로 만든 정적 빌드를 사용하는 경우에만 지정한다. 이 옵션은 빌드를 생략하므로 실제 모드 빌드의 데모 변환을 보장하지 않는다.

## Docker

```powershell
docker compose up --build
docker compose ps
docker compose down
```

호스트에는 `127.0.0.1:5181` 한 포트만 공개한다. 컨테이너 내부 8080은 컨테이너 네트워크 바인딩용이며 외부 공개 승인이 아니다. DB 볼륨·bind mount·env 파일을 연결하지 않는다. 비루트 사용자, 읽기 전용 이미지, 쓰기 가능한 일회성 `/tmp`, 권한 제거와 healthcheck를 사용한다. 이미지에는 `.env`, 키 파일, 실제 SQLite, 수집 자료, 로컬 의존성·빌드 캐시를 복사하지 않는다. 프론트는 `npm ci`, 백엔드는 `uv sync --locked`로 잠금 파일을 사용한다.

`GET /healthz`는 DB 연결을 확인하고 가상 데이터 모드 상태를 반환한다. healthcheck는 본문이나 사용자 입력을 로그에 남기지 않는다. Ctrl+C 또는 `docker compose down`으로 종료하면 서버 연결과 임시 DB를 정리하며, 다음 시작은 새로운 가상 데이터로 시작한다. health 실패 시 `docker compose logs demo`에서 시작·마이그레이션 오류를 확인한다. 이 로그에는 요청 access log가 없다.

## 검증과 남은 운영 결정

브라우저의 미리 열린 빈 TCP 연결이 후속 상세 API를 막지 않도록 요청별 스레드와 10초 연결 대기 제한을 사용한다. 요청 로그는 계속 끄고 쓰기는 격리 DB만 허용한다. `/artworks` 직접 진입과 새로고침도 SPA 경로로 처리한다.

2026-09-06 Windows에서 새 데모 빌드(TypeScript 검사 포함), 웹·health·검색 API 연결, 자동 종료를 실제 실행했다. 전용 통합 테스트 3개는 기존 SQLite 바이트 보존, 임시 파일 정리, 요청 로그 비출력, 경로 탐색·관리 화면·없는 자산의 노출 차단과 빈 사전 연결이 다음 요청을 막지 않는 동작을 확인했다. Docker CLI·기본 설치 경로·서비스가 없어 이미지 빌드와 컨테이너 기동은 실행하지 못했다. compose 구조와 복사 대상·제외 규칙을 정적으로 점검했으며 Linux 이미지 의존성 설치와 컨테이너 health·종료 확인은 Docker가 있는 환경에 남아 있다.

Python 표준 서버, 고정 로컬 설정, 일회성 DB는 공개 운영용 구성이 아니다. OD-006의 호스팅·비용·운영 관측, HTTPS·도메인·백업, 운영 비밀값과 접근 정책을 결정하기 전에는 이 compose를 인터넷에 공개하지 않는다.

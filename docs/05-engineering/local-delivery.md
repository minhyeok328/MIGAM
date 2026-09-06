---
title: "키 없는 로컬 통합 실행"
status: APPROVED
version: "1.0.0"
last_updated: "2026-09-06"
authoritative_for:
  - "TP-008 가상 데이터 웹·API 통합 실행과 Docker 재현"
related_documents:
  - "../07-execution/task-packets/TP-008-p0-product-completion.md"
  - "security-privacy.md"
  - "system-architecture.md"
---

# 키 없는 로컬 통합 실행

## 실행 경계

이 구성은 가상 전시로 P0 화면과 실제 Django API를 함께 확인하는 로컬 검토 환경이다. 실행 때마다 운영체제 임시 디렉터리에 SQLite를 만들고 migrate·데모 적재를 수행한다. 종료할 때 연결과 서버를 닫고 임시 DB를 제거한다. `backend/db.sqlite3`, 기존 `MIGAM_DB_PATH`, 수집 자료, 운영자 계정을 사용하지 않는다. 브라우저의 데모 취향·관심 저장 영역은 실제 데이터 모드와 분리하며 삭제는 화면의 내 데이터 관리에서 수행한다.

네이티브 실행과 Docker 모두 Python 표준 WSGI 서버로 정적 데모 빌드와 내부 API를 같은 origin에서 제공한다. `/admin/`은 이 실행기에서 열지 않는다. staff 운영은 [별도 운영 절차](staff-operations.md)를 따른다. 요청 경로·검색어·추천 본문은 access log로 출력하거나 저장하지 않는다. 앱과 API는 실행 중 외부 키를 요구하지 않는다. 의존성과 이미지의 최초 다운로드에는 네트워크가 필요하다.

## 네이티브 실행

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

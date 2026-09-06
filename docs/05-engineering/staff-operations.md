---
title: "P0 staff 운영 영역"
status: APPROVED
version: "1.0.0"
last_updated: "2026-09-06"
authoritative_for:
  - "Django Admin과 데이터 상태 화면의 인증·권한·읽기 계약"
related_documents:
  - "docs/05-engineering/security-privacy.md"
  - "docs/06-quality/acceptance-criteria.md"
  - "docs/07-execution/task-packets/TP-008-p0-product-completion.md"
---

# P0 staff 운영 영역

## 접근과 권한

`/admin/`과 `/admin/data-status/`는 활성 staff 운영자만 접근한다. Django 기본
Admin 로그인, 세션 인증, CSRF 검증을 사용한다. 비인증·비staff·비활성 계정은
로그인 화면으로 이동하며 데이터는 제공하지 않는다. 일반 사용자 가입 경로나
프론트엔드 로그인 기능은 만들지 않는다.

staff 플래그만으로 데이터 조회 권한을 부여하지 않는다. 모델의 `view` 또는
`change` 권한이 있는 경우에만 해당 모델의 집계·목록·Admin 링크를 보여준다.
권한 없는 부분은 숨기고, 읽을 수 있는 운영 모델이 없으면 상태 화면은 403을
반환한다. 관련 모델 권한이 없으면 관계 레코드의 설명과 링크도 노출하지 않는다.
Admin 데이터 응답은 캐시하지 않는다.

## 읽기와 증거

상태 화면은 전체·현재·예정·종료 전시, 저장된 freshness와 일정에 따른 재확인
대상, 열린 충돌·중복 후보, 현재 권리 확인이 필요한 미디어, 수집 결과,
기관 lifecycle·health·연속 최종 실패·우선 재검증·전이 근거를 보여준다.
최근 목록은 최대 20건이며 전체 목록은 해당 Admin 화면으로 연결한다.

기관 심사 결과와 표본 CORE_PASS는 `sources.yaml`의 승인된 심사값을 표시한다.
등록되지 않은 기관을 추정하여 PASS 또는 HOLD로 분류하지 않는다. 등록 심사값과
후속 수집 검증 결과를 구분한다. PROVISIONAL 검증 경과일은 서울 날짜를 기준으로
표시하고, 현재 검증 주기에서 마지막 실패 이후 서로 다른 날짜의 성공 횟수와
실패 횟수를 보여준다. 승격 여부를 화면에서 계산하거나 변경하지 않는다.
의미 변경과 승격 증거는 SourceRecord·Canonical·ChangeHistory 및
PromotionEvidence의 실제 Admin 레코드로 추적한다.

운영 모델과 정본·증거·검색 파생 모델의 Admin은 읽기 전용이다. 추가·수정·삭제와
일괄 변경을 차단한다. 수집·재검증·승격은 기존 명령 및 서비스의 품질·최신성·
권리·변경 이력 규칙을 통해 수행한다. 임의 정본 수정, Source 재개,
CollectionIssue 해결 표시, ACTIVE 승격, 권리 허용 플래그 직접 변경은 제공하지
않는다. 정책 차단·충돌 해소는 근거를 확인한 뒤 해당 도메인 서비스 작업으로
처리하며, 이 화면의 조회가 문제 해결로 간주되지 않는다.

원본 payload·원문 값·오류 원문·근거 본문은 기본 목록이나 상태 요약에 포함하지
않는다. SourceRecord payload와 오류 원문은 Admin 상세에서도 숨긴다. 수집 키는
환경변수 또는 로컬 환경 파일에서만 읽으며 화면에 출력하지 않는다. Django
사용자·그룹 관리 권한은 별도로 부여하며 운영자 계정을 자동 생성하지 않는다.

## 로컬 실행

저장소 루트에서 기존 데이터 백업 및 스키마 적용 절차를 먼저 수행한다. 기존
`scripts/prepare_local_data.py`는 SQLite 백업 후 migration을 적용한다.

```powershell
.\backend\.venv\Scripts\python.exe -X utf8 scripts/prepare_local_data.py
.\backend\.venv\Scripts\python.exe -X utf8 backend/manage.py createsuperuser --settings=backend.config.local_settings
.\backend\.venv\Scripts\python.exe -X utf8 backend/manage.py runserver 127.0.0.1:8000 --settings=backend.config.local_settings --insecure
```

운영자가 터미널에서 직접 자격 증명을 입력하고
`http://127.0.0.1:8000/admin/data-status/`에 접속한다. 암호를 코드·명령 인자·문서에
저장하지 않는다. 최소 권한 운영자는 필요한 모델의 조회 권한만 부여한다.

`--insecure`는 DEBUG가 꺼진 로컬 서버에서 Admin의 CSS를 제공하기 위한 옵션이다.
로컬 설정은 loopback 접속 전용이다. 외부 배포에는 별도 비밀키, 허용 호스트,
HTTPS, Secure 세션·CSRF 쿠키, 신뢰 프록시 설정 및 운영 계정 관리가 필요하며
로컬 개발 비밀키나 설정을 공개 환경에서 사용하지 않는다.

## 검증

`tests.admin`은 테스트 DB에서 익명·비staff·비활성 접근 차단, 모델별 권한,
정본 변경 차단, CSRF, 현재 데이터 집계와 재확인 규칙, 관련 레코드 링크 및
payload 비노출을 확인한다. 실제 DB migration과 운영자 계정 생성은 테스트가
수행하지 않는다.

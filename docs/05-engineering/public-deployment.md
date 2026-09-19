---
title: "Vercel 무료 공개 배포와 갱신"
status: APPROVED
version: "1.0.0"
last_updated: "2026-09-19"
authoritative_for:
  - "TP-012 공개 런타임·비공개 데이터 보관·일일 수집 경계"
related_documents:
  - "../07-execution/task-packets/TP-012-free-public-deployment.md"
  - "security-privacy.md"
  - "local-delivery.md"
---

# Vercel 무료 공개 배포와 갱신

2026-09-19 사용자 결정에 따라 기존 `migam-home-preview` 프로젝트를 Vercel Hobby에서 전체 방문자 기능으로 확장한다. 구현·배포·갱신 확인 결과는 작업 후 기록한다. 이 문서의 승인 상태는 구현 범위를 뜻하며 배포 성공 증거가 아니다.

## 구성

React 정적 자산과 Django WSGI API를 같은 origin으로 제공한다. 공개 API는 기존 내부 프론트 소비 계약이며 제3자용 API 상품을 추가하지 않는다. 운영 Admin URL은 공개 런타임에서 제외한다.

정본 SQLite는 private Blob에 보관한다. 예약 작업은 비공개 정본을 임시 파일에 받아 기존 파이프라인으로 갱신하고 무결성을 확인한 새 버전을 게시한다. API는 검증한 스냅샷을 임시 파일로 내려받아 읽기 전용으로 연다. Blob 주소·토큰·DB 다운로드 기능은 응답에 넣지 않는다. 갱신 실패는 원본의 공식 확인 시각을 바꾸지 않는다.

매일 06시대(Asia/Seoul)의 Vercel Cron은 인증된 서버 경로만 호출한다. 동일 날짜 중복 실행과 경쟁 갱신을 방지한다. 서울 CSV는 승인 데이터셋의 공식 전체 내려받기 경로만 사용하고, 문화정보 API는 기존 키와 승인된 기관 범위로 순차 호출한다. 조회 실패·접근 차단·핵심 구조 오류는 기존 Source/기관/레코드 게이트를 유지한다.

서울 데이터셋의 `데이터 갱신일`을 매번 공식 페이지에서 확인한다. 새 버전만 전체 CSV를 받고, 같은 버전은 앞서 검증하여 비공개 저장한 허용 필드 레코드를 재사용한다. 메타데이터 확인 자체가 실패하면 공식 재확인으로 처리하지 않는다. 전송 중 일시 오류는 다음 날 재시도하지만, 403·429나 완전 다운로드 후 구조 오류는 같은 버전의 재다운로드를 막고 운영자 검토를 요구한다. 문화정보 API는 최근 1년부터 향후 180일까지 목록을 확인하고, 목록의 장소로 범위를 먼저 줄인 뒤 상세의 기관·주소 일치를 다시 검사한다. 이미 알려진 재검증 대상 ID도 별도로 확인한다. API 호출은 실행당 최대 100회이며 시간 예산을 넘기면 실패로 기록한다.

API는 최대 5분 간격으로 새 스냅샷을 확인한다. 날짜·최신성 파생 상태는 임시 복사본에서 다시 계산하고 읽기 전용 연결로 전환한다. 새 스냅샷 검증 실패 시 이미 검증된 이전 복사본을 유지한다. SDK 자체 사용량 텔레메트리도 `VERCEL_TELEMETRY_DISABLED=1`로 끈다.

## 환경과 비밀값

`DJANGO_SECRET_KEY`, `CRON_SECRET`, `BLOB_READ_WRITE_TOKEN`, `CULTURE_PORTAL_SERVICE_KEY`는 서버 환경으로만 주입한다. `VITE_KAKAO_JAVASCRIPT_KEY`는 지도용 공개 클라이언트 키이며 허용 도메인을 제한한다. 환경 파일과 키 값은 저장소·빌드 로그·API 응답에 넣지 않는다. Blob·수집 API 키는 프론트에 주입하지 않는다.

관심·취향은 기존 브라우저 저장소를 유지한다. 앱은 원문 검색어·추천 본문·정확 좌표를 로그로 남기지 않으며 별도 Analytics·오류 수집 SDK를 추가하지 않는다. 호스팅 사업자의 필수 요청 메타데이터는 앱의 사용자 행동 데이터 수집으로 확장하지 않는다.

## 무료 한도와 복구

Hobby의 사용량 한도 초과는 기능 중단으로 처리하고 자동 유료 전환하지 않는다. Blob 크기와 보관 버전 수를 제한하며 마지막 정상 데이터와 직전 복구 버전을 유지한다. 배포 롤백과 데이터 롤백은 별도로 취급한다. 무료 호스팅은 가용성 보장이나 데이터 정확성 보장을 뜻하지 않는다.

## 코드 푸시와 운영 전환

2026-09-19 사용자는 우선 준비된 코드를 커밋·푸시하도록 요청했다. 키 설정과 초기 정본 게시가 남아 있으므로 `vercel.json`의 `git.deploymentEnabled.main=false`로 `main` 푸시의 자동 배포를 보류한다. 명시적 CLI 배포는 이 설정과 별개다. 운영 키 설정·초기 데이터 갱신·실제 API 검증을 마친 뒤 운영 전환하고 자동 배포 설정을 다시 활성화한다.

## 공식 근거

- [Vercel Django](https://vercel.com/docs/frameworks/full-stack/django)
- [Python runtime](https://vercel.com/docs/functions/runtimes/python)
- [Hobby](https://vercel.com/docs/plans/hobby)
- [Blob 무료 한도](https://vercel.com/docs/vercel-blob/usage-and-pricing)
- [Cron 실행 한도](https://vercel.com/docs/cron-jobs/usage-and-pricing)
- [Git 자동 배포 설정](https://vercel.com/docs/project-configuration/git-configuration)

## 2026-09-19 구현·검증 상태

- 기존 `min-hyeok-s-projects/migam-home-preview`의 Hobby 플랜을 확인했다. 전용 private Blob `migam-data`를 Production에 연결했다. 운영 도메인은 아직 기존 배포를 유지한다.
- 전체 앱 미리보기 빌드 `dpl_GnQ264U6u7bZq1xkiSSq2Nda3jHp`가 READY다. Django의 끝 슬래시가 있는 경로도 `/api` 함수에 도달하도록 정규식 rewrite를 사용한다. 키·데이터가 없는 미리보기에서 `data_temporarily_unavailable`, 인증 없는 Cron에서 `unauthorized`를 실제 확인했다. 정상 검색·추천을 제공하는 운영 배포의 증거는 아니다.
- 백엔드 전체 323개 검사와 이후 추가한 목록 범위·배포 경로 검사 2개가 통과했다. 프론트 110개, OpenAPI 일치, 운영 프론트 빌드, migration 변경 없음, diff 형식 검사를 확인했다. 공개 WSGI의 실제 검색·host 검사·Admin 제외·DB 쓰기 거부도 가상 DB로 확인했다.
- 브라우저 시나리오 24개는 Chromium·390px 모바일·WebKit·공식 안내 프로젝트에서 통과했다. Firefox 7개는 Windows 바이너리의 side-by-side 구성 오류로 실행하지 못했다. 첫 전체 명령은 종료 대기 중 중단했고 Firefox 별도 재실행으로 환경 오류를 확인했다. 전체 E2E 명령 성공으로 간주하지 않는다.
- 운영 의존성 `npm audit --omit=dev`는 취약점 0건이었다. 빌드 도구를 포함한 Vercel 설치 로그에는 high 2건 경고가 있어 별도 의존성 검토 대상이다.
- `CULTURE_PORTAL_SERVICE_KEY`, `VITE_KAKAO_JAVASCRIPT_KEY`, 새 `DJANGO_SECRET_KEY`·`CRON_SECRET`을 해당 프로젝트 Production에 저장하는 작업은 자동 승인 검토가 명시적 비밀값 전송 동의를 요구하여 중단했다. 사용자의 안전성 질문에는 저장 방식과 접근 경계를 설명했으며 최종 저장 동의를 기다린다. 해당 4개 값은 아직 추가하지 않았다.
- 실제 공식 입력으로 초기 정본을 갱신·게시하는 작업, Production 배포, 원격 일일 수집 성공 및 실제 데이터 사용자 흐름 확인은 아직 남아 있다. 로컬 DB는 수정하지 않았다. 이후 사용자 요청에 따라 이 준비 상태를 커밋·푸시 대상으로 확정했다.

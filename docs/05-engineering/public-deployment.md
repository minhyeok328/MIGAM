---
title: "Vercel 무료 공개 배포와 갱신"
status: APPROVED
version: "1.0.1"
last_updated: "2026-09-21"
authoritative_for:
  - "TP-012 공개 런타임·비공개 데이터 보관·일일 수집 경계"
related_documents:
  - "../07-execution/task-packets/TP-012-free-public-deployment.md"
  - "security-privacy.md"
  - "local-delivery.md"
---

# Vercel 무료 공개 배포와 갱신

2026-09-19 사용자 결정에 따라 기존 `migam-home-preview` 프로젝트를 Vercel Hobby에서 전체 방문자 기능으로 확장했다. 실제 운영 전환과 검증 결과는 아래 날짜별 기록을 따른다. 문서의 승인 상태 자체는 배포 성공 증거가 아니다.

## 구성

React 정적 자산과 Django WSGI API를 같은 origin으로 제공한다. 공개 API는 기존 내부 프론트 소비 계약이며 제3자용 API 상품을 추가하지 않는다. 운영 Admin URL은 공개 런타임에서 제외한다.

국내 방문자와 공식 데이터 제공처의 지연을 줄이도록 함수는 Hobby에서 허용하는 단일 서울 리전(`icn1`)에 배치한다.

정본 SQLite는 private Blob에 보관한다. 예약 작업은 비공개 정본을 임시 파일에 받아 기존 파이프라인으로 갱신하고 무결성을 확인한 새 버전을 게시한다. API는 검증한 스냅샷을 임시 파일로 내려받아 읽기 전용으로 연다. Blob 주소·토큰·DB 다운로드 기능은 응답에 넣지 않는다. 갱신 실패는 원본의 공식 확인 시각을 바꾸지 않는다.

매일 06시대(Asia/Seoul)의 Vercel Cron은 인증된 서버 경로만 호출한다. 동일 날짜 중복 실행과 경쟁 갱신을 방지한다. 서울 CSV는 승인 데이터셋의 공식 전체 내려받기 경로만 사용하고, 문화정보 API는 기존 키와 승인된 기관 범위로 순차 호출한다. 조회 실패·접근 차단·핵심 구조 오류는 기존 Source/기관/레코드 게이트를 유지한다.

서울 데이터셋의 `데이터 갱신일`을 매번 공식 페이지에서 확인한다. 새 버전만 전체 CSV를 받고, 같은 버전은 앞서 검증하여 비공개 저장한 허용 필드 레코드를 재사용한다. 메타데이터 확인 자체가 실패하면 공식 재확인으로 처리하지 않는다. 전송 중 일시 오류는 다음 날 재시도하지만, 403·429나 완전 다운로드 후 구조 오류는 같은 버전의 재다운로드를 막고 운영자 검토를 요구한다. 문화정보 API는 최근 1년부터 향후 180일까지 목록을 페이지당 1,000건으로 확인하고, 목록의 장소로 범위를 먼저 줄인 뒤 상세의 기관·주소 일치를 다시 검사한다. 이미 알려진 재검증 대상 ID도 별도로 확인한다. 응답의 실제 페이지 크기로 종료를 판단하며 API 호출은 실행당 최대 100회, 시간 예산은 90초다. 예산을 넘기면 실패로 기록한다.

API는 최대 5분 간격으로 새 스냅샷을 확인한다. 날짜·최신성 파생 상태는 임시 복사본에서 다시 계산하고 읽기 전용 연결로 전환한다. 새 스냅샷 검증 실패 시 이미 검증된 이전 복사본을 유지한다. SDK 자체 사용량 텔레메트리도 `VERCEL_TELEMETRY_DISABLED=1`로 끈다.

## 환경과 비밀값

`DJANGO_SECRET_KEY`, `CRON_SECRET`, `BLOB_READ_WRITE_TOKEN`, `CULTURE_PORTAL_SERVICE_KEY`는 서버 환경으로만 주입한다. `VITE_KAKAO_JAVASCRIPT_KEY`는 지도용 공개 클라이언트 키이며 허용 도메인을 제한한다. 환경 파일과 키 값은 저장소·빌드 로그·API 응답에 넣지 않는다. Blob·수집 API 키는 프론트에 주입하지 않는다.

관심·취향은 기존 브라우저 저장소를 유지한다. 앱은 원문 검색어·추천 본문·정확 좌표를 로그로 남기지 않으며 별도 Analytics·오류 수집 SDK를 추가하지 않는다. 호스팅 사업자의 필수 요청 메타데이터는 앱의 사용자 행동 데이터 수집으로 확장하지 않는다.

## 무료 한도와 복구

Hobby의 사용량 한도 초과는 기능 중단으로 처리하고 자동 유료 전환하지 않는다. Blob 크기와 보관 버전 수를 제한하며 마지막 정상 데이터와 직전 복구 버전을 유지한다. 배포 롤백과 데이터 롤백은 별도로 취급한다. 무료 호스팅은 가용성 보장이나 데이터 정확성 보장을 뜻하지 않는다.

## 코드 푸시와 운영 전환

2026-09-19에는 운영 키와 초기 정본이 준비되지 않아 `main` 푸시의 자동 배포를 보류했다. 2026-09-21 운영 키 설정·세 Source의 원격 갱신 성공·실제 검색/상세/추천 API 검증 후 `git.deploymentEnabled.main=true`로 자동 배포를 다시 활성화한다. 이후 `main` 푸시는 운영 배포를 생성하므로 비밀값·DB 제외와 변경 범위 검사를 유지한다.

## 공식 근거

- [Vercel Django](https://vercel.com/docs/frameworks/full-stack/django)
- [Python runtime](https://vercel.com/docs/functions/runtimes/python)
- [Hobby](https://vercel.com/docs/plans/hobby)
- [Blob 무료 한도](https://vercel.com/docs/vercel-blob/usage-and-pricing)
- [Cron 실행 한도](https://vercel.com/docs/cron-jobs/usage-and-pricing)
- [Git 자동 배포 설정](https://vercel.com/docs/project-configuration/git-configuration)
- [함수 리전과 Hobby 단일 리전 제한](https://vercel.com/docs/functions/configuring-functions/region)

## 2026-09-19 구현·검증 상태

- 기존 `min-hyeok-s-projects/migam-home-preview`의 Hobby 플랜을 확인했다. 전용 private Blob `migam-data`를 Production에 연결했다. 운영 도메인은 아직 기존 배포를 유지한다.
- 전체 앱 미리보기 빌드 `dpl_GnQ264U6u7bZq1xkiSSq2Nda3jHp`가 READY다. Django의 끝 슬래시가 있는 경로도 `/api` 함수에 도달하도록 정규식 rewrite를 사용한다. 키·데이터가 없는 미리보기에서 `data_temporarily_unavailable`, 인증 없는 Cron에서 `unauthorized`를 실제 확인했다. 정상 검색·추천을 제공하는 운영 배포의 증거는 아니다.
- 백엔드 전체 323개 검사와 이후 추가한 목록 범위·배포 경로 검사 2개가 통과했다. 프론트 110개, OpenAPI 일치, 운영 프론트 빌드, migration 변경 없음, diff 형식 검사를 확인했다. 공개 WSGI의 실제 검색·host 검사·Admin 제외·DB 쓰기 거부도 가상 DB로 확인했다.
- 브라우저 시나리오 24개는 Chromium·390px 모바일·WebKit·공식 안내 프로젝트에서 통과했다. Firefox 7개는 Windows 바이너리의 side-by-side 구성 오류로 실행하지 못했다. 첫 전체 명령은 종료 대기 중 중단했고 Firefox 별도 재실행으로 환경 오류를 확인했다. 전체 E2E 명령 성공으로 간주하지 않는다.
- 운영 의존성 `npm audit --omit=dev`는 취약점 0건이었다. 빌드 도구를 포함한 Vercel 설치 로그에는 high 2건 경고가 있어 별도 의존성 검토 대상이다.
- `CULTURE_PORTAL_SERVICE_KEY`, `VITE_KAKAO_JAVASCRIPT_KEY`, 새 `DJANGO_SECRET_KEY`·`CRON_SECRET`을 해당 프로젝트 Production에 저장하는 작업은 자동 승인 검토가 명시적 비밀값 전송 동의를 요구하여 중단했다. 사용자의 안전성 질문에는 저장 방식과 접근 경계를 설명했으며 최종 저장 동의를 기다린다. 해당 4개 값은 아직 추가하지 않았다.
- 실제 공식 입력으로 초기 정본을 갱신·게시하는 작업, Production 배포, 원격 일일 수집 성공 및 실제 데이터 사용자 흐름 확인은 아직 남아 있다. 로컬 DB는 수정하지 않았다. 이후 사용자 요청에 따라 이 준비 상태를 커밋·푸시 대상으로 확정했다.

## 2026-09-21 운영 전환과 검증 결과

사용자는 네 값의 용도·공개 범위·Vercel Secret의 접근 경계 설명을 확인한 뒤, `min-hyeok-s-projects/migam-home-preview`의 Production에 기존 문화정보 API·카카오 JavaScript 키와 새 Django·Cron 비밀값을 저장하고 실제 데이터 갱신·운영 배포·검증을 마무리하도록 명시적으로 승인했다. 서버용 세 값은 Secret, 지도용 키는 공개 클라이언트 설정으로 관리한다. 유료 전환은 승인 범위에 포함하지 않는다.

첫 원격 수집에서 SeMA는 성공했고 세종 CSV는 불완전 전송, 문화정보는 시간 예산 초과로 실패했다. 공식 목록 17,895건을 100건씩 읽으면 최소 179회여서 100회 예산으로 완료할 수 없다. 실제 공식 첫 페이지에서 `numOfrows=1000` 요청과 응답 1,000건을 확인했으며, 기존 기간·기관 필터·엔드포인트를 유지한 채 페이지 크기만 조정한다. 서울 리전 복구 실행에서 두 서울 Source는 성공했으나 수원 2건은 공식 주소 표기 변경으로 기관 매칭에서 제외됐다. 확인된 정확한 주소 두 표기만 허용하는 근거를 `source-qualification.md`와 `sources.yaml`에 기록했고, 다른 주소와 임의 별관 표기는 계속 거부한다.

초기 배포의 수동 복구는 원인을 확인하고 수정한 실패에만 수행한다. 운영자는 이전 작업의 종료를 확인하고 해당 스냅샷·실패 실행·복구 사유를 보존한 뒤 완료된 날짜별 claim만 해제한다. 정상 예약 실행의 날짜별 중복 방지는 유지하며, 성공한 서울 입력은 캐시를 재사용하고 403·429 차단이나 구조 오류의 다운로드 마커는 해제하지 않는다.

- 승인된 네 값은 해당 프로젝트의 Production에만 저장했다. 문화정보·Django·Cron은 Secret, 지도 키는 공개 Config다. 기존 Blob 연결과 Hobby 플랜을 유지했다.
- 수정된 서울 리전 배포에서 `/api/refresh`가 HTTP 200과 세 Source의 `SUCCESS`를 반환하고 새 스냅샷을 게시했다. 초기 실패 기록은 삭제하지 않았다.
- 공식 URL의 HTML 엔티티 문제는 원문을 보존하면서 해석하도록 수정했다. 해당 전시 9건을 공식 상세 API로 다시 확인해 기존 파이프라인에서 성공 처리하고 정본을 게시했다. 일일 claim을 추가로 해제하지 않았다.
- 주소의 검토된 정확 일치 허용·미승인 주소 거부와 URL 원문 보존 회귀검사를 추가했고, 백엔드 전체 327개 테스트가 통과했다. 실제 검색·상세·제목 검색·빈 검색과 기본 추천 6건의 응답을 확인했다. 로컬 원본 DB의 SHA-256은 작업 전과 동일하다.
- [공개 운영 주소](https://migam-home-preview.vercel.app/)를 전체 앱으로 전환했다. 최초 운영 배포 `dpl_HA2exnLYDAmwqZgM6q7hTrmJiqfF`의 READY 상태와 서울 리전, `/api/refresh`의 일일 Cron 등록을 실제 프로젝트 메타데이터에서 확인했다. 한국 시간 매일 06시대이며 Hobby에서는 정확한 분 단위 실행을 보장하지 않는다. 원격 갱신 성공은 실제 운영 경로를 인증해 수동 실행한 결과이고, 다음 날 예약 시각의 첫 자동 실행은 아직 관찰하지 않았다.
- 공개 주소에서 인증 없는 갱신은 401, Admin 경로는 404였다. 같은 날짜의 인증된 재호출은 HTTP 200과 `ALREADY_CLAIMED`를 반환해 추가 수집을 막았다.
- 실제 Chromium 브라우저에서 검색→상세, 상세 직접 새로고침, 관심 저장 후 새로고침·저장 목록, 비교, 추천 6건, 기관 페이지와 카카오 지도 확대·복귀를 확인했다. 1440px 데스크톱과 390px 모바일 뷰포트를 사용했고 모바일 추천·상세에 가로 넘침이 없었다. 브라우저 오류는 0건이며 폰트 preload 사용 시점 경고만 있었다. 실제 모바일 기기 검증으로 간주하지 않는다.

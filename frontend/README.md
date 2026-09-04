# 미감 프론트엔드 · TP-006

React·TypeScript·Vite 기반의 미감 브랜드 홈과 전시·기관 탐색 화면입니다. `/`는 자체 생성한 가상 미술관 필름과 브랜드 관점만 담고 API를 호출하지 않습니다. `/discover`는 전시·기관 검색과 조건 추천을 소유하며, 검색은 조밀한 카탈로그 카드, 추천은 에디토리얼 카드로 구분합니다. Tailwind CSS, 직접 사용하는 Radix Dialog/Tabs, Lucide React를 사용합니다. 실제 취향 테스트·상세·관심 저장·비교·지도는 아직 포함하지 않습니다.

## 실행

Node.js 24.15 이상, npm, Python 3.11 이상, uv가 필요합니다. 검증 환경은 Windows, Node.js 24.15.0, npm 11.12.1입니다. 최초 의존성 설치에는 패키지 레지스트리 접근이 필요하지만 데모·자동 테스트에는 외부 API 키나 `.env`가 필요 없습니다.

저장소 루트의 첫 터미널:

```powershell
uv run --project backend python scripts/run_demo_api.py
```

`frontend`의 두 번째 터미널:

```powershell
npm ci --ignore-scripts
npm run dev:demo
```

[브랜드 홈](http://127.0.0.1:5173/)은 로컬 장식 자산만 사용합니다. [전시 탐색](http://127.0.0.1:5173/discover)은 Vite `/api` 프록시를 거쳐 Django `127.0.0.1:8001`의 실제 FTS5 검색·추천 서비스로 연결됩니다. `/discover#recommend`로 직접 들어가면 조건 추천 탭에서 시작합니다. 두 프로세스는 각각 `Ctrl+C`로 종료합니다. 데모 실행기는 재실행할 때 새 임시 SQLite를 만들고 정상 종료 시 정리합니다. 기존 `backend/db.sqlite3`를 읽거나 수정하지 않습니다. 데모 seed는 명시적 데모 설정 및 비어 있는 데이터베이스만 허용합니다.

가상 전시 10건·기관 3곳 중 기본 검색은 현재·예정 8건입니다. 종료·취소 전시는 상태를 선택해 확인할 수 있습니다. 추천에서 예산 `0`을 적용하면 주요 추천 2건과 가격 확인 필요 1건을 구분합니다. `휠체어 접근`·`섬광 회피`의 필수조건과 `제주` 0건도 체험할 수 있습니다. 가상 공식 링크는 이동 버튼을 제공하지 않습니다. 실제 Source의 추천 특성 수집·백필 완료를 의미하지 않습니다.

## 실제 로컬 DB 사용

데모 대신 기존 정본을 읽으려면 API 서버는 저장소 루트에서 다음으로 실행합니다. `migrate`는 실제 로컬 DB에 적용하므로 데모 체험만 할 때는 실행하지 않습니다.

```powershell
uv run --project backend python backend/manage.py migrate
uv run --project backend python backend/manage.py runserver 127.0.0.1:8000 --settings=backend.config.local_settings
```

프론트엔드는 `npm run dev`로 실행합니다. 이 모드는 `/api`를 `127.0.0.1:8000`으로 보내고 가상 데이터 표시를 사용하지 않습니다. 포트 5173이 이미 사용 중이면 종료한 뒤 모드를 바꿉니다. API가 없으면 입력을 유지한 오류와 재시도를 표시합니다. 외부 수집은 자동으로 시작하지 않으며 지역·근거가 부족한 실제 데이터는 결과가 적을 수 있습니다.

두 모드는 loopback 개발 전용입니다. 공개 배포·CORS 개방·인증 설정을 대신하지 않습니다.

## 데이터와 UI 경계

- [OpenAPI 정본](../openapi/internal-v1.yaml) → 생성 `src/shared/api/generated.ts` → openapi-fetch → Zod → UI 모델 순서입니다. 생성 파일은 직접 수정하지 않습니다.
- 검색 유형·정렬·상태와 추천의 지역·날짜·예산·분위기·안전·예약·시간 입력을 지원합니다. 기본 목록은 탭 진입 시 로드하며, 입력 변경은 검색/추천 버튼을 눌러야 적용됩니다.
- TanStack Query는 응답을 비영속 메모리에, Zustand는 draft와 적용 조건을 현재 페이지 메모리에만 둡니다. 새로고침하면 초기화됩니다. 입력을 페이지 URL·브라우저 저장소·로그·분석 서비스에 쓰지 않습니다.
- `/`에서는 discovery provider를 마운트하지 않고 API를 호출하지 않습니다. `/discover#recommend`는 사용자 입력이 아닌 고정 초기 탭 식별자이며 검색어·필터·추천 payload는 fragment나 query에 넣지 않습니다.
- 로컬 Django 접근 로그는 끄고 Vite 내부 API 프록시 오류의 query는 가립니다. 브라우저 자체 개발자 도구나 사용자가 설정한 기록 정책까지 통제하는 것은 아닙니다.
- 필수조건은 자동 해제하지 않습니다. 예약·시간 기본값은 선호이고, API가 구분한 확인 필요 후보를 주요 추천과 섞지 않습니다. 날짜는 전시 기간 비교이지 휴관일·예약 가능 여부 확인이 아닙니다.
- `INLINE` + 안전한 HTTP(S) URL만 이미지로 요청합니다. `HIDDEN`·`LINK_ONLY`·로드 실패는 텍스트 카드로 표시합니다. 외부 링크는 안전한 URL·새 탭·referrer 최소화 정책을 따릅니다.

## 검증

`frontend`에서:

```powershell
npm run api:check
npm test
npm run build
npm run format:check
```

`build`는 엄격한 TypeScript 검사와 프로덕션 번들 생성을 포함합니다. 관람시간 최소/최대 중 하나 이상을 요구하는 생성 타입도 컴파일 단계에서 검사합니다. OpenAPI를 바꾼 뒤에는 `npm run api:generate`로 갱신합니다. `npm run format`은 생성 타입을 제외한 프론트 코드만 정리합니다.

저장소 루트에서:

```powershell
uv run --project backend python backend/manage.py test tests --verbosity 1
git diff --check
```

자동 검증은 경계·요청·상태·컴포넌트 테스트와 실제 Django API 통합 테스트입니다. 브라우저 E2E·실제 모바일·200% 확대·스크린리더 검수는 아직 수행하지 않았습니다. 전체 P0 접근성 검증도 남아 있습니다. 구체적인 결과는 [TP-006 실행 증거](../docs/07-execution/task-packets/TP-006-frontend-discovery.md)에 기록합니다.

## 레퍼런스와 홈 자산

[OlfIt](https://github.com/Joraemon-s-Secret-Gadgets/olfit)은 여백, 얇은 구분선, 선택과 추천 이유의 연결만 참고했습니다. 자산·코드·문구·정확한 배색과 화면 구도는 복제하지 않았습니다. 미감의 기존 컬러와 시스템 한글 Serif/Sans를 사용하며 원격 폰트를 요청하지 않습니다.

[Houston Group](https://houstongroup.com.au/)에서는 고정 헤더, 첫 화면을 채우는 미디어, 큰 선언문과 풀폭 장면의 에디토리얼 리듬만 참고했습니다. 색감·세부 디자인·서체·코드·미디어는 복제하지 않았습니다. 미감 홈은 웜 아이보리·먹색·석회색·흐린 청회색·옅은 흙색으로 별도 구성합니다. 홈 이미지·영상의 출처와 사용 경계는 [홈 장식 미디어 자산](../docs/04-ux/assets/home/README.md)에 기록합니다.

# 홈 장식 미디어 자산

이 폴더의 원본은 2026-09-04에 미감 홈을 위해 이미지 생성 모델로 만든 프로젝트 자체 생성 자산이다. 외부 전시·작품·작가·기관의 이미지를 원본으로 사용하지 않았다. 모두 브랜드 분위기를 위한 장식이며 실제 전시 정보, 추천 근거 또는 `MediaAsset` 레코드와 연결하지 않는다.

## v2 몰입형 홈 필름

[`v2/source/`](v2/source/)의 PNG 6종은 하나의 가상 현대미술관을 배경으로 한 16:9 장면이다. 현재 배포 자산은 [`frontend/public/assets/home/film/`](../../../../frontend/public/assets/home/film/)의 섹션 WebP 3개, 1920×1080·960×540 poster 2개, 무음 MP4·WebM 2개다. 화면에서 직접 쓰지 않는 WebP 3개는 [`v2/derivatives/`](v2/derivatives/)에 보관한다.

공통 생성 지시는 `photorealistic-natural` 에디토리얼 미술관 사진, 자연광, 약한 35mm 필름 그레인, 웜 아이보리·먹색·석회색·흐린 청회색·옅은 흙색, 넓은 여백이다. 가상 인물은 특정 실존 인물을 닮지 않은 작은 실루엣이나 뒷모습만 허용한다. 실존 작품·작가·기관·브랜드·읽을 수 있는 표지·로고·워터마크, 원색·네온·강한 RGB 조명, 광고 캠페인 같은 광택을 금지한다.

| 원본 (`v2/source/`) | 장면 | WebP 위치·용도 |
| --- | --- | --- |
| `migam-film-01-morning-gallery-source.png` | 오전 자연광이 길게 들어오는 조용한 전시장과 관람객 한 명 | [제작용 파생본](v2/derivatives/migam-film-01-morning-gallery-1920.webp); 배포용 poster 2종의 원본 장면 |
| `migam-film-02-textile-walk-source.png` | 반투명 천 설치 사이를 천천히 걷는 두 사람 | [제작용 파생본](v2/derivatives/migam-film-02-textile-walk-1920.webp) |
| `migam-film-03-material-study-source.png` | 한지·도자·무광 금속이 겹친 물성 클로즈업 | [03 재료의 감각](../../../../frontend/public/assets/home/film/migam-film-03-material-study-1920.webp) |
| `migam-film-04-paused-gaze-source.png` | 넓은 여백 속 추상 조형물 앞 관람객의 뒷모습 | [02 머무는 시선](../../../../frontend/public/assets/home/film/migam-film-04-paused-gaze-1920.webp) |
| `migam-film-05-glass-corridor-source.png` | 얇은 유리와 겹친 그림자가 이어지는 복도형 전시장 | [01 공간의 온도](../../../../frontend/public/assets/home/film/migam-film-05-glass-corridor-1920.webp) |
| `migam-film-06-afterglow-source.png` | 사람이 빠져나간 뒤 빛만 남은 전시장 | [제작용 파생본](v2/derivatives/migam-film-06-afterglow-1920.webp) |

영상은 약 10~12초 동안 여섯 장면을 2~4%의 느린 패닝·확대와 짧은 디졸브로 연결한다. UI에서는 영상과 이미지에 빈 대체 텍스트 또는 접근성 트리 제외를 사용한다. `prefers-reduced-motion`, 모바일 우선 표시, 영상 로딩·재생 실패에서는 poster가 남고, 제목과 CTA는 항상 별도 HTML로 제공한다.

제작용 FFmpeg 필터는 [`v2/film-filter.txt`](v2/film-filter.txt)에 보존한다. 입력 0~5는 위 여섯 장면 순서다. 배포 영상의 `migam-home-film-v1` 파일명은 현재 사용하는 영상의 버전이며, 아래의 이전 이미지 시안 v1과 구분한다.

## v1 보존 자산

첫 에디토리얼 시안의 PNG 3개는 [`archive/v1/source/`](archive/v1/source/), 반응형 WebP 6개는 [`archive/v1/webp/`](archive/v1/webp/)에 보관한다. 각각 `migam-hero-space`, `migam-hero-material`, `migam-hero-refraction` 계열이다. 갈색 중심의 추상 구도는 v2에서 대체됐으며 현재 홈과 배포 폴더에는 포함하지 않는다.

홈에서 제외한 관점 문구는 [문구 기록](archive/editorial-copy.md)에 보존한다. 제작 원본·보관용 자료를 앱의 `public`에 복사하지 않으며, 실제 화면 구성은 [홈 설계](../../home-design.md)를 따른다.

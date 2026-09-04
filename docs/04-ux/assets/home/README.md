# 홈 장식 미디어 자산

이 폴더의 원본은 2026-09-04에 미감 홈을 위해 이미지 생성 모델로 만든 프로젝트 자체 생성 자산이다. 외부 전시·작품·작가·기관의 이미지를 원본으로 사용하지 않았다. 모두 브랜드 분위기를 위한 장식이며 실제 전시 정보, 추천 근거 또는 `MediaAsset` 레코드와 연결하지 않는다.

## v2 몰입형 홈 필름

`v2/source/`의 PNG 6종은 하나의 가상 현대미술관을 배경으로 한 16:9 장면이다. 프론트 파생본은 `frontend/public/assets/home/film/`의 1920×1080 WebP, 1920×1080·960×540 poster, 무음 MP4·WebM이다.

공통 생성 지시는 `photorealistic-natural` 에디토리얼 미술관 사진, 자연광, 약한 35mm 필름 그레인, 웜 아이보리·먹색·석회색·흐린 청회색·옅은 흙색, 넓은 여백이다. 가상 인물은 특정 실존 인물을 닮지 않은 작은 실루엣이나 뒷모습만 허용한다. 실존 작품·작가·기관·브랜드·읽을 수 있는 표지·로고·워터마크, 원색·네온·강한 RGB 조명, 광고 캠페인 같은 광택을 금지한다.

| 원본 | 장면 지시 | 프론트 파생본 |
| --- | --- | --- |
| `v2/source/migam-film-01-morning-gallery-source.png` | 오전 자연광이 길게 들어오는 조용한 전시장과 관람객 한 명 | `film/migam-film-01-morning-gallery-1920.webp`와 poster 2종 |
| `v2/source/migam-film-02-textile-walk-source.png` | 반투명 천 설치 사이를 천천히 걷는 두 사람 | `film/migam-film-02-textile-walk-1920.webp` |
| `v2/source/migam-film-03-material-study-source.png` | 한지·도자·무광 금속이 겹친 물성 클로즈업 | `film/migam-film-03-material-study-1920.webp` |
| `v2/source/migam-film-04-paused-gaze-source.png` | 넓은 여백 속 추상 조형물 앞 관람객의 뒷모습 | `film/migam-film-04-paused-gaze-1920.webp` |
| `v2/source/migam-film-05-glass-corridor-source.png` | 얇은 유리와 겹친 그림자가 이어지는 복도형 전시장 | `film/migam-film-05-glass-corridor-1920.webp` |
| `v2/source/migam-film-06-afterglow-source.png` | 사람이 빠져나간 뒤 빛만 남은 전시장 | `film/migam-film-06-afterglow-1920.webp` |

영상은 약 10~12초 동안 여섯 장면을 2~4%의 느린 패닝·확대와 짧은 디졸브로 연결한다. UI에서는 영상과 이미지에 빈 대체 텍스트 또는 접근성 트리 제외를 사용한다. `prefers-reduced-motion`, 모바일 우선 표시, 영상 로딩·재생 실패에서는 poster가 남고, 제목과 CTA는 항상 별도 HTML로 제공한다.

## v1 보존 자산

`source/`의 `migam-hero-space-source.png`, `migam-hero-material-source.png`, `migam-hero-refraction-source.png`와 `frontend/public/assets/home/`의 기존 WebP 6종은 첫 에디토리얼 시안 기록으로 보존한다. 갈색 중심의 추상 구도는 v2에서 대체됐으며 현재 홈 런타임에서는 참조하지 않는다.

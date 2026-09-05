# 미감 웹폰트

2026-09-05 사용자 결정에 따라 제목·전시명에는 **마루 부리**, 본문·검색창·필터·버튼·내비게이션에는 **SUIT**를 사용합니다. 로고 형태의 최종 확정은 OD-004에 남아 있습니다.

공식 배포 WOFF2 원본을 수정·서브셋 변환 없이 보관합니다. 필요한 굵기만 CSS에서 선언하고, 동일 출처의 `/assets/fonts/`에서 제공합니다. 외부 CDN 요청·설치형 의존성은 없습니다. 기본 굵기 두 파일을 preload하고 모든 굵기에 `font-display: swap`과 시스템 fallback을 적용합니다.

| 파일 | 굵기 | 바이트 | SHA-256 |
| --- | --- | ---: | --- |
| MaruBuri-Regular.woff2 | 400 | 433,776 | 4cf1341cf2f23fb3e263712dfde1d8f25eedcc328b696a2e5a2c8add55e5c17b |
| SUIT-Regular.woff2 | 400 | 167,672 | 7a1971b4e54d6d797f105f2d8ad2fc5f5d6fd532195f582d74f4403177e83185 |
| SUIT-Medium.woff2 | 500 | 170,956 | 8b69b1832781a1d08867c11979cb01023f7ade30e19cb9e0b8f93588964223f8 |
| SUIT-SemiBold.woff2 | 600 | 171,164 | a0ea79e549e2ef42930d16c9c5b40600132a7f3661fe0e26a84a20c2c8d182a0 |
| SUIT-Bold.woff2 | 700 | 171,380 | 044e7df5d44e38ea371e9d808165fdec8d05257589bdad21da8f3b79ad4000de |

## 공식 출처와 라이선스

- 마루 부리: [네이버 소개](https://hangeul.naver.com/maruproject_11), [공식 웹폰트 CSS](https://hangeul.pstatic.net/hangeul_static/css/maru-buri.css), [Regular WOFF2](https://hangeul.pstatic.net/hangeul_static/webfont/MaruBuri/MaruBuri-Regular.woff2).
- 마루 부리의 [네이버 공식 라이선스 안내](https://help.naver.com/service/11029/contents/18088?lang=ko&osType=PC)는 나눔글꼴과 동일한 SIL OFL 1.1을 적용합니다. 저작권 고지와 영문 전문은 [LICENSE-MARU-BURI.txt](LICENSE-MARU-BURI.txt)에 동봉합니다.
- SUIT: [제작자 저장소](https://github.com/sun-typeface/SUIT), [공식 배포 경로의 CSS](https://cdn.jsdelivr.net/gh/sun-typeface/SUIT@2/fonts/static/woff2/SUIT.css). CSS와 같은 디렉터리에서 위 네 파일을 확보했습니다.
- SUIT의 저작권 고지와 SIL OFL 1.1 전문은 [LICENSE-SUIT.txt](LICENSE-SUIT.txt)에 동봉합니다. [원본 라이선스](https://cdn.jsdelivr.net/gh/sun-typeface/SUIT@2/LICENSE)와 함께 보관합니다.

폰트를 교체·재배포할 때도 각 저작권 고지와 라이선스 전문을 포함합니다. 폰트 자체의 단독 판매는 허용되지 않습니다.

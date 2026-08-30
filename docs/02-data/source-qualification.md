---
title: "미감(美感) P0 Source Qualification"
status: APPROVED
version: "1.0.0"
last_updated: "2026-08-30"
authoritative_for:
  - "OD-003 후보 기관의 최근 전시 표본 심사 증거"
  - "공식 구조화 출처의 접근·권리·필드 검증 현황"
  - "실제 P0 allowlist 확정 전에 남은 차단 조건"
related_documents:
  - "../00-governance/decision-register.md"
  - "./data-source-policy.md"
  - "./data-model.md"
  - "./data-pipeline.md"
  - "../07-execution/implementation-readiness.md"
---

# 미감(美感) P0 Source Qualification

## 1. 목적과 판정 경계

이 문서는 `OD-003`을 해결하기 위한 후보 심사 증거다. 출처 정책을 새로 정의하거나, `sources.yaml`을 대신하거나, 이 기록만으로 기관을 `PROVISIONAL`에 올리지 않는다. 판정 기준은 [Data Source Policy](data-source-policy.md)의 최근 전시 5건, 최소 4건 `CORE_PASS`, 구조적 핵심 누락과 정책·접근 제한 시 `HOLD` 규칙을 그대로 따른다.

- 검토 기준 시각: `2026-08-30`, `Asia/Seoul`
- 표본 범위: 공식 기관 페이지의 현재·예정 전시와 시작일 기준 가장 최근 종료 전시
- 핵심 항목: 전시명, 정확한 시작일·종료일, 실제 장소, 행정 지역, 유효 상태, 전시 단위 공식 상세 URL, 공식 책임 출처
- 페이지 표본 합격과 자동 수집 Source 합격을 별도로 판정한다.
- 이미지, 포스터, 작품 이미지와 장문 설명은 사실 메타데이터와 별도 권리 검토 전까지 수집·저장·표시 대상이 아니다.

## 2. 현재 결론

초기 후보 6곳의 공식 페이지 표본과 후속 대체 후보를 검토했다. 두 인증키도 로컬 환경에 주입했다. 한눈에보는문화정보조회서비스는 정식 키로 `resultCode=00`을 확인했고, 서울 열린데이터광장에는 HTTP Open API와 별도로 HTTPS에서 내려받을 수 있는 공식 `Sheet` 데이터가 있음을 확인했다.

실응답과 대체 Source를 비교한 결과 최종 allowlist 추천안 5곳을 확보했다. 세종문화회관 본관 전시공간, 서울시립 서서울미술관, 서울시립 사진미술관, 수원시립미술관 행궁 본관은 `5/5 CORE_PASS`, 국립민속박물관 서울 본관은 `4/5 CORE_PASS`다. 민속박물관의 실패 1건은 해당 실패 건을 포함한 본관 API 레코드 총 9건 점검에서 한 번만 확인된 공식 URL 공란으로 `RECORD_EXCEPTION` 격리가 가능하다.

초기 후보 중 서울시립미술관 운영망 표본은 공식 HTTPS Sheet 묶음으로 `5/5`를 충족했지만, 최종 추천안에서는 물리적으로 독립된 주소와 장소 코드를 가진 서서울미술관과 사진미술관을 별도 Institution 후보로 심사한다. 서울역사박물관 본관은 최근 5건 `4/5`, 확장 10건 `8/10`이어도 실제 장소 평탄화가 반복되어 `HOLD`다. 나머지 후보도 날짜 충돌·누락·최신성 또는 자동 수집 이용조건 문제로 `HOLD`다.

따라서 현재 판정은 다음과 같다.

- 최종 승인 5곳: 후보 심사 `PASS`, 첫 lifecycle `PROVISIONAL`
- 서울시립미술관 운영망 5건 표본: `PASS`; 최종안에서는 서서울·사진미술관의 독립된 5건 표본으로 대체
- 서울역사박물관 공식 HTTPS Sheet: 최근 5건 `4/5`, 확장 10건 `8/10`; 반복 장소 평탄화로 `HOLD`
- 서울공예박물관 공식 HTTPS Sheet: `2/5`, `HOLD`
- 문화정보 API: 인증·호출 `PASS`; MMCA는 표본 `5/5`이나 추가 현재 전시 날짜 충돌 재검증 전 `HOLD`, 대한민국역사박물관·예술의전당은 기준 미달 `HOLD`
- 서울 HTTP Open API: 안전한 HTTPS 전송 경로가 없어 사용하지 않음
- InstitutionAllowlistEntry: 승인 5곳 `PROVISIONAL`, 나머지 후보는 `CANDIDATE`의 `HOLD` 심사 결과 유지
- [`sources.yaml`](../../sources.yaml): 승인 Source 3개와 InstitutionAllowlistEntry 5개 등록
- [고정 fixture](../../fixtures/source-qualification.json): 표본 25건, `CORE_PASS` 24건, 격리 1건
- `OD-003`: `RESOLVED`
- 직접 HTML 크롤링: 이용조건·robots·호출 제한의 명시적 허용이 확인되지 않아 금지

## 3. 공식 구조화 출처 심사

### 3.1 서울 열린데이터광장: HTTP Open API와 HTTPS Sheet

| 항목 | 확인 결과 |
| --- | --- |
| 공식 등록 | [서울 열린데이터광장 — 서울시 문화행사 정보 `OA-15486`](https://data.seoul.go.kr/dataList/OA-15486/S/1/datasetView.do) |
| 책임 주체 | 서울특별시 문화본부 문화정책과, 원천 시스템 서울문화포털 |
| HTTP Open API | `http://openapi.seoul.go.kr:8088/{KEY}/json/culturalEventInfo/{START}/{END}/` |
| HTTPS Sheet | Sheet 미리보기 최대 1,000건, 전체 데이터는 CSV 다운로드. Open API 외 서비스는 약관 동의 후 인증키 없이 이용 가능 |
| 기관별 보강 | [세종문화회관 `OA-2708`](https://data.seoul.go.kr/dataList/OA-2708/S/1/datasetView.do), [SeMA 국문 `OA-15323`](https://data.seoul.go.kr/dataList/OA-15323/S/1/datasetView.do), [SeMA 영문 `OA-15324`](https://data.seoul.go.kr/dataList/OA-15324/S/1/datasetView.do) |
| 갱신 | `OA-15486` 매일 1회, SeMA 영문 매일, SeMA 국문 변경 시. 검토일 데이터 갱신일 `2026-08-30` |
| 이용조건 | 공공누리 제1유형, 출처표시 조건으로 상업적 이용·변경 가능, 제3저작권자 없음. 결과 노출 시 `서울특별시 공공데이터` 사용 표시 필요 |
| 핵심 후보 필드 | `TITLE`, `STRTDATE`, `END_DATE`, `PLACE`, `GUNAME`, `ORG_NAME`, `HMPG_ADDR` |
| 보조 필드 | `CODENAME`, `DATE`, `USE_FEE`, `INQUIRY`, `ORG_LINK`, 좌표, 행사시간 |
| 제외 필드 | `MAIN_IMG`, 장문 설명·프로그램·출연자 정보는 별도 권리·필요성 승인 전 제외 |

`HMPG_ADDR`는 서울문화포털의 전시 단위 상세 URL 후보로 사용한다. `ORG_LINK`는 예매처나 제3자 사이트일 수 있으므로 공식 기관 도메인 allowlist를 통과하기 전에는 정본 상세 URL로 채택하지 않는다.

공개 `sample` 응답은 HTTP에서 `INFO-000`으로 성공해 스키마를 확인했다. 그러나 endpoint는 인증키를 URL 경로에 포함하며 HTTPS 8088 연결은 TLS handshake 단계에서 실패한다. 서울 열린데이터광장도 [2026-08-27 공식 답변](https://data.seoul.go.kr/together/notice/inquireView.do?seq=6e6a8a4b04f963e2ad09f73d961a6027&ditcCd=QNA01&pageIndex=1&bbsCd=10003)에서 HTTPS를 현재 지원하지 않고 향후 지원도 어렵다고 밝혔다. [Open API 이용안내](https://data.seoul.go.kr/together/guide/useGuide.do)와 [FAQ](https://data.seoul.go.kr/together/notice/faqList.do?bbsCd=10002&ditcCd=FAQ02&seq=d47bc57aea53d6c6ab244c05a6eb2259)에도 HTTP 8088 주소만 안내되어 있다.

따라서 인증서 검증 우회 대상이 아니며, 정식 키를 평문 HTTP로 보내는 실호출은 하지 않는다. 대신 [이용약관](https://data.seoul.go.kr/etc/accessTerms.do)이 파일변환·다운로드 서비스를 정의하고 인증키 없는 이용과 출처표시 조건을 명시한 HTTPS Sheet를 공식 데이터 파일 Source로 심사한다. Sheet 다운로드의 내부 세션·폼 경로와 JSON 변환 경로는 공개 REST 계약으로 채택하지 않는다. 전체 CSV 파일 어댑터만 사용하고 응답 헤더·스키마 smoke test와 변경 감지를 둔다. 별도 다운로드 할당량은 공개되지 않았으므로 P0에서는 Source 갱신 확인당 최대 1회 순차 다운로드하고 `403`·`429`에서 즉시 중단하며 무제한 이용을 가정하지 않는다.

#### 3.1.1 초기 후보의 HTTPS Sheet 표본 판정

| 후보 범위 | 공식 Sheet 결과 | 판정 |
| --- | --- | --- |
| 서울시립미술관 운영망 | `OA-15486` 단독 `4/5`; 국문·영문 SeMA Sheet를 묶으면 `5/5` | 후보 심사 `PASS` |
| 서울공예박물관 | `2/5`; 1건 누락, 장소 오값 1건, 종료일 오값 1건 | `HOLD` |
| 서울역사박물관 본관 | 최근 5건 `4/5`, 확장 10건 `8/10`; `여민공수`는 본관·분관 장소를 합치고 `마음의 사귐, 여운이 물결처럼`은 기획전시실 A·B를 포괄 장소로 평탄화 | 반복적 실제 장소 손실로 `HOLD` |

SeMA의 누락 행 `AMOR EX MACHINA`는 영문 Sheet와 공식 영문 상세에서 보완된다. 서울공예박물관은 `안동별궁`이 Sheet의 전시1동 3층과 공식 페이지의 전시3동 3층으로 충돌하고, `漆-옻나무에서 칠기로` 종료일도 Sheet `2025-12-31`과 공식 `2026-12-31`이 충돌한다. 서울역사박물관은 `여민공수`의 본관·분관 합침뿐 아니라 확장 표본에서도 `기획전시실 A, B`를 `기획전시실`로 축약했다. 같은 핵심 필드에서 2/10 실패가 반복되므로 한 행만의 `RECORD_EXCEPTION`으로 격리하지 않는다.

#### 3.1.2 기관 원본 HTTPS Sheet 대체 후보

| 후보 범위 | 공식 Sheet | Source 결과 | 판정 |
| --- | --- | ---: | --- |
| 세종문화회관 본관 전시공간 | [세종문화회관 공연·전시 정보 `OA-2708`](https://data.seoul.go.kr/dataList/OA-2708/S/1/datasetView.do) | `5/5` | 후보 심사 `PASS` |
| 서울시립 서서울미술관 | [SeMA 국문 `OA-15323`](https://data.seoul.go.kr/dataList/OA-15323/S/1/datasetView.do), `DP_PLACE='서울시립 서서울미술관'` | `5/5` | 후보 심사 `PASS` |
| 서울시립 사진미술관 | [SeMA 국문 `OA-15323`](https://data.seoul.go.kr/dataList/OA-15323/S/1/datasetView.do), `DP_PLACE='서울시립 사진미술관'` | `5/5` | 후보 심사 `PASS` |

두 Sheet는 공공누리 제1유형이고 전체 CSV를 HTTPS로 내려받을 수 있다. `OA-2708`은 `2026-08-29`, `OA-15323`은 `2026-08-30` 갱신본을 확인했다. 제목·기간·실제 장소·전시 단위 공식 상세 URL을 허용하고, 지역은 [세종문화회관 공식 주소](https://www.sejongpac.or.kr/portal/performance/exhibit/performList.do?menuNo=200558), [서서울미술관 공식 주소](https://sema.seoul.go.kr/kr/visit/seoseoul), [사진미술관 공식 주소](https://sema.seoul.go.kr/kr/visit/photosema)를 정확한 장소값과 고정 매핑한다. 상태는 시작일·종료일과 기준시각으로 파생한다. 이미지와 장문 설명은 제외한다.

`OA-2708`은 공연과 전시가 섞인 Source이므로 다음 필드와 교집합 필터를 고정한다. 원본 ID는 `PERFORM_IDX`, 제목은 `TITLE`, 기간은 `START_DATE`·`END_DATE`, 실제 장소는 `PLACE_LIST`, 공식 상세 URL은 `INFO_URL`이다.

```text
GENRE_NAME IN ('전시기타', '기획전시')
AND PLACE_LIST IN (
  '세종미술관 1관',
  '세종미술관 2관',
  '세종미술관 1관,세종미술관 2관',
  '세종미술관1/2관',
  '야외전시'
)
AND INFO_URL의 performIdx = PERFORM_IDX
AND INFO_URL의 menuNo = '200558'
```

`뮤지컬`, `연극`, `클래식`, `국악`, `공연기타`, `체험` 장르와 전시 allowlist 밖 장소는 제외한다. `menuNo=200558`은 한국어 전시 상세 경로를 확인해 공연 상세와 영문 중복을 차단하는 무결성 가드다.

`OA-15323`은 `DP_EX_NO`를 원본 ID로 사용하고 `DP_SEQ`는 사용하지 않는다. 제목은 `DP_NAME`, 기간은 `DP_START`·`DP_END`, 실제 장소는 `DP_PLACE`, 공식 상세 URL은 `DP_LNK`다. 서서울·사진미술관은 다음 필터와 URL 무결성 가드를 각각 적용한다.

```text
DP_PLACE IN (
  '서울시립 서서울미술관',
  '서울시립 사진미술관'
)
AND DP_LNK의 호스트·경로 =
  https://sema.seoul.go.kr/kr/whatson/exhibition/detail
AND query(DP_LNK).exNo = DP_EX_NO
```

`ORG50`·`ORG51`은 Sheet 값이 아니라 SeMA 공식 웹 목록의 `exPlace` 교차검증 코드이므로 원본 필터나 기관 식별자로 저장하지 않는다.

### 3.2 한눈에보는문화정보조회서비스

| 항목 | 확인 결과 |
| --- | --- |
| 공식 등록 | [공공데이터포털 — 한국문화정보원 한눈에보는문화정보조회서비스](https://www.data.go.kr/data/15138937/openapi.do) |
| 목록 호출 | `https://apis.data.go.kr/B553457/cultureinfo/period2` |
| 상세 호출 | `https://apis.data.go.kr/B553457/cultureinfo/detail2` |
| 인증·제한 | 공공데이터포털 `serviceKey` 필수. 개발계정 일일 10,000회, 개발·운영 자동승인 |
| 실응답 | 정식 키에서 `resultCode=00`; `2025-01-01`~`2027-12-31`, 공연·전시 범주의 전체 건수 `28,321` 확인 |
| 이용조건 | 무료, 이용허락범위 제한 없음 |
| 핵심 후보 필드 | `seq`, 제목, 시작일·종료일, 장소, 주소·지역, 기관 공식 상세 URL |
| 제외 필드 | 이미지·포스터·기관 장문 설명은 개별 KOGL 또는 권리 승인 전 제외 |

정확 일치 검색만으로는 표본을 안정적으로 찾을 수 없었다. `×`, `「」`·`《》`, 부제와 긴 제목이 정규화되거나 축약되어 부분 키워드 조회와 `detail2` 교차확인이 필요했다. 따라서 제목만으로 레코드를 동일시하지 않고 `seq`, 기간, 장소, 기관 공식 URL을 함께 비교했다.

#### 3.2.1 정식 키 실응답 판정

| 후보 범위 | API 레코드 매핑 | 후보 범위 기준 `CORE_PASS` | 핵심 문제 | 판정 |
| --- | ---: | ---: | --- | --- |
| 국립현대미술관 서울 | `5/5` | `5/5` | 추가 현재 전시 1건의 종료일이 공식 최신값과 충돌 | 재검증 전 `HOLD` |
| 대한민국역사박물관 | `4/5` | `2/5` | 1건 미조회, 종료일 충돌 2건 | `HOLD` |
| 예술의전당 한가람미술관 제7전시실 | `4/5` | `0/5` | 1건 미조회, 매핑 4건 모두 제7전시실 확인 불가 | `HOLD` |

`API 레코드 매핑`은 같은 전시로 식별 가능한 행을 찾았다는 뜻이며 `CORE_PASS`가 아니다. 전역 정책은 API 하나가 층·전시실까지 제공할 것을 요구하지 않으며, 공식 Source 묶음의 필드별 증거를 허용한다. MMCA 서울과 대한민국역사박물관처럼 후보 범위가 건물인 경우 건물 수준 장소도 실제 개최 장소로 인정할 수 있다. 반면 후보 자체가 `제7전시실`인 예술의전당 행은 어떤 승인 Source에서든 해당 전시실 근거가 필요하다. 총 15건 중 13건을 공식 상세 URL까지 매핑했고, 현재 후보 범위 기준 7건이 `CORE_PASS`다.

| 기관 | 표본 전시 | 문화정보 `seq` | 결과 |
| --- | --- | ---: | --- |
| MMCA | 서도호 | `366251` | 건물 범위 `CORE_PASS` |
| MMCA | 사각사각 소곤소곤 | `395525` | 건물 범위 `CORE_PASS`; 영문 제목으로만 검색하면 누락 |
| MMCA | MMCA×LG OLED 시리즈 2026 | `364982` | 건물 범위 `CORE_PASS` |
| MMCA | 올해의 작가상 2026 | `364451` | 건물 범위 `CORE_PASS` |
| MMCA | 이것은 개념미술이 (아니)다 | `364984` | `CORE_PASS` |
| 대한민국역사박물관 | 다시 보는 제헌절 | `394040` | 종료일 `2026-08-31`로 충돌 |
| 대한민국역사박물관 | 바람의 길목 DMZ | `394039` | 건물 범위 `CORE_PASS` |
| 대한민국역사박물관 | 밤풍경 | `371276` | 종료일 `2026-03-22`로 충돌 |
| 대한민국역사박물관 | 1945-1948 역사 되찾기, 다시 우리로 | `371277` | 건물 범위 `CORE_PASS` |
| 대한민국역사박물관 | 태극기, 함께해 온 나날들 | — | 레코드 미조회 |
| 예술의전당 | 스페인의 거장 고야 | `385759` | 기간·공식 URL 일치, 제7전시실 누락 |
| 예술의전당 | 2026 서리풀 청년작가 특별전 「작업 진행 중」 | `379137` | 제목 괄호 정규화, 제7전시실 누락 |
| 예술의전당 | 2026 청년미술상점 아트페어 | — | 레코드 미조회 |
| 예술의전당 | DAF2026 : ART & DESIGN 경계를 넘어 | `376670` | 기간·공식 URL 일치, 제7전시실 누락 |
| 예술의전당 | 볼로냐 일러스트 원화전 59th | `363852` | 제목 축약, 기간·공식 URL 일치, 제7전시실 누락 |

대한민국역사박물관의 두 종료일은 공식 상세와 직접 충돌한다. `다시 보는 제헌절`의 공식 종료일은 `2026-10-11`이고, `밤풍경`은 `2026-06-22`다. MMCA 추가 표본 `그래도 해보던 날들`도 문화정보 `seq=376588`은 `2026-08-30` 종료지만 현재 MMCA 공식 목록은 `2027-02-28`이다. 반환 13건의 상세 URL은 각 기관 공식 도메인으로 연결되었지만, URL 일치만으로 날짜·장소 누락을 상쇄하지 않는다. MMCA는 이 변경이 다음 공식 갱신 안에 반영되는지 재확인하기 전까지 Source를 보류한다.

#### 3.2.2 문화정보 API 대체 후보

| 후보 범위 | `CORE_PASS` | 핵심 결과 | 판정 |
| --- | ---: | --- | --- |
| 수원시립미술관 행궁 본관 | `5/5` | `seq`, 기간, 정조로 833 주소, 경기·수원 지역, 전시별 SUMA 공식 URL 일치 | 후보 심사 `PASS` |
| 국립민속박물관 서울 본관 | `4/5` | 4건 일치; `seq=348222` 한 건만 `detail2.url` 공란 | 단건 격리 조건으로 후보 심사 `PASS` |
| 경기도미술관 | `3/5` | 예정전 1건 미조회, 종료일 없는 상설전 1건 최소 품질 실패 | `HOLD` |
| 인천아트플랫폼 | `3/5` | 최근 표본 2건 미조회 | `HOLD` |
| 국립중앙박물관 용산관 | `2/5` | 최근 테마전 3건 연속 미조회 | `HOLD` |
| 국립고궁박물관 서울관 | `3/5` | 1건 미조회, 1건 종료일 충돌 | `HOLD` |

국립민속박물관은 본관으로 정확히 분류되는 API 레코드 9건의 `detail2`를 추가 점검했고 공식 URL 공란은 `seq=348222` 한 건에서만 나타났다. 이 레코드는 정본에 넣지 않고 `RECORD_EXCEPTION`으로 격리한다. 같은 필드에서 다시 발생하면 즉시 반복 패턴으로 재분류해 해당 Institution 범위를 차단한다. 문화정보 API에서는 제목·기간·장소·주소·지역·공식 URL만 사용하고, 이미지·포스터·장문 설명은 제외한다.

### 3.3 기관 자체 구조화 출처

| 기관 | 공식 구조화 후보 | 기술 표본 | 정책·운영 판정 |
| --- | --- | ---: | --- |
| MMCA | [공식 전시 JSON](https://www.mmca.go.kr/exhibitions/AjaxExhibitionList.do), [공개 CSV](https://www.mmca.go.kr/exhibitions/AjaxExhibitionListCsv.do?langCd=KOR&pageIndex=1&ExcelDate=Y) | JSON `5/5` | JSON은 비문서화 내부 endpoint이고 CSV에는 안정된 상세 식별자가 없어, 반복 이용 확인·안전한 교차키 설계 전 `HOLD` |
| 대한민국역사박물관 | [전용 KCISA API](https://www.data.go.kr/data/15121511/openapi.do?recommendDataYn=Y) `getMCHBspecial` | 현재 키로 검증 불가 | 한눈에보는문화정보 키와 별도 활용신청 필요; 발급 후 5건 재검증 |
| 예술의전당 제7전시실 | [공식 목록 JSON](https://www.sac.or.kr/site/main/show/dataList), [공공데이터 CSV](https://www.data.go.kr/data/3076480/fileData.do?recommendDataYn=Y) | JSON `5/5`, CSV `2/5` | JSON은 비문서화 내부 endpoint, CSV는 2026-05 갱신으로 최신성 부족; 반복 이용 확인 전 `HOLD` |

MMCA와 예술의전당의 내부 JSON은 제목·기간·정확한 전시실·상태·공식 상세 식별자를 기술적으로 모두 제공한다. 그러나 웹 화면이 사용한다는 사실만으로 자동 반복 수집·저장 허가를 추정하지 않는다. 대한민국역사박물관 전용 API endpoint는 `https://api.kcisa.kr/openapi/service/rest/meta2020/getMCHBspecial`이며, 현재 발급받은 키와 다른 서비스 승인 범위다.

### 3.4 경기도 데이터

[공공데이터포털의 경기도 문화 행사 현황](https://www.data.go.kr/data/15117057/openapi.do)은 실시간·무료·이용허락범위 제한 없음으로 등록되어 있으나, 연결된 경기데이터드림 상세에는 요청 주소·서비스명·출력 필드·샘플 URL이 노출되지 않아 호출을 재현할 수 없었다. 임의로 추정한 서비스명은 사용하지 않는다.

기존 통합 데이터 대신 안내된 [경기문화재단 전시 프로그램](https://data.gg.go.kr/portal/data/service/selectServicePage.do?infId=Z1DVMOXKESXV0PKD9WXH31859759&infSeq=1) 등 대체 데이터도 정식 키에서 생성되는 요청 URL·스키마·샘플 응답을 확인하기 전까지 `HOLD`다. 이에 따라 경기도미술관과 백남준아트센터는 이번 P0 초기 후보에서 제외한다.

### 3.5 기관 공식 HTML

기관 페이지는 표본 검증과 API 결과 교차확인의 증거로만 사용한다. 자동 접근을 명시적으로 허용하는 약관·robots·호출 제한을 확인하지 못한 기관 페이지는 수집 Source로 등록하지 않는다. 브라우저에 공개되어 있다는 사실만으로 반복 수집·저장·재배포 허가를 추정하지 않는다.

## 4. P0 최종 allowlist 추천안

| 후보 범위 | 승인할 공식 Source | Source 결과 | 허용 핵심 매핑 | 후보 판정 |
| --- | --- | ---: | --- | --- |
| 세종문화회관 본관 전시공간 | 서울 공식 HTTPS Sheet `OA-2708` | `5/5` | 원본 ID, 제목, 기간, 장소, 공식 상세 URL; 종로구 고정 매핑; 상태 날짜 파생 | `PASS` |
| 서울시립 서서울미술관 | 서울 공식 HTTPS Sheet `OA-15323` | `5/5` | 원본 ID, 제목, 기간, `DP_PLACE`, 공식 상세 URL; 정확 장소값→금천구 고정 매핑; 상태 날짜 파생 | `PASS` |
| 서울시립 사진미술관 | 서울 공식 HTTPS Sheet `OA-15323` | `5/5` | 원본 ID, 제목, 기간, `DP_PLACE`, 공식 상세 URL; 정확 장소값→도봉구 고정 매핑; 상태 날짜 파생 | `PASS` |
| 수원시립미술관 행궁 본관 | 문화정보 API `period2`·`detail2` | `5/5` | `seq`, 제목, 기간, 장소, 주소·지역, 공식 상세 URL; 상태 날짜 파생 | `PASS` |
| 국립민속박물관 서울 본관 | 문화정보 API `period2`·`detail2` | `4/5` | 같은 필드; `seq=348222`은 공식 URL 공란으로 격리 | `PASS` |

이 다섯 곳은 서울 4곳과 경기 1곳, 미술관·박물관·공공문화공간을 포함한다. 서서울미술관과 사진미술관은 같은 운영 기관·Source를 공유하지만 서로 다른 물리 주소와 안정된 장소 코드를 가진 별도 Institution이다. 운영 기관, 실제 개최 장소, 주최 기관을 같은 식별자로 합치지 않으며 같은 제목의 다른 장소·기간 occurrence를 제목만으로 중복 제거하지 않는다. 모든 후보에서 이미지·포스터·장문 설명은 허용 필드에서 제외한다.

## 5. 후보별 최근 전시 5건

아래 URL은 수집 대상이 아니라 표본 판정과 향후 API 레코드 매핑 근거다. 각 행은 검토 시점에 핵심 항목을 모두 확인해 `CORE_PASS`로 판정했다.

### 5.1 국립현대미술관 서울 — `5/5`

| 전시 | 기간 | 장소 | 공식 상세 |
| --- | --- | --- | --- |
| 서도호 | 2026-08-27 ~ 2027-02-09 | 서울 지하 1층 3·4·5전시실, 2층 MMCA 스튜디오 | [MMCA `exhId=202601200002041`](https://www.mmca.go.kr/exhibitions/exhibitionsDetail.do?exhFlag=2&exhId=202601200002041) |
| 사각사각 소곤소곤 (Crinkle, Crinkle, Whisper, Whisper) | 2026-08-15 ~ 2026-10-25 | 서울 교육동 2층 | [MMCA `exhId=202608200002088`](https://www.mmca.go.kr/exhibitions/exhibitionsDetail.do?exhFlag=2&exhId=202608200002088) |
| MMCA×LG OLED 시리즈 2026 | 2026-07-31 ~ 2026-11-29 | 서울 B1 서울박스 | [MMCA `exhId=202601060002028`](https://www.mmca.go.kr/exhibitions/exhibitionsDetail.do?exhFlag=2&exhId=202601060002028) |
| 올해의 작가상 2026 | 2026-07-24 ~ 2026-12-06 | 서울 1층·지하 1층 | [MMCA `exhId=202512310002018`](https://www.mmca.go.kr/exhibitions/exhibitionsDetail.do?exhId=202512310002018) |
| 이것은 개념미술이 (아니)다 | 2026-06-19 ~ 2026-10-11 | 국립현대미술관 서울 | [MMCA `exhId=202601060002027`](https://www.mmca.go.kr/exhibitions/exhibitionsDetail.do?exhFlag=1&exhId=202601060002027) |

### 5.2 서울시립미술관 운영망 — `5/5`

| 전시 | 기간 | 장소 | 공식 상세 |
| --- | --- | --- | --- |
| 김희천: 두더지들 | 2026-08-20 ~ 2026-11-08 | 서울시립 서서울미술관 B1 제1·2전시실, 다목적홀 | [SeMA `exNo=1565012`](https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1565012) |
| 조숙진: 지나가는 자리 | 2026-07-29 ~ 2026-11-15 | 서울시립 남서울미술관 1층 야외, 2층 전시실 | [SeMA `exNo=1556711`](https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1556711) |
| 유영국: 산은 내 안에 있다 | 2026-05-19 ~ 2026-10-25 | 서울시립미술관 서소문본관 1층 | [SeMA `exNo=1529410`](https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1529410) |
| AMOR EX MACHINA | 2026-04-30 ~ 2026-09-06 | 서울시립미술관 서소문본관 2·3층, 크리스탈 갤러리 | [SeMA English `exNo=1526751`](https://sema.seoul.go.kr/en/whatson/exhibition/detail?exNo=1526751) |
| 가나아트컬렉션 《기술의 저변: 경계에 선 장면들》 | 2026-04-16 ~ 2026-11-22 | 서울시립미술관 서소문본관 2층 | [SeMA `exNo=1509709`](https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1509709) |

### 5.3 서울공예박물관 — `5/5`

| 전시 | 기간 | 장소 | 공식 상세 |
| --- | --- | --- | --- |
| 공예동행@쇼윈도 #5. 사라진 뒤에도 이어지는 길 | 2026-09-09 ~ 2026-10-11 | 전시3동 1층 쇼윈도 갤러리 | [SeMoCA `193`](https://craftmuseum.seoul.go.kr/exhibit/plan/view/193) |
| 제2회 서울시 유리지공예상 기념전 | 2026-09-01 ~ 2026-10-11 | 전시1동 1층 로비 | [SeMoCA `192`](https://craftmuseum.seoul.go.kr/exhibit/plan/view/192) |
| 공예동행@쇼윈도 #4. 몸에 베인 기억을 묻다 | 2026-07-22 ~ 2026-08-30 | 전시3동 1층 쇼윈도 갤러리 | [SeMoCA `191`](https://craftmuseum.seoul.go.kr/exhibit/plan/view/191) |
| 공예협력전시 《안동별궁, 시간의 겹》 | 2026-04-28 ~ 2027-08-29 | 전시3동 3층 | [SeMoCA `184`](https://craftmuseum.seoul.go.kr/exhibit/plan/view/184) |
| 漆-옻나무에서 칠기로 | 2025-06-27 ~ 2026-12-31 | 전시2동 3층 공예아카이브실 | [SeMoCA `161`](https://craftmuseum.seoul.go.kr/exhibit/plan/view/161) |

### 5.4 대한민국역사박물관 — `5/5`

| 전시 | 기간 | 장소 | 공식 상세 |
| --- | --- | --- | --- |
| 다시 보는 제헌절 | 2026-07-16 ~ 2026-10-11 | 3층 다목적홀 | [NMCKH `EXH_0000000262`](https://www.much.go.kr/MUCH/contents/M02010100000.do?exhCode=EXH_0000000262&page=1&schExhCategory=EXH01&schM=view&searchExhDivision=play) |
| 바람의 길목 DMZ | 2026-06-11 ~ 2026-09-13 | 3층 기획전시실 | [NMCKH `EXH_0000000258`](https://www.much.go.kr/MUCH/contents/M02010100000.do?exhCode=EXH_0000000258&page=1&schExhCategory=EXH01&schM=view&searchExhDivision=play) |
| 밤풍경 | 2025-12-11 ~ 2026-06-22 | 3층 주제관 | [NMCKH `EXH_0000000252`](https://www.much.go.kr/MUCH/contents/M02010100000.do?exhCode=EXH_0000000252&page=1&schExhCategory=EXH01&schM=view&searchExhDivision=play) |
| 1945-1948 역사 되찾기, 다시 우리로 | 2025-12-18 ~ 2026-03-31 | 3층 기획전시실 | [NMCKH 공식 웹진](https://www.much.go.kr/webzine/vol56/s01.html) |
| 태극기, 함께해 온 나날들 | 2025-08-08 ~ 2025-11-16 | 3층 전시실 | [NMCKH `EXH_0000000248`](https://www.much.go.kr/MUCH/contents/M02010100000.do?exhCode=EXH_0000000248&page=1&schExhCategory=EXH01&schM=view&searchExhDivision=play) |

### 5.5 예술의전당 한가람미술관 제7전시실 — `5/5`

| 전시 | 기간 | 장소 | 공식 상세 |
| --- | --- | --- | --- |
| 스페인의 거장 고야: 이성이 잠들 때, 괴물이 깨어난다 | 2026-06-26 ~ 2026-09-30 | 한가람미술관 제7전시실 | [SAC `SN=78392`](https://www.sac.or.kr/site/main/show/show_view?SN=78392) |
| 2026 서리풀 청년작가 특별전 「작업 진행 중」 | 2026-05-30 ~ 2026-06-14 | 한가람미술관 제7전시실 | [SAC `SN=76452`](https://www.sac.or.kr/site/main/show/show_view?SN=76452) |
| 2026 청년미술상점 아트페어 | 2026-05-22 ~ 2026-05-24 | 한가람미술관 제7전시실 | [SAC `SN=76459`](https://www.sac.or.kr/site/main/show/show_view?SN=76459) |
| DAF2026 : ART & DESIGN 경계를 넘어 | 2026-04-16 ~ 2026-05-16 | 한가람미술관 제7전시실 | [SAC `SN=78013`](https://www.sac.or.kr/site/main/show/show_view?SN=78013&tab=5) |
| 77가지 시선, 일상 속 행복을 물들이다 볼로냐 일러스트 원화전 59th | 2025-12-27 ~ 2026-03-28 | 한가람미술관 제7전시실 | [SAC `SN=76172`](https://www.sac.or.kr/site/main/show/show_view?SN=76172) |

### 5.6 서울역사박물관 본관 — `5/5`

| 전시 | 기간 | 장소 | 공식 상세 |
| --- | --- | --- | --- |
| 서울도시계획 대관람 | 2026-08-14 ~ 2026-11-08 | 기획전시실 A | [서울역사박물관 `seq=20260723145427523`](https://museum.seoul.go.kr/www/board/NR_boardView.do?bbsCd=1002&q_exhSttus=next&seq=20260723145427523&sso=ok) |
| 여민공수與民共守 | 2026-07-14 ~ 2026-10-25 | 기획전시실 B | [서울역사박물관 `seq=20260615104640628`](https://museum.seoul.go.kr/www/board/NR_boardView.do?bbsCd=1002&q_exhSttus=next&seq=20260615104640628&sso=ok) |
| 한성부입니다 | 2026-04-30 ~ 2026-07-12 | 기획전시실 A | [서울역사박물관 `seq=20260415102529675`](https://museum.seoul.go.kr/www/board/NR_boardView.do?bbsCd=1002&q_exhSttus=next&seq=20260415102529675&sso=ok) |
| 볼 빨간 돼지의 종이 모험 | 2026-03-27 ~ 2026-06-07 | 기획전시실 B | [서울역사박물관 `seq=20260304133907030`](https://museum.seoul.go.kr/www/board/NR_boardView.do?bbsCd=1002&q_exhSttus=next&seq=20260304133907030&sso=ok) |
| BURTYNSKY: EXTRACTION / ABSTRACTION | 2025-12-13 ~ 2026-03-02 | 기획전시실 A | [서울역사박물관 `seq=20251117091555682`](https://museum.seoul.go.kr/www/board/NR_boardView.do?bbsCd=1002&q_exhSttus=next&seq=20251117091555682&sso=ok) |

`여민공수`의 Sheet 행은 본관과 한양도성박물관의 기간·장소를 한 행에 합친다. 확장 표본 5건 중 4건은 일치했지만, `마음의 사귐, 여운이 물결처럼`도 공식 상세의 `기획전시실 A, B`를 Sheet에서 `기획전시실`로 축약했다. 전체 10건 중 실제 장소 실패가 2건 반복되므로 제목만으로 occurrence를 분리하거나 포괄 장소를 정답으로 저장하지 않는다.

확장 표본은 `한글편지, 문안 아뢰옵고`, `미증유의 대홍수: 1925 을축년`, `우리들의 광복절`, `국무령 이상룡과 임청각`이 Sheet와 공식 상세에서 일치했다. [`마음의 사귐, 여운이 물결처럼`](https://museum.seoul.go.kr/www/board/NR_boardView.do?bbsCd=1002&q_exhSttus=prev&seq=20250420195650848&sso=ok)은 기간·지역·상태·공식 URL은 일치했으나 실제 장소가 불일치해 확장 5건은 `4/5 CORE_PASS`다.

### 5.7 세종문화회관 본관 전시공간 — `5/5`

| 전시 | 기간 | 장소 | 공식 상세 |
| --- | --- | --- | --- |
| 제3회 호반미술상 | 2026-09-02 ~ 2026-09-29 | 세종미술관 1·2관 | [세종문화회관 `performIdx=37607`](https://www.sejongpac.or.kr/portal/performance/performance/performTicket.do?performIdx=37607&menuNo=200558) |
| 인상주의를 넘어: 르누아르 · 드가 · 고흐 · 마티스 · 피카소 | 2026-05-28 ~ 2026-08-23 | 세종미술관 1·2관 | [세종문화회관 `performIdx=37023`](https://www.sejongpac.or.kr/portal/performance/performance/performTicket.do?performIdx=37023&menuNo=200558) |
| 박신양의 전시쑈 《제4의 벽》 | 2026-03-06 ~ 2026-05-10 | 세종미술관 1·2관 | [세종문화회관 `performIdx=36909`](https://www.sejongpac.or.kr/portal/performance/performance/performTicket.do?performIdx=36909&menuNo=200558) |
| 2026 아뜰리에 광화 봄전시 《피어나는 빛》 | 2026-04-11 ~ 2026-06-19 | 야외전시 | [세종문화회관 `performIdx=37167`](https://www.sejongpac.or.kr/portal/performance/performance/performTicket.do?performIdx=37167&menuNo=200558) |
| 2025 아뜰리에 광화 겨울 전시 《영원》 | 2025-12-21 ~ 2026-03-19 | 야외전시 | [세종문화회관 `performIdx=36879`](https://www.sejongpac.or.kr/portal/performance/performance/performTicket.do?performIdx=36879&menuNo=200558) |

### 5.8 서울시립 서서울미술관 — `5/5`

| 전시 | 기간 | 장소 | 공식 상세 |
| --- | --- | --- | --- |
| 플레이 라운지 《어쩌면 우리에게 더 멋진 일이 있을지도 몰라》 | 2026-09-01 ~ 2026-10-11 | 서울시립 서서울미술관 | [SeMA `exNo=1576627`](https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1576627) |
| 미디어 작가전 《김희천: 두더지들》 | 2026-08-20 ~ 2026-11-08 | 서울시립 서서울미술관 | [SeMA `exNo=1565012`](https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1565012) |
| 개관 특별 미디어 소장품전 《서서울의 투명한 \|청소년\| 기계》 | 2026-05-14 ~ 2026-07-26 | 서울시립 서서울미술관 | [SeMA `exNo=1528398`](https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1528398) |
| SeMA 프로젝트V_얄루 | 2026-03-12 ~ 2026-07-26 | 서울시립 서서울미술관 | [SeMA `exNo=1498110`](https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1498110) |
| 개관특별전 《우리의 시간은 여기서부터》 | 2026-03-12 ~ 2026-07-26 | 서울시립 서서울미술관 | [SeMA `exNo=1498975`](https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1498975) |

### 5.9 서울시립 사진미술관 — `5/5`

| 전시 | 기간 | 장소 | 공식 상세 |
| --- | --- | --- | --- |
| 《마틴 파 : We Are Martin Parr》 | 2026-07-16 ~ 2026-10-18 | 서울시립 사진미술관 | [SeMA `exNo=1553791`](https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1553791) |
| 2026 서울사진축제 《컴백홈》 | 2026-04-09 ~ 2026-06-14 | 서울시립 사진미술관 | [SeMA `exNo=1515171`](https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1515171) |
| 《사진이 할 수 있는 모든 것》 | 2025-11-26 ~ 2026-03-01 | 서울시립 사진미술관 | [SeMA `exNo=1470699`](https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1470699) |
| 《광채光彩: 시작의 순간들》 | 2025-05-29 ~ 2025-10-12 | 서울시립 사진미술관 | [SeMA `exNo=1409653`](https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1409653) |
| 스토리지 스토리 Storage Story | 2025-05-29 ~ 2025-10-12 | 서울시립 사진미술관 | [SeMA `exNo=1410085`](https://sema.seoul.go.kr/kr/whatson/exhibition/detail?exNo=1410085) |

### 5.10 수원시립미술관 행궁 본관 — `5/5`

| 전시 | 기간 | 장소 | 공식 상세·문화정보 ID |
| --- | --- | --- | --- |
| 2026 국제전 《패트리샤 피치니니: 킨쉽》 | 2026-07-23 ~ 2026-11-01 | 수원시립미술관 행궁 본관 | [SUMA `ge_idx=1266`](https://suma.suwon.go.kr/exhi/current_view.do?lang=ko&ge_idx=1266), `seq=394181` |
| 2026 소장품전 《블랑 블랙 파노라마》 | 2026-02-12 ~ 2027-03-01 | 수원시립미술관 행궁 본관 | [SUMA `ge_idx=1258`](https://suma.suwon.go.kr/exhi/schedule_view.do?lang=ko&ge_idx=1258), `seq=368076` |
| 《입는 존재》 | 2026-03-19 ~ 2026-06-28 | 수원시립미술관 행궁 본관 | [SUMA `ge_idx=1260`](https://suma.suwon.go.kr/exhi/current_view.do?lang=ko&ge_idx=1260), `seq=372683` |
| 2025 동시대미술전 《공생》 | 2025-09-26 ~ 2026-03-02 | 수원시립미술관 행궁 본관 | [SUMA `ge_idx=1250`](https://suma.suwon.go.kr/exhi/current_view.do?lang=ko&ge_idx=1250), `seq=347904` |
| 《머무르는 순간, 흐르는 마음》 | 2025-09-26 ~ 2026-01-11 | 수원시립미술관 행궁 본관 | [SUMA `ge_idx=1252`](https://suma.suwon.go.kr/exhi/current_view.do?lang=ko&ge_idx=1252), `seq=347906` |

### 5.11 국립민속박물관 서울 본관 — 공식 페이지 `5/5`, 문화정보 API `4/5`

| 전시 | 기간 | 장소 | 공식 상세·문화정보 ID |
| --- | --- | --- | --- |
| 제로: 민속의 길에서 만난 북한 | 2026-08-12 ~ 2027-02-14 | 본관 기획전시실 Ⅰ | [NFM `planExhibitionIdx=1640`](https://www.nfm.go.kr/user/planexhibition/home/20/selectPlanExhibitionNView.do?planExhibitionIdx=1640&page=1), `seq=394528` |
| 가나다락-글놀이 말놀이 | 2026-05-13 ~ 2026-08-30 | 본관 기획전시실 2 | [NFM `planExhibitionIdx=1637`](https://www.nfm.go.kr/user/planexhibition/home/20/selectPlanExhibitionNView.do?planExhibitionIdx=1637&page=1), `seq=380350` |
| 말馬들이 많네-우리 일상 속 말 | 2025-12-16 ~ 2026-03-02 | 본관 기획전시실 2 | [NFM `planExhibitionIdx=1632`](https://www.nfm.go.kr/user/planexhibition/home/20/selectPlanExhibitionLView.do?planExhibitionIdx=1632&page=1), `seq=365861` |
| 출산, 모두의 잔치 | 2025-12-03 ~ 2026-05-10 | 본관 기획전시실 1 | [NFM `planExhibitionIdx=1631`](https://www.nfm.go.kr/user/planexhibition/home/20/selectPlanExhibitionLView.do?planExhibitionIdx=1631&page=1), `seq=365859` |
| 다시 만난 하늘: 보물 신·구법천문도 복원기 | 2025-09-17 ~ 2025-11-03 | 본관 기획전시실 2 | [NFM `planExhibitionIdx=1611`](https://www.nfm.go.kr/user/planexhibition/home/20/selectPlanExhibitionLView.do?page=1&planExhibitionIdx=1611), `seq=348222` |

마지막 행은 문화정보 `detail2.url`이 공란이므로 자동 수집 결과에서는 `CORE_FAIL`로 격리한다. 공식 페이지 URL을 수동으로 채워 정상 레코드처럼 승격하지 않는다.

## 6. 보류한 다른 후보

| 후보 | 페이지 표본 | `HOLD` 사유 |
| --- | ---: | --- |
| 국립현대미술관 서울 | `5/5` | 문화정보 표본은 `5/5`지만 추가 현재 전시 종료일이 공식 최신값보다 6개월 짧고 안정된 보완 Source 결합이 미확정 |
| 서울공예박물관 | `5/5` | 공식 Sheet `2/5`; 1건 누락, 장소 오값 1건, 종료일 오값 1건 |
| 대한민국역사박물관 | `5/5` | 문화정보 `2/5`; 1건 누락, 종료일 충돌 2건; 전용 API는 별도 활용신청 필요 |
| 예술의전당 한가람미술관 제7전시실 | `5/5` | 문화정보 `0/5`; 공식 JSON 이용조건 미확인, 공개 CSV 최신성 부족 |
| 서울역사박물관 본관 | `5/5` | 공식 Sheet 최근 `4/5`, 확장 `8/10`; 실제 장소 평탄화가 반복됨 |
| 아르코미술관 | `5/5` | 승인된 구조화 API를 확인하지 못했고 웹페이지 반복 접근·재사용 범위가 불명확함 |
| 리움미술관 | `3/5` | 최근 표본에서 핵심 항목 누락이 허용 한도를 넘음 |
| 서울시립 북서울미술관 | `4/5` | 상시 야외조각전의 Sheet 종료일이 `2020-12-31`로 남아 최신성 충돌 |
| 경기도미술관 | `3/5` | 문화정보에서 예정전 1건 미조회, 종료일 없는 상설전 1건 최소 품질 실패 |
| 백남준아트센터 | `4/5` | 대체 경기도 API의 실제 endpoint·스키마·샘플 응답 미확인 |
| 인천아트플랫폼 | `3/5` | 문화정보에서 최근 표본 2건 미조회 |
| 국립중앙박물관 용산관 | `2/5` | 문화정보에서 최근 테마전 3건 연속 미조회 |
| 국립고궁박물관 서울관 | `3/5` | 문화정보에서 1건 미조회, 1건 종료일 충돌 |

## 7. 인증키 발급 후 실행 기록과 후속 작업

인증키는 저장소, 문서, fixture, 로그에 기록하지 않고 환경 변수나 로컬 비밀 저장소로만 전달한다.

### 7.1 서울 열린데이터광장

1. 일반 OpenAPI 인증키 발급과 `SEOUL_OPEN_DATA_KEY` 로컬 주입을 완료했다.
2. `sample` 키로 스키마와 정상 응답을 확인했다.
3. 정식 키는 URL 경로에 포함되어 평문 HTTP로 전송되므로 실호출하지 않았다. 로그 마스킹만으로 전송 구간 노출을 해결할 수 없다.
4. 별도 인증키 없이 HTTPS로 내려받는 공식 Sheet를 대체 Source로 확인하고 기관별 표본을 검증했다. 최종 추천안의 세종문화회관 본관 전시공간, 서서울미술관, 사진미술관은 각각 `5/5`다.
5. 초기 후보 중 서울시립미술관 운영망은 `5/5`, 서울공예박물관은 `2/5`, 서울역사박물관 본관은 확장 표본 `8/10`이다. 서울 HTTP Open API 키는 계속 사용하지 않는다.
6. 승인 Sheet 3곳의 15개 표본을 비밀값 없는 고정 fixture로 만들고 원본 ID·공식 URL·기간·장소 매핑을 재현했다.

### 7.2 한눈에보는문화정보조회서비스

1. `CULTURE_PORTAL_SERVICE_KEY` 로컬 주입과 정식 키 성공 응답 확인을 완료했다.
2. `period2`의 기간 조회와 부분 키워드 검색, `detail2`를 함께 사용해 15개 표본 중 13개를 기관 공식 상세 URL까지 매핑했다.
3. 후보 범위 기준 결과는 MMCA 서울 `5/5`, 대한민국역사박물관 `2/5`, 예술의전당 제7전시실 `0/5 CORE_PASS`다.
4. MMCA는 표본 자체는 통과했지만 추가 현재 전시의 종료일이 공식 최신값보다 6개월 짧아 다음 갱신 반영을 확인하기 전까지 `HOLD`다. 나머지 두 후보는 기준 미달이다.
5. 대체 후보에서는 수원시립미술관 행궁 본관 `5/5`, 국립민속박물관 서울 본관 `4/5`로 후보 심사를 통과했다.
6. 경기도미술관·인천아트플랫폼·국립고궁박물관은 `3/5`, 국립중앙박물관 용산관은 `2/5`로 `HOLD`다.
7. 승인 API 2곳의 10개 표본도 같은 fixture에 포함했다. `seq=348222`은 공식 URL 공란을 그대로 `CORE_FAIL`·`RECORD_EXCEPTION`으로 보존하며, 이미지·포스터·장문 설명은 계속 제외한다.

## 8. OD-003 종료 조건

다음을 모두 충족할 때만 `OD-003`을 `RESOLVED`로 바꾸고 `sources.yaml`을 만든다.

1. 최종 기관 5~10곳마다 비밀값을 노출하지 않는 HTTPS 수집 경로와 호출·다운로드 제한을 기록한다. 추천안 5곳은 이 조건을 충족한다.
2. 후보 기관별 최근 전시 5건 중 최소 4건이 승인할 Source 묶음에서도 `CORE_PASS`다. 추천안 5곳은 각각 `5/5`, `5/5`, `5/5`, `5/5`, `4/5`로 충족한다.
3. 같은 핵심 필드의 반복 누락, 기관·분관 오귀속, 제목만의 잘못된 중복 제거가 없다.
4. 공식 상세 URL과 원본 식별자 매핑을 고정 fixture로 재현할 수 있다.
5. 허용 필드를 사실 메타데이터로 제한하고 이미지·장문 콘텐츠 권리 경계를 기록한다.
6. 통과한 기관만 `PROVISIONAL`로 등록하고, 실패 기관은 증거와 함께 `HOLD`로 남긴다.

승인 5곳은 표본·안전한 접근·이용조건 게이트를 충족했고, 비밀값 없는 fixture에서 원본 ID·공식 URL 매핑과 `5/5`, `5/5`, `5/5`, `5/5`, `4/5` 판정을 재현했다. [`sources.yaml`](../../sources.yaml)에 승인 Source 3개와 5곳을 `PROVISIONAL`로 등록하고 실패 후보는 이 문서의 `HOLD` 증거로 남겼으므로 `OD-003`을 `RESOLVED`로 전환한다.

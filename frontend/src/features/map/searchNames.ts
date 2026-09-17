import type { Place } from './provider';

type ReviewedTarget = {
  institution: string;
  area: string;
  venues?: string[];
  name: string;
  placeNames?: string[];
  address: string;
  source: string;
  note?: string;
};

// Search hints, not canonical location data. Reviewed 2026-09-17.
// Evidence and venue scope: docs/06-quality/map-search-verification.md.
const reviewedTargets: ReviewedTarget[] = [
  {
    institution: '세종문화회관 본관 전시공간',
    area: '서울 종로구',
    venues: [
      '세종미술관 1관',
      '세종미술관 2관',
      '세종미술관 1관,세종미술관 2관',
      '세종미술관1/2관',
    ],
    name: '세종미술관',
    placeNames: ['세종문화회관 미술관'],
    address: '서울 종로구 세종대로 175',
    source: 'https://www.sejongpac.or.kr/portal/main/contents.do?menuNo=200352',
  },
  {
    institution: '서울시립 서서울미술관',
    area: '서울 금천구',
    name: '서울시립 서서울미술관',
    address: '서울 금천구 시흥대로79길 65',
    source: 'https://sema.seoul.go.kr/kr/sema/landing',
  },
  {
    institution: '서울시립 사진미술관',
    area: '서울 도봉구',
    name: '서울시립 사진미술관',
    address: '서울 도봉구 마들로13길 68',
    source: 'https://sema.seoul.go.kr/kr/visit/photosema',
  },
  {
    institution: '서울시립 북서울미술관',
    area: '서울 노원구',
    name: '서울시립 북서울미술관',
    address: '서울 노원구 동일로 1238',
    source: 'https://sema.seoul.go.kr/kr/visit/bukseoul',
  },
  {
    institution: '서울시립미술관 서소문본관',
    area: '서울 중구',
    name: '서울시립미술관 서소문본관',
    address: '서울 중구 덕수궁길 61',
    source: 'https://sema.seoul.go.kr/kr/visit/seosomun',
  },
  {
    institution: '수원시립미술관 행궁 본관',
    area: '경기 수원시',
    name: '수원시립미술관',
    address: '경기 수원시 팔달구 정조로 833',
    source:
      'https://www.suwon.go.kr/sw-www/sw-visitsuwon/sw-visitsuwon-01/sw-visitsuwon-01-05/sw-visitsuwon-01-05-01.jsp',
  },
  {
    institution: '서울시립 남서울미술관',
    area: '서울 관악구',
    name: '서울시립 남서울미술관',
    address: '서울 관악구 남부순환로 2076',
    source: 'https://sema.seoul.go.kr/kr/visit/namseoul',
  },
  {
    institution: '서울시립 미술아카이브',
    area: '서울 종로구',
    name: '서울시립 미술아카이브',
    placeNames: ['서울시립 미술아카이브 모음동'],
    address: '서울 종로구 평창문화로 101',
    source: 'https://sema.seoul.go.kr/kr/visit/art_archive',
    note: '여러 동으로 나뉜 기관입니다. 방문할 동과 전시실은 공식 전시 안내에서 확인해주세요.',
  },
  {
    institution: '국립민속박물관 서울 본관',
    area: '서울 종로구',
    name: '국립민속박물관',
    venues: ['국립민속박물관 서울 본관', '국립민속박물관 서울 본관 기획전시실 Ⅰ'],
    placeNames: ['국립민속박물관 본관'],
    address: '서울 종로구 삼청로 37',
    source: 'https://www.nfm.go.kr/',
  },
];

const compact = (value: string) => value.replace(/\s+/g, '');
export const normalizeAddress = (value: string) =>
  value
    .trim()
    .replace(/\s+/g, ' ')
    .replace(/^서울특별시 /, '서울 ')
    .replace(/^경기도 /, '경기 ');

export function mapSearchPlan(institution: string, area: string, venue = institution) {
  const target = reviewedTargets.find(
    (entry) =>
      entry.institution === institution &&
      entry.area === area &&
      (entry.venues ?? [entry.institution]).some((name) => compact(name) === compact(venue)),
  );
  const names = [target?.name ?? (venue.trim() || institution), institution];
  return { target, area, queries: [...new Set(names.map((name) => `${area} ${name}`))] };
}

export function matchesMapPlace(place: Place, plan: ReturnType<typeof mapSearchPlan>) {
  const address = normalizeAddress(place.address);
  if (!plan.target) return address.startsWith(`${normalizeAddress(plan.area)} `);
  if (address !== normalizeAddress(plan.target.address)) return false;
  if (place.kind === 'address') return true;
  return [plan.target.name, ...(plan.target.placeNames ?? [])].some(
    (name) => compact(name) === compact(place.name),
  );
}

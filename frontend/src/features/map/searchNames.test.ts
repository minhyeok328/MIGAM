import { expect, it } from 'vitest';
import { mapSearchPlan, matchesMapPlace } from './searchNames';

const cases = [
  [
    '세종문화회관 본관 전시공간',
    '서울 종로구',
    '세종미술관 1관,세종미술관 2관',
    '세종미술관',
    '서울 종로구 세종대로 175',
  ],
  [
    '서울시립 서서울미술관',
    '서울 금천구',
    '서울시립 서서울미술관',
    '서울시립 서서울미술관',
    '서울 금천구 시흥대로79길 65',
  ],
  [
    '서울시립 사진미술관',
    '서울 도봉구',
    '서울시립 사진미술관',
    '서울시립 사진미술관',
    '서울 도봉구 마들로13길 68',
  ],
  [
    '서울시립 북서울미술관',
    '서울 노원구',
    '서울시립 북서울미술관',
    '서울시립 북서울미술관',
    '서울 노원구 동일로 1238',
  ],
  [
    '서울시립미술관 서소문본관',
    '서울 중구',
    '서울시립미술관 서소문본관',
    '서울시립미술관 서소문본관',
    '서울 중구 덕수궁길 61',
  ],
  [
    '수원시립미술관 행궁 본관',
    '경기 수원시',
    '수원시립미술관 행궁 본관',
    '수원시립미술관',
    '경기 수원시 팔달구 정조로 833',
  ],
  [
    '서울시립 남서울미술관',
    '서울 관악구',
    '서울시립 남서울미술관',
    '서울시립 남서울미술관',
    '서울 관악구 남부순환로 2076',
  ],
  [
    '서울시립 미술아카이브',
    '서울 종로구',
    '서울시립 미술아카이브',
    '서울시립 미술아카이브',
    '서울 종로구 평창문화로 101',
  ],
  [
    '국립민속박물관 서울 본관',
    '서울 종로구',
    '국립민속박물관 서울 본관 기획전시실 Ⅰ',
    '국립민속박물관',
    '서울 종로구 삼청로 37',
  ],
];

it.each(cases)('covers the reviewed venue for %s', (institution, area, venue, name, address) => {
  const plan = mapSearchPlan(institution, area, venue);
  expect(plan.queries[0]).toBe(`${area} ${name}`);
  expect(plan.target?.address).toBe(address);
  expect(plan.queries.length).toBeLessThanOrEqual(2);
  expect(new Set(plan.queries).size).toBe(plan.queries.length);
});

it('does not reuse indoor or main-building hints for another venue or region', () => {
  expect(mapSearchPlan(cases[0][0], cases[0][1], '야외전시').target).toBeUndefined();
  expect(mapSearchPlan(cases[8][0], cases[8][1], '국립민속박물관 파주관').target).toBeUndefined();
  expect(
    mapSearchPlan(cases[5][0], cases[5][1], '수원시립 아트스페이스광교').target,
  ).toBeUndefined();
  expect(mapSearchPlan(cases[0][0], '서울 중구', cases[0][2]).target).toBeUndefined();
});

it('uses actual venue then institution for future unregistered institutions without guessing aliases', () => {
  const plan = mapSearchPlan('새 문화재단', '서울 강남구', '새 전시장 2관');
  expect(plan.queries).toEqual(['서울 강남구 새 전시장 2관', '서울 강남구 새 문화재단']);
  expect(plan.target).toBeUndefined();
});

it('rejects unrelated facilities, another district and another address', () => {
  const plan = mapSearchPlan(cases[3][0], cases[3][1], cases[3][2]);
  const place = {
    id: '1',
    name: '서울시립북서울미술관',
    address: cases[3][4],
    latitude: 37,
    longitude: 127,
  };
  expect(matchesMapPlace(place, plan)).toBe(true);
  expect(matchesMapPlace({ ...place, name: '서울시립북서울미술관 주차장' }, plan)).toBe(false);
  expect(matchesMapPlace({ ...place, name: '카페세마' }, plan)).toBe(false);
  expect(matchesMapPlace({ ...place, address: '서울 노원구 동일로 1239' }, plan)).toBe(false);
  const unreviewed = mapSearchPlan('미술관', '서울 중구', '전시장');
  expect(matchesMapPlace({ ...place, address: '서울 중구 덕수궁길 61' }, unreviewed)).toBe(true);
  expect(matchesMapPlace(place, unreviewed)).toBe(false);
});

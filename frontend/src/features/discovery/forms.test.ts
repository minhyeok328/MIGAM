import { describe, expect, it } from 'vitest';
import {
  buildRecommendationRequest,
  buildSearchRequest,
  emptyRecommendationDraft,
  emptySearchDraft,
} from './forms';
import { createDiscoveryStore } from './store';

describe('explicit discovery inputs', () => {
  it('sends an exhibition period without claiming verified opening dates', () => {
    expect(
      buildRecommendationRequest({
        ...emptyRecommendationDraft,
        start: '2026-09-07',
        end: '2026-09-13',
        accessibility: ['WHEELCHAIR_ACCESS'],
      }),
    ).toEqual({
      limit: 6,
      exhibition_dates: { start: '2026-09-07', end: '2026-09-13' },
      required_accessibility: ['WHEELCHAIR_ACCESS'],
    });
  });
  it('keeps only explicit safety and taste conditions in the launch request', () => {
    expect(
      buildRecommendationRequest({
        ...emptyRecommendationDraft,
        accessibility: ['WHEELCHAIR_ACCESS'],
        sensory: ['FLASHING_LIGHTS'],
        moods: ['CALM'],
      }),
    ).toEqual({
      limit: 6,
      required_accessibility: ['WHEELCHAIR_ACCESS'],
      avoided_sensory: ['FLASHING_LIGHTS'],
      preferred_features: [{ axis: 'MOOD', value: 'CALM' }],
    });
    expect(buildRecommendationRequest(emptyRecommendationDraft)).toEqual({ limit: 6 });
  });

  it.each([
    { start: '2026-09-20', end: '2026-09-10' },
    { start: '2026-02-30', end: '2026-03-01' },
    { start: '2026-09-10' },
    { district: '종로구' },
    { moods: ['CALM', 'LIVELY', 'IMMERSIVE', 'EXPERIMENTAL'] },
  ])('rejects invalid inputs without silently removing conditions: %j', (patch) => {
    expect(() => buildRecommendationRequest({ ...emptyRecommendationDraft, ...patch })).toThrow();
  });

  it('encodes search enums and region without carrying recommendation payload', () => {
    expect(
      buildSearchRequest({
        ...emptySearchDraft,
        q: ' 소리 ',
        type: 'INSTITUTION',
        area: '서울',
        lifecycle: 'ENDED',
      }),
    ).toEqual({
      q: '소리',
      type: 'INSTITUTION',
      region_area: '서울',
      lifecycle: ['ENDED'],
      sort: 'RELEVANCE',
      page_size: 24,
    });
    expect(buildSearchRequest(emptySearchDraft).lifecycle).toBeUndefined();
  });

  it('keeps draft separate until apply and gives each applied search a new revision', () => {
    const store = createDiscoveryStore();
    store.getState().setSearch({ q: '첫 검색' });
    expect(store.getState().searchRequest.q).toBeUndefined();
    store.getState().applySearch();
    const revision = store.getState().searchRevision;
    store.getState().setSearch({ q: '수정 중' });
    expect(store.getState().searchRequest.q).toBe('첫 검색');
    store.getState().setTab('recommend');
    store.getState().setTab('search');
    expect(store.getState().searchDraft.q).toBe('수정 중');
    store.getState().applySearch();
    expect(store.getState().searchRevision).toBe(revision + 1);
    expect(store.getState().searchRequest.q).toBe('수정 중');
  });
});

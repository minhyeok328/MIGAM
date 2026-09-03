import { describe, expect, it } from 'vitest';
import {
  buildRecommendationRequest,
  buildSearchRequest,
  emptyRecommendationDraft,
  emptySearchDraft,
} from './forms';
import { createDiscoveryStore } from './store';

describe('explicit discovery inputs', () => {
  it('preserves free budget and separates required safety from preferred visits', () => {
    expect(
      buildRecommendationRequest({
        ...emptyRecommendationDraft,
        budget: '0',
        accessibility: ['WHEELCHAIR_ACCESS'],
        sensory: ['FLASHING_LIGHTS'],
        reservationType: 'NOT_REQUIRED',
        durationMax: '90',
        moods: ['CALM'],
      }),
    ).toEqual({
      limit: 6,
      max_budget_krw: 0,
      required_accessibility: ['WHEELCHAIR_ACCESS'],
      avoided_sensory: ['FLASHING_LIGHTS'],
      reservation: { mode: 'PREFERRED', types: ['NOT_REQUIRED'] },
      duration: { mode: 'PREFERRED', maximum_minutes: 90 },
      preferred_features: [{ axis: 'MOOD', value: 'CALM' }],
    });
  });

  it('sends required reservation and duration only when explicitly selected', () => {
    expect(
      buildRecommendationRequest({
        ...emptyRecommendationDraft,
        reservationType: 'TIMED_ENTRY',
        reservationMode: 'REQUIRED',
        durationMin: '30',
        durationMax: '90',
        durationMode: 'REQUIRED',
      }),
    ).toMatchObject({
      reservation: { mode: 'REQUIRED', types: ['TIMED_ENTRY'] },
      duration: { mode: 'REQUIRED', minimum_minutes: 30, maximum_minutes: 90 },
    });
    expect(buildRecommendationRequest(emptyRecommendationDraft)).toEqual({ limit: 6 });
  });

  it.each([
    { start: '2026-09-20', end: '2026-09-10' },
    { start: '2026-02-30', end: '2026-03-01' },
    { start: '2026-09-10' },
    { budget: '-1' },
    { budget: '100abc' },
    { budget: 'Infinity' },
    { durationMin: '100', durationMax: '50' },
    { durationMax: '0' },
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

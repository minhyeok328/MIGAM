import { beforeEach, expect, it } from 'vitest';
import { createPersonalStore, personalKey, recommendationSignals } from './store';

beforeEach(() => localStorage.clear());

it('does not discard existing interests when the limit is reached', () => {
  const store = createPersonalStore(false);
  for (let id = 1; id <= 101; id++) store.getState().toggleLike('exhibitions', id);
  expect(store.getState().data.exhibitions).toHaveLength(100);
  expect(store.getState().data.exhibitions).toContain(1);
  expect(store.getState().data.exhibitions).not.toContain(101);
});

it('persists only explicit IDs and taste, keeps comparison in memory, bounds recents', () => {
  const store = createPersonalStore(false);
  expect(localStorage.length).toBe(0);
  store.getState().toggleLike('exhibitions', 7);
  store.getState().setTaste([{ axis: 'MOOD', value: 'CALM' }]);
  for (let id = 1; id <= 25; id++) store.getState().recordRecent(id);
  for (let id = 1; id <= 4; id++) store.getState().toggleCompare(id);
  expect(store.getState().compare).toEqual([1, 2, 3]);
  expect(store.getState().data.recent).toHaveLength(20);
  const saved = JSON.parse(localStorage.getItem(personalKey(false))!);
  expect(Object.keys(saved).sort()).toEqual([
    'artworks',
    'exhibitions',
    'institutions',
    'recent',
    'taste',
    'version',
  ]);
  expect(createPersonalStore(false).getState().data.exhibitions).toEqual([7]);
  expect(createPersonalStore(false).getState().compare).toEqual([]);
  expect(createPersonalStore(true).getState().data.exhibitions).toEqual([]);
});

it('preserves older interests when adding artwork IDs and clears them with likes', () => {
  localStorage.setItem(
    personalKey(false),
    JSON.stringify({
      version: 1,
      exhibitions: [4],
      institutions: [2],
      recent: [7],
      taste: [],
    }),
  );
  const store = createPersonalStore(false);
  expect(store.getState().data.exhibitions).toEqual([4]);
  expect(store.getState().data.artworks).toEqual([]);
  store.getState().toggleLike('artworks', 10);
  expect(createPersonalStore(false).getState().data.artworks).toEqual([10]);
  expect(recommendationSignals(store.getState().data)).not.toHaveProperty('liked_artwork_ids');
  store.getState().clear('likes');
  expect(store.getState().data.artworks).toEqual([]);
  expect(store.getState().data.recent).toEqual([7]);
});

it('drops corrupt or unknown-version data and survives unavailable storage', () => {
  localStorage.setItem(personalKey(false), '{"version":99,"q":"private"}');
  expect(createPersonalStore(false).getState().data.exhibitions).toEqual([]);
  expect(localStorage.getItem(personalKey(false))).toBeNull();
  const broken = {
    getItem: () => {
      throw new Error();
    },
    setItem: () => {
      throw new Error();
    },
    removeItem: () => {
      throw new Error();
    },
  };
  const store = createPersonalStore(false, broken);
  store.getState().toggleLike('exhibitions', 9);
  expect(store.getState().data.exhibitions).toEqual([9]);
  expect(store.getState().storageFailed).toBe(true);
});

it('clears selected data and never uses recent views as recommendation signals', () => {
  const store = createPersonalStore(false);
  store.getState().toggleLike('exhibitions', 1);
  store.getState().recordRecent(2);
  store.getState().setTaste([{ axis: 'MEDIA_DETAIL', value: 'PAINTING' }]);
  expect(recommendationSignals(store.getState().data)).toEqual({
    liked_exhibition_ids: [1],
    preferred_features: [{ axis: 'MEDIA_DETAIL', value: 'PAINTING' }],
  });
  store.getState().clear('likes');
  expect(store.getState().data.recent).toEqual([2]);
  expect(store.getState().data.taste).toHaveLength(1);
  store.getState().clear('all');
  expect(localStorage.getItem(personalKey(false))).toBeNull();
  expect(recommendationSignals(store.getState().data)).toEqual({});
});

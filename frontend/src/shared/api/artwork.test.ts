import { expect, it } from 'vitest';
import { parseArtworkDetail, parseArtworkList } from './schemas';
import { artworkDetailFixture } from '../../test/artworkFixture';

it('keeps pending sources empty and rejects hidden media URLs and private fields', () => {
  const pending = {
    total: 0,
    page: 1,
    page_size: 24,
    has_more: false,
    results: [],
    availability: 'SOURCE_PENDING',
  };
  expect(parseArtworkList(pending).results).toEqual([]);
  expect(() => parseArtworkList({ ...pending, results: [artworkDetailFixture.artwork] })).toThrow();
  expect(() => parseArtworkDetail({ ...artworkDetailFixture, raw_payload: {} })).toThrow();
  const unsafe = structuredClone(artworkDetailFixture);
  unsafe.artwork.media.media_url = 'https://example.com/unlicensed.jpg' as never;
  expect(() => parseArtworkDetail(unsafe)).toThrow();
});

it('preserves unknown culture and refuses inferred exhibition links', () => {
  expect(parseArtworkDetail(artworkDetailFixture).artwork.cultural_context.is_korean).toBeNull();
  const invalid = structuredClone(artworkDetailFixture);
  invalid.artwork.cultural_context.is_korean = true as never;
  expect(() => parseArtworkDetail(invalid)).toThrow();
  expect(() =>
    parseArtworkDetail({
      ...artworkDetailFixture,
      exhibition_links: { state: 'CONFIRMED', exhibitions: [] },
    }),
  ).toThrow();
});

import { expect, it } from 'vitest';
import { createDiscoveryApi } from './client';
import { parseExhibitionDetail } from './schemas';
import { detailFixture } from '../../test/fixtures';

it('parses unknown details without inventing visit facts', () => {
  const detail = parseExhibitionDetail(detailFixture);
  expect(detail.item.title).toBe('고요의 형태');
  expect(detail.visit_information.price.amount).toBeNull();
  expect(detail.operating_schedule.visit_availability).toBeNull();
});
it('rejects unsafe reservation URLs and unexpected private fields', () => {
  const invalid = structuredClone(detailFixture);
  invalid.visit_information.reservation.official_urls = ['javascript:alert(1)'] as never[];
  expect(() => parseExhibitionDetail(invalid)).toThrow();
  expect(() => parseExhibitionDetail({ ...detailFixture, raw_payload: {} })).toThrow();
});
it('fetches detail without credentials and distinguishes missing data', async () => {
  const api = createDiscoveryApi(async (request) => {
    expect((request as Request).credentials).toBe('omit');
    return new Response('{}', { status: 404 });
  });
  await expect(api.exhibition(999)).rejects.toMatchObject({ kind: 'not_found' });
});

import { describe, expect, it } from 'vitest';
import { createDiscoveryApi } from './client';
import { parseSearchResponse, parseRecommendationResponse } from './schemas';
import { exhibitionFixture, searchFixture, recommendationFixture } from '../../test/fixtures';

describe('API boundary', () => {
  it('maps canonical source and status facts without inventing visit details', () => {
    const result = parseSearchResponse(searchFixture);
    expect(result.items[0]).toMatchObject({
      kind: 'exhibition',
      title: '고요의 형태',
      image: null,
      sourceOwner: '가상 미감 미술관',
      lifecycle: 'CURRENT',
    });
  });

  it.each([
    { source: null },
    { official_url: 'javascript:alert(1)' },
    { official_url: 'https://user:pass@example.com/' },
    { start_date: '2026-02-30' },
    { end_date: '2025-01-01' },
    { eligibility: 'EXCLUDED' },
    { freshness: 'UNVERIFIED' },
    { title: '' },
  ])('rejects untrusted facts instead of displaying them: %j', (patch) => {
    expect(() =>
      parseSearchResponse({ ...searchFixture, results: [{ ...exhibitionFixture, ...patch }] }),
    ).toThrow();
  });

  it('never forwards an image URL for hidden or link-only media', () => {
    for (const status of ['HIDDEN', 'LINK_ONLY']) {
      const result = parseSearchResponse({
        ...searchFixture,
        results: [
          {
            ...exhibitionFixture,
            media: {
              status,
              media_url: 'https://example.com/private.jpg',
              page_url: null,
              credit_line: null,
            },
          },
        ],
      });
      expect(result.items[0]).toMatchObject({ image: null });
    }
  });

  it('rejects unsafe or absent inline image URLs', () => {
    for (const media of [
      {
        status: 'INLINE',
        media_url: 'data:image/svg+xml,evil',
        page_url: null,
        credit_line: '출처',
      },
      { status: 'INLINE', media_url: null, page_url: null, credit_line: null },
    ])
      expect(() =>
        parseSearchResponse({ ...searchFixture, results: [{ ...exhibitionFixture, media }] }),
      ).toThrow();
  });

  it('keeps verification candidates separate from ranked recommendations', () => {
    const result = parseRecommendationResponse(recommendationFixture);
    expect(result.recommendations[0].reason).toBe('선택한 분위기와 이어져요.');
    expect(result.needsVerification[0].verification).toEqual(['관람료 확인 필요']);
    expect(result.needsVerification[0].matchLevel).toBeUndefined();
    expect(result.recommendations[0]).not.toHaveProperty('score');
  });

  it('rejects ended recommendations and duplicated IDs across the two groups', () => {
    expect(() =>
      parseRecommendationResponse({
        ...recommendationFixture,
        recommendations: [{ ...recommendationFixture.recommendations[0], lifecycle: 'ENDED' }],
      }),
    ).toThrow();
    expect(() =>
      parseRecommendationResponse({
        ...recommendationFixture,
        needs_verification: [{ ...recommendationFixture.needs_verification[0], id: 1 }],
      }),
    ).toThrow();
  });

  it('sends typed GET parameters and POST body without credentials or cache', async () => {
    const requests: Request[] = [];
    const api = createDiscoveryApi(async (request) => {
      requests.push(new Request(request));
      return Response.json(requests.length === 1 ? searchFixture : recommendationFixture);
    });
    await api.search({ q: '소리', lifecycle: ['CURRENT', 'UPCOMING'], page: 2, page_size: 24 });
    await api.recommend({ max_budget_krw: 0, required_accessibility: ['WHEELCHAIR_ACCESS'] });
    expect(new URL(requests[0].url).searchParams.getAll('lifecycle')).toEqual([
      'CURRENT',
      'UPCOMING',
    ]);
    expect(new URL(requests[0].url).searchParams.get('q')).toBe('소리');
    expect(requests[1].url).not.toContain('WHEELCHAIR');
    expect(await requests[1].json()).toEqual({
      max_budget_krw: 0,
      required_accessibility: ['WHEELCHAIR_ACCESS'],
    });
    expect(requests.every((r) => r.credentials === 'omit' && r.cache === 'no-store')).toBe(true);
  });

  it('sanitizes network, HTTP and schema errors and forwards cancellation', async () => {
    for (const response of [
      new Response('private SQL', { status: 500 }),
      Response.json({ private: 'secret' }),
    ]) {
      const api = createDiscoveryApi(async () => response);
      await expect(api.search({})).rejects.toThrow('전시 정보를 불러오지 못했어요.');
    }
    const controller = new AbortController();
    controller.abort();
    const api = createDiscoveryApi(async (request) => {
      expect(new Request(request).signal.aborted).toBe(true);
      throw new DOMException('Aborted', 'AbortError');
    });
    await expect(api.search({}, controller.signal)).rejects.toMatchObject({ name: 'AbortError' });
  });
});

export const exhibitionFixture = {
  type: 'EXHIBITION' as const,
  id: 1,
  title: '고요의 형태',
  institution: { id: 1, name: '가상 미감 미술관' },
  lifecycle: 'CURRENT' as const,
  start_date: '2026-09-01',
  end_date: '2026-10-31',
  venue: '가상 미감 미술관 1층',
  region: { area: '서울', district: '종로구' },
  official_url: 'https://example.com/exhibitions/1',
  freshness: 'FRESH' as const,
  eligibility: 'VERIFIED' as const,
  last_verified_at: '2026-09-03T00:00:00Z',
  source: {
    source_id: 'demo',
    source_record_id: 'one',
    source_owner: '가상 미감 미술관',
    last_seen_at: '2026-09-03T00:00:00Z',
  },
  media: { status: 'HIDDEN' as const, media_url: null, page_url: null, credit_line: null },
};

export const searchFixture = {
  total: 1,
  page: 1,
  page_size: 24,
  has_more: false,
  results: [exhibitionFixture],
};

export const recommendationFixture = {
  algorithm_version: 'p0-recommendation-1.0.0',
  candidate_count: 2,
  recommendations: [
    {
      ...exhibitionFixture,
      match_level: 'GOOD_MATCH' as const,
      is_exploration: false,
      reasons: [
        {
          code: 'PREFERRED_FEATURE' as const,
          text: '선택한 분위기와 이어져요.',
          feature: { axis: 'MOOD' as const, value: 'CALM' },
        },
      ],
    },
  ],
  needs_verification: [
    {
      ...exhibitionFixture,
      id: 2,
      title: '빛을 따라 걷는 시간',
      verification_reasons: ['PRICE_UNKNOWN' as const],
    },
  ],
};

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

export const detailFixture = {
  exhibition: exhibitionFixture,
  content: null,
  visit_information: {
    price: { state: 'UNKNOWN', amount: null, currency: null, is_free: null, evidence: [] },
    reservation: {
      state: 'UNKNOWN',
      reservation_type: null,
      official_urls: [],
      guidance: [],
      evidence: [],
    },
    duration: { state: 'UNKNOWN', minimum_minutes: null, maximum_minutes: null, evidence: [] },
    accessibility: [],
    sensory: [],
  },
  features: [],
  operating_schedule: { state: 'UNKNOWN', visit_availability: null, rules: [] },
};

export const contentFixture = {
  introduction: '파도의 움직임을 그림과 음악으로 경험하는 전시입니다.',
  highlights: ['여러 장의 그림을 연결한 애니메이션', '영상과 피아노 음악의 만남'],
  visit_notes: [
    { kind: 'PRICE', text: '무료' },
    { kind: 'HOURS', text: '화–금 10:00–20:00. 월요일 휴관.' },
    { kind: 'LOCATION', text: '미술관 1층 제3전시실' },
  ],
  official_url: exhibitionFixture.official_url,
  source_owner: '가상 미감 미술관',
  reviewed_at: '2026-09-07T07:00:00Z',
  expires_at: '2026-10-07T07:00:00Z',
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

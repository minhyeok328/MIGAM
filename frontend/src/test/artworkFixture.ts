import { exhibitionFixture } from './fixtures';
export const artworkDetailFixture = {
  artwork: {
    type: 'ARTWORK',
    id: 1,
    source_artwork_id: 'demo-artwork-1',
    title: '가상 작품: 선의 안부',
    creator: { name: '가상 작가', official_id: 'fictional-creator-1', state: 'KNOWN' },
    production_year: '2026',
    medium: '종이에 회화',
    collection_institution: { id: 1, name: '가상 미감 미술관' },
    cultural_context: { state: 'UNKNOWN', value: null, is_korean: null },
    official_url: 'https://example.com/artworks/1',
    last_verified_at: exhibitionFixture.last_verified_at,
    eligibility: 'DEMO',
    is_demo: true,
    source: exhibitionFixture.source,
    media: { status: 'HIDDEN', media_url: null, page_url: null, credit_line: null },
    features: [
      {
        axis: 'MEDIA_GROUP',
        value: 'PAINTING',
        evidence_kind: 'DIRECT',
        rule_version: null,
        source: exhibitionFixture.source,
      },
    ],
  },
  similar_artworks: [],
  exhibition_links: { state: 'UNCONFIRMED', exhibitions: [] },
};

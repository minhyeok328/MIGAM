import { z } from 'zod';
import type { components } from './generated';

const text = z.string().trim().min(1);
const id = z.number().int().positive();
const date = z.iso.date();
const timestamp = z.iso.datetime({ offset: true });
const safeUrl = z.string().refine((value) => {
  try {
    const url = new URL(value);
    return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password;
  } catch {
    return false;
  }
}, 'Unsafe URL');
const region = z.strictObject({ area: z.string(), district: z.string() });
const source = z.strictObject({
  source_id: text,
  source_record_id: text,
  source_owner: text,
  last_seen_at: timestamp,
});
const media = z
  .strictObject({
    status: z.enum(['INLINE', 'LINK_ONLY', 'HIDDEN']),
    media_url: z.string().nullable(),
    page_url: z.string().nullable(),
    credit_line: z.string().nullable(),
  })
  .superRefine((value, context) => {
    if (value.status === 'INLINE' && !safeUrl.safeParse(value.media_url).success) {
      context.addIssue({ code: 'custom', message: 'Unsafe inline media', path: ['media_url'] });
    }
    if (
      value.status !== 'HIDDEN' &&
      value.page_url !== null &&
      !safeUrl.safeParse(value.page_url).success
    ) {
      context.addIssue({ code: 'custom', message: 'Unsafe media page', path: ['page_url'] });
    }
  });
const exhibitionFields = {
  type: z.literal('EXHIBITION'),
  id,
  title: text,
  institution: z.strictObject({ id, name: text }),
  lifecycle: z.enum(['CURRENT', 'UPCOMING', 'ENDED', 'CANCELED']),
  start_date: date,
  end_date: date,
  venue: text,
  region,
  official_url: safeUrl,
  freshness: z.enum(['FRESH', 'STALE']),
  eligibility: z.literal('VERIFIED'),
  last_verified_at: timestamp,
  source,
  media,
};
const exhibition = z
  .strictObject(exhibitionFields)
  .refine((row) => row.start_date <= row.end_date) satisfies z.ZodType<
  components['schemas']['ExhibitionSearchResult']
>;
const institution = z.strictObject({
  type: z.literal('INSTITUTION'),
  id,
  name: text,
  region,
  searchable_exhibition_count: id,
}) satisfies z.ZodType<components['schemas']['InstitutionSearchResult']>;
const feature = z.strictObject({
  axis: z.enum([
    'MEDIA_GROUP',
    'MEDIA_DETAIL',
    'THEME',
    'MOOD',
    'EXPERIENCE',
    'SPACE_TYPE',
    'EVENT_FORMAT',
  ]),
  value: z.string().regex(/^[A-Z0-9][A-Z0-9_:-]{0,63}$/),
});
const reason = z.strictObject({
  code: z.enum([
    'PREFERRED_FEATURE',
    'LIKED_EXHIBITION_FEATURE',
    'LIKED_INSTITUTION',
    'PREFERRED_RESERVATION',
    'PREFERRED_DURATION',
    'FRESH_OFFICIAL_INFORMATION',
    'OFFICIAL_INFORMATION',
    'EXPLORATION_CONNECTION',
    'EXPLORATION_NOVELTY',
  ]),
  text,
  feature: feature.nullable(),
});
const visitAvailability = z
  .strictObject({
    first_open_date: z.iso.date(),
    opens_at: z.iso.time({ precision: 0 }),
    closes_at: z.iso.time({ precision: 0 }),
    verified_at: z.iso.datetime({ offset: true }),
  })
  .refine((row) => row.opens_at < row.closes_at)
  .nullable()
  .optional();
const validVisitDate = (row: {
  start_date: string;
  end_date: string;
  visit_availability?: z.infer<typeof visitAvailability>;
}) =>
  row.start_date <= row.end_date &&
  (!row.visit_availability ||
    (row.start_date <= row.visit_availability.first_open_date &&
      row.visit_availability.first_open_date <= row.end_date));
const recommendation = z
  .strictObject({
    ...exhibitionFields,
    lifecycle: z.enum(['CURRENT', 'UPCOMING']),
    match_level: z.enum(['VERY_CLOSE', 'GOOD_MATCH', 'SOME_MATCH', 'GENERAL', 'EXPLORATION']),
    is_exploration: z.boolean(),
    visit_availability: visitAvailability,
    reasons: z.array(reason).min(1).max(3),
  })
  .refine(validVisitDate)
  .refine((row) => row.is_exploration === (row.match_level === 'EXPLORATION')) satisfies z.ZodType<
  components['schemas']['ExhibitionRecommendation']
>;
const verification = z
  .strictObject({
    ...exhibitionFields,
    lifecycle: z.enum(['CURRENT', 'UPCOMING']),
    verification_reasons: z
      .array(z.enum(['PRICE_UNKNOWN', 'RESERVATION_UNKNOWN', 'DURATION_UNKNOWN']))
      .min(1)
      .max(3),
    visit_availability: visitAvailability,
  })
  .refine(validVisitDate) satisfies z.ZodType<components['schemas']['VerificationCandidate']>;

export type MatchLevel = components['schemas']['ExhibitionRecommendation']['match_level'];
export type ExhibitionView = ReturnType<typeof presentExhibition> & {
  reason?: string;
  matchLevel?: MatchLevel;
  exploration?: boolean;
  verification?: string[];
  visitAvailability?: z.infer<typeof visitAvailability>;
};
export type InstitutionView = {
  kind: 'institution';
  id: number;
  name: string;
  area: string;
  district: string;
  exhibitionCount: number;
};
export type SearchPage = {
  total: number;
  page: number;
  hasMore: boolean;
  items: (ExhibitionView | InstitutionView)[];
};
export type RecommendationPage = {
  recommendations: ExhibitionView[];
  needsVerification: ExhibitionView[];
  candidateCount: number;
};

export function presentExhibition(row: components['schemas']['ExhibitionSearchResult']) {
  return {
    kind: 'exhibition' as const,
    id: row.id,
    title: row.title,
    institution: row.institution.name,
    lifecycle: row.lifecycle,
    startDate: row.start_date,
    endDate: row.end_date,
    venue: row.venue,
    area: row.region.area,
    district: row.region.district,
    officialUrl: row.official_url,
    freshness: row.freshness,
    verifiedAt: row.last_verified_at,
    sourceOwner: row.source.source_owner,
    image: row.media.status === 'INLINE' ? row.media.media_url : null,
    mediaPage: row.media.status === 'HIDDEN' ? null : row.media.page_url,
    credit: row.media.status === 'INLINE' ? row.media.credit_line : null,
  };
}

const evidence = z.strictObject({
  scope: z.enum(['EXHIBITION', 'INSTITUTION']),
  verified_at: timestamp,
  source,
});
const evidenceFields = {
  state: z.enum(['CONFIRMED', 'UNKNOWN', 'CONFLICT']),
  evidence: z.array(evidence),
};
const factFields = {
  ...evidenceFields,
  value: z.enum(['CONFIRMED_POSITIVE', 'CONFIRMED_NEGATIVE']).nullable(),
  details: z.array(z.string()),
};
const detailSchema = z.strictObject({
  exhibition,
  content: z
    .strictObject({
      introduction: text.max(2000),
      highlights: z.array(text.max(300)).max(3),
      visit_notes: z
        .array(
          z.strictObject({
            kind: z.enum(['PRICE', 'HOURS', 'RESERVATION', 'AGE', 'LOCATION']),
            text: text.max(500),
          }),
        )
        .max(5)
        .refine((notes) => new Set(notes.map((note) => note.kind)).size === notes.length),
      official_url: safeUrl.refine((url) => url.startsWith('https://')),
      source_owner: text,
      reviewed_at: timestamp,
      expires_at: timestamp,
    })
    .refine((content) => {
      const duration = Date.parse(content.expires_at) - Date.parse(content.reviewed_at);
      return duration > 0 && duration <= 30 * 24 * 60 * 60 * 1000;
    })
    .nullable(),
  visit_information: z.strictObject({
    price: z.strictObject({
      ...evidenceFields,
      amount: z.number().nonnegative().nullable(),
      currency: z.string().nullable(),
      is_free: z.boolean().nullable(),
    }),
    reservation: z.strictObject({
      ...evidenceFields,
      reservation_type: z
        .enum([
          'NOT_REQUIRED',
          'REQUIRED',
          'RECOMMENDED',
          'TIMED_ENTRY',
          'ON_SITE',
          'FIRST_COME',
          'PROGRAM_ONLY',
        ])
        .nullable(),
      official_urls: z.array(safeUrl),
      guidance: z.array(z.string()),
    }),
    duration: z.strictObject({
      ...evidenceFields,
      minimum_minutes: id.nullable(),
      maximum_minutes: id.nullable(),
    }),
    accessibility: z.array(
      z.strictObject({
        ...factFields,
        kind: z.enum([
          'WHEELCHAIR_ACCESS',
          'MOBILITY_ACCESS',
          'CAPTIONS',
          'SIGN_LANGUAGE',
          'AUDIO_DESCRIPTION',
          'AGE_CONDITION',
        ]),
      }),
    ),
    sensory: z.array(
      z.strictObject({
        ...factFields,
        kind: z.enum([
          'LOUD_SOUND',
          'SUDDEN_SOUND',
          'FLASHING_LIGHTS',
          'DARK_SPACE',
          'NARROW_OR_ENCLOSED_SPACE',
        ]),
      }),
    ),
  }),
  features: z.array(
    feature.extend({
      evidence_kind: z.enum(['DIRECT', 'DERIVED']),
      rule_version: z.string().nullable(),
      source,
    }),
  ),
  operating_schedule: z.strictObject({
    state: z.enum(['OPEN', 'CLOSED', 'UNKNOWN']),
    visit_availability: visitAvailability.unwrap(),
    rules: z.array(
      z.strictObject({
        status: z.enum(['CONFIRMED', 'UNKNOWN']),
        kind: z.enum(['REGULAR', 'OVERRIDE']),
        effective_from: date,
        effective_to: date,
        weekdays: z.array(z.number().int().min(0).max(6)),
        is_open: z.boolean().nullable(),
        opens_at: z.iso.time({ precision: 0 }).nullable(),
        closes_at: z.iso.time({ precision: 0 }).nullable(),
        rule_version: z.string(),
        evidence,
      }),
    ),
  }),
}) satisfies z.ZodType<components['schemas']['ExhibitionDetailResponse']>;

export function parseExhibitionDetail(input: unknown) {
  const parsed = detailSchema
    .refine(
      (detail) => !detail.content || detail.content.official_url === detail.exhibition.official_url,
      'Content belongs to a different official exhibition',
    )
    .parse(input);
  return { ...parsed, item: presentExhibition(parsed.exhibition) };
}
export type ExhibitionDetail = ReturnType<typeof parseExhibitionDetail>;

const artwork = z
  .strictObject({
    type: z.literal('ARTWORK'),
    id,
    source_artwork_id: text.max(255),
    title: text.max(500),
    creator: z
      .strictObject({
        name: text.max(255),
        official_id: text.max(255).nullable(),
        state: z.enum(['KNOWN', 'UNKNOWN']),
      })
      .refine((v) => v.state !== 'UNKNOWN' || v.official_id === null),
    production_year: text.max(100),
    medium: text.max(500),
    collection_institution: z.strictObject({ id, name: text }),
    cultural_context: z
      .strictObject({
        state: z.enum(['CONFIRMED', 'UNKNOWN']),
        value: text.max(255).nullable(),
        is_korean: z.boolean().nullable(),
      })
      .refine((v) => v.state !== 'UNKNOWN' || (v.value === null && v.is_korean === null)),
    official_url: safeUrl.refine((v) => v.startsWith('https://')),
    last_verified_at: timestamp,
    eligibility: z.enum(['VERIFIED', 'DEMO']),
    is_demo: z.boolean(),
    source,
    media: z.strictObject({
      status: z.literal('HIDDEN'),
      media_url: z.null(),
      page_url: z.null(),
      credit_line: z.null(),
    }),
    features: detailSchema.shape.features,
  })
  .refine((v) => v.is_demo === (v.eligibility === 'DEMO')) satisfies z.ZodType<
  components['schemas']['ArtworkResult']
>;
export type ArtworkView = z.infer<typeof artwork>;
export function parseArtworkList(input: unknown) {
  return z
    .strictObject({
      total: z.number().int().nonnegative(),
      page: id,
      page_size: id.max(24),
      has_more: z.boolean(),
      availability: z.enum(['DEMO', 'SOURCE_PENDING']),
      results: z.array(artwork).max(24),
    })
    .refine(
      (v) =>
        v.availability !== 'SOURCE_PENDING' || (v.total === 0 && !v.results.length && !v.has_more),
    )
    .refine((v) => v.availability !== 'DEMO' || v.results.every((item) => item.is_demo))
    .parse(input);
}
export function parseArtworkDetail(input: unknown) {
  return z
    .strictObject({
      artwork,
      similar_artworks: z
        .array(
          z.strictObject({
            artwork,
            reasons: z
              .array(z.enum(['SAME_CREATOR', 'SAME_COLLECTION']))
              .min(1)
              .max(2),
          }),
        )
        .max(6),
      exhibition_links: z.strictObject({
        state: z.literal('UNCONFIRMED'),
        exhibitions: z.array(exhibition).max(0),
      }),
    })
    .parse(input);
}

export function parseInstitutionDetail(input: unknown) {
  const parsed = z
    .strictObject({
      institution,
      total: z.number().int().nonnegative(),
      page: id,
      page_size: id.max(24),
      has_more: z.boolean(),
      exhibitions: z.array(exhibition).max(24),
    })
    .parse(input);
  return { ...parsed, items: parsed.exhibitions.map(presentExhibition) };
}

export function parseSearchResponse(input: unknown): SearchPage {
  const parsed = z
    .strictObject({
      total: z.number().int().nonnegative(),
      page: id,
      page_size: id.max(24),
      has_more: z.boolean(),
      results: z.array(z.discriminatedUnion('type', [exhibition, institution])).max(24),
    })
    .parse(input);
  return {
    total: parsed.total,
    page: parsed.page,
    hasMore: parsed.has_more,
    items: parsed.results.map((row) =>
      row.type === 'EXHIBITION'
        ? presentExhibition(row)
        : {
            kind: 'institution',
            id: row.id,
            name: row.name,
            area: row.region.area,
            district: row.region.district,
            exhibitionCount: row.searchable_exhibition_count,
          },
    ),
  };
}

const verificationLabels = {
  PRICE_UNKNOWN: '관람료 확인 필요',
  RESERVATION_UNKNOWN: '예약 정보 확인 필요',
  DURATION_UNKNOWN: '관람시간 확인 필요',
};
export function parseRecommendationResponse(input: unknown): RecommendationPage {
  const parsed = z
    .strictObject({
      algorithm_version: text,
      candidate_count: z.number().int().nonnegative(),
      recommendations: z.array(recommendation).max(24),
      needs_verification: z.array(verification).max(24),
    })
    .superRefine((value, context) => {
      const ids = [...value.recommendations, ...value.needs_verification].map((row) => row.id);
      if (new Set(ids).size !== ids.length || ids.length > value.candidate_count) {
        context.addIssue({ code: 'custom', message: 'Invalid candidate partition' });
      }
    })
    .parse(input);
  return {
    candidateCount: parsed.candidate_count,
    recommendations: parsed.recommendations.map((row) => ({
      ...presentExhibition(row),
      reason: row.reasons[0].text,
      matchLevel: row.match_level,
      exploration: row.is_exploration,
      visitAvailability: row.visit_availability,
    })),
    needsVerification: parsed.needs_verification.map((row) => ({
      ...presentExhibition(row),
      verification: row.verification_reasons.map((code) => verificationLabels[code]),
      visitAvailability: row.visit_availability,
    })),
  };
}

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
const recommendation = z
  .strictObject({
    ...exhibitionFields,
    lifecycle: z.enum(['CURRENT', 'UPCOMING']),
    match_level: z.enum(['VERY_CLOSE', 'GOOD_MATCH', 'SOME_MATCH', 'GENERAL', 'EXPLORATION']),
    is_exploration: z.boolean(),
    reasons: z.array(reason).min(1).max(3),
  })
  .refine(
    (row) =>
      row.start_date <= row.end_date && row.is_exploration === (row.match_level === 'EXPLORATION'),
  ) satisfies z.ZodType<components['schemas']['ExhibitionRecommendation']>;
const verification = z
  .strictObject({
    ...exhibitionFields,
    lifecycle: z.enum(['CURRENT', 'UPCOMING']),
    verification_reasons: z
      .array(z.enum(['PRICE_UNKNOWN', 'RESERVATION_UNKNOWN', 'DURATION_UNKNOWN']))
      .min(1)
      .max(3),
  })
  .refine((row) => row.start_date <= row.end_date) satisfies z.ZodType<
  components['schemas']['VerificationCandidate']
>;

export type MatchLevel = components['schemas']['ExhibitionRecommendation']['match_level'];
export type ExhibitionView = ReturnType<typeof presentExhibition> & {
  reason?: string;
  matchLevel?: MatchLevel;
  exploration?: boolean;
  verification?: string[];
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

function presentExhibition(row: components['schemas']['ExhibitionSearchResult']) {
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
    })),
    needsVerification: parsed.needs_verification.map((row) => ({
      ...presentExhibition(row),
      verification: row.verification_reasons.map((code) => verificationLabels[code]),
    })),
  };
}

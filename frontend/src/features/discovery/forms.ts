import { z } from 'zod';
import type { RecommendationRequest, SearchRequest } from '../../shared/api/client';

export const areas = [
  '서울',
  '경기',
  '인천',
  '부산',
  '대구',
  '대전',
  '광주',
  '울산',
  '세종',
  '강원',
  '충북',
  '충남',
  '전북',
  '전남',
  '경북',
  '경남',
  '제주',
];
export const moods = [
  { value: 'CALM', label: '차분한', description: '조용히 천천히 머물며 감상' },
  { value: 'IMMERSIVE', label: '몰입형', description: '소리·영상·공간에 둘러싸여 감상' },
  { value: 'LIVELY', label: '활기찬', description: '색채·움직임·에너지가 강한 경험' },
  { value: 'REFLECTIVE', label: '사유형', description: '작품의 의미를 생각하며 보는 전시' },
  { value: 'PARTICIPATORY', label: '참여형', description: '직접 조작하거나 움직임에 반응' },
  { value: 'EXPERIMENTAL', label: '실험적', description: '낯선 매체와 새로운 표현을 탐색' },
] as const;
export const accessibilityOptions = {
  WHEELCHAIR_ACCESS: '휠체어 접근',
  MOBILITY_ACCESS: '이동 편의',
  CAPTIONS: '자막',
  SIGN_LANGUAGE: '수어',
  AUDIO_DESCRIPTION: '음성 해설',
};
export const sensoryOptions = {
  LOUD_SOUND: '큰 소리',
  SUDDEN_SOUND: '갑작스러운 소리',
  FLASHING_LIGHTS: '섬광',
  DARK_SPACE: '어두운 공간',
  NARROW_OR_ENCLOSED_SPACE: '좁거나 밀폐된 공간',
};
export const reservationOptions = {
  NOT_REQUIRED: '예약 없이 관람',
  REQUIRED: '사전 예약',
  RECOMMENDED: '예약 권장',
  TIMED_ENTRY: '회차별 입장',
  ON_SITE: '현장 접수',
  FIRST_COME: '선착순',
  PROGRAM_ONLY: '프로그램만 예약',
};
export type SearchDraft = {
  q: string;
  area: string;
  district: string;
  type: NonNullable<SearchRequest['type']>;
  lifecycle: 'DEFAULT' | 'ALL' | 'CURRENT' | 'UPCOMING' | 'ENDED' | 'CANCELED';
  sort: NonNullable<SearchRequest['sort']>;
};
export type RecommendationDraft = {
  area: string;
  district: string;
  start: string;
  end: string;
  budget: string;
  accessibility: string[];
  sensory: string[];
  moods: string[];
  reservationType: string;
  reservationMode: 'REQUIRED' | 'PREFERRED';
  durationMin: string;
  durationMax: string;
  durationMode: 'REQUIRED' | 'PREFERRED';
};
export const emptySearchDraft: SearchDraft = {
  q: '',
  area: '',
  district: '',
  type: 'EXHIBITION',
  lifecycle: 'DEFAULT',
  sort: 'RELEVANCE',
};
export const emptyRecommendationDraft: RecommendationDraft = {
  area: '',
  district: '',
  start: '',
  end: '',
  budget: '',
  accessibility: [],
  sensory: [],
  moods: [],
  reservationType: '',
  reservationMode: 'PREFERRED',
  durationMin: '',
  durationMax: '',
  durationMode: 'PREFERRED',
};

function checkRegion(area: string, district: string) {
  if (district.trim() && !area) throw new Error('시·군·구를 입력하려면 먼저 시·도를 선택해주세요.');
  if (area.length > 100 || district.length > 100)
    throw new Error('지역은 100자 이내로 입력해주세요.');
}
function integer(value: string, label: string, minimum: number): number | undefined {
  if (!value.trim()) return undefined;
  const number = Number(value);
  if (!/^\d+$/.test(value.trim()) || !Number.isSafeInteger(number) || number < minimum)
    throw new Error(`${label}은 ${minimum} 이상의 정수로 입력해주세요.`);
  return number;
}
function known<T extends string>(values: string[], options: Record<T, string>): T[] {
  if (values.some((value) => !(value in options)) || new Set(values).size !== values.length)
    throw new Error('선택한 조건을 다시 확인해주세요.');
  return values as T[];
}

export function buildSearchRequest(draft: SearchDraft): SearchRequest {
  checkRegion(draft.area, draft.district);
  if (draft.q.trim().length > 100) throw new Error('검색어는 100자 이내로 입력해주세요.');
  return {
    ...(draft.q.trim() ? { q: draft.q.trim() } : {}),
    type: draft.type,
    sort: draft.sort,
    page_size: 24,
    ...(draft.area ? { region_area: draft.area } : {}),
    ...(draft.district.trim() ? { region_district: draft.district.trim() } : {}),
    ...(draft.lifecycle === 'DEFAULT'
      ? {}
      : {
          lifecycle:
            draft.lifecycle === 'ALL'
              ? ['CURRENT', 'UPCOMING', 'ENDED', 'CANCELED']
              : [draft.lifecycle],
        }),
  };
}

export function buildRecommendationRequest(draft: RecommendationDraft): RecommendationRequest {
  checkRegion(draft.area, draft.district);
  const request: RecommendationRequest = { limit: 6 };
  if (draft.area)
    request.region = {
      area: draft.area,
      ...(draft.district.trim() ? { district: draft.district.trim() } : {}),
    };
  if (draft.start || draft.end) {
    if (
      !z.iso.date().safeParse(draft.start).success ||
      !z.iso.date().safeParse(draft.end).success ||
      draft.start > draft.end
    )
      throw new Error('방문 시작일과 종료일을 올바른 순서로 입력해주세요.');
    request.visit_dates = { start: draft.start, end: draft.end };
  }
  const budget = integer(draft.budget, '최대 예산', 0);
  if (budget !== undefined) request.max_budget_krw = budget;
  if (draft.accessibility.length)
    request.required_accessibility = known(draft.accessibility, accessibilityOptions);
  if (draft.sensory.length) request.avoided_sensory = known(draft.sensory, sensoryOptions);
  if (draft.reservationType)
    request.reservation = {
      mode: draft.reservationMode,
      types: known([draft.reservationType], reservationOptions),
    };
  const minimum = integer(draft.durationMin, '최소 관람시간', 1);
  const maximum = integer(draft.durationMax, '최대 관람시간', 1);
  if (minimum !== undefined && maximum !== undefined && minimum > maximum)
    throw new Error('최대 관람시간은 최소 시간보다 작을 수 없습니다.');
  if (minimum !== undefined)
    request.duration = {
      mode: draft.durationMode,
      minimum_minutes: minimum,
      ...(maximum !== undefined ? { maximum_minutes: maximum } : {}),
    };
  else if (maximum !== undefined)
    request.duration = { mode: draft.durationMode, maximum_minutes: maximum };
  if (
    draft.moods.length > 3 ||
    new Set(draft.moods).size !== draft.moods.length ||
    draft.moods.some((value) => !moods.some((mood) => mood.value === value))
  )
    throw new Error('분위기는 서로 다른 항목을 최대 3개까지 선택해주세요.');
  if (draft.moods.length)
    request.preferred_features = draft.moods.map((value) => ({ axis: 'MOOD', value }));
  return request;
}

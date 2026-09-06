import { createStore } from 'zustand/vanilla';
import { z } from 'zod';
import type { RecommendationRequest } from '../../shared/api/client';

export type TasteFeature = NonNullable<RecommendationRequest['preferred_features']>[number];
const ids = z
  .array(z.number().int().positive())
  .max(100)
  .refine((v) => new Set(v).size === v.length);
const schema = z.strictObject({
  version: z.literal(1),
  exhibitions: ids,
  institutions: ids,
  artworks: ids.default([]),
  recent: ids.max(20),
  taste: z
    .array(
      z.strictObject({
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
      }),
    )
    .max(30),
});
type PersonalData = z.infer<typeof schema>;
type Storage = Pick<globalThis.Storage, 'getItem' | 'setItem' | 'removeItem'>;
type ClearScope = 'likes' | 'taste' | 'recent' | 'all';
type State = {
  data: PersonalData;
  compare: number[];
  storageFailed: boolean;
  revision: number;
  toggleLike: (kind: 'exhibitions' | 'institutions' | 'artworks', id: number) => void;
  toggleCompare: (id: number) => void;
  recordRecent: (id: number) => void;
  setTaste: (taste: TasteFeature[]) => void;
  clear: (scope: ClearScope) => void;
  retrySave: () => void;
};
const empty = (): PersonalData => ({
  version: 1,
  exhibitions: [],
  institutions: [],
  artworks: [],
  recent: [],
  taste: [],
});
export const personalKey = (demo: boolean) => `migam:personal:v1${demo ? ':demo' : ''}`;
const validId = (id: number) => Number.isSafeInteger(id) && id > 0;

export function createPersonalStore(demo: boolean, storage?: Storage) {
  const key = personalKey(demo);
  let initial = empty();
  let failed = false;
  try {
    storage ??= window.localStorage;
    const raw = storage.getItem(key);
    if (raw) {
      const parsed = schema.safeParse(JSON.parse(raw));
      if (parsed.success) initial = parsed.data;
      else storage.removeItem(key);
    }
  } catch {
    try {
      storage?.removeItem(key);
    } catch {
      /* Storage unavailable; session remains usable. */
    }
    failed = true;
  }
  return createStore<State>()((set, get) => {
    function save(data: PersonalData, remove = false) {
      let storageFailed = false;
      try {
        if (!storage) throw new Error('Storage unavailable');
        if (remove) storage.removeItem(key);
        else storage.setItem(key, JSON.stringify(data));
      } catch {
        storageFailed = true;
      }
      set({ data, storageFailed, revision: get().revision + 1 });
    }
    return {
      data: initial,
      compare: [],
      storageFailed: failed,
      revision: 0,
      toggleLike: (kind, id) => {
        if (!validId(id)) return;
        const data = get().data;
        const values = data[kind];
        if (!values.includes(id) && values.length >= 100) return;
        save({
          ...data,
          [kind]: values.includes(id) ? values.filter((v) => v !== id) : [...values, id],
        });
      },
      toggleCompare: (id) => {
        if (!validId(id)) return;
        const values = get().compare;
        if (values.includes(id)) set({ compare: values.filter((v) => v !== id) });
        else if (values.length < 3) set({ compare: [...values, id] });
      },
      recordRecent: (id) => {
        if (validId(id) && get().data.recent[0] !== id)
          save({
            ...get().data,
            recent: [id, ...get().data.recent.filter((v) => v !== id)].slice(0, 20),
          });
      },
      setTaste: (taste) => save(schema.parse({ ...get().data, taste })),
      clear: (scope) => {
        const data = get().data;
        save(
          scope === 'all'
            ? empty()
            : {
                ...data,
                ...(scope === 'likes' ? { exhibitions: [], institutions: [], artworks: [] } : {}),
                ...(scope === 'taste' ? { taste: [] } : {}),
                ...(scope === 'recent' ? { recent: [] } : {}),
              },
          scope === 'all',
        );
        if (scope === 'all') set({ compare: [] });
      },
      retrySave: () => save(get().data),
    };
  });
}
export type PersonalStore = ReturnType<typeof createPersonalStore>;
export function recommendationSignals(data: PersonalData): Partial<RecommendationRequest> {
  return {
    ...(data.exhibitions.length ? { liked_exhibition_ids: data.exhibitions } : {}),
    ...(data.institutions.length ? { liked_institution_ids: data.institutions } : {}),
    ...(data.taste.length ? { preferred_features: data.taste } : {}),
  };
}

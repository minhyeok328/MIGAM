import { createStore } from 'zustand/vanilla';
import type { RecommendationRequest, SearchRequest } from '../../shared/api/client';
import {
  buildRecommendationRequest,
  buildSearchRequest,
  emptyRecommendationDraft,
  emptySearchDraft,
  type RecommendationDraft,
  type SearchDraft,
} from './forms';

type DiscoveryState = {
  tab: 'search' | 'recommend';
  searchDraft: SearchDraft;
  recommendationDraft: RecommendationDraft;
  searchRequest: SearchRequest;
  recommendationRequest: RecommendationRequest;
  searchRevision: number;
  recommendationRevision: number;
  setTab: (tab: 'search' | 'recommend') => void;
  setSearch: (patch: Partial<SearchDraft>) => void;
  setRecommendation: (patch: Partial<RecommendationDraft>) => void;
  applySearch: () => void;
  applyRecommendation: () => void;
};

export function createDiscoveryStore() {
  return createStore<DiscoveryState>()((set, get) => ({
    tab: 'search',
    searchDraft: { ...emptySearchDraft },
    recommendationDraft: { ...emptyRecommendationDraft },
    searchRequest: buildSearchRequest(emptySearchDraft),
    recommendationRequest: { limit: 6 },
    searchRevision: 0,
    recommendationRevision: 0,
    setTab: (tab) => set({ tab }),
    setSearch: (patch) => set((state) => ({ searchDraft: { ...state.searchDraft, ...patch } })),
    setRecommendation: (patch) =>
      set((state) => ({ recommendationDraft: { ...state.recommendationDraft, ...patch } })),
    applySearch: () =>
      set((state) => ({
        searchRequest: buildSearchRequest(get().searchDraft),
        searchRevision: state.searchRevision + 1,
      })),
    applyRecommendation: () =>
      set((state) => ({
        recommendationRequest: buildRecommendationRequest(get().recommendationDraft),
        recommendationRevision: state.recommendationRevision + 1,
      })),
  }));
}
export type DiscoveryStore = ReturnType<typeof createDiscoveryStore>;

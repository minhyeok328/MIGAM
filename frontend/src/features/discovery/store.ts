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

export type DiscoveryTab = 'search' | 'recommend';

type DiscoveryState = {
  tab: DiscoveryTab;
  searchDraft: SearchDraft;
  appliedSearchDraft: SearchDraft;
  recommendationDraft: RecommendationDraft;
  searchRequest: SearchRequest;
  recommendationRequest: RecommendationRequest;
  searchRevision: number;
  recommendationRevision: number;
  setTab: (tab: DiscoveryTab) => void;
  setSearch: (patch: Partial<SearchDraft>) => void;
  setRecommendation: (patch: Partial<RecommendationDraft>) => void;
  applySearch: () => void;
  refineSearch: (patch: Partial<SearchDraft>) => void;
  applyRecommendation: () => void;
};

export function createDiscoveryStore(initialTab: DiscoveryTab = 'search') {
  return createStore<DiscoveryState>()((set, get) => ({
    tab: initialTab,
    searchDraft: { ...emptySearchDraft },
    appliedSearchDraft: { ...emptySearchDraft },
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
        appliedSearchDraft: { ...get().searchDraft },
        searchRevision: state.searchRevision + 1,
      })),
    refineSearch: (patch) =>
      set((state) => {
        const appliedSearchDraft = { ...state.appliedSearchDraft, ...patch };
        return {
          searchRequest: buildSearchRequest(appliedSearchDraft),
          appliedSearchDraft,
          searchDraft: { ...state.searchDraft, ...patch },
          searchRevision: state.searchRevision + 1,
        };
      }),
    applyRecommendation: () =>
      set((state) => ({
        recommendationRequest: buildRecommendationRequest(get().recommendationDraft),
        recommendationRevision: state.recommendationRevision + 1,
      })),
  }));
}
export type DiscoveryStore = ReturnType<typeof createDiscoveryStore>;

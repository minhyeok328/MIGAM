import createClient from 'openapi-fetch';
import { ZodError } from 'zod';
import type { components, operations, paths } from './generated';
import {
  parseSearchResponse,
  parseRecommendationResponse,
  parseExhibitionDetail,
  parseInstitutionDetail,
  parseArtworkList,
  parseArtworkDetail,
} from './schemas';

export type SearchRequest = NonNullable<operations['searchDiscovery']['parameters']['query']>;
export type ArtworkRequest = NonNullable<operations['listArtworks']['parameters']['query']>;
export type RecommendationRequest = components['schemas']['RecommendationRequest'];
export class DiscoveryApiError extends Error {
  constructor(public readonly kind: 'network' | 'contract' | 'not_found' = 'network') {
    super('전시 정보를 불러오지 못했어요.');
  }
}

export function createDiscoveryApi(fetchImpl: typeof fetch = fetch) {
  const client = createClient<paths>({
    baseUrl: globalThis.location?.origin ?? 'http://localhost',
    fetch: fetchImpl,
    credentials: 'omit',
    cache: 'no-store',
    referrerPolicy: 'no-referrer',
  });
  async function guard<T>(operation: () => Promise<T>): Promise<T> {
    try {
      return await operation();
    } catch (error) {
      if (error && typeof error === 'object' && 'name' in error && error.name === 'AbortError')
        throw error;
      if (error instanceof DiscoveryApiError) throw error;
      throw new DiscoveryApiError(error instanceof ZodError ? 'contract' : 'network');
    }
  }
  return {
    artworks: (query: ArtworkRequest, signal?: AbortSignal) =>
      guard(async () => {
        const { data, response } = await client.GET('/api/internal/v1/artworks/', {
          params: { query },
          signal,
        });
        if (!response.ok) throw new DiscoveryApiError();
        return parseArtworkList(data);
      }),
    artwork: (id: number, signal?: AbortSignal) =>
      guard(async () => {
        const { data, response } = await client.GET('/api/internal/v1/artworks/{id}/', {
          params: { path: { id } },
          signal,
        });
        if (!response.ok)
          throw new DiscoveryApiError(response.status === 404 ? 'not_found' : 'network');
        return parseArtworkDetail(data);
      }),
    exhibition: (id: number, signal?: AbortSignal) =>
      guard(async () => {
        const { data, response } = await client.GET('/api/internal/v1/exhibitions/{id}/', {
          params: { path: { id } },
          signal,
        });
        if (!response.ok)
          throw new DiscoveryApiError(response.status === 404 ? 'not_found' : 'network');
        return parseExhibitionDetail(data);
      }),
    institution: (id: number, page = 1, signal?: AbortSignal) =>
      guard(async () => {
        const { data, response } = await client.GET('/api/internal/v1/institutions/{id}/', {
          params: { path: { id }, query: { page, page_size: 24 } },
          signal,
        });
        if (!response.ok)
          throw new DiscoveryApiError(response.status === 404 ? 'not_found' : 'network');
        return parseInstitutionDetail(data);
      }),
    search: (query: SearchRequest, signal?: AbortSignal) =>
      guard(async () => {
        const { data, response } = await client.GET('/api/internal/v1/search/', {
          params: { query },
          signal,
        });
        if (!response.ok) throw new DiscoveryApiError();
        return parseSearchResponse(data);
      }),
    recommend: (body: RecommendationRequest, signal?: AbortSignal) =>
      guard(async () => {
        const { data, response } = await client.POST('/api/internal/v1/recommendations/', {
          body,
          signal,
        });
        if (!response.ok) throw new DiscoveryApiError();
        return parseRecommendationResponse(data);
      }),
  };
}
export type DiscoveryApi = ReturnType<typeof createDiscoveryApi>;

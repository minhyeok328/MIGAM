import createClient from 'openapi-fetch';
import { ZodError } from 'zod';
import type { components, operations, paths } from './generated';
import { parseSearchResponse, parseRecommendationResponse } from './schemas';

export type SearchRequest = NonNullable<operations['searchDiscovery']['parameters']['query']>;
export type RecommendationRequest = components['schemas']['RecommendationRequest'];
export class DiscoveryApiError extends Error {
  constructor(public readonly kind: 'network' | 'contract' = 'network') {
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
      throw new DiscoveryApiError(error instanceof ZodError ? 'contract' : 'network');
    }
  }
  return {
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

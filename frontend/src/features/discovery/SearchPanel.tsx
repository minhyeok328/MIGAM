import { useState } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { ArrowDown, Search } from 'lucide-react';
import { useDiscovery } from '../../app/providers';
import { areas, type SearchDraft } from './forms';
import { ExhibitionCard, InstitutionCard } from '../../entities/ExhibitionCard';
import { EmptyState, ErrorNotice, FormError, LoadingState } from '../../shared/ui/Feedback';

export function SearchPanel() {
  const { state, api, demo } = useDiscovery();
  const [error, setError] = useState('');
  const draft = state.searchDraft;
  const query = useInfiniteQuery({
    queryKey: ['search', state.searchRevision],
    initialPageParam: 1,
    queryFn: ({ pageParam, signal }) =>
      api.search({ ...state.searchRequest, page: pageParam }, signal),
    getNextPageParam: (page) => (page.hasMore ? page.page + 1 : undefined),
  });
  const items = query.data?.pages.flatMap((page) => page.items) ?? [];
  const applied = state.searchRequest;
  const lifecycleLabels = {
    CURRENT: '현재 전시',
    UPCOMING: '예정 전시',
    ENDED: '종료 전시',
    CANCELED: '취소된 전시',
  };
  const update = <K extends keyof SearchDraft>(key: K, value: SearchDraft[K]) =>
    state.setSearch({ [key]: value });
  return (
    <>
      <form
        className="search-form"
        autoComplete="off"
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          try {
            state.applySearch();
            setError('');
          } catch (e) {
            setError((e as Error).message);
          }
        }}
      >
        <div className="search-bar">
          <Search size={23} strokeWidth={1.5} aria-hidden="true" />
          <label className="sr-only" htmlFor="search-keyword">
            전시·기관 검색어
          </label>
          <input
            id="search-keyword"
            type="search"
            maxLength={100}
            placeholder="어떤 전시가 궁금하세요? 전시명, 기관명으로 검색"
            value={draft.q}
            onChange={(event) => update('q', event.target.value)}
          />
          <button className="primary-button" type="submit">
            검색하기 <Search size={17} aria-hidden="true" />
          </button>
        </div>
        <div className="filter-grid search-filters">
          <label className="field">
            대상
            <select
              value={draft.type}
              onChange={(e) => update('type', e.target.value as SearchDraft['type'])}
            >
              <option value="EXHIBITION">전시</option>
              <option value="INSTITUTION">기관</option>
              <option value="ALL">전체</option>
            </select>
          </label>
          <label className="field">
            시·도
            <select
              value={draft.area}
              onChange={(e) => state.setSearch({ area: e.target.value, district: '' })}
            >
              <option value="">모든 지역</option>
              {areas.map((area) => (
                <option key={area}>{area}</option>
              ))}
            </select>
          </label>
          <label className="field">
            시·군·구
            <input
              placeholder="전체"
              maxLength={100}
              disabled={!draft.area}
              value={draft.district}
              onChange={(e) => update('district', e.target.value)}
            />
          </label>
          <label className="field">
            전시 상태
            <select
              value={draft.lifecycle}
              onChange={(e) => update('lifecycle', e.target.value as SearchDraft['lifecycle'])}
            >
              <option value="DEFAULT">기본 · 검색어가 있으면 과거 포함</option>
              <option value="CURRENT">현재 전시</option>
              <option value="UPCOMING">예정 전시</option>
              <option value="ENDED">종료 전시</option>
              <option value="CANCELED">취소된 전시</option>
              <option value="ALL">모든 상태</option>
            </select>
          </label>
          <label className="field">
            정렬
            <select
              value={draft.sort}
              onChange={(e) => update('sort', e.target.value as SearchDraft['sort'])}
            >
              <option value="RELEVANCE">관련도순</option>
              <option value="LATEST_START">최신 시작일순</option>
              <option value="ENDING_SOON">종료 임박순</option>
              <option value="UPCOMING_START">예정 시작일순</option>
            </select>
          </label>
        </div>
        <FormError message={error} />
      </form>
      <section aria-label="검색 결과" className="results-section">
        <div className="section-heading">
          <div>
            <span className="editorial-label">EXHIBITION INDEX</span>
            <h2>발견을 기다리는 전시{state.searchRequest.type !== 'EXHIBITION' && '와 공간'}</h2>
          </div>
          <p role="status" aria-live="polite">
            {query.data ? `${query.data.pages[0].total}개의 결과` : '목록 준비 중'}
          </p>
        </div>
        <div className="applied-tags" aria-label="적용한 검색 조건">
          <span>
            대상: {{ EXHIBITION: '전시', INSTITUTION: '기관', ALL: '전체' }[applied.type ?? 'ALL']}
          </span>
          <span>
            {(
              applied.lifecycle ??
              (applied.q
                ? (['CURRENT', 'UPCOMING', 'ENDED', 'CANCELED'] as const)
                : (['CURRENT', 'UPCOMING'] as const))
            )
              .map((value) => lifecycleLabels[value])
              .join(' · ')}
          </span>
          <span>
            {
              {
                RELEVANCE: '관련도순',
                LATEST_START: '최신 시작일순',
                ENDING_SOON: '종료 임박순',
                UPCOMING_START: '예정 시작일순',
              }[applied.sort ?? 'RELEVANCE']
            }
          </span>
          {state.searchRequest.q && <span>검색어: {state.searchRequest.q}</span>}
          {state.searchRequest.region_area && (
            <span>
              {state.searchRequest.region_area} {state.searchRequest.region_district}
            </span>
          )}
          <span>검색 버튼을 누르면 조건이 적용됩니다</span>
        </div>
        {query.isPending && <LoadingState />}
        {query.isError && (
          <ErrorNotice
            error={query.error}
            retry={() => {
              if (query.isFetchNextPageError) void query.fetchNextPage();
              else void query.refetch();
            }}
          />
        )}
        {query.data && !items.length && <EmptyState />}
        <div className="results-grid catalog-results-grid">
          {items.map((item, index) =>
            item.kind === 'exhibition' ? (
              <ExhibitionCard
                key={`e-${item.id}`}
                item={item}
                index={index}
                demo={demo}
                variant="catalog"
              />
            ) : (
              <InstitutionCard key={`i-${item.id}`} item={item} />
            ),
          )}
        </div>
        {query.hasNextPage && (
          <div className="load-more">
            <button
              className="secondary-button"
              type="button"
              disabled={query.isFetchingNextPage}
              onClick={() => void query.fetchNextPage()}
            >
              {query.isFetchingNextPage ? '다음 전시를 불러오는 중…' : '전시 더 보기'}
              <ArrowDown size={17} aria-hidden="true" />
            </button>
          </div>
        )}
      </section>
    </>
  );
}

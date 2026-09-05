import { useRef, useState } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { ArrowDown, Search, X } from 'lucide-react';
import { useDiscovery } from '../../app/providers';
import type { SearchDraft } from './forms';
import { SearchFilterDialog } from './SearchFilterDialog';
import { ExhibitionCard, InstitutionCard } from '../../entities/ExhibitionCard';
import { EmptyState, ErrorNotice, FormError, LoadingState } from '../../shared/ui/Feedback';

const lifecycleLabels = {
  DEFAULT: '기본',
  ALL: '모든 상태',
  CURRENT: '현재 전시',
  UPCOMING: '예정 전시',
  ENDED: '종료 전시',
  CANCELED: '취소된 전시',
};

export function SearchPanel() {
  const { state, api, demo } = useDiscovery();
  const [error, setError] = useState('');
  const resultHeading = useRef<HTMLHeadingElement>(null);
  const draft = state.searchDraft;
  const applied = state.appliedSearchDraft;
  const query = useInfiniteQuery({
    queryKey: ['search', state.searchRevision],
    initialPageParam: 1,
    queryFn: ({ pageParam, signal }) =>
      api.search({ ...state.searchRequest, page: pageParam }, signal),
    getNextPageParam: (page) => (page.hasMore ? page.page + 1 : undefined),
  });
  const items = query.data?.pages.flatMap((page) => page.items) ?? [];
  const filterCount =
    Number(applied.type !== 'EXHIBITION') +
    Number(!!applied.area) +
    Number(applied.lifecycle !== 'DEFAULT');
  const chips: { key: string; label: string; patch: Partial<SearchDraft> }[] = [];
  if (applied.q.trim())
    chips.push({ key: 'q', label: `검색어: ${applied.q.trim()}`, patch: { q: '' } });
  if (applied.type !== 'EXHIBITION')
    chips.push({
      key: 'type',
      label: applied.type === 'ALL' ? '전체' : '기관',
      patch: { type: 'EXHIBITION' },
    });
  if (applied.area)
    chips.push({
      key: 'region',
      label: [applied.area, applied.district.trim()].filter(Boolean).join(' '),
      patch: { area: '', district: '' },
    });
  if (applied.lifecycle !== 'DEFAULT')
    chips.push({
      key: 'lifecycle',
      label: lifecycleLabels[applied.lifecycle],
      patch: { lifecycle: 'DEFAULT' },
    });

  function refine(patch: Partial<SearchDraft>) {
    try {
      state.refineSearch(patch);
      setError('');
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const resultLabel = { EXHIBITION: '전시', INSTITUTION: '기관', ALL: '결과' }[applied.type];
  return (
    <>
      <form
        className="search-form"
        role="search"
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
          <label className="sr-only" htmlFor="search-keyword">
            전시·기관 검색어
          </label>
          <input
            id="search-keyword"
            type="search"
            maxLength={100}
            placeholder="전시명·기관명으로 검색"
            value={draft.q}
            onChange={(event) => state.setSearch({ q: event.target.value })}
          />
          <button className="primary-button" type="submit">
            <span className="search-submit-label">검색하기</span>
            <Search size={19} aria-hidden="true" />
          </button>
        </div>
        <FormError message={error} />
      </form>
      <section aria-label="검색 결과" className="results-section search-results">
        <div className="search-results-toolbar">
          <div role="status" aria-live="polite">
            <h2 ref={resultHeading} tabIndex={-1}>
              {query.data
                ? `${resultLabel} ${query.data.pages[0].total}개`
                : query.isError
                  ? `${resultLabel} 목록`
                  : '불러오는 중…'}
            </h2>
          </div>
          <div className="search-result-actions">
            <SearchFilterDialog count={filterCount} />
            <label className="search-sort">
              <span className="sr-only">정렬</span>
              <select
                value={applied.sort}
                onChange={(e) => refine({ sort: e.target.value as SearchDraft['sort'] })}
              >
                <option value="RELEVANCE">관련도순</option>
                <option value="LATEST_START">최신 시작일순</option>
                <option value="ENDING_SOON">종료 임박순</option>
                <option value="UPCOMING_START">예정 시작일순</option>
              </select>
            </label>
          </div>
        </div>
        {chips.length > 0 && (
          <div className="search-applied-filters" aria-label="적용한 검색 조건">
            {chips.map((chip) => (
              <button
                key={chip.key}
                type="button"
                className="search-filter-chip"
                aria-label={`${chip.label} 해제`}
                onClick={() => {
                  refine(chip.patch);
                  resultHeading.current?.focus();
                }}
              >
                {chip.label}
                <X size={14} aria-hidden="true" />
              </button>
            ))}
          </div>
        )}
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

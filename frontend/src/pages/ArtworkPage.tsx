import { useState } from 'react';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { useDiscovery } from '../app/providers';
import type { ArtworkView } from '../shared/api/schemas';
import { ProductLayout } from './ProductLayout';
import { DetailFailure } from './DetailPage';
import { LikeButton } from '../features/personal/PersonalControls';

export function ArtworkCard({ artwork }: { artwork: ArtworkView }) {
  return (
    <article className="artwork-card">
      <p className="editorial-label">{artwork.is_demo ? '가상 작품 · 데모' : '소장 작품'}</p>
      <h2>
        <a href={`/artworks/${artwork.id}`} aria-label={`${artwork.title} 상세 보기`}>
          {artwork.title}
        </a>
      </h2>
      <p>
        {artwork.creator.name} · {artwork.production_year}
      </p>
      <p>{artwork.medium}</p>
      <p className="detail-note">{artwork.collection_institution.name}</p>
      <p className="detail-note">이미지 없이 작품 정보로 안내합니다.</p>
    </article>
  );
}

export function ArtworkPage() {
  const { api, demo } = useDiscovery();
  const [draft, setDraft] = useState('');
  const [request, setRequest] = useState({ q: '', revision: 0 });
  const query = useInfiniteQuery({
    queryKey: ['artworks', request.revision],
    initialPageParam: 1,
    queryFn: ({ pageParam, signal }) =>
      api.artworks(
        { ...(request.q ? { q: request.q } : {}), page: pageParam, page_size: 24 },
        signal,
      ),
    getNextPageParam: (page) => (page.has_more ? page.page + 1 : undefined),
  });
  const first = query.data?.pages[0];
  const items =
    query.data?.pages.flatMap((p) => p.results).filter((item) => item.is_demo === demo) ?? [];
  return (
    <ProductLayout
      title="작품에서 시작하는 발견"
      intro="마음이 가는 작품을 살펴보고 관심을 저장해보세요. 확인된 작품의 특성으로 전시를 추천합니다."
    >
      <form
        className="artwork-search"
        role="search"
        autoComplete="off"
        onSubmit={(event) => {
          event.preventDefault();
          setRequest({ q: draft.trim(), revision: request.revision + 1 });
        }}
      >
        <label className="field">
          작품·작가·소장기관
          <input
            type="search"
            maxLength={100}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="이름으로 찾아보세요"
          />
        </label>
        <button className="primary-button" type="submit">
          작품 검색
        </button>
      </form>
      {query.isPending && <p role="status">작품을 불러오고 있어요.</p>}
      {query.isError && <DetailFailure error={query.error} retry={() => void query.refetch()} />}
      {first?.availability === 'SOURCE_PENDING' ? (
        <div className="empty-state" role="status">
          <h2>작품 정보를 준비하고 있어요.</h2>
          <p>공식 출처와 이용 범위를 확인한 작품부터 소개할 예정입니다.</p>
          <a className="secondary-button" href="/discover">
            전시 둘러보기
          </a>
        </div>
      ) : (
        first && (
          <>
            <p className="detail-note" role="status">
              {first.total}개의 작품{demo && ' · 모두 기능 확인용 가상 자료입니다.'}
            </p>
            {!items.length && (
              <div className="empty-state">
                <h2>조건에 맞는 작품이 없어요.</h2>
                <p>입력한 이름을 확인해주세요.</p>
              </div>
            )}
            <div className="results-grid">
              {items.map((artwork) => (
                <ArtworkCard key={artwork.id} artwork={artwork} />
              ))}
            </div>
          </>
        )
      )}
      {query.hasNextPage && (
        <button
          className="secondary-button"
          disabled={query.isFetchingNextPage}
          onClick={() => void query.fetchNextPage()}
        >
          작품 더 보기
        </button>
      )}
    </ProductLayout>
  );
}

export function ArtworkDetailPage({ id }: { id: number }) {
  const { api, demo } = useDiscovery();
  const query = useQuery({
    queryKey: ['artwork', id],
    queryFn: ({ signal }) => api.artwork(id, signal),
  });
  const detail = query.data;
  const artwork = detail?.artwork.is_demo === demo ? detail.artwork : undefined;
  return (
    <ProductLayout title={artwork?.title ?? '작품 상세'}>
      {query.isPending && <p role="status">작품을 불러오고 있어요.</p>}
      {query.isError && <DetailFailure error={query.error} retry={() => void query.refetch()} />}
      {artwork && detail && (
        <>
          <div className="detail-actions">
            <LikeButton id={id} kind="artworks" />
            <a className="text-button" href="/discover#recommend">
              관심 작품으로 전시 추천받기
            </a>
          </div>
          <div className="detail-columns">
            <ArtworkCard artwork={artwork} />
            <section className="detail-facts" aria-label="작품 정보">
              <h2>작품의 기록</h2>
              <dl>
                {[
                  ['제작자', artwork.creator.name],
                  ['제작연도', artwork.production_year],
                  ['매체', artwork.medium],
                  ['소장기관', artwork.collection_institution.name],
                  ['문화권', artwork.cultural_context.value ?? '확인 필요'],
                ].map(([label, value]) => (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
              </dl>
              <p className="detail-note">
                출처: {artwork.source.source_owner} · 확인{' '}
                {new Date(artwork.last_verified_at).toLocaleDateString('ko-KR', {
                  timeZone: 'Asia/Seoul',
                })}
              </p>
              {!demo && (
                <a
                  className="secondary-button"
                  href={artwork.official_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  referrerPolicy="no-referrer"
                >
                  공식 작품 안내 ↗
                </a>
              )}
              <h3>관련 전시</h3>
              <p>공식 출품 관계가 확인된 전시는 아직 없어요.</p>
            </section>
          </div>
          <section className="artwork-related" aria-label="함께 살펴볼 작품">
            <h2>함께 살펴볼 작품</h2>
            {!detail.similar_artworks.length && <p>확인된 유사 작품이 아직 없어요.</p>}
            <div className="results-grid">
              {detail.similar_artworks
                .filter((item) => item.artwork.is_demo === demo)
                .map((item) => (
                  <div key={item.artwork.id}>
                    <p className="detail-note">
                      {item.reasons
                        .map((r) => (r === 'SAME_CREATOR' ? '같은 제작자' : '같은 소장기관'))
                        .join(' · ')}
                    </p>
                    <ArtworkCard artwork={item.artwork} />
                  </div>
                ))}
            </div>
          </section>
        </>
      )}
    </ProductLayout>
  );
}

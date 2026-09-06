import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useDiscovery, usePersonal } from '../app/providers';
import { ProductLayout } from './ProductLayout';
import { ExhibitionCard } from '../entities/ExhibitionCard';
import { LikeButton, CompareButton } from '../features/personal/PersonalControls';
import { DetailFailure } from './DetailPage';
import { ArtworkCard } from './ArtworkPage';

function SavedArtwork({ id }: { id: number }) {
  const { api, demo } = useDiscovery();
  const query = useQuery({
    queryKey: ['artwork', id],
    queryFn: ({ signal }) => api.artwork(id, signal),
  });
  return (
    <div className="saved-item">
      {query.isPending && <p role="status">작품 확인 중…</p>}
      {query.data?.artwork.is_demo === demo && <ArtworkCard artwork={query.data.artwork} />}
      {query.isError && <DetailFailure error={query.error} retry={() => void query.refetch()} />}
      <div className="detail-actions">
        <LikeButton id={id} kind="artworks" />
      </div>
    </div>
  );
}

function SavedExhibition({ id, recent }: { id: number; recent: boolean }) {
  const { api, demo } = useDiscovery();
  const query = useQuery({
    queryKey: ['exhibition', id],
    queryFn: ({ signal }) => api.exhibition(id, signal),
  });
  return (
    <div className="saved-item">
      {query.isPending && <p role="status">전시 확인 중…</p>}
      {query.data && <ExhibitionCard item={query.data.item} demo={demo} />}
      {query.isError && <DetailFailure error={query.error} retry={() => void query.refetch()} />}
      <div className="detail-actions">
        {!recent && <LikeButton id={id} />}
        {query.data && <CompareButton id={id} />}
      </div>
    </div>
  );
}
function SavedInstitution({ id }: { id: number }) {
  const { api } = useDiscovery();
  const query = useQuery({
    queryKey: ['institution-summary', id],
    queryFn: ({ signal }) => api.institution(id, 1, signal),
  });
  return (
    <article className="institution-card">
      {query.isPending && <p role="status">기관 확인 중…</p>}
      {query.data && (
        <>
          <h2>{query.data.institution.name}</h2>
          <p>현재 등록 전시 {query.data.total}개</p>
          <a className="text-button" href={`/institutions/${id}`}>
            기관 상세 보기 →
          </a>
        </>
      )}
      {query.isError && <DetailFailure error={query.error} retry={() => void query.refetch()} />}
      <LikeButton id={id} kind="institutions" />
    </article>
  );
}
export function SavedPage() {
  const personal = usePersonal();
  const [tab, setTab] = useState<'exhibitions' | 'institutions' | 'artworks' | 'recent'>(
    'exhibitions',
  );
  const [limit, setLimit] = useState(20);
  const ids = personal.data[tab];
  return (
    <ProductLayout
      title="관심과 최근 기록"
      intro="관심은 이 브라우저에만 저장됩니다. 최근 본 전시는 추천 취향에 반영하지 않아요."
    >
      <div className="detail-actions" role="group" aria-label="저장 항목 종류">
        {(
          [
            ['exhibitions', '전시'],
            ['institutions', '기관'],
            ['artworks', '작품'],
            ['recent', '최근 본 전시'],
          ] as const
        ).map(([value, label]) => (
          <button
            key={value}
            className="secondary-button"
            aria-pressed={tab === value}
            onClick={() => {
              setTab(value);
              setLimit(20);
            }}
          >
            {label} {personal.data[value].length}
          </button>
        ))}
      </div>
      {!ids.length && (
        <div className="empty-state">
          <h2>아직 저장된 항목이 없어요.</h2>
          <p>마음에 드는 전시·작품·기관의 상세에서 관심을 저장해보세요.</p>
          <a href="/discover" className="secondary-button">
            전시 둘러보기
          </a>
        </div>
      )}
      <div className="results-grid">
        {ids
          .slice(0, limit)
          .map((id) =>
            tab === 'artworks' ? (
              <SavedArtwork key={id} id={id} />
            ) : tab === 'institutions' ? (
              <SavedInstitution key={id} id={id} />
            ) : (
              <SavedExhibition key={id} id={id} recent={tab === 'recent'} />
            ),
          )}
      </div>
      {limit < ids.length && (
        <button className="secondary-button" onClick={() => setLimit((n) => n + 20)}>
          저장 항목 더 보기
        </button>
      )}
    </ProductLayout>
  );
}

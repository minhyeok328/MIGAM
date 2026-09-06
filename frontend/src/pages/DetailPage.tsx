import { useEffect } from 'react';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { useDiscovery, usePersonal } from '../app/providers';
import { DiscoveryApiError } from '../shared/api/client';
import type { ExhibitionDetail } from '../shared/api/schemas';
import { ProductLayout } from './ProductLayout';
import { LoadingState, ErrorNotice } from '../shared/ui/Feedback';
import { ExhibitionCard } from '../entities/ExhibitionCard';
import { LikeButton, CompareButton } from '../features/personal/PersonalControls';
import {
  accessibilityOptions,
  sensoryOptions,
  reservationOptions,
} from '../features/discovery/forms';
import { MapPanel } from '../features/map/MapPanel';

export const stateLabel = (state: string) =>
  state === 'CONFLICT' ? '출처 간 정보 충돌 · 확인 필요' : '확인 필요';
export function factRows(detail: ExhibitionDetail) {
  const labels: Record<string, string> = {
    ...accessibilityOptions,
    ...sensoryOptions,
    AGE_CONDITION: '연령 조건',
  };
  const facts = [...detail.visit_information.accessibility, ...detail.visit_information.sensory];
  return Object.entries(labels).map(([kind, label]) => {
    const fact = facts.find((item) => item.kind === kind);
    return [
      label,
      fact?.state === 'CONFIRMED'
        ? `${fact.value === 'CONFIRMED_POSITIVE' ? '해당 사항 확인됨' : '해당 사항 없음 확인됨'}${fact.details.length ? ` · ${fact.details.join(' · ')}` : ''}`
        : stateLabel(fact?.state ?? 'UNKNOWN'),
    ];
  });
}
export function visitRows(detail: ExhibitionDetail) {
  const v = detail.visit_information;
  const schedule = detail.operating_schedule;
  return [
    [
      '관람료',
      v.price.state === 'CONFIRMED'
        ? v.price.is_free
          ? '무료'
          : `${v.price.amount?.toLocaleString('ko-KR')} ${v.price.currency === 'KRW' ? '원' : (v.price.currency ?? '')}`
        : stateLabel(v.price.state),
    ],
    [
      '예약',
      v.reservation.state === 'CONFIRMED' && v.reservation.reservation_type
        ? reservationOptions[v.reservation.reservation_type]
        : stateLabel(v.reservation.state),
    ],
    [
      '예상 관람시간',
      v.duration.state === 'CONFIRMED'
        ? `${v.duration.minimum_minutes ?? '?'}–${v.duration.maximum_minutes ?? '?'}분`
        : stateLabel(v.duration.state),
    ],
    [
      '확인된 첫 관람일',
      schedule.visit_availability
        ? `${schedule.visit_availability.first_open_date} · ${schedule.visit_availability.opens_at.slice(0, 5)}–${schedule.visit_availability.closes_at.slice(0, 5)}`
        : ['ENDED', 'CANCELED'].includes(detail.item.lifecycle)
          ? '현재 관람 불가'
          : schedule.state === 'CLOSED'
            ? '관람 가능한 개관일 없음'
            : '확인 필요',
    ],
  ];
}
export function DetailFailure({ error, retry }: { error: unknown; retry: () => void }) {
  return error instanceof DiscoveryApiError && error.kind === 'not_found' ? (
    <div className="empty-state">
      <h2>현재 표시할 수 없는 항목이에요.</h2>
      <p>삭제되었거나 공식 정보의 재확인이 필요할 수 있어요.</p>
      <a className="secondary-button" href="/discover">
        전시 탐색으로
      </a>
    </div>
  ) : (
    <ErrorNotice error={error} retry={retry} />
  );
}
export function ExhibitionDetailPage({ id }: { id: number }) {
  const { api, demo } = useDiscovery();
  const personal = usePersonal();
  const query = useQuery({
    queryKey: ['exhibition', id],
    queryFn: ({ signal }) => api.exhibition(id, signal),
  });
  const detail = query.data;
  useEffect(() => {
    if (detail) personal.recordRecent(id);
  }, [detail, id, personal.recordRecent]);
  return (
    <ProductLayout title={detail?.item.title ?? '전시 상세'}>
      {query.isPending && <LoadingState />}
      {query.isError && <DetailFailure error={query.error} retry={() => void query.refetch()} />}
      {detail && (
        <>
          <div className="detail-actions">
            <LikeButton id={id} />
            <CompareButton id={id} />
            <a className="text-button" href={`/institutions/${detail.exhibition.institution.id}`}>
              {detail.item.institution} 보기 →
            </a>
          </div>
          <div className="detail-columns">
            <ExhibitionCard item={detail.item} demo={demo} variant="editorial" />
            <section className="detail-facts" aria-labelledby="visit-title">
              <h2 id="visit-title">방문 전에 확인할 정보</h2>
              <dl>
                {visitRows(detail).map(([label, value]) => (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
              </dl>
              <h3>접근성·감각 정보</h3>
              <dl>
                {[
                  ...detail.visit_information.accessibility,
                  ...detail.visit_information.sensory,
                ].map((fact) => (
                  <div key={fact.kind}>
                    <dt>
                      {
                        (
                          {
                            ...accessibilityOptions,
                            ...sensoryOptions,
                            AGE_CONDITION: '연령 조건',
                          } as Record<string, string>
                        )[fact.kind]
                      }
                    </dt>
                    <dd>
                      {fact.state === 'CONFIRMED'
                        ? fact.value === 'CONFIRMED_POSITIVE'
                          ? '해당 사항 확인됨'
                          : '해당 사항 없음 확인됨'
                        : stateLabel(fact.state)}
                      {fact.details.length > 0 && ` · ${fact.details.join(' · ')}`}
                    </dd>
                  </div>
                ))}
              </dl>
              {!detail.visit_information.accessibility.length &&
                !detail.visit_information.sensory.length && <p>공식 정보 확인 필요</p>}
              <p className="detail-note">
                미확인 정보는 제공하지 않는다는 뜻이 아닙니다. 관람 전 공식 안내를 확인해주세요.
              </p>
              <details className="source-details">
                <summary>방문 정보의 근거</summary>
                {visitRows(detail).every(([, value]) => value.includes('확인 필요')) && (
                  <p>현재 확인된 방문 정보가 없습니다.</p>
                )}
                {[
                  ...detail.visit_information.price.evidence,
                  ...detail.visit_information.reservation.evidence,
                  ...detail.visit_information.duration.evidence,
                  ...detail.operating_schedule.rules.map((r) => r.evidence),
                ].map((proof, index) => (
                  <p key={index}>
                    {proof.source.source_owner} ·{' '}
                    {proof.scope === 'INSTITUTION' ? '기관 공통 안내' : '전시 안내'} ·{' '}
                    {new Date(proof.verified_at).toLocaleString('ko-KR', {
                      timeZone: 'Asia/Seoul',
                    })}
                  </p>
                ))}
              </details>
              {!demo &&
                detail.visit_information.reservation.official_urls.map((url) => (
                  <a
                    key={url}
                    className="secondary-button"
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    referrerPolicy="no-referrer"
                  >
                    공식 예약 안내 ↗
                  </a>
                ))}
            </section>
          </div>
          <MapPanel
            key={id}
            institution={detail.item.institution}
            area={`${detail.item.area} ${detail.item.district}`}
            demo={demo}
          />
        </>
      )}
    </ProductLayout>
  );
}
export function InstitutionDetailPage({ id }: { id: number }) {
  const { api, demo } = useDiscovery();
  const query = useInfiniteQuery({
    queryKey: ['institution', id],
    initialPageParam: 1,
    queryFn: ({ pageParam, signal }) => api.institution(id, pageParam, signal),
    getNextPageParam: (page) => (page.has_more ? page.page + 1 : undefined),
  });
  const first = query.data?.pages[0];
  return (
    <ProductLayout
      title={first?.institution.name ?? '기관 상세'}
      intro={
        first
          ? `${first.institution.region.area} ${first.institution.region.district} · 전시 ${first.total}개`
          : undefined
      }
    >
      {query.isPending && <LoadingState />}
      {query.isError && <DetailFailure error={query.error} retry={() => void query.refetch()} />}
      {first && (
        <>
          <div className="detail-actions">
            <LikeButton id={id} kind="institutions" />
          </div>
          <div className="results-grid">
            {query
              .data!.pages.flatMap((p) => p.items)
              .map((item, index) => (
                <ExhibitionCard key={item.id} item={item} index={index} demo={demo} />
              ))}
          </div>
        </>
      )}
      {query.hasNextPage && (
        <button
          className="secondary-button"
          disabled={query.isFetchingNextPage}
          onClick={() => void query.fetchNextPage()}
        >
          전시 더 보기
        </button>
      )}
    </ProductLayout>
  );
}

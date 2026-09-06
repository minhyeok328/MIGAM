import { useQueries } from '@tanstack/react-query';
import { useDiscovery, usePersonal } from '../app/providers';
import { ProductLayout } from './ProductLayout';
import { visitRows, factRows, DetailFailure } from './DetailPage';
import { accessibilityOptions, sensoryOptions } from '../features/discovery/forms';
import { LikeButton, CompareButton } from '../features/personal/PersonalControls';

export function ComparePage() {
  const { api, demo } = useDiscovery();
  const personal = usePersonal();
  const queries = useQueries({
    queries: personal.compare.map((id) => ({
      queryKey: ['exhibition', id],
      queryFn: ({ signal }: { signal: AbortSignal }) => api.exhibition(id, signal),
    })),
  });
  const labels = [
    '상태',
    '기간',
    '장소',
    '관람료',
    '예약',
    '예상 관람시간',
    '확인된 첫 관람일',
    ...Object.values(accessibilityOptions),
    ...Object.values(sensoryOptions),
    '연령 조건',
    '정보 확인',
  ];
  const states = {
    CURRENT: '현재 전시',
    UPCOMING: '예정 전시',
    ENDED: '종료 · 관람 불가',
    CANCELED: '취소 · 관람 불가',
  };
  return (
    <ProductLayout
      title="전시 비교"
      intro="최대 3개 전시를 비교할 수 있어요. 비교 선택은 현재 창에서 유지됩니다."
    >
      {!queries.length ? (
        <div className="empty-state">
          <h2>비교할 전시를 골라주세요.</h2>
          <a className="secondary-button" href="/discover">
            전시 둘러보기
          </a>
        </div>
      ) : (
        <div className="comparison-table-wrap">
          <table className="comparison-table">
            <caption className="sr-only">선택한 전시의 상태와 방문 정보 비교</caption>
            <thead>
              <tr>
                <th scope="col">비교 항목</th>
                {queries.map((query, index) => (
                  <th scope="col" key={personal.compare[index]}>
                    {query.data ? (
                      <a href={`/exhibitions/${query.data.item.id}`}>{query.data.item.title}</a>
                    ) : query.isPending ? (
                      '불러오는 중…'
                    ) : (
                      '정보 확인 필요'
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {labels.map((label, row) => (
                <tr key={label}>
                  <th scope="row">{label}</th>
                  {queries.map((query, index) => {
                    const detail = query.data;
                    const values = detail
                      ? [
                          states[detail.item.lifecycle],
                          `${detail.item.startDate} — ${detail.item.endDate}`,
                          `${detail.item.area} ${detail.item.district} · ${detail.item.venue}`,
                          ...visitRows(detail).map(([, value]) => value),
                          ...factRows(detail).map(([, value]) => value),
                          `${detail.item.sourceOwner} · ${detail.item.freshness === 'STALE' ? '재확인 필요 · ' : ''}${new Date(detail.item.verifiedAt).toLocaleDateString('ko-KR', { timeZone: 'Asia/Seoul' })}`,
                        ]
                      : [];
                    return (
                      <td
                        key={personal.compare[index]}
                        data-title={detail?.item.title ?? `전시 ${index + 1}`}
                      >
                        {values[row] ?? '확인 필요'}
                      </td>
                    );
                  })}
                </tr>
              ))}
              <tr>
                <th scope="row">선택</th>
                {queries.map((query, index) => (
                  <td
                    key={personal.compare[index]}
                    data-title={query.data?.item.title ?? `전시 ${index + 1}`}
                  >
                    <div className="detail-actions">
                      <LikeButton id={personal.compare[index]} />
                      <CompareButton id={personal.compare[index]} />
                    </div>
                    {query.isError && (
                      <DetailFailure error={query.error} retry={() => void query.refetch()} />
                    )}
                    {query.data && !demo && (
                      <a
                        href={query.data.item.officialUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        referrerPolicy="no-referrer"
                      >
                        공식 안내 ↗
                      </a>
                    )}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </ProductLayout>
  );
}

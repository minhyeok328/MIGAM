import { useEffect, useRef, useState } from 'react';
import { createKakaoProvider, type MapProvider, type MapView, type Place } from './provider';

export function MapPanel({
  institution,
  area,
  demo = false,
  provider,
}: {
  institution: string;
  area: string;
  demo?: boolean;
  provider?: MapProvider;
}) {
  const [defaultProvider] = useState(() =>
    createKakaoProvider(import.meta.env.VITE_KAKAO_JAVASCRIPT_KEY ?? ''),
  );
  const mapProvider = provider ?? defaultProvider;
  const embedded = Boolean(provider || import.meta.env.VITE_KAKAO_JAVASCRIPT_KEY);
  const [places, setPlaces] = useState<Place[]>([]);
  const [place, setPlace] = useState<Place | null>(null);
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapView | null>(null);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  useEffect(() => {
    if (!place || !container.current) return;
    try {
      map.current = mapProvider.render(container.current, place);
    } catch {
      setStatus('지도를 표시하지 못했어요. 공식 안내와 장소 검색 링크를 이용해주세요.');
    }
    return () => {
      map.current?.destroy();
      map.current = null;
    };
  }, [place, mapProvider]);
  return (
    <section className="map-panel" aria-labelledby="map-title">
      <h2 id="map-title">장소와 지도</h2>
      {demo ? (
        <p>가상 기관은 실제 지도에 표시하지 않습니다.</p>
      ) : (
        <>
          <p>
            {embedded
              ? '선택하면 기관명과 지역으로 카카오 장소 검색을 실행합니다. 주소를 확인한 뒤 장소를 골라주세요.'
              : '카카오맵에서 기관의 위치와 길찾기를 확인할 수 있어요. 실제 전시장 주소는 공식 안내와 함께 확인해주세요.'}
          </p>
          <div className="detail-actions">
            {embedded && (
              <button
                className="secondary-button"
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  setStatus('장소를 찾고 있어요.');
                  try {
                    const result = await mapProvider.search(`${area} ${institution}`);
                    if (!mounted.current) return;
                    setPlaces(result);
                    setStatus(
                      result.length
                        ? '카카오 장소 검색 결과입니다. 실제 방문 장소가 맞는지 확인해주세요.'
                        : '일치하는 장소를 찾지 못했어요. 공식 안내에서 주소를 확인해주세요.',
                    );
                  } catch {
                    if (mounted.current)
                      setStatus(
                        '현재 지도를 불러올 수 없어요. 카카오맵에서 장소를 직접 확인할 수 있습니다.',
                      );
                  } finally {
                    if (mounted.current) setBusy(false);
                  }
                }}
              >
                지도에서 장소 찾기
              </button>
            )}
            <a
              className="text-button"
              href={`https://map.kakao.com/link/search/${encodeURIComponent(`${area} ${institution}`)}`}
              target="_blank"
              rel="noopener noreferrer"
              referrerPolicy="no-referrer"
            >
              카카오맵에서 검색 ↗
            </a>
          </div>
          <p role="status">{status}</p>
          {places.length > 0 && (
            <ul className="map-places">
              {places.map((value) => (
                <li key={value.id}>
                  <button
                    className="secondary-button"
                    aria-pressed={value.id === place?.id}
                    onClick={() => setPlace(value)}
                  >
                    {value.name} · {value.address}
                  </button>
                </li>
              ))}
            </ul>
          )}
          {place && (
            <>
              <div ref={container} className="map-canvas" aria-label={`${place.name} 지도`} />
              <button
                className="secondary-button"
                onClick={() => {
                  if (!navigator.geolocation) {
                    setStatus('이 브라우저에서는 위치 기능을 사용할 수 없어요.');
                    return;
                  }
                  navigator.geolocation.getCurrentPosition(
                    (position) => {
                      if (mounted.current && map.current) {
                        map.current.locate(position.coords.latitude, position.coords.longitude);
                        setStatus('현재 위치를 지도에 표시했어요. 좌표는 저장하지 않습니다.');
                      }
                    },
                    () => {
                      if (mounted.current)
                        setStatus(
                          '현재 위치를 확인할 수 없어요. 선택한 장소 지도는 계속 사용할 수 있습니다.',
                        );
                    },
                    { timeout: 10000, maximumAge: 0, enableHighAccuracy: false },
                  );
                }}
              >
                내 위치 표시
              </button>
            </>
          )}
        </>
      )}
    </section>
  );
}

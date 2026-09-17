import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { createKakaoProvider, type MapProvider, type MapView, type Place } from './provider';
import { mapSearchPlan, matchesMapPlace } from './searchNames';
import { MapControls } from './MapControls';

export function MapPanel({
  institution,
  area,
  venue,
  demo = false,
  provider,
}: {
  institution: string;
  area: string;
  venue?: string;
  demo?: boolean;
  provider?: MapProvider;
}) {
  const [defaultProvider] = useState(() =>
    createKakaoProvider(import.meta.env.VITE_KAKAO_JAVASCRIPT_KEY ?? ''),
  );
  const mapProvider = provider ?? defaultProvider;
  const embedded = Boolean(provider || import.meta.env.VITE_KAKAO_JAVASCRIPT_KEY);
  const searchPlan = useMemo(
    () => mapSearchPlan(institution, area, venue),
    [institution, area, venue],
  );
  const [places, setPlaces] = useState<Place[]>([]);
  const [place, setPlace] = useState<Place | null>(null);
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);
  const [canRetry, setCanRetry] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapView | null>(null);
  const descriptionId = useId();

  useEffect(() => {
    let active = true;
    setPlaces([]);
    setPlace(null);
    setCanRetry(false);
    setBusy(embedded && !demo);
    setStatus(
      demo
        ? ''
        : embedded
          ? '지도를 불러오는 중이에요.'
          : '지도를 표시할 수 없어요. 위의 공식 전시 안내에서 위치를 확인해주세요.',
    );
    if (!embedded || demo) return;

    // Defer until effect setup settles so StrictMode cleanup can cancel duplicate work.
    queueMicrotask(async () => {
      if (!active) return;
      try {
        let result: Place[] = [];
        for (const query of searchPlan.queries) {
          result = (await mapProvider.search(query)).filter((candidate) =>
            matchesMapPlace(candidate, searchPlan),
          );
          if (!active) return;
          if (result.length) break;
        }
        if (!result.length && searchPlan.target) {
          result = (await mapProvider.geocode(searchPlan.target.address)).filter((candidate) =>
            matchesMapPlace(candidate, searchPlan),
          );
          if (!active) return;
        }
        setPlaces(result);
        if (result.length && searchPlan.target) {
          const name = searchPlan.target.name.replace(/\s+/g, '');
          const selected =
            result.find((candidate) => candidate.name.replace(/\s+/g, '') === name) ?? result[0];
          setPlace(selected);
          setStatus('');
        } else {
          setCanRetry(!result.length);
          setStatus(
            result.length
              ? '실제 방문 장소가 맞는지 주소를 확인한 뒤 선택해주세요.'
              : '일치하는 장소를 찾지 못했어요. 공식 안내에서 주소를 확인해주세요.',
          );
        }
      } catch {
        if (active) {
          setCanRetry(true);
          setStatus(
            '현재 지도를 불러올 수 없어요. 다시 시도하거나 위의 공식 전시 안내를 확인해주세요.',
          );
        }
      } finally {
        if (active) setBusy(false);
      }
    });
    return () => {
      active = false;
    };
  }, [searchPlan, mapProvider, embedded, demo, attempt]);

  useEffect(() => {
    if (!place || !container.current) return;
    let view: MapView;
    try {
      view = mapProvider.render(container.current, place);
      map.current = view;
    } catch {
      setPlace(null);
      setCanRetry(true);
      setStatus('지도를 표시하지 못했어요. 다시 시도하거나 위의 공식 전시 안내를 확인해주세요.');
      return;
    }
    return () => {
      if (map.current === view) map.current = null;
      view.destroy();
    };
  }, [place, mapProvider]);

  return (
    <section className="map-panel" aria-label="전시장 지도">
      {demo ? (
        <p>가상 기관은 실제 지도에 표시하지 않습니다.</p>
      ) : (
        <>
          {!place && status && <p role="status">{status}</p>}
          {embedded && canRetry && (
            <button
              className="secondary-button"
              disabled={busy}
              onClick={() => setAttempt((value) => value + 1)}
            >
              지도 다시 불러오기
            </button>
          )}
          {!place && !searchPlan.target && places.length > 0 && (
            <ul className="map-places">
              {places.map((value) => (
                <li key={value.id}>
                  <button
                    className="secondary-button"
                    onClick={() => {
                      setPlace(value);
                      setStatus('');
                    }}
                  >
                    {value.name} · {value.address}
                  </button>
                </li>
              ))}
            </ul>
          )}
          {place && (
            <>
              <p id={descriptionId} className="sr-only">
                {place.name} · {place.address}
                {place.kind === 'address' &&
                  ' 공식 주소의 위치이며 전시실·입구 위치는 공식 안내에서 확인해주세요.'}
                {searchPlan.target?.note && ' ' + searchPlan.target.note}
              </p>
              <div className="map-frame">
                <div
                  ref={container}
                  className="map-canvas"
                  aria-label={place.name + ' 지도'}
                  aria-describedby={descriptionId}
                />
                <MapControls key={place.id} view={map} />
              </div>
            </>
          )}
        </>
      )}
    </section>
  );
}

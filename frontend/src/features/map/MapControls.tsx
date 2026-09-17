import { useEffect, useRef, useState, type RefObject } from 'react';
import { Crosshair, MapPin, Minus, Plus, X } from 'lucide-react';
import type { MapView } from './provider';

export function MapControls({ view }: { view: RefObject<MapView | null> }) {
  const [locating, setLocating] = useState(false);
  const [notice, setNotice] = useState('');
  const request = useRef(0);
  useEffect(
    () => () => {
      request.current += 1;
    },
    [],
  );

  function locate() {
    const activeMap = view.current;
    if (!activeMap) return;
    if (!navigator.geolocation) {
      setNotice('이 브라우저에서는 현재 위치를 확인할 수 없어요.');
      return;
    }
    const id = ++request.current;
    const isCurrent = () => request.current === id && view.current === activeMap;
    setLocating(true);
    setNotice('현재 위치를 확인하고 있어요.');
    try {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          if (!isCurrent()) return;
          activeMap.locate(position.coords.latitude, position.coords.longitude);
          setLocating(false);
          setNotice('현재 위치를 표시했어요.');
        },
        (error) => {
          if (!isCurrent()) return;
          setLocating(false);
          setNotice(
            error.code === 1
              ? '위치 권한이 꺼져 있어요. 브라우저에서 허용하면 사용할 수 있어요.'
              : '현재 위치를 확인하지 못했어요. 잠시 후 다시 시도해주세요.',
          );
        },
        { timeout: 10000, maximumAge: 0, enableHighAccuracy: false },
      );
    } catch {
      if (isCurrent()) {
        setLocating(false);
        setNotice('현재 위치를 확인할 수 없어요.');
      }
    }
  }

  return (
    <>
      <div className="map-controls" role="group" aria-label="지도 조작">
        <button
          type="button"
          aria-label="현재 위치"
          title="현재 위치"
          disabled={locating}
          onClick={locate}
        >
          <Crosshair size={19} aria-hidden="true" />
        </button>
        <div className="map-zoom-controls">
          <button
            type="button"
            aria-label="지도 확대"
            title="지도 확대"
            onClick={() => view.current?.zoom('in')}
          >
            <Plus size={20} aria-hidden="true" />
          </button>
          <button
            type="button"
            aria-label="지도 축소"
            title="지도 축소"
            onClick={() => view.current?.zoom('out')}
          >
            <Minus size={20} aria-hidden="true" />
          </button>
        </div>
        <button
          type="button"
          aria-label="전시장 위치로 돌아가기"
          title="전시장 위치로 돌아가기"
          onClick={() => {
            request.current += 1;
            setLocating(false);
            setNotice('');
            view.current?.reset();
          }}
        >
          <MapPin size={19} aria-hidden="true" />
        </button>
      </div>
      {notice && (
        <div className="map-notice">
          <p role="status">{notice}</p>
          <button
            type="button"
            aria-label="지도 알림 닫기"
            title="닫기"
            onClick={() => setNotice('')}
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>
      )}
    </>
  );
}

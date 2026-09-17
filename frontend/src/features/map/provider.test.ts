import { afterEach, expect, it, vi } from 'vitest';

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
  delete window.kakao;
  document.head
    .querySelectorAll('script[src*="dapi.kakao.com"]')
    .forEach((script) => script.remove());
});

async function setupGeocoder(rows: unknown[], status = 'OK') {
  vi.resetModules();
  const addressSearch = vi.fn((_address, callback) => callback(rows, status));
  window.kakao = {
    maps: {
      load: (ready: () => void) => ready(),
      services: {
        Status: { OK: 'OK', ZERO_RESULT: 'ZERO_RESULT' },
        AnalyzeType: { EXACT: 'EXACT' },
        Geocoder: class {
          addressSearch = addressSearch;
        },
      },
    },
  } as unknown as NonNullable<Window['kakao']>;
  const { createKakaoProvider } = await import('./provider');
  const provider = createKakaoProvider('test-key');
  const pending = provider.geocode('서울 종로구 세종대로 175');
  document.head.querySelector('script[src*="dapi.kakao.com"]')!.dispatchEvent(new Event('load'));
  return { pending, addressSearch, provider };
}

it('uses exact address matching and distinguishes road-address coordinates from places', async () => {
  const row = {
    address_name: '서울 종로구 세종로 81-3',
    road_address: { address_name: '서울 종로구 세종대로 175' },
    x: '126.97',
    y: '37.57',
  };
  const { pending, addressSearch } = await setupGeocoder([
    row,
    { ...row, x: '' },
    { ...row, y: 'NaN' },
    { ...row, x: '181' },
    { ...row, road_address: null },
  ]);
  expect(await pending).toEqual([
    {
      id: 'address:서울 종로구 세종대로 175',
      name: '공식 주소 위치',
      address: '서울 종로구 세종대로 175',
      latitude: 37.57,
      longitude: 126.97,
      kind: 'address',
    },
  ]);
  expect(addressSearch).toHaveBeenCalledWith('서울 종로구 세종대로 175', expect.any(Function), {
    analyze_type: 'EXACT',
  });
});

it('returns no candidates for zero results and rejects service errors', async () => {
  const empty = await setupGeocoder([], 'ZERO_RESULT');
  await expect(empty.pending).resolves.toEqual([]);
  document.head.querySelector('script[src*="dapi.kakao.com"]')!.remove();
  const failed = await setupGeocoder([], 'ERROR');
  await expect(failed.pending).rejects.toThrow('MAP_UNAVAILABLE');
});

it('does not load the SDK for an address without a key', async () => {
  const { createKakaoProvider } = await import('./provider');
  await expect(createKakaoProvider('').geocode('서울 종로구 세종대로 175')).rejects.toThrow(
    'MAP_UNAVAILABLE',
  );
  expect(document.head.querySelector('script[src*="dapi.kakao.com"]')).toBeNull();
});

it('zooms within road map limits and returns to the exhibition center and scale', async () => {
  const { pending, provider } = await setupGeocoder([]);
  await pending;
  let level = 4;
  const movedCenter = { latitude: 37.6, longitude: 127.1 };
  const map = {
    getCenter: vi.fn(() => movedCenter),
    relayout: vi.fn(),
    getLevel: () => level,
    setLevel: vi.fn((value: number) => {
      level = value;
    }),
    setCenter: vi.fn(),
  };
  const removeMarker = vi.fn();
  const listeners = new Map<string, () => void>();
  const removeListener = vi.fn();
  window.kakao!.maps.event = {
    addListener: (_map, name, callback) => {
      listeners.set(name, callback);
    },
    removeListener,
  };
  let resize!: () => void;
  const observe = vi.fn();
  const disconnect = vi.fn();
  vi.stubGlobal(
    'ResizeObserver',
    class {
      constructor(callback: () => void) {
        resize = callback;
      }
      observe = observe;
      disconnect = disconnect;
    },
  );
  window.kakao!.maps.LatLng = vi.fn(function (latitude: number, longitude: number) {
    return { latitude, longitude };
  }) as unknown as NonNullable<Window['kakao']>['maps']['LatLng'];
  window.kakao!.maps.Map = vi.fn(function () {
    return map;
  }) as unknown as NonNullable<Window['kakao']>['maps']['Map'];
  window.kakao!.maps.Marker = vi.fn(function () {
    return { setMap: removeMarker };
  }) as unknown as NonNullable<Window['kakao']>['maps']['Marker'];
  const container = document.createElement('div');
  const view = provider.render(container, {
    id: 'venue',
    name: '전시장',
    address: '서울 주소',
    latitude: 37.57,
    longitude: 126.97,
  });
  expect(observe).toHaveBeenCalledWith(container);
  resize();
  expect(map.relayout).toHaveBeenCalledOnce();
  expect(map.setCenter).toHaveBeenLastCalledWith({ latitude: 37.57, longitude: 126.97 });
  listeners.get('dragend')!();
  map.getCenter.mockReturnValue({ latitude: 38, longitude: 128 });
  resize();
  expect(map.setCenter).toHaveBeenLastCalledWith(movedCenter);
  view.zoom('in');
  expect(level).toBe(3);
  view.zoom('out');
  expect(level).toBe(4);
  level = 1;
  view.zoom('in');
  expect(level).toBe(1);
  level = 14;
  view.zoom('out');
  expect(level).toBe(14);
  view.reset();
  expect(level).toBe(4);
  expect(map.setCenter).toHaveBeenLastCalledWith({ latitude: 37.57, longitude: 126.97 });
  view.destroy();
  expect(disconnect).toHaveBeenCalledOnce();
  expect(removeListener).toHaveBeenCalledTimes(2);
  expect(removeMarker).toHaveBeenCalledWith(null);
});

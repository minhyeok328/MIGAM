export type Place = {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  kind?: 'address';
};
export type MapView = {
  destroy: () => void;
  locate: (latitude: number, longitude: number) => void;
  zoom: (direction: 'in' | 'out') => void;
  reset: () => void;
};
export type MapProvider = {
  search: (query: string) => Promise<Place[]>;
  geocode: (address: string) => Promise<Place[]>;
  render: (container: HTMLElement, place: Place) => MapView;
};
type Point = object;
type Marker = { setMap: (map: object | null) => void };
type Kakao = {
  maps: {
    load: (ready: () => void) => void;
    LatLng: new (latitude: number, longitude: number) => Point;
    Map: new (
      container: HTMLElement,
      options: { center: Point; level: number },
    ) => {
      getCenter: () => Point;
      setCenter: (point: Point) => void;
      relayout: () => void;
      getLevel: () => number;
      setLevel: (level: number) => void;
    };
    Marker: new (options: { map: object; position: Point }) => Marker;
    event: {
      addListener: (target: object, type: string, listener: () => void) => void;
      removeListener: (target: object, type: string, listener: () => void) => void;
    };
    services: {
      Status: { OK: string; ZERO_RESULT: string };
      AnalyzeType: { EXACT: string };
      Geocoder: new () => {
        addressSearch: (
          address: string,
          callback: (
            rows: {
              address_name: string;
              road_address: { address_name: string } | null;
              x: string;
              y: string;
            }[],
            status: string,
          ) => void,
          options: { analyze_type: string },
        ) => void;
      };
      Places: new () => {
        keywordSearch: (
          query: string,
          callback: (
            rows: {
              id: string;
              place_name: string;
              road_address_name: string;
              address_name: string;
              x: string;
              y: string;
            }[],
            status: string,
          ) => void,
        ) => void;
      };
    };
  };
};
declare global {
  interface Window {
    kakao?: Kakao;
  }
}
let sdkPromise: Promise<Kakao> | undefined;
async function loadSdk(key: string): Promise<Kakao> {
  if (!key) throw new Error('MAP_UNAVAILABLE');
  if (!sdkPromise)
    sdkPromise = new Promise<Kakao>((resolve, reject) => {
      const script = document.createElement('script');
      const timer = window.setTimeout(fail, 12000);
      function fail() {
        window.clearTimeout(timer);
        script.remove();
        sdkPromise = undefined;
        reject(new Error('MAP_UNAVAILABLE'));
      }
      script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(key)}&libraries=services&autoload=false`;
      script.async = true;
      script.referrerPolicy = 'strict-origin-when-cross-origin';
      script.onerror = fail;
      script.onload = () => {
        if (!window.kakao?.maps) {
          fail();
          return;
        }
        window.kakao.maps.load(() => {
          window.clearTimeout(timer);
          resolve(window.kakao!);
        });
      };
      document.head.append(script);
    });
  return sdkPromise;
}
export function createKakaoProvider(key: string): MapProvider {
  let sdk: Kakao | undefined;
  return {
    async search(query) {
      sdk = await loadSdk(key);
      return new Promise<Place[]>((resolve, reject) => {
        const timer = window.setTimeout(() => reject(new Error('MAP_UNAVAILABLE')), 10000);
        new sdk!.maps.services.Places().keywordSearch(query, (rows, status) => {
          window.clearTimeout(timer);
          if (status === sdk!.maps.services.Status.ZERO_RESULT) {
            resolve([]);
            return;
          }
          if (status !== sdk!.maps.services.Status.OK) {
            reject(new Error('MAP_UNAVAILABLE'));
            return;
          }
          resolve(
            rows
              .filter(
                (row) =>
                  Number.isFinite(Number(row.y)) &&
                  Number.isFinite(Number(row.x)) &&
                  Math.abs(Number(row.y)) <= 90 &&
                  Math.abs(Number(row.x)) <= 180,
              )
              .slice(0, 5)
              .map((row) => ({
                id: row.id,
                name: row.place_name,
                address: row.road_address_name || row.address_name,
                latitude: Number(row.y),
                longitude: Number(row.x),
              })),
          );
        });
      });
    },
    async geocode(address) {
      sdk = await loadSdk(key);
      return new Promise<Place[]>((resolve, reject) => {
        const timer = window.setTimeout(() => reject(new Error('MAP_UNAVAILABLE')), 10000);
        new sdk!.maps.services.Geocoder().addressSearch(
          address,
          (rows, status) => {
            window.clearTimeout(timer);
            if (status === sdk!.maps.services.Status.ZERO_RESULT) {
              resolve([]);
              return;
            }
            if (status !== sdk!.maps.services.Status.OK) {
              reject(new Error('MAP_UNAVAILABLE'));
              return;
            }
            resolve(
              rows
                .filter(
                  (row) =>
                    row.road_address &&
                    row.x.trim() &&
                    row.y.trim() &&
                    Number.isFinite(Number(row.x)) &&
                    Number.isFinite(Number(row.y)) &&
                    Math.abs(Number(row.y)) <= 90 &&
                    Math.abs(Number(row.x)) <= 180,
                )
                .slice(0, 5)
                .map((row) => ({
                  id: `address:${row.road_address!.address_name}`,
                  name: '공식 주소 위치',
                  address: row.road_address!.address_name,
                  latitude: Number(row.y),
                  longitude: Number(row.x),
                  kind: 'address',
                })),
            );
          },
          { analyze_type: sdk!.maps.services.AnalyzeType.EXACT },
        );
      });
    },
    render(container, place) {
      if (!sdk) throw new Error('MAP_UNAVAILABLE');
      const maps = sdk.maps;
      const point = new maps.LatLng(place.latitude, place.longitude);
      const map = new maps.Map(container, { center: point, level: 4 });
      const marker = new maps.Marker({ map, position: point });
      let location: Marker | undefined;
      let center = point;
      const rememberCenter = () => {
        center = map.getCenter();
      };
      maps.event.addListener(map, 'dragend', rememberCenter);
      maps.event.addListener(map, 'zoom_changed', rememberCenter);
      const resize = new ResizeObserver(() => {
        map.relayout();
        map.setCenter(center);
      });
      resize.observe(container);
      return {
        zoom(direction) {
          map.setLevel(Math.min(14, Math.max(1, map.getLevel() + (direction === 'in' ? -1 : 1))));
        },
        reset() {
          center = point;
          map.setCenter(point);
          map.setLevel(4);
        },
        locate(latitude, longitude) {
          location?.setMap(null);
          center = new maps.LatLng(latitude, longitude);
          location = new maps.Marker({ map, position: center });
          map.setCenter(center);
        },
        destroy() {
          resize.disconnect();
          maps.event.removeListener(map, 'dragend', rememberCenter);
          maps.event.removeListener(map, 'zoom_changed', rememberCenter);
          marker.setMap(null);
          location?.setMap(null);
          container.replaceChildren();
        },
      };
    },
  };
}

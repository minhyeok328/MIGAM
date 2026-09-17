import { StrictMode } from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import { MapPanel } from './MapPanel';
import type { Place } from './provider';

const sejongPlace: Place = {
  id: '25587453',
  name: '세종문화회관 미술관',
  address: '서울 종로구 세종대로 175',
  latitude: 37.57,
  longitude: 126.97,
};
const sejong = {
  institution: '세종문화회관 본관 전시공간',
  area: '서울 종로구',
  venue: '세종미술관 1관,세종미술관 2관',
};
function makeProvider(places: Place[] = [sejongPlace]) {
  return {
    search: vi.fn<(_: string) => Promise<Place[]>>().mockResolvedValue(places),
    geocode: vi.fn<(_: string) => Promise<Place[]>>().mockResolvedValue([]),
    render: vi.fn(() => ({ destroy: vi.fn(), locate: vi.fn(), zoom: vi.fn(), reset: vi.fn() })),
  };
}
afterEach(() => vi.unstubAllGlobals());

it('automatically shows the reviewed venue once in StrictMode without requesting user location', async () => {
  const provider = makeProvider();
  const getCurrentPosition = vi.fn();
  vi.stubGlobal('navigator', { geolocation: { getCurrentPosition } });
  const { unmount } = render(
    <StrictMode>
      <MapPanel {...sejong} provider={provider} />
    </StrictMode>,
  );
  await screen.findByLabelText('세종문화회관 미술관 지도');
  await waitFor(() => expect(provider.render).toHaveBeenCalledOnce());
  expect(provider.search).toHaveBeenCalledExactlyOnceWith('서울 종로구 세종미술관');
  expect(provider.geocode).not.toHaveBeenCalled();
  expect(screen.queryByRole('button', { name: '지도에서 장소 찾기' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /세종문화회관 미술관 ·/ })).not.toBeInTheDocument();
  expect(getCurrentPosition).not.toHaveBeenCalled();
  expect(screen.getByRole('button', { name: '현재 위치' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '지도 확대' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '지도 축소' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '전시장 위치로 돌아가기' })).toBeInTheDocument();
  expect(screen.queryByRole('heading')).not.toBeInTheDocument();
  expect(screen.queryByRole('link')).not.toBeInTheDocument();
  expect(screen.queryByRole('status')).not.toBeInTheDocument();
  expect(screen.getByLabelText('세종문화회관 미술관 지도')).toHaveAccessibleDescription(
    '세종문화회관 미술관 · 서울 종로구 세종대로 175',
  );
  const view = provider.render.mock.results[0].value;
  unmount();
  expect(view.destroy).toHaveBeenCalledOnce();
});

it('connects inside-map zoom and recenter controls to the current map', async () => {
  const provider = makeProvider();
  const user = userEvent.setup();
  render(<MapPanel {...sejong} provider={provider} />);
  await screen.findByLabelText('세종문화회관 미술관 지도');
  const view = provider.render.mock.results[0].value;
  await user.click(screen.getByRole('button', { name: '지도 확대' }));
  await user.click(screen.getByRole('button', { name: '지도 축소' }));
  await user.click(screen.getByRole('button', { name: '전시장 위치로 돌아가기' }));
  expect(view.zoom.mock.calls).toEqual([['in'], ['out']]);
  expect(view.reset).toHaveBeenCalledOnce();
});

it('requests location only on click and keeps denied-location feedback inside the map', async () => {
  const user = userEvent.setup();
  const provider = makeProvider();
  const getCurrentPosition = vi.fn();
  vi.stubGlobal('navigator', { geolocation: { getCurrentPosition } });
  const { unmount } = render(<MapPanel {...sejong} provider={provider} />);
  await screen.findByLabelText('세종문화회관 미술관 지도');
  const view = provider.render.mock.results[0].value;
  expect(getCurrentPosition).not.toHaveBeenCalled();
  await user.click(screen.getByRole('button', { name: '현재 위치' }));
  expect(screen.getByRole('button', { name: '현재 위치' })).toBeDisabled();
  await act(async () => getCurrentPosition.mock.calls[0][1]({ code: 1 }));
  expect(screen.getByRole('status')).toHaveTextContent('위치 권한');
  expect(view.locate).not.toHaveBeenCalled();
  expect(screen.getByLabelText('세종문화회관 미술관 지도')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: '지도 알림 닫기' }));
  expect(screen.queryByRole('status')).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: '현재 위치' }));
  await act(async () =>
    getCurrentPosition.mock.calls[1][0]({ coords: { latitude: 37.5, longitude: 127.1 } }),
  );
  expect(view.locate).toHaveBeenCalledExactlyOnceWith(37.5, 127.1);
  await user.click(screen.getByRole('button', { name: '현재 위치' }));
  unmount();
  await act(async () =>
    getCurrentPosition.mock.calls[2][0]({ coords: { latitude: 37.6, longitude: 127.2 } }),
  );
  expect(view.locate).toHaveBeenCalledOnce();
});

it('prefers the representative reviewed place when multiple same-address candidates exist', async () => {
  const representative = {
    ...sejongPlace,
    name: '서울시립 미술아카이브',
    address: '서울 종로구 평창문화로 101',
  };
  const provider = makeProvider([
    { ...representative, id: 'annex', name: '서울시립 미술아카이브 모음동' },
    representative,
  ]);
  render(
    <MapPanel
      institution="서울시립 미술아카이브"
      area="서울 종로구"
      venue="서울시립 미술아카이브"
      provider={provider}
    />,
  );
  await screen.findByLabelText('서울시립 미술아카이브 지도');
  expect(provider.render).toHaveBeenCalledWith(expect.any(HTMLElement), representative);
});

it('searches unreviewed venues automatically but requires selection before displaying a candidate', async () => {
  const user = userEvent.setup();
  const provider = makeProvider();
  render(
    <MapPanel institution="새 기관" venue="새 전시장" area="서울 종로구" provider={provider} />,
  );
  const result = await screen.findByRole('button', { name: /세종문화회관 미술관 ·/ });
  expect(provider.render).not.toHaveBeenCalled();
  await user.click(result);
  expect(provider.render).toHaveBeenCalledOnce();
});

it('demo never loads a map even when a provider is available', async () => {
  const provider = makeProvider();
  render(<MapPanel {...sejong} demo provider={provider} />);
  await act(async () => {});
  expect(provider.search).not.toHaveBeenCalled();
  expect(provider.geocode).not.toHaveBeenCalled();
  expect(screen.queryByRole('link', { name: '카카오맵에서 검색 ↗' })).not.toBeInTheDocument();
});

it('shows a minimal unavailable state without links or SDK when no key is configured', async () => {
  const scripts = document.scripts.length;
  render(<MapPanel {...sejong} />);
  await act(async () => {});
  expect(document.scripts.length).toBe(scripts);
  expect(screen.queryByRole('button', { name: '지도 다시 불러오기' })).not.toBeInTheDocument();
  expect(screen.queryByRole('link')).not.toBeInTheDocument();
  expect(screen.getByRole('status')).toHaveTextContent('위의 공식 전시 안내');
});

it('tries the institution after an empty preferred search without another click', async () => {
  const provider = makeProvider();
  provider.search.mockResolvedValueOnce([]);
  render(<MapPanel {...sejong} provider={provider} />);
  await screen.findByLabelText('세종문화회관 미술관 지도');
  expect(provider.search.mock.calls).toEqual([
    ['서울 종로구 세종미술관'],
    ['서울 종로구 세종문화회관 본관 전시공간'],
  ]);
});

it('automatically displays an exact official address when name results are unrelated', async () => {
  const provider = makeProvider([{ ...sejongPlace, name: '세종문화회관 주차장' }]);
  provider.geocode.mockResolvedValue([
    {
      ...sejongPlace,
      id: 'wrong-address',
      name: '공식 주소 위치',
      kind: 'address',
      address: '서울 종로구 세종대로 지하 175',
    },
    { ...sejongPlace, id: 'address:1', name: '공식 주소 위치', kind: 'address' },
  ]);
  render(<MapPanel {...sejong} provider={provider} />);
  await screen.findByLabelText('공식 주소 위치 지도');
  expect(provider.geocode).toHaveBeenCalledExactlyOnceWith('서울 종로구 세종대로 175');
  expect(screen.queryByRole('status')).not.toBeInTheDocument();
  expect(screen.getByLabelText('공식 주소 위치 지도')).toHaveAccessibleDescription(/전시실·입구/);
  expect(provider.render).toHaveBeenCalledWith(
    expect.any(HTMLElement),
    expect.objectContaining({ id: 'address:1' }),
  );
});

it('stops on API errors and retries only on explicit retry', async () => {
  const user = userEvent.setup();
  const provider = makeProvider();
  provider.search.mockRejectedValueOnce(new Error('MAP_UNAVAILABLE'));
  render(<MapPanel {...sejong} provider={provider} />);
  const retry = await screen.findByRole('button', { name: '지도 다시 불러오기' });
  expect(provider.search).toHaveBeenCalledOnce();
  expect(provider.geocode).not.toHaveBeenCalled();
  expect(screen.getByRole('status')).toHaveTextContent('현재 지도를 불러올 수 없어요.');
  await user.click(retry);
  await screen.findByLabelText('세종문화회관 미술관 지도');
  expect(provider.search).toHaveBeenCalledTimes(2);
  expect(screen.queryByRole('button', { name: '지도 다시 불러오기' })).not.toBeInTheDocument();
});

it('does not use a reviewed address for the wrong region when no results exist', async () => {
  const provider = makeProvider([]);
  render(<MapPanel institution={sejong.institution} area="서울 중구" provider={provider} />);
  await screen.findByRole('button', { name: '지도 다시 불러오기' });
  expect(provider.search.mock.calls).toEqual([['서울 중구 세종문화회관 본관 전시공간']]);
  expect(provider.geocode).not.toHaveBeenCalled();
  expect(screen.getByRole('status')).toHaveTextContent('일치하는 장소를 찾지 못했어요.');
});

it('discards a late result from an earlier detail and cleans up the displayed map', async () => {
  const provider = makeProvider();
  let resolveOld!: (places: Place[]) => void;
  provider.search.mockReturnValueOnce(
    new Promise((resolve) => {
      resolveOld = resolve;
    }),
  );
  const { rerender, unmount } = render(<MapPanel {...sejong} provider={provider} />);
  await waitFor(() => expect(provider.search).toHaveBeenCalledOnce());
  const suwon = {
    ...sejongPlace,
    id: 'suwon',
    name: '수원시립미술관',
    address: '경기 수원시 팔달구 정조로 833',
  };
  provider.search.mockResolvedValue([suwon]);
  rerender(
    <MapPanel institution="수원시립미술관 행궁 본관" area="경기 수원시" provider={provider} />,
  );
  await screen.findByLabelText('수원시립미술관 지도');
  await act(async () => resolveOld([sejongPlace]));
  expect(screen.queryByLabelText('세종문화회관 미술관 지도')).not.toBeInTheDocument();
  expect(provider.render).toHaveBeenCalledOnce();
  unmount();
  expect(provider.render.mock.results[0].value.destroy).toHaveBeenCalledOnce();
});

it('does not continue fallback searches after leaving the detail', async () => {
  const provider = makeProvider();
  let finish!: (places: Place[]) => void;
  provider.search.mockReturnValueOnce(
    new Promise((resolve) => {
      finish = resolve;
    }),
  );
  const { unmount } = render(<MapPanel {...sejong} provider={provider} />);
  await waitFor(() => expect(provider.search).toHaveBeenCalledOnce());
  unmount();
  await act(async () => finish([]));
  expect(provider.search).toHaveBeenCalledOnce();
  expect(provider.geocode).not.toHaveBeenCalled();
  expect(provider.render).not.toHaveBeenCalled();
});

it('offers retry and points to the existing official exhibition guidance when rendering fails', async () => {
  const provider = makeProvider();
  provider.render.mockImplementationOnce(() => {
    throw new Error('MAP_UNAVAILABLE');
  });
  render(<MapPanel {...sejong} provider={provider} />);
  await screen.findByRole('button', { name: '지도 다시 불러오기' });
  expect(screen.getByRole('status')).toHaveTextContent('지도를 표시하지 못했어요.');
  expect(screen.queryByLabelText('세종문화회관 미술관 지도')).not.toBeInTheDocument();
  expect(screen.queryByRole('link')).not.toBeInTheDocument();
  expect(screen.getByRole('status')).toHaveTextContent('위의 공식 전시 안내');
});

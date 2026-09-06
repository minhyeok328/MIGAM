import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { MapPanel } from './MapPanel';
import { createKakaoProvider } from './provider';

it('loads no external map until explicit action and requires place selection', async () => {
  const user = userEvent.setup();
  const destroy = vi.fn();
  const provider = {
    search: vi.fn(async () => [
      { id: '1', name: '기관 장소', address: '서울 주소', latitude: 37, longitude: 127 },
    ]),
    render: vi.fn(() => ({ destroy, locate: vi.fn() })),
  };
  const { unmount } = render(<MapPanel institution="미술관" area="서울" provider={provider} />);
  expect(provider.search).not.toHaveBeenCalled();
  await user.click(screen.getByRole('button', { name: '지도에서 장소 찾기' }));
  await screen.findByRole('button', { name: '기관 장소 · 서울 주소' });
  expect(provider.render).not.toHaveBeenCalled();
  await user.click(screen.getByRole('button', { name: '기관 장소 · 서울 주소' }));
  expect(provider.render).toHaveBeenCalledOnce();
  unmount();
  expect(destroy).toHaveBeenCalledOnce();
});
it('missing keys do not append a script and demo never invokes the provider', async () => {
  const initial = document.scripts.length;
  await expect(createKakaoProvider('').search('서울 기관')).rejects.toThrow();
  expect(document.scripts.length).toBe(initial);
  const provider = { search: vi.fn(), render: vi.fn() };
  render(<MapPanel institution="가상" area="서울" demo provider={provider} />);
  expect(screen.queryByRole('button', { name: '지도에서 장소 찾기' })).not.toBeInTheDocument();
  expect(provider.search).not.toHaveBeenCalled();
});

it('offers only the external map link when no embedded key is configured', () => {
  render(<MapPanel institution="서소문본관" area="서울 중구" />);
  expect(screen.queryByRole('button', { name: '지도에서 장소 찾기' })).not.toBeInTheDocument();
  expect(screen.getByRole('link', { name: '카카오맵에서 검색 ↗' })).toHaveAttribute(
    'target',
    '_blank',
  );
});

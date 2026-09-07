import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it } from 'vitest';
import { App } from './App';
import { createDiscoveryApi } from '../shared/api/client';
import { detailFixture, searchFixture, recommendationFixture } from '../test/fixtures';
import { artworkDetailFixture } from '../test/artworkFixture';
afterEach(() => {
  localStorage.clear();
  window.history.replaceState(null, '', '/');
});

it('connects artwork detail, interest and verified features to recommendations', async () => {
  const user = userEvent.setup();
  const bodies: object[] = [];
  const api = createDiscoveryApi(async (input) => {
    const req = new Request(input);
    if (req.method === 'POST') {
      bodies.push(await req.json());
      return Response.json(recommendationFixture);
    }
    if (req.url.includes('/artworks/1/')) return Response.json(artworkDetailFixture);
    if (req.url.includes('/artworks/'))
      return Response.json({
        total: 1,
        page: 1,
        page_size: 24,
        has_more: false,
        availability: 'DEMO',
        results: [artworkDetailFixture.artwork],
      });
    return Response.json(searchFixture);
  });
  window.history.replaceState(null, '', '/artworks');
  render(<App api={api} demo />);
  await user.click(await screen.findByRole('link', { name: '가상 작품: 선의 안부 상세 보기' }));
  expect(
    await screen.findByRole('heading', { level: 1, name: '가상 작품: 선의 안부' }),
  ).toBeInTheDocument();
  expect(screen.getByText('공식 출품 관계가 확인된 전시는 아직 없어요.')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: '관심 저장' }));
  expect(JSON.parse(localStorage.getItem('migam:personal:v1:demo')!).artworks).toEqual([1]);
  await user.click(screen.getByRole('link', { name: '관심 작품으로 전시 추천받기' }));
  await waitFor(() =>
    expect(bodies).toContainEqual(
      expect.objectContaining({ preferred_features: [{ axis: 'MEDIA_GROUP', value: 'PAINTING' }] }),
    ),
  );
  expect(localStorage.getItem('migam:personal:v1:demo')).not.toContain('선의 안부');
});

it('explains a pending artwork source without displaying demo data in normal mode', async () => {
  window.history.replaceState(null, '', '/artworks');
  render(
    <App
      api={createDiscoveryApi(async () =>
        Response.json({
          total: 0,
          page: 1,
          page_size: 24,
          has_more: false,
          results: [],
          availability: 'SOURCE_PENDING',
        }),
      )}
    />,
  );
  expect(await screen.findByText('작품 정보를 준비하고 있어요.')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '관심 저장' })).not.toBeInTheDocument();
});

it('connects discovery to detail, saved comparison and confirmed local reset', async () => {
  const user = userEvent.setup();
  const api = createDiscoveryApi(async (input) => {
    const req = new Request(input);
    return Response.json(req.url.includes('/exhibitions/') ? detailFixture : searchFixture);
  });
  window.history.replaceState(null, '', '/discover');
  render(<App api={api} />);
  await user.type(screen.getByRole('searchbox'), '사적인 입력');
  await user.click(await screen.findByRole('link', { name: '고요의 형태 상세 보기' }));
  expect(await screen.findByRole('heading', { level: 1, name: '고요의 형태' })).toBeInTheDocument();
  const visitInfo = screen.getByRole('region', { name: '관람 안내' });
  expect(within(visitInfo).getAllByRole('link', { name: '공식 전시 안내' }).length).toBe(1);
  for (const link of within(visitInfo).getAllByRole('link', { name: '공식 전시 안내' })) {
    expect(link).toHaveAttribute('href', detailFixture.exhibition.official_url);
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  }
  expect(within(visitInfo).queryByText('확인된 첫 관람일')).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: '관심 저장' }));
  await user.click(screen.getByRole('button', { name: '비교 추가' }));
  await user.click(screen.getByRole('link', { name: /비교.*1/ }));
  expect(await screen.findByRole('heading', { level: 1, name: '전시 비교' })).toBeInTheDocument();
  expect(await screen.findByRole('link', { name: '고요의 형태' })).toBeInTheDocument();
  expect(screen.queryByRole('rowheader', { name: '확인된 첫 관람일' })).not.toBeInTheDocument();
  expect(screen.getAllByRole('link', { name: '공식 안내에서 확인' }).length).toBeGreaterThan(0);
  await user.click(screen.getByRole('link', { name: '전시 찾기' }));
  expect(screen.getByRole('searchbox')).toHaveValue('사적인 입력');
  expect(localStorage.getItem('migam:personal:v1')).not.toContain('사적인 입력');
  await user.click(screen.getByRole('link', { name: '내 데이터' }));
  await user.click(screen.getByRole('button', { name: '모든 로컬 데이터 삭제' }));
  await user.keyboard('{Escape}');
  expect(screen.getByRole('button', { name: '모든 로컬 데이터 삭제' })).toHaveFocus();
  await user.click(screen.getByRole('button', { name: '모든 로컬 데이터 삭제' }));
  await user.click(screen.getByRole('button', { name: '삭제하기' }));
  expect(localStorage.getItem('migam:personal:v1')).toBeNull();
});

it('uses saved taste in recommendations without persisting conditions', async () => {
  const user = userEvent.setup();
  const bodies: object[] = [];
  const api = createDiscoveryApi(async (input) => {
    const req = new Request(input);
    if (req.method === 'POST') {
      bodies.push(await req.json());
      return Response.json(recommendationFixture);
    }
    return Response.json(searchFixture);
  });
  window.history.replaceState(null, '', '/taste');
  render(<App api={api} />);
  await user.click(screen.getByRole('checkbox', { name: '회화' }));
  await user.click(screen.getByRole('button', { name: '다음' }));
  await user.click(screen.getByRole('button', { name: '건너뛰기' }));
  await user.click(screen.getByRole('button', { name: '취향 저장' }));
  await user.click(screen.getByRole('link', { name: '취향과 가까운 전시 보기' }));
  await waitFor(() =>
    expect(bodies).toContainEqual(
      expect.objectContaining({ preferred_features: [{ axis: 'MEDIA_GROUP', value: 'PAINTING' }] }),
    ),
  );
});

it('keeps mixed opening evidence aligned with the correct exhibition in comparison', async () => {
  const user = userEvent.setup();
  const openDetail = {
    ...detailFixture,
    exhibition: { ...detailFixture.exhibition, id: 2, title: '개관일 확인 전시' },
    operating_schedule: {
      state: 'OPEN',
      rules: [],
      visit_availability: {
        first_open_date: '2026-09-08',
        opens_at: '10:00:00',
        closes_at: '18:00:00',
        verified_at: '2026-09-07T00:00:00Z',
      },
    },
  };
  window.history.replaceState(null, '', '/discover');
  render(
    <App
      api={createDiscoveryApi(async (input) => {
        const url = new Request(input).url;
        return Response.json(
          url.includes('/exhibitions/2/')
            ? openDetail
            : url.includes('/exhibitions/1/')
              ? detailFixture
              : {
                  ...searchFixture,
                  total: 2,
                  results: [detailFixture.exhibition, openDetail.exhibition],
                },
        );
      })}
    />,
  );
  await user.click(await screen.findByRole('link', { name: '고요의 형태 상세 보기' }));
  await user.click(await screen.findByRole('button', { name: '비교 추가' }));
  await user.click(screen.getByRole('link', { name: '전시 찾기' }));
  await user.click(await screen.findByRole('link', { name: '개관일 확인 전시 상세 보기' }));
  await user.click(await screen.findByRole('button', { name: '비교 추가' }));
  await user.click(screen.getByRole('link', { name: /비교.*2/ }));
  const openingRow = (await screen.findByRole('rowheader', { name: '확인된 첫 관람일' })).closest(
    'tr',
  )!;
  const cells = within(openingRow).getAllByRole('cell');
  expect(within(cells[0]).getByRole('link', { name: '공식 안내에서 확인' })).toHaveAttribute(
    'href',
    detailFixture.exhibition.official_url,
  );
  expect(cells[1]).toHaveTextContent('2026-09-08');
  const accessRow = screen.getByRole('rowheader', { name: '휠체어 접근' }).closest('tr')!;
  expect(within(accessRow).getAllByRole('link', { name: '공식 안내에서 확인' })).toHaveLength(2);
});

it('keeps unknown and conflicting demo facts free of external guidance links', async () => {
  window.history.replaceState(null, '', '/exhibitions/1');
  render(
    <App
      demo
      api={createDiscoveryApi(async () =>
        Response.json({
          ...detailFixture,
          visit_information: {
            ...detailFixture.visit_information,
            price: { ...detailFixture.visit_information.price, state: 'CONFLICT' },
          },
        }),
      )}
    />,
  );
  const info = await screen.findByRole('region', { name: '관람 안내' });
  expect(within(info).getByText('출처 간 정보 충돌 · 확인 필요')).toBeInTheDocument();
  expect(within(info).queryByRole('link')).not.toBeInTheDocument();
  expect(within(info).queryByText('무료')).not.toBeInTheDocument();
  expect(within(info).queryByText('확인된 첫 관람일')).not.toBeInTheDocument();
});

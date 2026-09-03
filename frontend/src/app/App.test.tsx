import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { App } from './App';
import { createDiscoveryApi } from '../shared/api/client';
import { exhibitionFixture, searchFixture, recommendationFixture } from '../test/fixtures';

function apiWith(handler: (request: Request) => Promise<Response> | Response) {
  return createDiscoveryApi(async (input) => handler(new Request(input)));
}
const response = () => Response.json(searchFixture);

describe('discovery user flows', () => {
  it('searches explicitly, appends more results, and replaces pages for a new query', async () => {
    const user = userEvent.setup();
    const api = apiWith((request) => {
      const query = new URL(request.url).searchParams;
      if (query.get('q') === '다른 전시')
        return Response.json({
          ...searchFixture,
          results: [{ ...exhibitionFixture, id: 3, title: '새로운 결과' }],
        });
      if (query.get('page') === '2')
        return Response.json({
          ...searchFixture,
          page: 2,
          total: 2,
          results: [{ ...exhibitionFixture, id: 2, title: '두 번째 전시' }],
        });
      return Response.json({ ...searchFixture, total: 2, has_more: true });
    });
    render(<App api={api} />);
    expect(await screen.findByRole('heading', { name: '고요의 형태' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '전시 더 보기' }));
    expect(await screen.findByRole('heading', { name: '두 번째 전시' })).toBeInTheDocument();
    await user.type(screen.getByRole('searchbox'), '다른 전시');
    await user.selectOptions(screen.getByLabelText('전시 상태'), 'ENDED');
    expect(screen.getByLabelText('적용한 검색 조건')).not.toHaveTextContent('종료 전시');
    expect(screen.getByRole('heading', { name: '두 번째 전시' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '검색하기' }));
    expect(await screen.findByRole('heading', { name: '새로운 결과' })).toBeInTheDocument();
    expect(screen.getByLabelText('적용한 검색 조건')).toHaveTextContent('종료 전시');
    expect(screen.queryByRole('heading', { name: '두 번째 전시' })).not.toBeInTheDocument();
  });

  it('preserves input on failure and retries without relaxing it', async () => {
    const user = userEvent.setup();
    let failed = true;
    const queries: string[] = [];
    const api = apiWith((request) => {
      const q = new URL(request.url).searchParams.get('q') ?? '';
      queries.push(q);
      return q && failed ? new Response('private failure', { status: 503 }) : response();
    });
    render(<App api={api} />);
    await screen.findByRole('heading', { name: '고요의 형태' });
    await user.type(screen.getByRole('searchbox'), '보존할 조건');
    await user.click(screen.getByRole('button', { name: '검색하기' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('불러오지 못했어요');
    expect(screen.getByRole('searchbox')).toHaveValue('보존할 조건');
    expect(screen.queryByText('private failure')).not.toBeInTheDocument();
    failed = false;
    await user.click(screen.getByRole('button', { name: '다시 시도' }));
    await screen.findByRole('heading', { name: '고요의 형태' });
    expect(queries.slice(-2)).toEqual(['보존할 조건', '보존할 조건']);
  });

  it('keeps existing cards when fetching the next page fails', async () => {
    const user = userEvent.setup();
    render(
      <App
        api={apiWith((request) =>
          new URL(request.url).searchParams.get('page') === '2'
            ? new Response('', { status: 503 })
            : Response.json({ ...searchFixture, has_more: true, total: 25 }),
        )}
      />,
    );
    await screen.findByRole('heading', { name: '고요의 형태' });
    await user.click(screen.getByRole('button', { name: '전시 더 보기' }));
    await screen.findByRole('alert');
    expect(screen.getByRole('heading', { name: '고요의 형태' })).toBeInTheDocument();
  });

  it('does not let a late previous response replace the current query', async () => {
    const user = userEvent.setup();
    let resolveOld!: (value: Response) => void;
    const api = apiWith((request) => {
      const q = new URL(request.url).searchParams.get('q');
      if (q === '이전')
        return new Promise((resolve) => {
          resolveOld = resolve;
        });
      if (q === '최신')
        return Response.json({
          ...searchFixture,
          results: [{ ...exhibitionFixture, title: '최신 결과' }],
        });
      return response();
    });
    render(<App api={api} />);
    await screen.findByRole('heading', { name: '고요의 형태' });
    await user.type(screen.getByRole('searchbox'), '이전');
    await user.click(screen.getByRole('button', { name: '검색하기' }));
    await waitFor(() => expect(resolveOld).toBeTypeOf('function'));
    await user.clear(screen.getByRole('searchbox'));
    await user.type(screen.getByRole('searchbox'), '최신');
    await user.click(screen.getByRole('button', { name: '검색하기' }));
    await screen.findByRole('heading', { name: '최신 결과' });
    await act(async () => resolveOld(response()));
    expect(screen.queryByRole('heading', { name: '고요의 형태' })).not.toBeInTheDocument();
  });

  it('sends zero budget and explicit safety and visit modes, restoring dialog focus', async () => {
    const user = userEvent.setup();
    const bodies: unknown[] = [];
    const api = apiWith(async (request) => {
      if (request.method !== 'POST') return response();
      bodies.push(await request.json());
      return Response.json(recommendationFixture);
    });
    render(<App api={api} />);
    await user.click(screen.getByRole('tab', { name: '조건으로 추천받기' }));
    await user.type(screen.getByLabelText('최대 예산 (원)'), '0');
    const trigger = screen.getByRole('button', { name: /자세한 조건/ });
    await user.click(trigger);
    expect(screen.getByRole('dialog')).toHaveAccessibleName('방문 조건 자세히');
    await user.click(screen.getByLabelText('휠체어 접근'));
    await user.selectOptions(screen.getByLabelText('예약 방식'), 'NOT_REQUIRED');
    await user.selectOptions(screen.getByLabelText('예약 조건 중요도'), 'REQUIRED');
    await user.keyboard('{Escape}');
    expect(trigger).toHaveFocus();
    await user.click(screen.getByRole('button', { name: '이 조건으로 추천받기' }));
    await waitFor(() =>
      expect(bodies.at(-1)).toMatchObject({
        max_budget_krw: 0,
        required_accessibility: ['WHEELCHAIR_ACCESS'],
        reservation: { mode: 'REQUIRED', types: ['NOT_REQUIRED'] },
      }),
    );
    const verified = await screen.findByRole('region', { name: '추천 전시' });
    expect(within(verified).getByRole('heading', { name: '고요의 형태' })).toBeInTheDocument();
    const uncertain = screen.getByRole('region', { name: '방문 전 확인이 필요한 전시' });
    expect(within(uncertain).getByText('관람료 확인 필요')).toBeInTheDocument();
    expect(within(verified).queryByText('빛을 따라 걷는 시간')).not.toBeInTheDocument();
    const applied = screen.getByLabelText('적용한 추천 조건');
    expect(applied).toHaveTextContent('휠체어 접근 · 필수');
    expect(applied).toHaveTextContent('예약 없이 관람 · 필수');
    await user.click(trigger);
    await user.click(screen.getByLabelText('휠체어 접근'));
    await user.keyboard('{Escape}');
    expect(applied).toHaveTextContent('휠체어 접근 · 필수');
  });

  it('displays honest zero results and keeps a required safety checkbox', async () => {
    const user = userEvent.setup();
    render(
      <App
        api={apiWith((request) =>
          request.method === 'POST'
            ? Response.json({
                algorithm_version: 'test',
                candidate_count: 0,
                recommendations: [],
                needs_verification: [],
              })
            : response(),
        )}
      />,
    );
    await user.click(screen.getByRole('tab', { name: '조건으로 추천받기' }));
    await user.click(screen.getByRole('button', { name: /자세한 조건/ }));
    await user.click(screen.getByLabelText('섬광'));
    await user.keyboard('{Escape}');
    await user.click(screen.getByRole('button', { name: '이 조건으로 추천받기' }));
    expect(await screen.findByText('조건에 맞는 전시가 없어요.')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /자세한 조건/ }));
    expect(screen.getByLabelText('섬광')).toBeChecked();
  });

  it('limits explicit moods to three and does not write browser storage or URL', async () => {
    const user = userEvent.setup();
    const before = window.location.href;
    render(
      <App
        api={apiWith((request) =>
          request.method === 'POST' ? Response.json(recommendationFixture) : response(),
        )}
      />,
    );
    await user.click(screen.getByRole('tab', { name: '조건으로 추천받기' }));
    for (const label of ['차분한', '몰입형', '활기찬'])
      await user.click(screen.getByRole('checkbox', { name: new RegExp(label) }));
    expect(screen.getByRole('checkbox', { name: /실험적/ })).toBeDisabled();
    expect(window.location.href).toBe(before);
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });

  it('uses text cards for hidden or failed images, and marks fictional demo content', async () => {
    const user = userEvent.setup();
    render(
      <App
        demo
        api={apiWith(() =>
          Response.json({
            ...searchFixture,
            results: [
              {
                ...exhibitionFixture,
                media: {
                  status: 'INLINE',
                  media_url: 'https://example.com/image.jpg',
                  page_url: null,
                  credit_line: '가상 이미지',
                },
              },
            ],
          }),
        )}
      />,
    );
    const image = await screen.findByRole('img');
    fireEvent.error(image);
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: '고요의 형태' })).toBeInTheDocument();
    expect(screen.getByText(/실제 전시가 아닙니다/)).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /공식 페이지/ })).not.toBeInTheDocument();
    await user.click(screen.getByRole('tab', { name: '전시 둘러보기' }));
  });
});

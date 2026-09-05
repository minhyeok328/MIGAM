import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it } from 'vitest';
import { App } from '../../app/App';
import { createDiscoveryApi } from '../../shared/api/client';
import { searchFixture } from '../../test/fixtures';

function renderSearch() {
  const requests: URLSearchParams[] = [];
  const api = createDiscoveryApi(async (input) => {
    requests.push(new URL(new Request(input).url).searchParams);
    return Response.json(searchFixture);
  });
  window.history.replaceState(null, '', '/discover');
  render(<App api={api} />);
  return requests;
}

afterEach(() => window.history.replaceState(null, '', '/'));

describe('search refinements', () => {
  it('loads results without choosing filters and discards dismissed filter edits', async () => {
    const user = userEvent.setup();
    const requests = renderSearch();
    await screen.findByRole('heading', { name: '고요의 형태' });
    expect(screen.queryByLabelText('시·도')).not.toBeInTheDocument();
    expect(requests[0].get('type')).toBe('EXHIBITION');
    expect(requests[0].has('lifecycle')).toBe(false);

    const trigger = screen.getByRole('button', { name: /^필터/ });
    await user.click(trigger);
    await user.selectOptions(screen.getByLabelText('시·도'), '서울');
    await user.type(screen.getByLabelText('시·군·구'), '종로구');
    await user.selectOptions(screen.getByLabelText('전시 상태'), 'ENDED');
    await user.keyboard('{Escape}');
    expect(trigger).toHaveFocus();
    expect(requests).toHaveLength(1);

    await user.click(trigger);
    expect(screen.getByLabelText('시·도')).toHaveValue('');
    expect(screen.getByLabelText('시·군·구')).toHaveValue('');
    expect(screen.getByLabelText('전시 상태')).toHaveValue('DEFAULT');
    await user.click(screen.getByRole('button', { name: '필터 닫기' }));
    await user.type(screen.getByRole('searchbox'), '고요{Enter}');
    await waitFor(() => expect(requests.at(-1)?.get('q')).toBe('고요'));
    expect(requests.at(-1)?.has('region_area')).toBe(false);
    expect(requests.at(-1)?.has('lifecycle')).toBe(false);
  });

  it('refines the applied query without submitting pending text and clears dependent regions', async () => {
    const user = userEvent.setup();
    const requests = renderSearch();
    await screen.findByRole('heading', { name: '고요의 형태' });
    await user.type(screen.getByRole('searchbox'), '고요{Enter}');
    await waitFor(() => expect(requests.at(-1)?.get('q')).toBe('고요'));
    await user.clear(screen.getByRole('searchbox'));
    await user.type(screen.getByRole('searchbox'), '아직 입력 중');

    await user.click(screen.getByRole('button', { name: /^필터/ }));
    await user.selectOptions(screen.getByLabelText('대상'), 'ALL');
    await user.selectOptions(screen.getByLabelText('시·도'), '서울');
    await user.type(screen.getByLabelText('시·군·구'), '종로구');
    await user.selectOptions(screen.getByLabelText('전시 상태'), 'ENDED');
    await user.click(screen.getByRole('button', { name: '필터 적용' }));
    await waitFor(() => expect(requests.at(-1)?.get('region_district')).toBe('종로구'));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(requests.at(-1)?.get('q')).toBe('고요');
    expect(requests.at(-1)?.get('lifecycle')).toBe('ENDED');

    await user.click(screen.getByRole('button', { name: /^필터/ }));
    expect(screen.getByLabelText('시·군·구')).toHaveValue('종로구');
    await user.selectOptions(screen.getByLabelText('시·도'), '경기');
    expect(screen.getByLabelText('시·군·구')).toHaveValue('');
    await user.keyboard('{Escape}');
    expect(screen.getByRole('button', { name: '서울 종로구 해제' })).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('정렬'), 'ENDING_SOON');
    await waitFor(() => expect(requests.at(-1)?.get('sort')).toBe('ENDING_SOON'));
    expect(requests.at(-1)?.get('q')).toBe('고요');
    await user.click(screen.getByRole('button', { name: '서울 종로구 해제' }));
    await waitFor(() => expect(requests.at(-1)?.has('region_area')).toBe(false));
    expect(requests.at(-1)?.has('region_district')).toBe(false);
    expect(requests.at(-1)?.get('lifecycle')).toBe('ENDED');
    expect(requests.at(-1)?.get('type')).toBe('ALL');
    expect(requests.at(-1)?.get('q')).toBe('고요');
    expect(screen.getByRole('searchbox')).toHaveValue('아직 입력 중');

    await user.click(screen.getByRole('button', { name: '종료 전시 해제' }));
    await user.click(screen.getByRole('button', { name: '전체 해제' }));
    await user.click(screen.getByRole('button', { name: '검색하기' }));
    await waitFor(() => expect(requests.at(-1)?.get('q')).toBe('아직 입력 중'));
    expect(requests.at(-1)?.get('type')).toBe('EXHIBITION');
    expect(requests.at(-1)?.has('lifecycle')).toBe(false);
    expect(requests.at(-1)?.get('sort')).toBe('ENDING_SOON');
    expect(window.location.search).toBe('');
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });
});

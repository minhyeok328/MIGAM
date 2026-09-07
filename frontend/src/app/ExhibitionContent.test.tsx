import { render, screen, within } from '@testing-library/react';
import { afterEach, expect, it } from 'vitest';
import { App } from './App';
import { createDiscoveryApi } from '../shared/api/client';
import { parseExhibitionDetail } from '../shared/api/schemas';
import { contentFixture, detailFixture } from '../test/fixtures';

afterEach(() => {
  localStorage.clear();
  window.history.replaceState(null, '', '/');
});

function renderDetail(data: unknown, demo = false) {
  window.history.replaceState(null, '', '/exhibitions/1');
  render(<App demo={demo} api={createDiscoveryApi(async () => Response.json(data))} />);
}

it('shows exhibition content and visit notes with one official link and no self card', async () => {
  renderDetail({ ...detailFixture, content: contentFixture });
  expect(await screen.findByText(contentFixture.introduction)).toBeInTheDocument();
  expect(screen.getByText(contentFixture.highlights[0])).toBeInTheDocument();
  const visit = screen.getByRole('region', { name: '관람 안내' });
  expect(within(visit).getByText('무료')).toBeInTheDocument();
  expect(within(visit).getByText(contentFixture.visit_notes[1].text)).toBeInTheDocument();
  expect(screen.getByText('2026. 9. 7. 확인')).toBeInTheDocument();
  expect(screen.getAllByRole('link', { name: '공식 전시 안내' })).toHaveLength(1);
  expect(screen.queryByRole('link', { name: '고요의 형태 상세 보기' })).not.toBeInTheDocument();
  expect(screen.queryByText('공식 안내에서 확인')).not.toBeInTheDocument();
  expect(screen.queryByText('휠체어 접근')).not.toBeInTheDocument();
  expect(screen.queryByText('예상 관람시간')).not.toBeInTheDocument();
  expect(screen.queryByText('확인된 첫 관람일')).not.toBeInTheDocument();
});

it('keeps detail useful without content and does not claim missing access is unavailable', async () => {
  renderDetail(detailFixture);
  expect(await screen.findByRole('heading', { level: 1, name: '고요의 형태' })).toBeInTheDocument();
  expect(screen.getByText(/서울 종로구 · 가상 미감 미술관 1층/)).toBeInTheDocument();
  expect(screen.getByText('전시 소개를 준비하고 있어요.')).toBeInTheDocument();
  expect(screen.getAllByRole('link', { name: '공식 전시 안내' })).toHaveLength(1);
  expect(screen.queryByText('휠체어 접근')).not.toBeInTheDocument();
  expect(screen.queryByText('무료')).not.toBeInTheDocument();
});

it('retains conflicts instead of masking them with reviewed visit notes', async () => {
  renderDetail({
    ...detailFixture,
    content: contentFixture,
    visit_information: {
      ...detailFixture.visit_information,
      price: { ...detailFixture.visit_information.price, state: 'CONFLICT' },
      accessibility: [
        {
          kind: 'WHEELCHAIR_ACCESS',
          state: 'CONFIRMED',
          value: 'CONFIRMED_POSITIVE',
          details: ['전시실에 경사로가 있습니다.'],
          evidence: [],
        },
      ],
    },
  });
  const visit = await screen.findByRole('region', { name: '관람 안내' });
  expect(within(visit).getByText('출처 간 정보 충돌 · 확인 필요')).toBeInTheDocument();
  expect(within(visit).queryByText('무료')).not.toBeInTheDocument();
  expect(within(visit).getByText(/전시실에 경사로가 있습니다/)).toBeInTheDocument();
});

it('does not link fictional content to an external official website', async () => {
  renderDetail({ ...detailFixture, content: contentFixture }, true);
  expect(await screen.findByText(contentFixture.introduction)).toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '공식 전시 안내' })).not.toBeInTheDocument();
});

it('rejects malformed content, duplicate notes and mismatched official provenance', () => {
  for (const content of [
    { ...contentFixture, introduction: '' },
    { ...contentFixture, official_url: 'javascript:alert(1)' },
    { ...contentFixture, official_url: 'https://other.example.test/' },
    {
      ...contentFixture,
      visit_notes: [contentFixture.visit_notes[0], contentFixture.visit_notes[0]],
    },
    { ...contentFixture, expires_at: contentFixture.reviewed_at },
  ]) {
    expect(() => parseExhibitionDetail({ ...detailFixture, content })).toThrow();
  }
});

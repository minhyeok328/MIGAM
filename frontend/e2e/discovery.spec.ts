import { test, expect, expectNoHorizontalOverflow, searchFor } from './fixtures';

test('home stays API-free and browsing opens the real search API', async ({ page }) => {
  const apiRequests: string[] = [];
  page.on('request', (request) => {
    if (new URL(request.url()).pathname.startsWith('/api/')) apiRequests.push(request.url());
  });
  await page.goto('/');
  await expect(page.getByRole('main')).toBeVisible();
  await expectNoHorizontalOverflow(page);
  expect(apiRequests).toEqual([]);
  await page.getByRole('link', { name: '전시 둘러보기', exact: true }).first().click();
  await expect(page).toHaveURL(/\/discover$/);
  await expect(page.getByRole('heading', { name: '전시 8개', exact: true })).toBeVisible();
  expect(apiRequests.some((url) => url.includes('/search/'))).toBe(true);
  await expectNoHorizontalOverflow(page);
});

test('search filters preserve unsubmitted text and empty results preserve the query', async ({
  page,
}) => {
  await page.goto('/discover');
  await expect(page.getByRole('heading', { name: '전시 8개', exact: true })).toBeVisible();
  await page.getByLabel('전시·기관 검색어').fill('고요');
  await page.getByRole('button', { name: '필터', exact: true }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toHaveAccessibleName('검색 필터');
  await dialog.getByRole('combobox', { name: '시·도', exact: true }).selectOption('서울');
  const response = page.waitForResponse(
    (result) => result.url().includes('/search/') && result.request().method() === 'GET',
  );
  await dialog.getByRole('button', { name: '필터 적용' }).click();
  const appliedURL = new URL((await response).url());
  expect(appliedURL.searchParams.get('q')).toBeNull();
  await expect(page.getByLabel('전시·기관 검색어')).toHaveValue('고요');
  await searchFor(page, '고요의 형태');
  await page.getByLabel('전시·기관 검색어').fill('존재하지않는전시회귀검사');
  await page.getByRole('button', { name: '검색하기', exact: true }).click();
  await expect(page.getByRole('heading', { name: '찾으시는 전시나 기관이 없어요.' })).toBeVisible();
  await expect(page.getByLabel('전시·기관 검색어')).toHaveValue('존재하지않는전시회귀검사');
});

test('period recommendations use exhibition overlap without hidden visit filters', async ({
  page,
}) => {
  await page.goto('/discover#recommend');
  await expect(page.getByText('6개의 추천', { exact: true })).toBeVisible();
  const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Seoul' }).format(new Date());
  await page.getByLabel('찾을 기간 시작일').fill(today);
  await page.getByLabel('찾을 기간 종료일').fill(today);
  await expect(page.getByLabel(/예산|예상 관람시간|예약 방식/)).toHaveCount(0);
  await page.getByRole('button', { name: '자세한 조건', exact: true }).click();
  await expect(page.getByRole('dialog', { name: '접근성·감각 조건' })).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('button', { name: '자세한 조건', exact: true })).toBeFocused();
  const response = page.waitForResponse(
    (result) => result.url().includes('/recommendations/') && result.request().method() === 'POST',
  );
  await page.getByRole('button', { name: '이 조건으로 추천받기' }).click();
  const result = await response;
  expect(result.ok()).toBe(true);
  expect(result.request().postDataJSON()).toEqual({
    limit: 6,
    exhibition_dates: { start: today, end: today },
  });
  const payload = await result.json();
  expect(payload.candidate_count).toBeGreaterThan(0);
  expect(payload.recommendations.length).toBeGreaterThan(0);
  expect(
    payload.recommendations.every(
      (item: { visit_availability: unknown }) => item.visit_availability == null,
    ),
  ).toBe(true);
  await expect(page.getByText(`전시 기간 ${today} — ${today}`, { exact: true })).toBeVisible();
  await expectNoHorizontalOverflow(page);
});

test('detail, saved state, comparison and reset stay connected across real page reloads', async ({
  page,
}) => {
  await page.goto('/discover');
  await searchFor(page, '고요의 형태');
  await page.getByRole('link', { name: '고요의 형태 상세 보기' }).click();
  await expect(page.getByRole('heading', { level: 1, name: '고요의 형태' })).toBeVisible();
  await page.getByRole('button', { name: '관심 저장', exact: true }).click();
  await page.reload();
  await expect(page.getByRole('button', { name: '관심 해제', exact: true })).toHaveAttribute(
    'aria-pressed',
    'true',
  );
  await expectNoHorizontalOverflow(page);
  await page.getByRole('button', { name: '비교 추가', exact: true }).click();
  await page.getByRole('link', { name: '관심 목록', exact: true }).click();
  await expect(page.getByRole('button', { name: '전시 1', exact: true })).toBeVisible();
  await page.getByRole('link', { name: '비교 1', exact: true }).click();
  await expect(page.getByRole('table')).toContainText('고요의 형태');
  await expect(page.getByRole('rowheader', { name: '운영일·시간', exact: true })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await page.getByRole('link', { name: '내 데이터', exact: true }).click();
  const reset = page.getByRole('button', { name: '모든 로컬 데이터 삭제', exact: true });
  await reset.click();
  await page.keyboard.press('Escape');
  await expect(reset).toBeFocused();
  await reset.click();
  await page.getByRole('dialog').getByRole('button', { name: '삭제하기', exact: true }).click();
  await expect(page.getByText('선택한 데이터를 초기화했어요.')).toBeVisible();
  await page.reload();
  await expect(page.getByRole('link', { name: '비교 0', exact: true })).toBeVisible();
  await page.getByRole('link', { name: '관심 목록', exact: true }).click();
  await expect(page.getByRole('heading', { name: '아직 저장된 항목이 없어요.' })).toBeVisible();
});

test('API failure can be retried without discarding the submitted search', async ({ page }) => {
  await page.goto('/discover');
  await expect(page.getByRole('heading', { name: '전시 8개', exact: true })).toBeVisible();
  const searchRoute = '**/api/internal/v1/search/**';
  await page.route(searchRoute, (route) =>
    route.fulfill({ status: 503, json: { detail: 'Isolated test outage' } }),
  );
  await page.getByLabel('전시·기관 검색어').fill('고요의 형태');
  await page.getByRole('button', { name: '검색하기', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('전시 정보를 불러오지 못했어요.');
  await expect(page.getByLabel('전시·기관 검색어')).toHaveValue('고요의 형태');
  await page.unroute(searchRoute);
  await page.getByRole('button', { name: '다시 시도' }).click();
  await expect(page.getByRole('heading', { name: '고요의 형태', exact: true })).toBeVisible();
});

test('fictional detail never links to invented official guidance', async ({ page }) => {
  await page.goto('/discover');
  await searchFor(page, '소리, 보이지 않는 풍경');
  await page.getByRole('link', { name: '소리, 보이지 않는 풍경 상세 보기' }).click();
  await expect(
    page.getByRole('heading', { level: 1, name: '소리, 보이지 않는 풍경' }),
  ).toBeVisible();
  await expect(page.getByRole('region', { name: '관람 안내' })).toBeVisible();
  await expect(
    page.getByRole('region', { name: '관람 안내' }).getByText('관람료', { exact: true }),
  ).toHaveCount(0);
  await expect(page.locator('a[href^="https://"]')).toHaveCount(0);
});

test('explicitly saved taste survives reload and reaches recommendations', async ({ page }) => {
  await page.goto('/taste');
  await page.getByRole('checkbox', { name: '회화', exact: true }).check();
  await page.getByRole('button', { name: '다음', exact: true }).click();
  await page.getByRole('button', { name: '건너뛰기', exact: true }).click();
  await page.getByRole('button', { name: '취향 저장', exact: true }).click();
  await expect(page.getByRole('heading', { level: 1, name: '지금 끌리는 취향' })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  const request = page.waitForRequest(
    (entry) => entry.url().includes('/recommendations/') && entry.method() === 'POST',
  );
  await page.getByRole('link', { name: '취향과 가까운 전시 보기', exact: true }).click();
  expect((await request).postDataJSON()).toEqual({
    limit: 6,
    preferred_features: [{ axis: 'MEDIA_GROUP', value: 'PAINTING' }],
  });
  await expect(page.getByText('저장한 취향 반영', { exact: true })).toBeVisible();
  await page.getByRole('link', { name: '취향', exact: true }).click();
  await page.reload();
  await expect(page.getByRole('checkbox', { name: '회화', exact: true })).toBeChecked();
});

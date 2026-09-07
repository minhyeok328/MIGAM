import { test, expect, expectNoHorizontalOverflow } from './fixtures';
import { contentFixture, detailFixture } from '../src/test/fixtures';

// The real UI contract is checked with a declared fictional response. No museum
// website, user database, or network freshness affects this regression test.
const officialURL = 'https://official.example.test/exhibitions/1';
const title = '공식 안내 연결 테스트 전시 · 가상 응답';
const detail = {
  ...detailFixture,
  exhibition: { ...detailFixture.exhibition, title, official_url: officialURL },
};

test.beforeEach(async ({ context }) => {
  await context.route('http://127.0.0.1:5183/api/**', async (route) => {
    if (new URL(route.request().url()).pathname === '/api/internal/v1/exhibitions/1/') {
      await route.fulfill({ json: detail });
    } else {
      throw new Error('Unexpected API call in the isolated official-guidance fixture');
    }
  });
});

test('unknown detail opens the official link in a separate tab with no referrer', async ({
  context,
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/exhibitions/1');
  await expect(page.getByRole('heading', { level: 1, name: title })).toBeVisible();
  await expect(page.getByText('확인된 첫 관람일', { exact: true })).toHaveCount(0);
  const link = page.getByRole('link', { name: '공식 전시 안내', exact: true });
  await expect(link).toHaveCount(1);
  await expect(link).toHaveAttribute('href', officialURL);
  await expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  await expectNoHorizontalOverflow(page);
  let referrer: string | undefined;
  await context.route(officialURL, async (route) => {
    referrer = route.request().headers()['referer'];
    await route.fulfill({ contentType: 'text/html', body: '<h1>Isolated official guidance</h1>' });
  });
  const popupPromise = page.waitForEvent('popup');
  await link.click();
  const popup = await popupPromise;
  await expect(popup.getByRole('heading', { name: 'Isolated official guidance' })).toBeVisible();
  expect(referrer).toBeUndefined();
  await expect(page).toHaveURL(/\/exhibitions\/1$/);
  await popup.close();
});

test('reviewed content explains the exhibition and visit without repeated unknown rows', async ({
  page,
}) => {
  await page.route('http://127.0.0.1:5183/api/internal/v1/exhibitions/1/', (route) =>
    route.fulfill({
      json: { ...detail, content: { ...contentFixture, official_url: officialURL } },
    }),
  );
  await page.goto('/exhibitions/1');
  await expect(page.getByText(contentFixture.introduction)).toBeVisible();
  await expect(page.getByRole('region', { name: '관람 안내' })).toContainText('무료');
  await expect(page.getByText(contentFixture.visit_notes[1].text)).toBeVisible();
  await expect(page.getByRole('link', { name: '공식 전시 안내', exact: true })).toHaveCount(1);
  await expect(page.getByText('공식 안내에서 확인', { exact: true })).toHaveCount(0);
  await expect(page.getByRole('link', { name: `${title} 상세 보기` })).toHaveCount(0);
  await expect(page.getByText('휠체어 접근', { exact: true })).toHaveCount(0);
  await expectNoHorizontalOverflow(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByText(contentFixture.introduction)).toBeVisible();
  await expectNoHorizontalOverflow(page);
});

test('comparison keeps unknown values linked without inventing a first viewing date', async ({
  page,
}) => {
  await page.goto('/exhibitions/1');
  await page.getByRole('button', { name: '비교 추가', exact: true }).click();
  await page.getByRole('link', { name: '비교 1', exact: true }).click();
  await expect(page.getByRole('table')).toContainText(title);
  await expect(page.getByRole('rowheader', { name: '확인된 첫 관람일', exact: true })).toHaveCount(
    0,
  );
  const price = page
    .getByRole('row')
    .filter({ has: page.getByRole('rowheader', { name: '관람료', exact: true }) });
  await expect(
    price.getByRole('link', { name: '공식 안내에서 확인', exact: true }),
  ).toHaveAttribute('href', officialURL);
  await expect(price).not.toContainText('무료');
  await page.setViewportSize({ width: 390, height: 844 });
  await expectNoHorizontalOverflow(page);
});

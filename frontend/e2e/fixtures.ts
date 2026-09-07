import { test as base, expect, type Page } from '@playwright/test';

export const test = base.extend<{ browserGuard: void }>({
  browserGuard: [
    async ({ context, page, baseURL }, use) => {
      const unexpected: string[] = [];
      const errors: string[] = [];
      page.on('pageerror', (error) => errors.push(error.message));
      await context.route('**/*', async (route) => {
        const url = new URL(route.request().url());
        if (url.origin === new URL(baseURL!).origin) await route.continue();
        else {
          unexpected.push(url.origin);
          await route.abort();
        }
      });
      await use();
      expect(unexpected, 'The isolated browser must not contact external services').toEqual([]);
      expect(errors, 'The user flow must not produce uncaught JavaScript errors').toEqual([]);
    },
    { auto: true },
  ],
});

export { expect };

export async function expectNoHorizontalOverflow(page: Page) {
  await expect
    .poll(() =>
      page.evaluate(
        () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
      ),
    )
    .toBe(true);
}

export async function searchFor(page: Page, title: string) {
  await page.getByLabel('전시·기관 검색어').fill(title);
  await page.getByRole('button', { name: '검색하기', exact: true }).click();
  await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
}

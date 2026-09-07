import { defineConfig, devices } from '@playwright/test';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const frontend = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(frontend, '..');
const python = path.join(
  root,
  'backend',
  '.venv',
  process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python',
);
const environment = Object.fromEntries(
  Object.keys(process.env)
    .filter((name) => name.startsWith('VITE_'))
    .map((name) => [name, '']),
);

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 8_000 },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  outputDir: '../output/playwright/results',
  reporter: [['list'], ['html', { outputFolder: '../output/playwright/report', open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:5182',
    locale: 'ko-KR',
    timezoneId: 'Asia/Seoul',
    reducedMotion: 'reduce',
    serviceWorkers: 'block',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      testIgnore: '**/official-guidance.spec.ts',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
    },
    {
      name: 'mobile-chromium',
      testIgnore: '**/official-guidance.spec.ts',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 390, height: 844 },
        isMobile: true,
        hasTouch: true,
      },
    },
    {
      name: 'firefox',
      testIgnore: '**/official-guidance.spec.ts',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      testIgnore: '**/official-guidance.spec.ts',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'official-guidance',
      testMatch: '**/official-guidance.spec.ts',
      use: { ...devices['Desktop Chrome'], baseURL: 'http://127.0.0.1:5183' },
    },
  ],
  webServer: [
    {
      command: `"${python}" -X utf8 scripts/run_local_demo.py --port 5182`,
      cwd: root,
      url: 'http://127.0.0.1:5182/healthz',
      reuseExistingServer: false,
      timeout: 120_000,
      gracefulShutdown: { signal: 'SIGTERM', timeout: 5_000 },
    },
    {
      command:
        'node node_modules/vite/bin/vite.js --mode local-data --host 127.0.0.1 --port 5183 --strictPort',
      cwd: frontend,
      env: environment,
      url: 'http://127.0.0.1:5183',
      reuseExistingServer: false,
      timeout: 30_000,
      gracefulShutdown: { signal: 'SIGTERM', timeout: 5_000 },
    },
  ],
});

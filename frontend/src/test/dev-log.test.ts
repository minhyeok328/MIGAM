import { expect, it } from 'vitest';
import { sanitizeDevMessage } from '../../scripts/safe-log';

it('removes query data from proxy failure logs but retains useful static context', () => {
  expect(
    sanitizeDevMessage(
      'http proxy error: /api/internal/v1/search/?q=private-search&region_area=private-area\nECONNREFUSED',
    ),
  ).toBe('http proxy error: /api/internal/v1/search/?[redacted]\nECONNREFUSED');
  expect(sanitizeDevMessage('vite failed to compile src/app/App.tsx')).toBe(
    'vite failed to compile src/app/App.tsx',
  );
});

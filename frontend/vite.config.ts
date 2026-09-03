import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { createLogger } from 'vite';
import { sanitizeDevMessage } from './scripts/safe-log.ts';

const logger = createLogger();
for (const method of ['info', 'warn', 'warnOnce', 'error'] as const) {
  const original = logger[method].bind(logger);
  logger[method] = (message, options) => original(sanitizeDevMessage(message), options);
}

export default defineConfig(({ mode }) => ({
  customLogger: logger,
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: mode === 'demo' ? 'http://127.0.0.1:8001' : 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  test: { environment: 'jsdom', setupFiles: ['./src/test/setup.ts'], restoreMocks: true },
}));

import react from '@vitejs/plugin-react';
import path from 'path';
import {defineConfig} from 'vitest/config';

// Vitest configuration for the S-760 React UI (component/unit tests).
// Uses jsdom so React Testing Library can mount components, and the same `@`
// path alias as vite.config.ts so test imports resolve identically to the app.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, '.'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    css: false,
    // Playwright specs live under e2e/ and are run by `test:e2e`, not Vitest.
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules', 'dist', 'e2e/**'],
  },
});

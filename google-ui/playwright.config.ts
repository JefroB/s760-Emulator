import {defineConfig, devices} from '@playwright/test';

// Playwright E2E / visual-snapshot config for the composed S-760 React shell.
// `webServer` builds and serves the app via Vite preview so the composed shell
// (bezel + CRT/LCD/OLED canvases) is tested against production-equivalent output.
// Tests live under e2e/ to keep them separate from Vitest's src/**/*.test.tsx.
const PORT = Number(process.env.E2E_PORT ?? 4173);
const BASE_URL = `http://localhost:${PORT}`;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: {...devices['Desktop Chrome']},
    },
  ],
  webServer: {
    command: `npm run build && npm run preview -- --port=${PORT} --strictPort`,
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});

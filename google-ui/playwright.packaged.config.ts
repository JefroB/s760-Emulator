import {defineConfig,devices} from '@playwright/test';

// Package tests launch their own frozen service and use its URL/assets.
export default defineConfig({
  testDir:'./e2e',testMatch:['packaged-editing.spec.ts','packaged-setup.spec.ts','packaged-media.spec.ts','packaged-sampling.spec.ts','packaged-workflow.spec.ts'],workers:1,retries:0,
  reporter:'list',use:{...devices['Desktop Chrome'],trace:'retain-on-failure'},
});

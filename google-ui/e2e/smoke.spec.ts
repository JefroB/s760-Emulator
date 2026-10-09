import {expect, test} from '@playwright/test';

// Minimal E2E smoke test proving Playwright + the preview webServer wire up.
// Full composed-shell / visual-snapshot coverage lives in composed-shell.spec.ts
// (task 4.2); this stays as a fast, dependency-free liveness check.
test('app shell mounts', async ({page}) => {
  await page.goto('/');
  await expect(page.locator('#root')).toBeAttached();
});

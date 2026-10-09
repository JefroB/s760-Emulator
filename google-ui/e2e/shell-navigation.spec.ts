/**
 * shell-navigation.spec.ts
 *
 * Playwright E2E migration of the shell/navigation assertions REMOVED from the
 * MAME screenshot-scraping suite in ui-consolidation task 1.5 (R4.1/R4.2),
 * re-expressed against the REAL composed React shell (true ownership — R4.2,
 * R7.2). Component-level coverage lives in
 * src/components/ShellNavigationMigration.test.tsx (Vitest); this file covers
 * the COMPOSED shell — the chassis, Gotek bay, mode tabs and SYSTEM selection
 * all live together and navigation flows across the CRT area and the rack panel
 * in one app, which is exactly what the old
 * `test_seamless_mouse_navigation_between_crt_and_rack_ui` approximated by
 * scraping two MAME pixel regions.
 *
 * Uses the same fake bridge harness as composed-shell.spec.ts so the production
 * client/compositing path runs for real.
 */

import {expect, test} from '@playwright/test';
import {installFakeBridge} from './fakeBridge';

test.beforeEach(async ({page}) => {
  await installFakeBridge(page);
  await page.goto('/');
  await expect(page.locator('#root')).toBeAttached();
});

// Replaces test_rack_panel_and_embedded_lcd_rendering (chassis/Gotek chrome):
// the 1U chassis + Gotek bay are composed into the one React shell.
test('composed shell mounts the chassis chrome and the Gotek drive bay', async ({
  page,
}) => {
  // Two rack ears == a mounted 1U chassis (RackEar carries the "1U" marker).
  await expect(page.getByText('1U')).toHaveCount(2);
  // Hardware silkscreen model block identifies the real chassis.
  await expect(page.getByText('DIGITAL SAMPLER')).toBeVisible();
  // The Gotek drive bay badge is unique to the React GotekBay chrome.
  await expect(page.getByText('Gotek SFR1M44-U100K')).toBeVisible();
});

// Replaces test_gotek_oled_and_navigation_controls: the Gotek OLED readout +
// Prev/Next/Select controls are React-owned chrome in the composed shell.
test('Gotek OLED readout + Prev/Next/Select controls are present and clickable', async ({
  page,
}) => {
  await expect(page.getByTitle('Previous Image / Directory [<]')).toBeVisible();
  await expect(page.getByTitle('Next Image / Directory [>]')).toBeVisible();
  const sel = page.getByTitle('Mount / Select Disk [SEL]');
  await expect(sel).toBeVisible();
  // Clicking SEL drives the real mount flow (no throw, shell stays mounted).
  await sel.click();
  await expect(page.locator('#root')).toBeAttached();
});

// Replaces test_manual_sampling_and_mode_workflow (SYSTEM-tab outline) AND
// test_seamless_mouse_navigation_between_crt_and_rack_ui (SYSTEM-outline +
// Gotek navigation across CRT<->rack): drive the whole flow in the real shell.
test('seamless navigation: select SYSTEM mode tab, then step + mount on the Gotek bay', async ({
  page,
}) => {
  // Phase 1 (CRT-area control): click the SYSTEM mode tab on the front panel.
  const systemTab = page.getByTitle('Mode Button [SYSTEM]');
  await expect(systemTab).toBeVisible();
  await systemTab.click();
  // The active tab carries the amber selection outline (React equivalent of the
  // old Pen-5 red SYSTEM-tab outline). Assert the class reflects active state.
  await expect(systemTab).toHaveClass(/border-amber-500\/70/);

  // Phase 2 (rack-area control): step the Gotek to the next image, then mount.
  await page.getByTitle('Next Image / Directory [>]').click();
  await page.getByTitle('Mount / Select Disk [SEL]').click();

  // The whole cross-region flow ran in one shell without a reload/crash — the
  // "seamless CRT<->rack navigation" invariant, now against the real owner.
  await expect(page.locator('#root')).toBeAttached();
  await expect(systemTab).toHaveClass(/border-amber-500\/70/);
});

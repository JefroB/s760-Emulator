/**
 * composed-shell.spec.ts
 *
 * Playwright E2E / visual-snapshot tests of the COMPOSED S-760 React shell with
 * MOCKED bridge frames (spec task 4.2, Requirement R7.2).
 *
 * Strategy (robust against a built/preview app): a fake `window.WebSocket` is
 * installed via `page.addInitScript` BEFORE the app loads (see fakeBridge.ts).
 * On "open" it pushes a solid-color CRT RGBA frame, an LCD MONO1 frame, an OLED
 * MONO1 frame, and a telemetry JSON — so the production
 * `S760BridgeClient` -> `useSurfaceCanvas` -> `ctx.putImageData()` path runs for
 * real and the shell composites genuine buffers into its chrome.
 *
 * We assert:
 *  - the bezel/chassis chrome mounts (header + CRT/LCD/OLED housings),
 *  - the three live display `<canvas>` elements are present with the expected
 *    intrinsic dimensions (640x480 / 160x64 / 128x32),
 *  - the client actually connected and frames/telemetry flowed (via the fake
 *    socket diagnostics on `window.__fakeBridge`),
 *  - the composited CRT buffer actually contains the pushed solid color
 *    (pixel read-back from the live canvas — proof the buffer reached pixels),
 *  - a deterministic full-shell visual snapshot (animations disabled).
 *
 * Baselines are generated on first run with `--update-snapshots`.
 */

import {expect, test} from '@playwright/test';
import {CRT_FILL, GEOM, installFakeBridge} from './fakeBridge';

// A connected, composited shell with deterministic frames is the fixture for
// every test here.
test.beforeEach(async ({page}) => {
  await installFakeBridge(page);
  await page.goto('/');
  // Shell root is mounted once React renders.
  await expect(page.locator('#root')).toBeAttached();
});

test('composed shell chrome mounts (bezel + chassis)', async ({page}) => {
  // The top header chrome identifies the composed shell.
  await expect(page.getByText('S-760 Studio Suite')).toBeVisible();
  await expect(page.getByText('FlashFloppy Gotek OLED Mod')).toBeVisible();
  // The composed shell renders the three display surfaces as canvases: the CRT
  // (offline + live), the LCD (offline + live) and the Gotek OLED (live only —
  // its readout is DOM, the live bridge blit is a canvas). That is 5 canvases;
  // require at least the three live surfaces + the two offline simulations.
  const canvases = page.locator('canvas');
  expect(await canvases.count()).toBeGreaterThanOrEqual(5);
});

test('live CRT/LCD/OLED canvases exist with authentic intrinsic dimensions', async ({
  page,
}) => {
  // The live surface canvases carry the authoritative hardware geometries.
  // Each surface renders two canvases (offline simulation + live bridge blit);
  // there must be at least one canvas per surface at each native size.
  const dims = await page.evaluate(() => {
    const out: Array<{w: number; h: number}> = [];
    document.querySelectorAll('canvas').forEach((c) => {
      out.push({w: (c as HTMLCanvasElement).width, h: (c as HTMLCanvasElement).height});
    });
    return out;
  });

  const has = (w: number, h: number) => dims.some((d) => d.w === w && d.h === h);

  expect(has(GEOM.crt.w, GEOM.crt.h)).toBe(true); // 640x480 CRT (RFSC16A VDP)
  expect(has(GEOM.lcd.w, GEOM.lcd.h)).toBe(true); // 160x64 SED1335 LCD
  expect(has(GEOM.oled.w, GEOM.oled.h)).toBe(true); // 128x32 Gotek OLED
});

test('bridge client connects and the mocked frames + telemetry flow', async ({
  page,
}) => {
  // Wait until the fake socket has opened and pushed all three surfaces.
  await expect
    .poll(async () =>
      page.evaluate(() => {
        const d = window.__fakeBridge;
        if (!d) return null;
        return {
          opened: d.opened,
          telemetrySent: d.telemetrySent,
          crt: d.framesSent[0] ?? 0,
          lcd: d.framesSent[1] ?? 0,
          oled: d.framesSent[2] ?? 0,
          triedDefaultPort: d.urls.some((u) => u.includes('8760')),
        };
      }),
    )
    .toEqual({
      opened: true,
      telemetrySent: true,
      crt: 1,
      lcd: 1,
      oled: 1,
      triedDefaultPort: true,
    });
});

test('shell composites the real CRT buffer (pixel read-back = pushed color)', async ({
  page,
}) => {
  // Give the frame pump + putImageData a tick to land on the live CRT canvas.
  // The live CRT canvas is the 640x480 one with pointer-events disabled; read a
  // center pixel straight out of its 2D context and compare to the color the
  // fake bridge pushed. This proves the buffer traversed decode -> blit -> pixels.
  const pixel = await expect
    .poll(
      async () =>
        page.evaluate(() => {
          const crt = Array.from(document.querySelectorAll('canvas')).find(
            (c) => (c as HTMLCanvasElement).width === 640 && (c as HTMLCanvasElement).height === 480,
          ) as HTMLCanvasElement | undefined;
          if (!crt) return null;
          const ctx = crt.getContext('2d');
          if (!ctx) return null;
          const {data} = ctx.getImageData(320, 240, 1, 1);
          return {r: data[0], g: data[1], b: data[2], a: data[3]};
        }),
      {timeout: 10_000},
    )
    .toEqual({r: CRT_FILL.r, g: CRT_FILL.g, b: CRT_FILL.b, a: CRT_FILL.a});

  // (the poll above already asserts equality; `pixel` kept for clarity)
  void pixel;
});

test('composed shell visual snapshot (deterministic, animations disabled)', async ({
  page,
}) => {
  // Wait for all three composited surfaces so the snapshot is stable.
  await expect
    .poll(async () =>
      page.evaluate(() => {
        const d = window.__fakeBridge;
        return d ? (d.framesSent[0] ?? 0) + (d.framesSent[1] ?? 0) + (d.framesSent[2] ?? 0) : 0;
      }),
    )
    .toBe(3);

  // Kill CSS animations/transitions + the blinking caret so the snapshot is
  // deterministic across runs (the shell has pulsing LEDs / glows).
  await page.addStyleTag({
    content: `*, *::before, *::after {
      animation: none !important;
      transition: none !important;
      caret-color: transparent !important;
    }`,
  });

  // Let one more frame settle after disabling animations.
  await page.waitForTimeout(150);

  await expect(page).toHaveScreenshot('composed-shell.png', {
    fullPage: true,
    // Small tolerance absorbs sub-pixel font AA differences between machines.
    maxDiffPixelRatio: 0.02,
    animations: 'disabled',
  });
});

/**
 * fakeBridge.ts
 *
 * Playwright test harness that MOCKS the S-760 bridge transport so the composed
 * React shell can be exercised end-to-end WITHOUT a running C++ `S760Bridge`.
 *
 * The real `S760BridgeClient` (google-ui/src/bridge/S760BridgeClient.ts) connects
 * via `new WebSocket(ws://localhost:8760)` and decodes:
 *   - JSON telemetry  (S760ServerTelemetry)
 *   - binary display frames framed as
 *       [u8 surfaceId][u16 width LE][u16 height LE][u8 format][payload]
 *     surfaceId 0=CRT, 1=LCD, 2=OLED;  format 0=RGBA8888, 1=MONO1.
 *
 * Rather than stand up a server, we install a FAKE `window.WebSocket` via
 * `page.addInitScript` BEFORE the app module loads. On construction the fake
 * socket immediately "opens" and then pushes a deterministic set of frames +
 * telemetry, so the shell composites real buffers through its production
 * decode/blit path (useSurfaceCanvas -> ctx.putImageData).
 *
 * Everything the socket observes is recorded on `window.__fakeBridge` so the
 * spec can assert the client actually connected and that frames flowed.
 */

import type {Page} from '@playwright/test';

/** Deterministic solid CRT fill color (R,G,B,A) pushed as the CRT frame. */
export const CRT_FILL = {r: 0, g: 180, b: 220, a: 255} as const;

/** Surface geometries — must match the hpp / S760BridgeClient constants. */
export const GEOM = {
  crt: {w: 640, h: 480},
  lcd: {w: 160, h: 64},
  oled: {w: 128, h: 32},
} as const;

/** Shape of the diagnostics object the fake socket exposes on `window`. */
export interface FakeBridgeDiagnostics {
  /** URLs the app tried to open (proves the client attempted to connect). */
  urls: string[];
  /** Whether a fake socket reached the OPEN state. */
  opened: boolean;
  /** Count of binary frames pushed to the client, per surfaceId. */
  framesSent: Record<number, number>;
  /** Whether telemetry JSON was pushed. */
  telemetrySent: boolean;
  /** Raw JSON strings the client SENT back to the "server" (control msgs). */
  received: string[];
}

declare global {
  interface Window {
    __fakeBridge?: FakeBridgeDiagnostics;
  }
}

/**
 * Install the fake WebSocket + frame pump into the page context. Call this on a
 * `page` (or `context`) BEFORE `page.goto()` so the init script runs ahead of
 * the app's module graph and the real client picks up our fake constructor.
 *
 * The script is fully self-contained (serialized into the browser) and encodes
 * the frames with the exact production framing so the real decoder accepts them.
 */
export async function installFakeBridge(page: Page): Promise<void> {
  await page.addInitScript(
    ({crtFill, geom}) => {
      const diag = {
        urls: [] as string[],
        opened: false,
        framesSent: {} as Record<number, number>,
        telemetrySent: false,
        received: [] as string[],
      };
      window.__fakeBridge = diag;

      // --- frame encoders (mirror the wire protocol) ------------------------
      const FRAME_HEADER_SIZE = 6;
      const FMT_RGBA8888 = 0;
      const FMT_MONO1 = 1;

      function header(
        surfaceId: number,
        width: number,
        height: number,
        format: number,
        payloadLen: number,
      ): ArrayBuffer {
        const buf = new ArrayBuffer(FRAME_HEADER_SIZE + payloadLen);
        const view = new DataView(buf);
        view.setUint8(0, surfaceId);
        view.setUint16(1, width, true); // little-endian
        view.setUint16(3, height, true);
        view.setUint8(5, format);
        return buf;
      }

      function makeRgbaFrame(
        surfaceId: number,
        width: number,
        height: number,
        rgba: {r: number; g: number; b: number; a: number},
      ): ArrayBuffer {
        const payloadLen = width * height * 4;
        const buf = header(surfaceId, width, height, FMT_RGBA8888, payloadLen);
        const bytes = new Uint8Array(buf, FRAME_HEADER_SIZE);
        for (let i = 0; i < payloadLen; i += 4) {
          bytes[i] = rgba.r;
          bytes[i + 1] = rgba.g;
          bytes[i + 2] = rgba.b;
          bytes[i + 3] = rgba.a;
        }
        return buf;
      }

      function makeMono1Frame(
        surfaceId: number,
        width: number,
        height: number,
        litFn: (x: number, y: number) => boolean,
      ): ArrayBuffer {
        const stride = (width + 7) >> 3; // ceil(width/8), row-byte-aligned
        const payloadLen = stride * height;
        const buf = header(surfaceId, width, height, FMT_MONO1, payloadLen);
        const bytes = new Uint8Array(buf, FRAME_HEADER_SIZE);
        for (let y = 0; y < height; y++) {
          for (let x = 0; x < width; x++) {
            if (litFn(x, y)) {
              // MSB is the leftmost pixel in the byte.
              bytes[y * stride + (x >> 3)] |= 0x80 >> (x & 7);
            }
          }
        }
        return buf;
      }

      // --- fake WebSocket ----------------------------------------------------
      // Minimal stand-in that drives the real client's onopen/onmessage path.
      const RealWS = window.WebSocket;
      class FakeWebSocket {
        static readonly CONNECTING = 0;
        static readonly OPEN = 1;
        static readonly CLOSING = 2;
        static readonly CLOSED = 3;
        readonly CONNECTING = 0;
        readonly OPEN = 1;
        readonly CLOSING = 2;
        readonly CLOSED = 3;

        url: string;
        readyState = 0;
        binaryType: BinaryType = 'blob';
        onopen: ((ev: Event) => void) | null = null;
        onclose: ((ev: CloseEvent) => void) | null = null;
        onerror: ((ev: Event) => void) | null = null;
        onmessage: ((ev: MessageEvent) => void) | null = null;

        constructor(url: string) {
          this.url = url;
          diag.urls.push(url);
          // Open on the next microtask/tick, then pump the deterministic frames.
          setTimeout(() => this.openAndPump(), 0);
        }

        private emitMessage(data: string | ArrayBuffer): void {
          if (this.onmessage) {
            this.onmessage(new MessageEvent('message', {data}));
          }
        }

        private openAndPump(): void {
          this.readyState = 1;
          diag.opened = true;
          if (this.onopen) this.onopen(new Event('open'));

          // Telemetry first (JSON) so the connection indicator can reflect it.
          const telemetry = {
            timestamp: 1_000,
            fps: 60,
            crtWidth: geom.crt.w,
            crtHeight: geom.crt.h,
            lcdWidth: geom.lcd.w,
            lcdHeight: geom.lcd.h,
            gotekWidth: geom.oled.w,
            gotekHeight: geom.oled.h,
            peakL: 0.5,
            peakR: 0.5,
            activeVoices: 3,
            currentMode: 'DISK',
          };
          this.emitMessage(JSON.stringify(telemetry));
          diag.telemetrySent = true;

          // CRT: solid-color RGBA frame (deterministic for snapshots).
          this.emitMessage(
            makeRgbaFrame(0, geom.crt.w, geom.crt.h, crtFill),
          );
          diag.framesSent[0] = (diag.framesSent[0] ?? 0) + 1;

          // LCD: MONO1 160x64 — a simple deterministic checker/border pattern.
          this.emitMessage(
            makeMono1Frame(1, geom.lcd.w, geom.lcd.h, (x, y) => {
              const border = x === 0 || y === 0 || x === geom.lcd.w - 1 || y === geom.lcd.h - 1;
              return border || ((x >> 3) + (y >> 3)) % 2 === 0;
            }),
          );
          diag.framesSent[1] = (diag.framesSent[1] ?? 0) + 1;

          // OLED: MONO1 128x32 — top-half lit, bottom-half dark (deterministic).
          this.emitMessage(
            makeMono1Frame(2, geom.oled.w, geom.oled.h, (_x, y) => y < geom.oled.h / 2),
          );
          diag.framesSent[2] = (diag.framesSent[2] ?? 0) + 1;
        }

        send(data: string): void {
          // Record control messages the client sends back (input forwarding).
          if (typeof data === 'string') diag.received.push(data);
        }

        close(): void {
          this.readyState = 3;
          if (this.onclose) {
            this.onclose(new CloseEvent('close'));
          }
        }

        addEventListener(): void {
          /* the client only uses the on* handler properties */
        }
        removeEventListener(): void {
          /* no-op */
        }
      }

      // Keep the real constructor reachable for anything that needs it, but make
      // the app's `new WebSocket(...)` resolve to our fake.
      (FakeWebSocket as unknown as {Real: typeof WebSocket}).Real = RealWS;
      window.WebSocket = FakeWebSocket as unknown as typeof WebSocket;
    },
    {crtFill: CRT_FILL, geom: GEOM},
  );
}

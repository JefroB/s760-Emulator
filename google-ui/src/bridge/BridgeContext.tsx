/**
 * BridgeContext.tsx
 *
 * React wiring for the S-760 bridge (spec task 3.4). Provides a single shared
 * `S760BridgeClient` instance to the component tree and exposes:
 *
 *  - `useBridgeClient()`  — the shared client (for sending input / subscribing
 *    to frames imperatively).
 *  - `useBridgeStatus()`  — low-rate connection status for React state (the
 *    connection indicator). This is the ONLY per-frame-adjacent value allowed
 *    in React state; display pixels NEVER flow through state (see the design
 *    "Compositing rule — performance-critical").
 *  - `useBridgeTelemetry()` — low-rate telemetry (fps/peaks/mode) for status
 *    chrome, again never per-pixel data.
 *  - `useSurfaceCanvas()` — the performance-critical hook each display surface
 *    uses: it owns one preallocated `ImageData` per surface and blits incoming
 *    frames straight to a `<canvas>` ref via `ctx.putImageData()` inside the
 *    bridge frame callback, with NO `setState` per frame.
 *
 * Requirements: R6.1, R6.2, R6.3, R6.4
 */

import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  S760BridgeClient,
  S760BridgeClientOptions,
  ConnectionStatus,
  S760ServerTelemetry,
  SurfaceId,
  PixelFormat,
  S760Frame,
} from './S760BridgeClient';

// -----------------------------------------------------------------------------
//  Context
// -----------------------------------------------------------------------------

const BridgeClientContext = createContext<S760BridgeClient | null>(null);

export interface BridgeProviderProps {
  /** Options forwarded to the created client. */
  options?: S760BridgeClientOptions;
  /** Provide an already-constructed client (tests / custom transports). */
  client?: S760BridgeClient;
  /** Connect on mount (default true). */
  autoConnect?: boolean;
  children: React.ReactNode;
}

/**
 * Provides one shared `S760BridgeClient` to the subtree. Creates the client
 * once, subscribes to `window` `s760_input` events (so existing App.tsx emit
 * logic needs no change), connects on mount, and disposes on unmount.
 */
export const BridgeProvider: React.FC<BridgeProviderProps> = ({
  options,
  client,
  autoConnect = true,
  children,
}) => {
  // Construct exactly once; the client lives for the provider's lifetime.
  const clientRef = useRef<S760BridgeClient | null>(client ?? null);
  if (clientRef.current === null) {
    clientRef.current = new S760BridgeClient({ autoSubscribeInput: true, ...options });
  }

  useEffect(() => {
    const c = clientRef.current;
    if (!c) return;
    c.subscribeToWindowInput();
    if (autoConnect) c.connect();
    return () => {
      // Only dispose a client we own; a caller-provided client is their concern.
      if (!client) c.dispose();
      else c.disconnect();
    };
  }, [autoConnect, client]);

  return (
    <BridgeClientContext.Provider value={clientRef.current}>
      {children}
    </BridgeClientContext.Provider>
  );
};

/** The shared bridge client, or null if no provider is mounted. */
export function useBridgeClient(): S760BridgeClient | null {
  return useContext(BridgeClientContext);
}

// -----------------------------------------------------------------------------
//  Low-rate React state hooks (status + telemetry only — NEVER pixels)
// -----------------------------------------------------------------------------

/**
 * Subscribe to the bridge connection status. Safe to drive React state because
 * it changes at human rate (connect/disconnect), not per frame.
 */
export function useBridgeStatus(): ConnectionStatus {
  const client = useBridgeClient();
  const [status, setStatus] = useState<ConnectionStatus>(
    client ? client.getStatus() : 'disconnected',
  );
  useEffect(() => {
    if (!client) return;
    return client.onStatus(setStatus);
  }, [client]);
  return status;
}

/**
 * Subscribe to low-rate telemetry (fps, peaks, mode). This is metadata, not
 * per-pixel data, so routing it through React state is fine.
 */
export function useBridgeTelemetry(): S760ServerTelemetry | null {
  const client = useBridgeClient();
  const [telemetry, setTelemetry] = useState<S760ServerTelemetry | null>(null);
  useEffect(() => {
    if (!client) return;
    return client.onTelemetry(setTelemetry);
  }, [client]);
  return telemetry;
}

// -----------------------------------------------------------------------------
//  Performance-critical surface compositing hook
// -----------------------------------------------------------------------------

/** Tint color (RGB 0..255) applied to lit MONO1 pixels (LCD/OLED). */
export interface MonoTint {
  /** Lit-pixel color. */
  fg: [number, number, number];
  /** Unlit-pixel (background) color. */
  bg: [number, number, number];
}

export interface SurfaceCanvasOptions {
  /** For MONO1 surfaces (LCD/OLED), the lit/unlit tint. Ignored for CRT. */
  tint?: MonoTint;
}

/**
 * Imperatively blit the live frames for one surface onto a `<canvas>`.
 *
 * This is the hot path described by the design "Compositing rule": the returned
 * ref must be attached to a `<canvas>` whose intrinsic width/height match the
 * surface geometry. For each incoming frame we mutate a single preallocated
 * `ImageData.data` in place and call `ctx.putImageData()` — there is NO React
 * state update per frame, so React reconciliation never runs on the 60fps path.
 *
 * - CRT (RGBA8888): the payload is copied straight into `ImageData.data`.
 * - LCD/OLED (MONO1): each packed bit is unpacked to a pixel; lit → tint.fg,
 *   unlit → tint.bg. MSB is the leftmost pixel; rows are byte-aligned
 *   (stride = ceil(width/8)).
 *
 * @param surfaceId which surface's frames to render.
 * @param options   tint for MONO1 surfaces.
 * @returns a canvas ref to attach to the surface `<canvas>`.
 */
export function useSurfaceCanvas(
  surfaceId: SurfaceId,
  options: SurfaceCanvasOptions = {},
): React.RefObject<HTMLCanvasElement | null> {
  const client = useBridgeClient();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Keep the latest tint without re-subscribing the frame callback each render.
  const tintRef = useRef<MonoTint | undefined>(options.tint);
  tintRef.current = options.tint;

  useEffect(() => {
    if (!client) return;

    // One preallocated ImageData per surface instance (allocated lazily on the
    // first frame once we know the dimensions), reused + mutated in place.
    let imageData: ImageData | null = null;
    let ctx: CanvasRenderingContext2D | null = null;

    const onFrame = (frame: S760Frame): void => {
      const canvas = canvasRef.current;
      if (!canvas) return;

      // (Re)size the canvas + ImageData only when geometry changes.
      if (canvas.width !== frame.width) canvas.width = frame.width;
      if (canvas.height !== frame.height) canvas.height = frame.height;
      if (!ctx) ctx = canvas.getContext('2d');
      if (!ctx) return;
      if (
        !imageData ||
        imageData.width !== frame.width ||
        imageData.height !== frame.height
      ) {
        imageData = ctx.createImageData(frame.width, frame.height);
      }

      if (frame.format === PixelFormat.RGBA8888) {
        blitRgba(imageData, frame.payload);
      } else {
        blitMono1(imageData, frame, tintRef.current ?? DEFAULT_TINT);
      }
      ctx.putImageData(imageData, 0, 0);
    };

    return client.onFrame(surfaceId, onFrame);
  }, [client, surfaceId]);

  return canvasRef;
}

/** Default MONO1 tint (emerald-ish on near-black) if none supplied. */
const DEFAULT_TINT: MonoTint = { fg: [115, 255, 56], bg: [12, 20, 10] };

/**
 * Copy an RGBA8888 payload (wire byte order R,G,B,A) straight into the
 * ImageData backing store, which is also RGBA byte order. One memcpy-style
 * copy; no per-pixel math.
 */
function blitRgba(imageData: ImageData, payload: Uint8Array): void {
  const dst = imageData.data;
  const n = Math.min(dst.length, payload.length);
  dst.set(payload.subarray(0, n));
}

/**
 * Unpack a MONO1 frame (1bpp, MSB=leftmost, row-byte-aligned) into the RGBA
 * ImageData, tinting lit pixels fg and unlit pixels bg. Mutates `imageData`
 * in place.
 */
function blitMono1(imageData: ImageData, frame: S760Frame, tint: MonoTint): void {
  const { width, height, payload } = frame;
  const dst = imageData.data;
  const stride = (width + 7) >> 3; // ceil(width/8) bytes per row
  const [fr, fg, fb] = tint.fg;
  const [br, bg, bb] = tint.bg;

  let di = 0;
  for (let y = 0; y < height; y++) {
    const rowBase = y * stride;
    for (let x = 0; x < width; x++) {
      const byte = payload[rowBase + (x >> 3)];
      // MSB is the leftmost pixel in the byte.
      const lit = (byte >> (7 - (x & 7))) & 1;
      if (lit) {
        dst[di] = fr;
        dst[di + 1] = fg;
        dst[di + 2] = fb;
      } else {
        dst[di] = br;
        dst[di + 1] = bg;
        dst[di + 2] = bb;
      }
      dst[di + 3] = 255;
      di += 4;
    }
  }
}

/**
 * Resolve the emerald/amber backlight tint selection to concrete MONO1 colors.
 * Matches the RolandLCD on-screen palette so the composited buffer looks right
 * inside the LCD cutout (R6.2).
 */
export function backlightTint(color: 'emerald' | 'amber'): MonoTint {
  return color === 'emerald'
    ? { fg: [115, 255, 56], bg: [19, 44, 16] }
    : { fg: [255, 170, 36], bg: [43, 26, 6] };
}

/** Gotek OLED cyan-on-near-black tint (R6.3). */
export const GOTEK_OLED_TINT: MonoTint = { fg: [0, 242, 255], bg: [3, 7, 11] };

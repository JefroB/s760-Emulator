/**
 * S760BridgeClient.ts
 *
 * React-side client for the S-760 UI bridge. This is the TypeScript mirror of
 * the single-source-of-truth wire protocol in
 *   core/include/s760/s760_bridge_protocol.hpp
 * Keep the two in sync by hand; the C++ header is canonical.
 *
 * Responsibilities (spec task 3.3):
 *  - Connect to the in-process C++ `S760Bridge` over its concrete standalone
 *    transport (loopback WebSocket, default ws://localhost:8760), with graceful
 *    degradation to offline/local behaviour when no bridge is present, plus
 *    reconnect-with-backoff (design "Error Handling").
 *  - Send `S760ClientMessage` control messages (JSON) to the backend.
 *  - Decode `S760ServerTelemetry` (JSON) and binary display frames
 *    ([u8 surfaceId][u16 w LE][u16 h LE][u8 format][payload]).
 *  - Subscribe to the existing `window` `s760_input` CustomEvents (F5) and
 *    forward them to the backend under one contract regardless of backend.
 *  - Own the pointer: emit MOUSE_MOVE with a tunable sensitivity/acceleration
 *    factor producing normalized [0,1] coordinates (replaces the removed MAME
 *    8-bit ±127 relative-delta path, task 1.8).
 *  - Honour the audio-ownership boundary (R5.7): expose a `connected` state so
 *    the UI can restrict local Web Audio (soundFx) to haptics/clicks when a
 *    backend is authoritative for sampler-voice audio.
 *
 * Requirements: R5.3, R5.6, R5.7, R6.4
 */

// =============================================================================
//  Protocol mirror — keep in lockstep with s760_bridge_protocol.hpp
// =============================================================================

/** Bump when the C++ PROTOCOL_VERSION changes. */
export const PROTOCOL_VERSION = 1;

/** Default standalone/browser dev WebSocket port (hpp STANDALONE_DEV_WS_PORT). */
export const STANDALONE_DEV_WS_PORT = 8760;

/** Default standalone/browser dev WebSocket URL. */
export const DEFAULT_BRIDGE_URL = `ws://localhost:${STANDALONE_DEV_WS_PORT}`;

// --- Control messages (Client -> Server), JSON -------------------------------

/**
 * Canonical control message type tokens. These EXACT strings appear in the
 * `type` field on the wire and must match ClientMessageType::to_string in the
 * C++ header.
 */
export type S760ClientMessageType =
  | 'BUTTON_PRESS'
  | 'BUTTON_RELEASE'
  | 'DIAL_DELTA'
  | 'MOUSE_MOVE'
  | 'MOUSE_CLICK'
  | 'MOUNT_DISK'
  | 'NOTE_ON'
  | 'NOTE_OFF';

/**
 * Optional-payload mirror of the C++ ClientPayload. All fields are optional at
 * the JSON level; each message type requires the subset documented in the hpp.
 *
 *  BUTTON_PRESS / BUTTON_RELEASE : { id }
 *  DIAL_DELTA                    : { id, delta }   delta = signed detent count
 *  MOUSE_MOVE                    : { x, y }        normalized [0,1] (CRT space)
 *  MOUSE_CLICK                   : { x, y, button }
 *  MOUNT_DISK                    : { diskPath }
 *  NOTE_ON                       : { note, velocity }
 *  NOTE_OFF                      : { note, velocity? }
 */
export interface S760ClientPayload {
  id?: string;
  delta?: number;
  x?: number;
  y?: number;
  button?: number;
  diskPath?: string;
  note?: number;
  velocity?: number;
}

export interface S760ClientMessage {
  type: S760ClientMessageType;
  payload: S760ClientPayload;
}

// --- Telemetry (Server -> Client), JSON --------------------------------------

/** Fixed authoritative surface geometries (match hpp constants). */
export const CRT_WIDTH = 640;
export const CRT_HEIGHT = 480;
export const LCD_WIDTH = 160;
export const LCD_HEIGHT = 64;
export const GOTEK_WIDTH = 128;
export const GOTEK_HEIGHT = 32;

/** Mirrors the C++ ServerTelemetry struct / TS S760ServerTelemetry shape. */
export interface S760ServerTelemetry {
  timestamp: number;
  fps: number;
  crtWidth: number;
  crtHeight: number;
  lcdWidth: number;
  lcdHeight: number;
  gotekWidth: number;
  gotekHeight: number;
  peakL: number;
  peakR: number;
  activeVoices: number;
  currentMode: string;
}

// --- Binary frame framing (Server -> Client) ---------------------------------

/** surfaceId enum (hpp SurfaceId). */
export enum SurfaceId {
  CRT = 0,
  LCD = 1,
  OLED = 2,
}

/** pixel format enum (hpp PixelFormat). */
export enum PixelFormat {
  /** 32bpp, wire byte order R,G,B,A. Endianness-independent. CRT. */
  RGBA8888 = 0,
  /** 1bpp packed, 8px/byte, MSB=leftmost, row-byte-aligned. LCD/OLED. */
  MONO1 = 1,
}

/** Fixed binary frame header size: u8 + u16 + u16 + u8 (hpp FRAME_HEADER_SIZE). */
export const FRAME_HEADER_SIZE = 6;

/** Parsed binary frame header (hpp FrameHeader) plus its decoded payload view. */
export interface S760Frame {
  surfaceId: SurfaceId;
  width: number;
  height: number;
  format: PixelFormat;
  /** Raw payload bytes (not including the 6-byte header). */
  payload: Uint8Array;
}

/**
 * Exact payload size in bytes for a frame of the given format and dimensions.
 * RGBA8888 => w*h*4; MONO1 => ceil(w/8)*h (row-byte-aligned). Mirrors
 * hpp payload_size().
 */
export function payloadSize(format: PixelFormat, width: number, height: number): number {
  switch (format) {
    case PixelFormat.RGBA8888:
      return width * height * 4;
    case PixelFormat.MONO1:
      return Math.floor((width + 7) / 8) * height;
    default:
      return 0;
  }
}

// =============================================================================
//  Pointer ownership config (replaces removed MAME 8-bit delta path, task 1.8)
// =============================================================================

/**
 * Pointer sensitivity / acceleration configuration. The React shell owns the
 * pointer and emits NORMALIZED [0,1] CRT-space coordinates (NOT a wrapped 8-bit
 * ±127 relative delta). These constants tune how fast relative pointer input is
 * accumulated into the normalized position so the cursor feels responsive.
 */
export interface PointerConfig {
  /**
   * Base sensitivity: multiplies incoming relative pixel deltas before they are
   * converted to normalized CRT units. >1 makes the cursor move faster. Tunable.
   */
  sensitivity: number;
  /**
   * Acceleration exponent applied to the magnitude of fast motions. 1.0 = linear
   * (no acceleration); >1 accelerates large/fast moves for quick traversal while
   * keeping slow moves precise.
   */
  acceleration: number;
}

/** Default, deliberately brisk pointer feel (fast + responsive). Tunable. */
export const DEFAULT_POINTER_CONFIG: PointerConfig = {
  sensitivity: 2.5,
  acceleration: 1.35,
};

// =============================================================================
//  s760_input CustomEvent (F5) — existing React input layer shape
// =============================================================================

/** detail shape of the existing `window` `s760_input` CustomEvent (App.tsx). */
export interface S760InputEventDetail {
  type: string;
  payload: Record<string, unknown>;
  timestamp?: string;
}

// =============================================================================
//  Client options + callbacks
// =============================================================================

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected';

export interface S760BridgeClientOptions {
  /** WebSocket URL for the standalone transport. Defaults to DEFAULT_BRIDGE_URL. */
  url?: string;
  /** Auto-subscribe to window `s760_input` CustomEvents and forward them. */
  autoSubscribeInput?: boolean;
  /** Pointer sensitivity/acceleration tuning. */
  pointerConfig?: Partial<PointerConfig>;
  /** First reconnect delay in ms (backoff base). Default 500. */
  reconnectBaseMs?: number;
  /** Maximum reconnect delay in ms (backoff cap). Default 10000. */
  reconnectMaxMs?: number;
  /** Provide a WebSocket factory (for tests / non-browser hosts). */
  webSocketFactory?: (url: string) => WebSocket;
}

export type FrameCallback = (frame: S760Frame) => void;
export type TelemetryCallback = (telemetry: S760ServerTelemetry) => void;
export type StatusCallback = (status: ConnectionStatus) => void;

type Unsubscribe = () => void;

/**
 * Backend-agnostic bridge client. Speaks the one message contract over a
 * loopback WebSocket today; the same decode/encode path is reusable by a future
 * WebView JS<->C++ binding (feed bytes to `handleTextMessage` /
 * `handleBinaryMessage`).
 */
export class S760BridgeClient {
  private readonly url: string;
  private readonly reconnectBaseMs: number;
  private readonly reconnectMaxMs: number;
  private readonly wsFactory: (url: string) => WebSocket;

  private ws: WebSocket | null = null;
  private status: ConnectionStatus = 'disconnected';
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private closedByUser = false;

  private pointer: PointerConfig;
  /** Accumulated normalized pointer position in CRT space, clamped to [0,1]. */
  private pointerX = 0.5;
  private pointerY = 0.5;

  // Per-surface frame callbacks so task 3.4 can blit each surface independently.
  private readonly frameCallbacks = new Map<SurfaceId, Set<FrameCallback>>();
  private readonly telemetryCallbacks = new Set<TelemetryCallback>();
  private readonly statusCallbacks = new Set<StatusCallback>();

  private inputUnsub: Unsubscribe | null = null;
  private readonly boundInputListener: (e: Event) => void;

  constructor(private readonly options: S760BridgeClientOptions = {}) {
    this.url = options.url ?? DEFAULT_BRIDGE_URL;
    this.reconnectBaseMs = options.reconnectBaseMs ?? 500;
    this.reconnectMaxMs = options.reconnectMaxMs ?? 10000;
    this.pointer = { ...DEFAULT_POINTER_CONFIG, ...(options.pointerConfig ?? {}) };
    this.wsFactory =
      options.webSocketFactory ?? ((u: string) => new WebSocket(u));
    this.boundInputListener = (e: Event) => this.onWindowInput(e);

    if (options.autoSubscribeInput) {
      this.subscribeToWindowInput();
    }
  }

  // ---------------------------------------------------------------------------
  //  Connection lifecycle
  // ---------------------------------------------------------------------------

  /** Open the WebSocket transport and begin the reconnect lifecycle. */
  connect(): void {
    this.closedByUser = false;
    this.openSocket();
  }

  /** Close the transport and stop reconnecting. Degrades to offline/local. */
  disconnect(): void {
    this.closedByUser = true;
    this.clearReconnectTimer();
    if (this.ws) {
      try {
        this.ws.onopen = null;
        this.ws.onclose = null;
        this.ws.onerror = null;
        this.ws.onmessage = null;
        this.ws.close();
      } catch {
        /* ignore */
      }
      this.ws = null;
    }
    this.setStatus('disconnected');
  }

  /** Current connection status. */
  getStatus(): ConnectionStatus {
    return this.status;
  }

  /** True only when a backend is connected (authoritative, per R5.7). */
  isConnected(): boolean {
    return this.status === 'connected';
  }

  private openSocket(): void {
    this.clearReconnectTimer();
    this.setStatus('connecting');
    let socket: WebSocket;
    try {
      socket = this.wsFactory(this.url);
    } catch {
      // Could not even construct (e.g. no WebSocket in env): degrade + retry.
      this.scheduleReconnect();
      return;
    }
    this.ws = socket;
    // Binary frames arrive as ArrayBuffer for zero-copy DataView decoding.
    socket.binaryType = 'arraybuffer';

    socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.setStatus('connected');
    };
    socket.onclose = () => {
      this.ws = null;
      this.setStatus('disconnected');
      if (!this.closedByUser) {
        this.scheduleReconnect();
      }
    };
    socket.onerror = () => {
      // onclose will follow and drive the reconnect; nothing to do here.
    };
    socket.onmessage = (ev: MessageEvent) => this.onSocketMessage(ev);
  }

  private scheduleReconnect(): void {
    if (this.closedByUser) return;
    this.clearReconnectTimer();
    // Exponential backoff with cap (design "Error Handling": retry w/ backoff).
    const delay = Math.min(
      this.reconnectMaxMs,
      this.reconnectBaseMs * Math.pow(2, this.reconnectAttempts),
    );
    this.reconnectAttempts += 1;
    this.reconnectTimer = setTimeout(() => this.openSocket(), delay);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private setStatus(status: ConnectionStatus): void {
    if (this.status === status) return;
    this.status = status;
    for (const cb of this.statusCallbacks) cb(status);
  }

  // ---------------------------------------------------------------------------
  //  Inbound message decoding (transport-agnostic)
  // ---------------------------------------------------------------------------

  private onSocketMessage(ev: MessageEvent): void {
    const data = ev.data;
    if (typeof data === 'string') {
      this.handleTextMessage(data);
    } else if (data instanceof ArrayBuffer) {
      this.handleBinaryMessage(data);
    } else if (data && typeof (data as Blob).arrayBuffer === 'function') {
      // Some environments deliver Blob; convert then decode.
      (data as Blob).arrayBuffer().then((buf) => this.handleBinaryMessage(buf)).catch(() => {});
    }
  }

  /**
   * Decode a JSON control/telemetry message. Public so a WebView binding can
   * reuse the exact same decode path. Malformed JSON is discarded (design
   * "Error Handling": discard + log, never update from partial data).
   */
  handleTextMessage(text: string): void {
    let obj: unknown;
    try {
      obj = JSON.parse(text);
    } catch {
      console.warn('[S760BridgeClient] discarded malformed JSON message');
      return;
    }
    const telemetry = this.coerceTelemetry(obj);
    if (telemetry) {
      for (const cb of this.telemetryCallbacks) cb(telemetry);
    }
  }

  /**
   * Decode one binary display frame. Public so a WebView binding (ArrayBuffer
   * payload) can reuse it. Validates length against payloadSize() and discards
   * malformed frames.
   */
  handleBinaryMessage(buffer: ArrayBuffer): void {
    const frame = this.decodeFrame(buffer);
    if (!frame) return;
    const set = this.frameCallbacks.get(frame.surfaceId);
    if (set) {
      for (const cb of set) cb(frame);
    }
  }

  /**
   * Parse the 6-byte header ([u8 surfaceId][u16 w LE][u16 h LE][u8 format]) and
   * validate payload length. Returns null for malformed frames.
   */
  private decodeFrame(buffer: ArrayBuffer): S760Frame | null {
    if (buffer.byteLength < FRAME_HEADER_SIZE) {
      console.warn('[S760BridgeClient] discarded short binary frame');
      return null;
    }
    const view = new DataView(buffer);
    const surfaceIdRaw = view.getUint8(0);
    const width = view.getUint16(1, /* littleEndian */ true);
    const height = view.getUint16(3, /* littleEndian */ true);
    const formatRaw = view.getUint8(5);

    if (!(surfaceIdRaw in SurfaceId) || !isKnownFormat(formatRaw)) {
      console.warn('[S760BridgeClient] discarded frame with unknown surface/format');
      return null;
    }
    const format = formatRaw as PixelFormat;
    const expected = payloadSize(format, width, height);
    const actual = buffer.byteLength - FRAME_HEADER_SIZE;
    if (actual !== expected) {
      console.warn(
        `[S760BridgeClient] discarded frame: payload ${actual} != expected ${expected}`,
      );
      return null;
    }
    return {
      surfaceId: surfaceIdRaw as SurfaceId,
      width,
      height,
      format,
      payload: new Uint8Array(buffer, FRAME_HEADER_SIZE, expected),
    };
  }

  private coerceTelemetry(obj: unknown): S760ServerTelemetry | null {
    if (!obj || typeof obj !== 'object') return null;
    const o = obj as Record<string, unknown>;
    // Telemetry is identified by its numeric fps/timestamp + geometry fields.
    if (typeof o.fps !== 'number' || typeof o.timestamp !== 'number') return null;
    return {
      timestamp: o.timestamp,
      fps: o.fps,
      crtWidth: numberOr(o.crtWidth, CRT_WIDTH),
      crtHeight: numberOr(o.crtHeight, CRT_HEIGHT),
      lcdWidth: numberOr(o.lcdWidth, LCD_WIDTH),
      lcdHeight: numberOr(o.lcdHeight, LCD_HEIGHT),
      gotekWidth: numberOr(o.gotekWidth, GOTEK_WIDTH),
      gotekHeight: numberOr(o.gotekHeight, GOTEK_HEIGHT),
      peakL: numberOr(o.peakL, 0),
      peakR: numberOr(o.peakR, 0),
      activeVoices: numberOr(o.activeVoices, 0),
      currentMode: typeof o.currentMode === 'string' ? o.currentMode : '',
    };
  }

  // ---------------------------------------------------------------------------
  //  Outbound control messages
  // ---------------------------------------------------------------------------

  /**
   * Send a control message. When disconnected the message is dropped (graceful
   * offline/local degradation per R5.7 — the UI keeps working locally).
   */
  send(message: S760ClientMessage): void {
    if (!this.ws || this.status !== 'connected') return;
    try {
      this.ws.send(JSON.stringify(message));
    } catch {
      console.warn('[S760BridgeClient] send failed; dropping message');
    }
  }

  sendButtonPress(id: string): void {
    this.send({ type: 'BUTTON_PRESS', payload: { id } });
  }

  sendButtonRelease(id: string): void {
    this.send({ type: 'BUTTON_RELEASE', payload: { id } });
  }

  sendDialDelta(id: string, delta: number): void {
    this.send({ type: 'DIAL_DELTA', payload: { id, delta } });
  }

  sendMountDisk(diskPath: string): void {
    this.send({ type: 'MOUNT_DISK', payload: { diskPath } });
  }

  sendNoteOn(note: number, velocity: number): void {
    this.send({ type: 'NOTE_ON', payload: { note, velocity } });
  }

  sendNoteOff(note: number, velocity?: number): void {
    this.send({ type: 'NOTE_OFF', payload: { note, velocity } });
  }

  // --- Pointer ownership (normalized [0,1], tunable sensitivity) -------------

  /** Replace the pointer sensitivity/acceleration tuning at runtime. */
  setPointerConfig(config: Partial<PointerConfig>): void {
    this.pointer = { ...this.pointer, ...config };
  }

  /** Current absolute normalized pointer position (CRT space). */
  getPointerPosition(): { x: number; y: number } {
    return { x: this.pointerX, y: this.pointerY };
  }

  /** Set the absolute normalized pointer position directly (clamped to [0,1]). */
  setPointerPosition(x: number, y: number, emit = true): void {
    this.pointerX = clamp01(x);
    this.pointerY = clamp01(y);
    if (emit) this.send({ type: 'MOUSE_MOVE', payload: { x: this.pointerX, y: this.pointerY } });
  }

  /**
   * Apply a RELATIVE pointer motion (e.g. from a pointerlock movementX/Y in
   * device pixels) using the tunable sensitivity + acceleration, then emit the
   * resulting absolute NORMALIZED [0,1] position as a MOUSE_MOVE. This is the
   * replacement for the removed MAME 8-bit ±127 relative-delta register
   * (task 1.8): the backend receives normalized coordinates, never a wrapped
   * delta.
   */
  movePointerRelative(dxPixels: number, dyPixels: number): { x: number; y: number } {
    const ax = this.accelerate(dxPixels);
    const ay = this.accelerate(dyPixels);
    // Convert accelerated pixel deltas to normalized CRT units.
    this.pointerX = clamp01(this.pointerX + ax / CRT_WIDTH);
    this.pointerY = clamp01(this.pointerY + ay / CRT_HEIGHT);
    this.send({ type: 'MOUSE_MOVE', payload: { x: this.pointerX, y: this.pointerY } });
    return { x: this.pointerX, y: this.pointerY };
  }

  /** Emit a click at the current normalized pointer position. */
  clickPointer(button = 0): void {
    this.send({
      type: 'MOUSE_CLICK',
      payload: { x: this.pointerX, y: this.pointerY, button },
    });
  }

  /** Apply sensitivity + acceleration to a raw pixel delta. */
  private accelerate(deltaPixels: number): number {
    const sign = Math.sign(deltaPixels);
    const mag = Math.abs(deltaPixels);
    // acceleration: raise magnitude to the exponent (1.0 == linear).
    const accelerated = Math.pow(mag, this.pointer.acceleration);
    return sign * accelerated * this.pointer.sensitivity;
  }

  // ---------------------------------------------------------------------------
  //  Subscriptions (frames per surface, telemetry, status)
  // ---------------------------------------------------------------------------

  /** Subscribe to decoded frames for a specific surface (task 3.4 blits them). */
  onFrame(surfaceId: SurfaceId, cb: FrameCallback): Unsubscribe {
    let set = this.frameCallbacks.get(surfaceId);
    if (!set) {
      set = new Set();
      this.frameCallbacks.set(surfaceId, set);
    }
    set.add(cb);
    return () => set!.delete(cb);
  }

  onTelemetry(cb: TelemetryCallback): Unsubscribe {
    this.telemetryCallbacks.add(cb);
    return () => this.telemetryCallbacks.delete(cb);
  }

  onStatus(cb: StatusCallback): Unsubscribe {
    this.statusCallbacks.add(cb);
    // Emit current status immediately so late subscribers are in sync.
    cb(this.status);
    return () => this.statusCallbacks.delete(cb);
  }

  // ---------------------------------------------------------------------------
  //  window `s760_input` CustomEvent bridge (F5)
  // ---------------------------------------------------------------------------

  /**
   * Subscribe to the existing `window` `s760_input` CustomEvents and forward
   * them to the backend under the bridge contract. No-op outside a browser.
   */
  subscribeToWindowInput(): void {
    if (typeof window === 'undefined' || this.inputUnsub) return;
    window.addEventListener('s760_input', this.boundInputListener as EventListener);
    this.inputUnsub = () =>
      window.removeEventListener('s760_input', this.boundInputListener as EventListener);
  }

  unsubscribeFromWindowInput(): void {
    if (this.inputUnsub) {
      this.inputUnsub();
      this.inputUnsub = null;
    }
  }

  private onWindowInput(e: Event): void {
    const detail = (e as CustomEvent<S760InputEventDetail>).detail;
    if (!detail || typeof detail.type !== 'string') return;
    const msg = mapInputEventToClientMessage(detail);
    if (msg) this.send(msg);
  }

  // ---------------------------------------------------------------------------
  //  Teardown
  // ---------------------------------------------------------------------------

  /** Full teardown: stop forwarding input, close socket, drop callbacks. */
  dispose(): void {
    this.unsubscribeFromWindowInput();
    this.disconnect();
    this.frameCallbacks.clear();
    this.telemetryCallbacks.clear();
    this.statusCallbacks.clear();
  }
}

// =============================================================================
//  Mapping: existing s760_input events -> bridge contract
// =============================================================================

/**
 * Map one existing `s760_input` CustomEvent detail (App.tsx emits types like
 * MODE_CHANGE, ALPHA_DIAL_STEP, NAV_KEY, SOFT_KEY, VOLUME_CHANGE,
 * GOTEK_MOUNT_COMPLETE, AUDITION_TRIGGER, ...) onto a protocol
 * S760ClientMessage. Returns null for events that have no backend-input meaning
 * (purely cosmetic/local UI events), which are left to local handling.
 *
 * Note: pointer motion is intentionally NOT derived here — the shell owns the
 * pointer and should call `movePointerRelative`/`setPointerPosition` directly so
 * sensitivity/acceleration is applied (task 1.8 replacement).
 */
export function mapInputEventToClientMessage(
  detail: S760InputEventDetail,
): S760ClientMessage | null {
  const p = detail.payload ?? {};
  switch (detail.type) {
    case 'MODE_CHANGE':
      // Mode select maps to a button press identified by the mode name.
      return { type: 'BUTTON_PRESS', payload: { id: `MODE_${String(p.mode ?? '')}` } };

    case 'ALPHA_DIAL_STEP':
    case 'INC_DEC_BUTTON':
      return { type: 'DIAL_DELTA', payload: { id: 'ALPHA', delta: numberOr(p.delta, 0) } };

    case 'NAV_KEY':
      return { type: 'BUTTON_PRESS', payload: { id: `NAV_${String(p.direction ?? '')}` } };

    case 'ENTER_KEY':
      return { type: 'BUTTON_PRESS', payload: { id: 'ENTER' } };

    case 'EXIT_KEY':
      return { type: 'BUTTON_PRESS', payload: { id: 'EXIT' } };

    case 'SOFT_KEY':
      return { type: 'BUTTON_PRESS', payload: { id: `SOFT_${String(p.key ?? '')}` } };

    case 'VOLUME_CHANGE':
      return { type: 'DIAL_DELTA', payload: { id: 'VOLUME', delta: numberOr(p.volume, 0) } };

    case 'NOTE_ON':
      return {
        type: 'NOTE_ON',
        payload: { note: numberOr(p.note, 0), velocity: numberOr(p.velocity, 100) },
      };

    case 'NOTE_OFF':
      return {
        type: 'NOTE_OFF',
        payload: { note: numberOr(p.note, 0), velocity: numberOr(p.velocity, 0) },
      };

    case 'GOTEK_MOUNT_COMPLETE': {
      const diskPath = p.mountedDisk ?? p.disk ?? p.diskPath;
      if (typeof diskPath === 'string' && diskPath.length > 0) {
        return { type: 'MOUNT_DISK', payload: { diskPath } };
      }
      return null;
    }

    default:
      // AUDITION_TRIGGER, POWER_STATE_CHANGE, GOTEK_SELECT_DISK,
      // GOTEK_USB_TOGGLE, CUSTOM_DISK_ADDED, etc. are local/cosmetic — no
      // backend input equivalent, so leave them to local handling.
      return null;
  }
}

// =============================================================================
//  small helpers
// =============================================================================

function clamp01(v: number): number {
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

function numberOr(v: unknown, fallback: number): number {
  return typeof v === 'number' && Number.isFinite(v) ? v : fallback;
}

function isKnownFormat(raw: number): boolean {
  return raw === PixelFormat.RGBA8888 || raw === PixelFormat.MONO1;
}

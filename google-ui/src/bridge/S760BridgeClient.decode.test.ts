/**
 * Unit tests for S760BridgeClient inbound decode: binary display frames and
 * JSON telemetry, plus pointer-ownership emission over the socket.
 *
 * Covers task 4.1 item 3 (bridge client decode) and part of item 1 (pointer
 * sensitivity/acceleration math). Uses an injected fake WebSocket via the
 * client's `webSocketFactory` option so no real socket is needed; also exercises
 * the public handleTextMessage / handleBinaryMessage decode entry points.
 *
 * Validates: Requirements 7.1
 */
import {describe, it, expect, beforeEach, vi} from 'vitest';
import {
  S760BridgeClient,
  SurfaceId,
  PixelFormat,
  FRAME_HEADER_SIZE,
  payloadSize,
  CRT_WIDTH,
  CRT_HEIGHT,
  type S760Frame,
  type S760ServerTelemetry,
  type S760ClientMessage,
} from './S760BridgeClient';

/**
 * Minimal fake WebSocket implementing just enough of the browser API for the
 * client: binaryType, the four event handlers, send(), close(), and a readyState
 * progression. Tests drive it by invoking onopen/onmessage directly.
 */
class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  binaryType = 'blob';
  readyState = 0;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((ev: {data: unknown}) => void) | null = null;
  readonly sent: string[] = [];

  constructor(public readonly url: string) {
    FakeWebSocket.instances.push(this);
  }

  open(): void {
    this.readyState = 1;
    this.onopen?.();
  }

  deliver(data: unknown): void {
    this.onmessage?.({data});
  }

  send(data: string): void {
    this.sent.push(data);
  }

  close(): void {
    this.readyState = 3;
    this.onclose?.();
  }
}

/** Build a protocol binary frame: [u8 surfaceId][u16 w LE][u16 h LE][u8 format][payload]. */
function buildFrame(
  surfaceId: number,
  width: number,
  height: number,
  format: number,
  payloadLen: number,
): ArrayBuffer {
  const buf = new ArrayBuffer(FRAME_HEADER_SIZE + payloadLen);
  const view = new DataView(buf);
  view.setUint8(0, surfaceId);
  view.setUint16(1, width, true);
  view.setUint16(3, height, true);
  view.setUint8(5, format);
  // Fill payload with a recognizable ramp.
  const bytes = new Uint8Array(buf, FRAME_HEADER_SIZE);
  for (let i = 0; i < bytes.length; i++) bytes[i] = i & 0xff;
  return buf;
}

function makeConnectedClient() {
  FakeWebSocket.instances = [];
  const client = new S760BridgeClient({
    url: 'ws://test/bridge',
    webSocketFactory: (u) => new FakeWebSocket(u) as unknown as WebSocket,
  });
  client.connect();
  const sock = FakeWebSocket.instances[0];
  sock.open();
  return {client, sock};
}

describe('S760BridgeClient binary frame decode', () => {
  let client: S760BridgeClient;

  beforeEach(() => {
    client = new S760BridgeClient();
  });

  it('decodes a well-formed CRT RGBA frame and fires the CRT callback', () => {
    const frames: S760Frame[] = [];
    client.onFrame(SurfaceId.CRT, (f) => frames.push(f));
    const payloadLen = payloadSize(PixelFormat.RGBA8888, 4, 2); // 4*2*4 = 32
    client.handleBinaryMessage(buildFrame(SurfaceId.CRT, 4, 2, PixelFormat.RGBA8888, payloadLen));

    expect(frames).toHaveLength(1);
    expect(frames[0]).toMatchObject({
      surfaceId: SurfaceId.CRT,
      width: 4,
      height: 2,
      format: PixelFormat.RGBA8888,
    });
    expect(frames[0].payload.length).toBe(payloadLen);
    // Row-byte values follow the ramp we wrote.
    expect(Array.from(frames[0].payload.slice(0, 4))).toEqual([0, 1, 2, 3]);
  });

  it('decodes a MONO1 LCD frame with row-byte-aligned payload size', () => {
    const frames: S760Frame[] = [];
    client.onFrame(SurfaceId.LCD, (f) => frames.push(f));
    // 160x64 mono: ceil(160/8)=20 bytes/row * 64 = 1280.
    const payloadLen = payloadSize(PixelFormat.MONO1, 160, 64);
    expect(payloadLen).toBe(1280);
    client.handleBinaryMessage(buildFrame(SurfaceId.LCD, 160, 64, PixelFormat.MONO1, payloadLen));
    expect(frames).toHaveLength(1);
    expect(frames[0].surfaceId).toBe(SurfaceId.LCD);
    expect(frames[0].payload.length).toBe(1280);
  });

  it('routes frames only to the matching surface subscriber', () => {
    const crt: S760Frame[] = [];
    const lcd: S760Frame[] = [];
    client.onFrame(SurfaceId.CRT, (f) => crt.push(f));
    client.onFrame(SurfaceId.LCD, (f) => lcd.push(f));
    client.handleBinaryMessage(
      buildFrame(SurfaceId.OLED, 128, 32, PixelFormat.MONO1, payloadSize(PixelFormat.MONO1, 128, 32)),
    );
    expect(crt).toHaveLength(0);
    expect(lcd).toHaveLength(0);
  });

  it('discards a frame shorter than the header', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const frames: S760Frame[] = [];
    client.onFrame(SurfaceId.CRT, (f) => frames.push(f));
    client.handleBinaryMessage(new ArrayBuffer(FRAME_HEADER_SIZE - 1));
    expect(frames).toHaveLength(0);
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
  });

  it('discards a frame whose payload length does not match the header geometry', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const frames: S760Frame[] = [];
    client.onFrame(SurfaceId.CRT, (f) => frames.push(f));
    // Declare 4x2 RGBA (expects 32 payload bytes) but supply only 10.
    client.handleBinaryMessage(buildFrame(SurfaceId.CRT, 4, 2, PixelFormat.RGBA8888, 10));
    expect(frames).toHaveLength(0);
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
  });

  it('discards a frame with an unknown surface id or format', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const frames: S760Frame[] = [];
    client.onFrame(SurfaceId.CRT, (f) => frames.push(f));
    // surfaceId 9 is not a valid SurfaceId.
    client.handleBinaryMessage(buildFrame(9, 4, 2, PixelFormat.RGBA8888, 32));
    // format 7 is not a valid PixelFormat.
    client.handleBinaryMessage(buildFrame(SurfaceId.CRT, 4, 2, 7, 32));
    expect(frames).toHaveLength(0);
    expect(warn).toHaveBeenCalledTimes(2);
    warn.mockRestore();
  });
});

describe('S760BridgeClient telemetry decode', () => {
  let client: S760BridgeClient;

  beforeEach(() => {
    client = new S760BridgeClient();
  });

  it('parses a well-formed telemetry JSON and fires onTelemetry', () => {
    const got: S760ServerTelemetry[] = [];
    client.onTelemetry((t) => got.push(t));
    client.handleTextMessage(
      JSON.stringify({
        timestamp: 123456,
        fps: 60,
        crtWidth: 640,
        crtHeight: 480,
        lcdWidth: 160,
        lcdHeight: 64,
        gotekWidth: 128,
        gotekHeight: 32,
        peakL: 0.5,
        peakR: 0.25,
        activeVoices: 7,
        currentMode: 'SAMPLE',
      }),
    );
    expect(got).toHaveLength(1);
    expect(got[0]).toMatchObject({fps: 60, activeVoices: 7, currentMode: 'SAMPLE', peakL: 0.5});
  });

  it('fills defaults for missing geometry/metric fields', () => {
    const got: S760ServerTelemetry[] = [];
    client.onTelemetry((t) => got.push(t));
    client.handleTextMessage(JSON.stringify({timestamp: 1, fps: 30}));
    expect(got).toHaveLength(1);
    expect(got[0]).toMatchObject({
      crtWidth: 640,
      lcdWidth: 160,
      gotekWidth: 128,
      peakL: 0,
      activeVoices: 0,
      currentMode: '',
    });
  });

  it('discards malformed JSON without firing telemetry', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const got: S760ServerTelemetry[] = [];
    client.onTelemetry((t) => got.push(t));
    client.handleTextMessage('{not valid json');
    expect(got).toHaveLength(0);
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
  });

  it('ignores JSON lacking the telemetry discriminator fields', () => {
    const got: S760ServerTelemetry[] = [];
    client.onTelemetry((t) => got.push(t));
    client.handleTextMessage(JSON.stringify({hello: 'world'}));
    expect(got).toHaveLength(0);
  });
});

describe('S760BridgeClient over an injected fake socket', () => {
  it('routes socket messages through decode and reaches subscribers', () => {
    const {client, sock} = makeConnectedClient();
    expect(client.isConnected()).toBe(true);
    expect(sock.binaryType).toBe('arraybuffer');

    const frames: S760Frame[] = [];
    const telem: S760ServerTelemetry[] = [];
    client.onFrame(SurfaceId.CRT, (f) => frames.push(f));
    client.onTelemetry((t) => telem.push(t));

    sock.deliver(buildFrame(SurfaceId.CRT, 2, 2, PixelFormat.RGBA8888, payloadSize(PixelFormat.RGBA8888, 2, 2)));
    sock.deliver(JSON.stringify({timestamp: 5, fps: 59.9}));

    expect(frames).toHaveLength(1);
    expect(telem).toHaveLength(1);
    client.dispose();
  });

  it('emits MOUSE_MOVE with normalized [0,1] coords and applies sensitivity/acceleration', () => {
    const {client, sock} = makeConnectedClient();
    // From center (0.5, 0.5), move right by 100px. With default config
    // (sensitivity 2.5, acceleration 1.35): accel = 100^1.35 * 2.5.
    const result = client.movePointerRelative(100, 0);
    const accelerated = Math.pow(100, 1.35) * 2.5;
    const expectedX = Math.min(1, 0.5 + accelerated / CRT_WIDTH);
    expect(result.x).toBeCloseTo(expectedX, 6);
    expect(result.y).toBeCloseTo(0.5, 6);

    const sentMsg = JSON.parse(sock.sent.at(-1)!) as S760ClientMessage;
    expect(sentMsg.type).toBe('MOUSE_MOVE');
    expect(sentMsg.payload.x).toBeGreaterThanOrEqual(0);
    expect(sentMsg.payload.x).toBeLessThanOrEqual(1);
    client.dispose();
  });

  it('clamps normalized pointer position to [0,1] on large motions', () => {
    const {client} = makeConnectedClient();
    const r = client.movePointerRelative(100000, -100000);
    expect(r.x).toBe(1);
    expect(r.y).toBe(0);
    expect(client.getPointerPosition()).toEqual({x: 1, y: 0});
    client.dispose();
  });

  it('does not send control messages while disconnected (graceful offline)', () => {
    FakeWebSocket.instances = [];
    const client = new S760BridgeClient({
      webSocketFactory: (u) => new FakeWebSocket(u) as unknown as WebSocket,
    });
    // Not connected yet.
    client.sendButtonPress('ENTER');
    expect(FakeWebSocket.instances[0]?.sent ?? []).toHaveLength(0);
  });
});

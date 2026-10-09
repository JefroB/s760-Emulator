/**
 * Unit tests for the pure math of the bridge client: payloadSize() framing math
 * and the pointer sensitivity/acceleration behavior that replaces the removed
 * MAME 8-bit ±127 relative-delta path (task 1.8 / 3.3).
 *
 * Covers task 4.1 item 1 (rotary encoder / dial / pointer math) via the exported
 * pure surface.
 *
 * Validates: Requirements 7.1
 */
import {describe, it, expect} from 'vitest';
import {
  S760BridgeClient,
  PixelFormat,
  payloadSize,
} from './S760BridgeClient';

describe('payloadSize framing math', () => {
  it('RGBA8888 is width*height*4', () => {
    expect(payloadSize(PixelFormat.RGBA8888, 640, 480)).toBe(640 * 480 * 4);
    expect(payloadSize(PixelFormat.RGBA8888, 1, 1)).toBe(4);
  });

  it('MONO1 is row-byte-aligned: ceil(width/8)*height', () => {
    expect(payloadSize(PixelFormat.MONO1, 160, 64)).toBe(20 * 64);
    expect(payloadSize(PixelFormat.MONO1, 128, 32)).toBe(16 * 32);
    // Non-multiple-of-8 width rounds the row up to a whole byte.
    expect(payloadSize(PixelFormat.MONO1, 1, 1)).toBe(1);
    expect(payloadSize(PixelFormat.MONO1, 9, 1)).toBe(2);
  });
});

describe('pointer acceleration / sensitivity math', () => {
  // Use an unconnected client: movePointerRelative still accumulates + clamps
  // the normalized position; the send() is a no-op while disconnected.
  function client(cfg?: {sensitivity?: number; acceleration?: number}) {
    return new S760BridgeClient({pointerConfig: cfg});
  }

  it('linear (acceleration=1) scales deltas by sensitivity only', () => {
    const c = client({sensitivity: 2, acceleration: 1});
    c.setPointerPosition(0.5, 0.5, false);
    // Move +50px with sensitivity 2 => +100 CRT px => +100/640 normalized.
    const r = c.movePointerRelative(50, 0);
    expect(r.x).toBeCloseTo(0.5 + 100 / 640, 6);
  });

  it('is symmetric: opposite deltas cancel from the same start', () => {
    const c = client({sensitivity: 1.5, acceleration: 1.2});
    c.setPointerPosition(0.5, 0.5, false);
    c.movePointerRelative(40, 40);
    c.movePointerRelative(-40, -40);
    const p = c.getPointerPosition();
    expect(p.x).toBeCloseTo(0.5, 6);
    expect(p.y).toBeCloseTo(0.5, 6);
  });

  it('acceleration>1 makes a fast move travel more than two half-moves', () => {
    // One big move vs two small moves of the same total raw distance: with a
    // super-linear exponent the single fast move should cover more ground,
    // which is the whole point of pointer acceleration (fast = responsive).
    // Deltas are kept small so neither path saturates the [0,1] clamp.
    const fast = client({sensitivity: 1, acceleration: 1.5});
    fast.setPointerPosition(0.0, 0.5, false);
    const bigFirst = fast.movePointerRelative(20, 0).x;

    const slow = client({sensitivity: 1, acceleration: 1.5});
    slow.setPointerPosition(0.0, 0.5, false);
    slow.movePointerRelative(10, 0);
    const twoHalves = slow.movePointerRelative(10, 0).x;

    // Sanity: neither reached the clamp ceiling, so the comparison is meaningful.
    expect(bigFirst).toBeLessThan(1);
    expect(twoHalves).toBeLessThan(1);
    expect(bigFirst).toBeGreaterThan(twoHalves);
  });

  it('clamps the accumulated normalized position into [0,1]', () => {
    const c = client();
    c.setPointerPosition(0.5, 0.5, false);
    const r = c.movePointerRelative(-99999, 99999);
    expect(r.x).toBe(0);
    expect(r.y).toBe(1);
  });

  it('setPointerConfig retunes sensitivity at runtime', () => {
    const c = client({sensitivity: 1, acceleration: 1});
    c.setPointerPosition(0, 0.5, false);
    const slow = c.movePointerRelative(10, 0).x;
    c.setPointerConfig({sensitivity: 5});
    c.setPointerPosition(0, 0.5, false);
    const fast = c.movePointerRelative(10, 0).x;
    expect(fast).toBeGreaterThan(slow);
  });
});

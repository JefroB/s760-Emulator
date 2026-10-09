/**
 * Unit tests for mapInputEventToClientMessage() — the mapping from the existing
 * App.tsx `window` `s760_input` CustomEvent detail shapes onto the bridge
 * `S760ClientMessage` contract (task 3.3 / F5).
 *
 * Covers task 4.1 item 2: s760_input dispatch / mapping. The event type tokens
 * and payload shapes mirror what App.tsx actually emits (emitHardwareEvent).
 *
 * Validates: Requirements 7.1
 */
import {describe, it, expect} from 'vitest';
import {
  mapInputEventToClientMessage,
  type S760InputEventDetail,
} from './S760BridgeClient';

function detail(type: string, payload: Record<string, unknown> = {}): S760InputEventDetail {
  return {type, payload};
}

describe('mapInputEventToClientMessage', () => {
  it('maps MODE_CHANGE to a BUTTON_PRESS identified by the mode', () => {
    const msg = mapInputEventToClientMessage(detail('MODE_CHANGE', {mode: 'SAMPLE'}));
    expect(msg).toEqual({type: 'BUTTON_PRESS', payload: {id: 'MODE_SAMPLE'}});
  });

  it('maps ALPHA_DIAL_STEP to a DIAL_DELTA on the ALPHA encoder', () => {
    const msg = mapInputEventToClientMessage(detail('ALPHA_DIAL_STEP', {delta: 3}));
    expect(msg).toEqual({type: 'DIAL_DELTA', payload: {id: 'ALPHA', delta: 3}});
  });

  it('maps INC_DEC_BUTTON to the same ALPHA DIAL_DELTA', () => {
    const msg = mapInputEventToClientMessage(detail('INC_DEC_BUTTON', {delta: -1}));
    expect(msg).toEqual({type: 'DIAL_DELTA', payload: {id: 'ALPHA', delta: -1}});
  });

  it('defaults a missing dial delta to 0', () => {
    const msg = mapInputEventToClientMessage(detail('ALPHA_DIAL_STEP', {}));
    expect(msg).toEqual({type: 'DIAL_DELTA', payload: {id: 'ALPHA', delta: 0}});
  });

  it('maps NAV_KEY to a direction-specific button press', () => {
    const msg = mapInputEventToClientMessage(detail('NAV_KEY', {direction: 'UP'}));
    expect(msg).toEqual({type: 'BUTTON_PRESS', payload: {id: 'NAV_UP'}});
  });

  it('maps ENTER_KEY and EXIT_KEY to their named button presses', () => {
    expect(mapInputEventToClientMessage(detail('ENTER_KEY', {mode: 'DISK'}))).toEqual({
      type: 'BUTTON_PRESS',
      payload: {id: 'ENTER'},
    });
    expect(mapInputEventToClientMessage(detail('EXIT_KEY'))).toEqual({
      type: 'BUTTON_PRESS',
      payload: {id: 'EXIT'},
    });
  });

  it('maps SOFT_KEY to a key-identified button press', () => {
    const msg = mapInputEventToClientMessage(detail('SOFT_KEY', {key: 'F3', mode: 'DISK'}));
    expect(msg).toEqual({type: 'BUTTON_PRESS', payload: {id: 'SOFT_F3'}});
  });

  it('maps VOLUME_CHANGE to a DIAL_DELTA on the VOLUME control', () => {
    const msg = mapInputEventToClientMessage(detail('VOLUME_CHANGE', {volume: 85}));
    expect(msg).toEqual({type: 'DIAL_DELTA', payload: {id: 'VOLUME', delta: 85}});
  });

  it('maps NOTE_ON / NOTE_OFF carrying note + velocity', () => {
    expect(mapInputEventToClientMessage(detail('NOTE_ON', {note: 60, velocity: 120}))).toEqual({
      type: 'NOTE_ON',
      payload: {note: 60, velocity: 120},
    });
    expect(mapInputEventToClientMessage(detail('NOTE_OFF', {note: 60, velocity: 0}))).toEqual({
      type: 'NOTE_OFF',
      payload: {note: 60, velocity: 0},
    });
  });

  it('defaults NOTE_ON velocity to 100 when absent', () => {
    const msg = mapInputEventToClientMessage(detail('NOTE_ON', {note: 48}));
    expect(msg).toEqual({type: 'NOTE_ON', payload: {note: 48, velocity: 100}});
  });

  it('maps GOTEK_MOUNT_COMPLETE (App.tsx mountedDisk payload) to MOUNT_DISK', () => {
    const msg = mapInputEventToClientMessage(
      detail('GOTEK_MOUNT_COMPLETE', {mountedDisk: 'STRINGS.IMG'}),
    );
    expect(msg).toEqual({type: 'MOUNT_DISK', payload: {diskPath: 'STRINGS.IMG'}});
  });

  it('returns null for GOTEK_MOUNT_COMPLETE without a disk path', () => {
    expect(mapInputEventToClientMessage(detail('GOTEK_MOUNT_COMPLETE', {}))).toBeNull();
  });

  it.each([
    'AUDITION_TRIGGER',
    'POWER_STATE_CHANGE',
    'GOTEK_SELECT_DISK',
    'GOTEK_USB_TOGGLE',
    'CUSTOM_DISK_ADDED',
    'SOME_UNKNOWN_EVENT',
  ])('maps cosmetic/local event %s to null', (type) => {
    expect(mapInputEventToClientMessage(detail(type, {foo: 'bar'}))).toBeNull();
  });
});

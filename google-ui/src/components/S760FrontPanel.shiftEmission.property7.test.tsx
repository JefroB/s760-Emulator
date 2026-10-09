/**
 * Property-based test for single-event emission on Shift_Button activation
 * (design Property 7).
 *
 * Property 7: A Shift_Button activation emits exactly one event equal to the
 *   recorded chord event.
 *
 *   For any Verified renderable Shift_Button and any number of activations `n`
 *   (whether by mouse click, Enter, or Space), the Front_Panel emits exactly
 *   `n` input events through `onEventEmit` — one per activation — and each
 *   emitted event's `type` and every payload field match, value-for-value, the
 *   `ChordEventSpec` recorded in the Button_Mapping for that SHIFT function's
 *   hardware chord.
 *
 * This renders the REAL `S760FrontPanel` with an injected generated mapping
 * (via its `shiftButtonMapping` prop), spies `onEventEmit`, and drives
 * click / Enter / Space on the rendered Shift_Button(s) through
 * `@testing-library/user-event`. Assertions are SCOPED to the SHIFT button's
 * recorded chord `type`/`payload` (other front-panel interactions never fire in
 * these runs, and a fresh render is used per generated case) so the count/value
 * checks pin exactly the SHIFT emission path (R5.2 single channel).
 *
 * Validates: Requirements 3.2, 3.3, 5.1, 5.3, 5.4, 7.6
 *
 * Test tooling: Vitest + @testing-library/react + @testing-library/user-event +
 * fast-check (design "Testing Strategy > Tooling").
 */
import {describe, it, expect, vi, beforeAll} from 'vitest';
import {render, cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import fc from 'fast-check';
import {S760FrontPanel} from './S760FrontPanel';
import {soundFx} from '../audio/soundFx';
import {SamplerState, DEFAULT_DISK_IMAGES} from '../types/sampler';
import type {
  ButtonMappingEntry,
  ChordEventSpec,
  ShiftFunctionSpec,
} from '../data/shiftButtonMap';
import {verifiedShiftButtons} from '../data/shiftButtonSelectors';

// jsdom has no Web Audio API, and the shell's tactile buttons call
// soundFx.playClick() (which lazily constructs an AudioContext) before invoking
// their action callback. Disable the UI-haptics engine for this suite via its
// public API so playClick() early-returns — we are asserting emission behaviour,
// not audio.
beforeAll(() => {
  soundFx.setSoundEnabled(false);
  soundFx.setFloppySeekEnabled(false);

  // jsdom does not implement HTMLCanvasElement.getContext; the front panel
  // embeds the RolandLCD canvas (SED1335 surface) which calls it on mount.
  // Stub it to a no-op 2D-context-like object so the panel renders cleanly in
  // jsdom (we assert emission behaviour, not pixel output).
  if (!HTMLCanvasElement.prototype.getContext) {
    // (older jsdom) — nothing to override.
  }
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockImplementation(
    () =>
      ({
        canvas: document.createElement('canvas'),
        fillRect: () => {},
        clearRect: () => {},
        getImageData: () => ({data: new Uint8ClampedArray(0)}),
        putImageData: () => {},
        createImageData: () => ({data: new Uint8ClampedArray(0)}),
        setTransform: () => {},
        drawImage: () => {},
        save: () => {},
        restore: () => {},
        beginPath: () => {},
        moveTo: () => {},
        lineTo: () => {},
        closePath: () => {},
        stroke: () => {},
        fill: () => {},
        translate: () => {},
        scale: () => {},
        rotate: () => {},
        arc: () => {},
        rect: () => {},
        measureText: () => ({width: 0}),
        fillText: () => {},
        createLinearGradient: () => ({addColorStop: () => {}}),
      }) as unknown as CanvasRenderingContext2D,
  );
});

// -----------------------------------------------------------------------------
//  Front-panel fixtures (minimal valid stubs for every required prop).
// -----------------------------------------------------------------------------

/** A powered-on sampler state (the device must be powered on where relevant). */
function makeState(overrides: Partial<SamplerState> = {}): SamplerState {
  return {
    powerOn: true,
    volume: 85,
    volumeAngle: 45,
    alphaDialAngle: 0,
    mode: 'DISK',
    subMode: 'PLAY',
    activeCursorField: 0,
    cursorRow: 0,
    cursorCol: 0,
    backlightColor: 'emerald',
    currentPatchIndex: 0,
    currentPerfIndex: 0,
    sampleZoom: 1,
    sampleScrub: 25,
    gotek: {
      selectedImageIndex: 1,
      mountedImageIndex: 1,
      isBusy: false,
      currentTrack: 18,
      currentSide: 0,
      usbInserted: true,
      dialAngle: 0,
      statusText: 'READY',
    },
    peakL: false,
    peakR: false,
    midiRx: false,
    ...overrides,
  };
}

/** No-op handlers for every S760FrontPanel callback; override onEventEmit. */
function frontPanelHandlers(onEventEmit: (type: string, payload: unknown) => void) {
  return {
    onTogglePower: vi.fn(),
    onSetVolume: vi.fn(),
    onSetMode: vi.fn(),
    onAlphaDialStep: vi.fn(),
    onNavigate: vi.fn(),
    onIncDec: vi.fn(),
    onEnter: vi.fn(),
    onExit: vi.fn(),
    onSoftKey: vi.fn(),
    onSelectDiskIndex: vi.fn(),
    onMountDisk: vi.fn(),
    onToggleUsb: vi.fn(),
    onEventEmit,
    onTriggerAudition: vi.fn(),
  };
}

// -----------------------------------------------------------------------------
//  Arbitraries: generate a mapping that contains at least one renderable
//  (Verified, non-Gotek, event-bearing) SHIFT function with a generated
//  ChordEventSpec (type string + payload object).
// -----------------------------------------------------------------------------

/** Shared button-id alphabet (stable, distinct ids keep each descriptor 1:1). */
const buttonIdArb: fc.Arbitrary<string> = fc.constantFrom(
  'PATCH',
  'PART',
  'SAMPLE',
  'SYSTEM',
  'PERF',
  'DISK',
);

/**
 * A chord event payload. Uses JSON-serialisable scalar values keyed by short
 * strings so the recorded event is compared value-for-value without depending
 * on exotic/unstable generated values; `fc.anything()` would allow NaN/-0 etc.
 * that complicate value-for-value equality while adding no coverage here.
 */
const payloadArb: fc.Arbitrary<Record<string, unknown>> = fc.dictionary(
  fc.string({minLength: 1, maxLength: 6}),
  fc.oneof(
    fc.string(),
    fc.integer(),
    fc.boolean(),
    fc.constant(null),
  ),
  {maxKeys: 4},
);

/** A chord event (present variant): a type string + a payload object. */
const chordEventArb: fc.Arbitrary<ChordEventSpec> = fc.record({
  type: fc.string({minLength: 1, maxLength: 12}),
  payload: payloadArb,
});

/** A Verified, event-bearing SHIFT function reached through a target button. */
function verifiedShiftArb(buttonId: string): fc.Arbitrary<ShiftFunctionSpec> {
  return fc.record({
    targetButtonId: buttonIdArb,
    silkscreenLabel: fc.option(fc.string({minLength: 1, maxLength: 10}), {
      nil: null,
    }),
    description: fc.string({minLength: 1, maxLength: 16}),
    verification: fc.constant<'Verified'>('Verified'),
    manualPage: fc.constant('p.42'),
    reasonUnverified: fc.constant(null),
    event: chordEventArb,
  }) as fc.Arbitrary<ShiftFunctionSpec>;
}

/** One renderable entry: Verified SHIFT function, not Gotek-owned. */
function renderableEntryArb(buttonId: string): fc.Arbitrary<ButtonMappingEntry> {
  return verifiedShiftArb(buttonId).map((shift) => ({
    buttonId,
    primaryFunction: 'generated primary',
    shift,
    verification: 'Verified',
    manualPage: 'p.42',
    reasonUnverified: null,
    ownedByGotek: false,
  }));
}

/**
 * A mapping arbitrary guaranteeing at least one renderable Shift_Button. We
 * generate between 1 and 3 renderable entries over DISTINCT button ids so each
 * yields exactly one rendered Shift_Button with its own recorded event.
 */
const mappingArb: fc.Arbitrary<readonly ButtonMappingEntry[]> = fc
  .uniqueArray(buttonIdArb, {minLength: 1, maxLength: 3})
  .chain((ids) =>
    fc.tuple(...ids.map((id) => renderableEntryArb(id))),
  );

// -----------------------------------------------------------------------------
//  The property.
// -----------------------------------------------------------------------------

describe('Property 7: a Shift_Button activation emits exactly one event equal to the recorded chord event', () => {
  it('n activations (click / Enter / Space) => n emissions, each matching the ChordEventSpec value-for-value', async () => {
    await fc.assert(
      fc.asyncProperty(
        mappingArb,
        // Number of activations per button.
        fc.integer({min: 1, max: 4}),
        // Which activation gesture to use.
        fc.constantFrom<'click' | 'enter' | 'space'>('click', 'enter', 'space'),
        async (mapping, n, gesture) => {
          // The exact descriptors the panel will render (one per entry here).
          const descriptors = verifiedShiftButtons(mapping);
          expect(descriptors.length).toBeGreaterThan(0);

          const onEventEmit = vi.fn();
          // delay:null removes user-event's inter-event timers so 100 generated
          // renders with multiple activations complete well within the budget.
          const user = userEvent.setup({delay: null});

          const {container} = render(
            <S760FrontPanel
              state={makeState()}
              diskList={DEFAULT_DISK_IMAGES}
              shiftButtonMapping={mapping}
              {...frontPanelHandlers(onEventEmit)}
            />,
          );

          try {
            for (const descriptor of descriptors) {
              // Clear between buttons so each button's emissions are asserted in
              // isolation (two generated buttons may share an event type; this
              // keeps the count/value checks scoped to the button under test).
              onEventEmit.mockClear();

              const btn = container.querySelector(
                `[data-shift-button="${descriptor.buttonId}"]`,
              ) as HTMLButtonElement | null;
              expect(btn).not.toBeNull();

              for (let i = 0; i < n; i++) {
                if (gesture === 'click') {
                  await user.click(btn!);
                } else {
                  btn!.focus();
                  await user.keyboard(gesture === 'enter' ? '{Enter}' : ' ');
                }
              }

              // Exactly n emissions for n activations — one per activation, no
              // extra/alternate/bypassing emission (R5.4, R5.2) — and each
              // emitted event equals the recorded chord event value-for-value:
              // the type and every payload field match (R3.2, R3.3, R5.1, R5.3,
              // R7.6).
              expect(onEventEmit.mock.calls.length).toBe(n);
              for (const call of onEventEmit.mock.calls) {
                expect(call[0]).toBe(descriptor.event.type);
                expect(call[1]).toEqual(descriptor.event.payload);
              }
            }
          } finally {
            cleanup();
          }
        },
      ),
      {numRuns: 100},
    );
    // 100 full React renders + user-event activations are not instantaneous;
    // give the whole property a generous budget.
  }, 60000);
});

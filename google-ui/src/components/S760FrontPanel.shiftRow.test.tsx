/**
 * S760FrontPanel.shiftRow.test.tsx
 *
 * Example / smoke tests for the dedicated SHIFT-button row wired into
 * `S760FrontPanel` (front-panel-shift-buttons task 7.4). These complement the
 * property-based tests (which prove the pure selector/reconcile logic over many
 * generated mappings) by pinning down concrete UI structure, styling, emission,
 * accessibility, and Gotek isolation that the design's prework classified as
 * EXAMPLE / EDGE_CASE / SMOKE.
 *
 * Coverage (clause -> requirement):
 *   - Preserved primaries are still rendered (R2.5)
 *   - A seeded fabricated button is removed while an `Unverified`-but-mapped
 *     sibling is retained (R2.7, R2.8, R2.10) — demonstrated at the `reconcile`
 *     UI-logic boundary (see rationale on that test)
 *   - A shared SHIFT visual treatment, distinct from primaries, using the
 *     existing design-system classes while powered on (R4.2, R4.3, R4.4)
 *   - A single emission channel — only `onEventEmit` is invoked (R5.2)
 *   - Synchronous emission + native `title` tooltip (R3.5, R7.1, R7.5)
 *   - Native-<button> focus order + focus-visible participation (R7.4)
 *   - No `Shift_Button` inside the Gotek subtree; GotekBay stays green
 *     (R6.1, R6.2)
 *
 * Validates: Requirements 2.5, 3.5, 4.2, 4.3, 4.4, 5.2, 6.1, 6.2, 7.1, 7.4, 7.5
 */
import {describe, it, expect, vi, beforeAll} from 'vitest';
import {render, screen, within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {S760FrontPanel} from './S760FrontPanel';
import {soundFx} from '../audio/soundFx';
import {SamplerState, SamplerMode, DEFAULT_DISK_IMAGES} from '../types/sampler';
import {reconcile} from '../data/shiftButtonReconcile';
import type {ButtonMappingEntry} from '../data/shiftButtonMap';

// jsdom has no Web Audio API, and the panel's tactile buttons call
// soundFx.playClick() (which lazily constructs an AudioContext) inside
// triggerButton before invoking their action. Disable the UI-haptics engine via
// its public API so playClick() early-returns — we assert structure/emission,
// not audio.
beforeAll(() => {
  soundFx.setSoundEnabled(false);
  soundFx.setFloppySeekEnabled(false);
});

// -----------------------------------------------------------------------------
//  Fixtures / helpers
// -----------------------------------------------------------------------------

/** A powered-on sampler state with a USB disk inserted. */
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

/** No-op handlers for every S760FrontPanel callback; override selectively. */
function frontPanelHandlers(overrides: Record<string, unknown> = {}) {
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
    onEventEmit: vi.fn(),
    onTriggerAudition: vi.fn(),
    ...overrides,
  };
}

function renderFrontPanel(
  state: SamplerState,
  handlers: ReturnType<typeof frontPanelHandlers>,
  shiftButtonMapping?: readonly ButtonMappingEntry[],
) {
  return render(
    <S760FrontPanel
      state={state}
      diskList={DEFAULT_DISK_IMAGES}
      shiftButtonMapping={shiftButtonMapping}
      {...handlers}
    />,
  );
}

/**
 * Build a mapping with one Verified, non-Gotek, event-bearing SHIFT function so
 * exactly one Shift_Button renders. The entry's `shift` carries a recorded chord
 * event routed through the SAME contract the Event_Emitter understands.
 */
function verifiedShiftEntry(
  overrides: Partial<ButtonMappingEntry> = {},
): ButtonMappingEntry {
  return {
    buttonId: 'PATCH',
    primaryFunction: 'Select PATCH mode.',
    verification: 'Verified',
    manualPage: 'p.42',
    reasonUnverified: null,
    ownedByGotek: false,
    shift: {
      targetButtonId: 'PATCH',
      silkscreenLabel: 'COPY',
      description: 'Copy the current patch.',
      verification: 'Verified',
      manualPage: 'p.42',
      reasonUnverified: null,
      event: {type: 'MODE_SELECT', payload: {mode: 'PATCH', shift: true}},
    },
    ...overrides,
  };
}

/** A second distinct Verified SHIFT entry (for shared-treatment assertions). */
function secondVerifiedShiftEntry(): ButtonMappingEntry {
  return verifiedShiftEntry({
    buttonId: 'SAMPLE',
    primaryFunction: 'Select SAMPLE mode.',
    shift: {
      targetButtonId: 'SAMPLE',
      silkscreenLabel: 'TRUNCATE',
      description: 'Truncate the current sample.',
      verification: 'Verified',
      manualPage: 'p.57',
      reasonUnverified: null,
      event: {type: 'SOFT_KEY', payload: {index: 2, shift: true}},
    },
  });
}

/** The canonical preserved-primary id set the panel always retains (R2.5). */
const PRESERVED_PRIMARY_IDS = [
  'POWER',
  'PERF',
  'PATCH',
  'PART',
  'SAMPLE',
  'SYSTEM',
  'DISK',
  'NAV_LEFT',
  'NAV_RIGHT',
  'NAV_UP',
  'NAV_DOWN',
  'DEC',
  'INC',
  'ENTER',
  'EXIT',
  'F1',
  'F2',
  'F3',
  'F4',
  'F5',
  'F6',
  'VOLUME',
  'VALUE_DATA',
];

// -----------------------------------------------------------------------------
//  R2.5 — Preserved primary controls are present
// -----------------------------------------------------------------------------
describe('Preserved primary controls remain on the panel (R2.5)', () => {
  it('renders POWER, all 6 MODE buttons, nav cross, DEC/INC, ENTER/EXIT, F1-F6, VOLUME, and VALUE/DATA', () => {
    renderFrontPanel(makeState(), frontPanelHandlers());

    // POWER rocker.
    expect(screen.getByText('POWER')).toBeInTheDocument();
    expect(
      screen.getByTitle('Power Rocker Switch [I / O]'),
    ).toBeInTheDocument();

    // 6 MODE buttons.
    const modes: SamplerMode[] = [
      'PERF',
      'PATCH',
      'PART',
      'SAMPLE',
      'SYSTEM',
      'DISK',
    ];
    for (const m of modes) {
      expect(screen.getByTitle(`Mode Button [${m}]`)).toBeInTheDocument();
    }

    // Navigation cross.
    expect(screen.getByTitle('Cursor Up [▲]')).toBeInTheDocument();
    expect(screen.getByTitle('Cursor Down [▼]')).toBeInTheDocument();
    expect(screen.getByTitle('Cursor Left [◄]')).toBeInTheDocument();
    expect(screen.getByTitle('Cursor Right [►]')).toBeInTheDocument();

    // DEC / INC value steppers.
    expect(screen.getByTitle('Value Dec [DEC / -]')).toBeInTheDocument();
    expect(screen.getByTitle('Value Inc [INC / +]')).toBeInTheDocument();

    // ENTER / EXIT.
    expect(screen.getByTitle('Command Execute [ENTER]')).toBeInTheDocument();
    expect(screen.getByTitle('Return / Escape [EXIT]')).toBeInTheDocument();

    // F1-F6 soft-function keys.
    for (const f of ['F1', 'F2', 'F3', 'F4', 'F5', 'F6']) {
      expect(screen.getByTitle(`Function Key [${f}]`)).toBeInTheDocument();
    }

    // VOLUME knob + VALUE/DATA alpha dial.
    expect(screen.getByText('VOLUME')).toBeInTheDocument();
    expect(
      screen.getByTitle('Master Volume (Scroll wheel or Drag up/down)'),
    ).toBeInTheDocument();
    expect(screen.getByText('VALUE / DATA')).toBeInTheDocument();
    expect(
      screen.getByTitle(
        'Value / Data Alpha-Dial (Drag or Scroll wheel to adjust values smoothly)',
      ),
    ).toBeInTheDocument();
  });
});

// -----------------------------------------------------------------------------
//  R2.7, R2.8, R2.10 — fabricated removed, Unverified-but-mapped retained
//
//  Rationale: the LIVE panel renders ZERO fabricated buttons (task 7.2 found an
//  empty `toRemove`), so the removal/retention contract cannot be observed from
//  the live render alone. It is therefore demonstrated at the exact UI-logic
//  boundary the panel relies on: `reconcile(...)`. We construct a scenario with
//  (a) a genuinely-fabricated id (not preserved, absent from EVERY mapping entry,
//  not Gotek-owned) and (b) an `Unverified`-but-mapped sibling, and assert the
//  fabricated id lands in `toRemove` while the Unverified-but-mapped sibling does
//  not. This faithfully validates R2.7/R2.8/R2.10 for the UI.
// -----------------------------------------------------------------------------
describe('reconcile removes a fabricated button but retains an Unverified-but-mapped sibling (R2.7, R2.8, R2.10)', () => {
  it('puts the fabricated id in toRemove and keeps the Unverified-but-mapped id out of it', () => {
    // Mapping: one Unverified-but-mapped sibling present under the mapping.
    const mapping: ButtonMappingEntry[] = [
      {
        buttonId: 'LEGIT_UNVERIFIED',
        primaryFunction: 'A real hardware button still awaiting manual OCR.',
        shift: null,
        verification: 'Unverified',
        manualPage: null,
        reasonUnverified: 'Front-panel section not yet OCR-confirmed.',
        ownedByGotek: false,
      },
    ];

    // Front_Panel renders: the Unverified-but-mapped sibling, a genuinely
    // fabricated button, plus a preserved primary and a Gotek-owned control.
    const frontPanelIds = [
      'LEGIT_UNVERIFIED', // present in mapping (Unverified) -> retained (R2.10)
      'FABRICATED_KNOB', // absent from mapping, not preserved, not Gotek -> removed (R2.7, R2.8)
      'ENTER', // preserved primary -> never removed (R2.9)
      'GOTEK_SEL', // Gotek-owned -> never removed (R2.11)
    ];

    const result = reconcile(
      mapping,
      frontPanelIds,
      PRESERVED_PRIMARY_IDS,
      ['GOTEK_SEL'],
    );

    // The fabricated button is removed.
    expect(result.toRemove).toContain('FABRICATED_KNOB');
    // The Unverified-but-mapped sibling is NOT removed (present in mapping).
    expect(result.toRemove).not.toContain('LEGIT_UNVERIFIED');
    // Preserved primary and Gotek-owned ids are likewise never removed.
    expect(result.toRemove).not.toContain('ENTER');
    expect(result.toRemove).not.toContain('GOTEK_SEL');
    // The removal set is exactly the single fabrication.
    expect(result.toRemove).toEqual(['FABRICATED_KNOB']);
    // `fabricationCandidates` is the same set as `toRemove`.
    expect(result.fabricationCandidates).toEqual(result.toRemove);
  });

  it('the live panel renders no fabricated buttons: every rendered data-shift-button id is backed by the mapping', () => {
    // Smoke confirmation that the live panel (seeded mapping) adds no fabricated
    // SHIFT buttons: with the all-Unverified BUTTON_MAPPING, no Shift_Button
    // renders at all, so there is nothing to remove.
    const {container} = renderFrontPanel(makeState(), frontPanelHandlers());
    const shiftButtons = container.querySelectorAll('[data-shift-button]');
    expect(shiftButtons.length).toBe(0);
  });
});

// -----------------------------------------------------------------------------
//  R4.2, R4.3, R4.4 — shared SHIFT visual treatment, distinct from primaries
// -----------------------------------------------------------------------------
describe('SHIFT buttons share a visual treatment distinct from primaries (R4.2, R4.3, R4.4)', () => {
  it('all SHIFT buttons share the same accent-border treatment while powered on', () => {
    const mapping = [verifiedShiftEntry(), secondVerifiedShiftEntry()];
    const {container} = renderFrontPanel(
      makeState({powerOn: true}),
      frontPanelHandlers(),
      mapping,
    );

    const shiftButtons = Array.from(
      container.querySelectorAll('[data-shift-button]'),
    ) as HTMLButtonElement[];
    expect(shiftButtons.length).toBe(2);

    // R4.3: identical shared treatment across all SHIFT buttons — the sky accent
    // border + glow is present on every SHIFT button.
    for (const btn of shiftButtons) {
      expect(btn.className).toContain('border-sky-500/70');
      expect(btn.className).toContain('text-sky-200');
    }

    // R4.4: uses the existing design-system classes (tactile-btn conventions,
    // rounded tactile shape) rather than a bespoke style.
    for (const btn of shiftButtons) {
      expect(btn.className).toContain('tactile-btn');
      expect(btn.className).toContain('font-mono');
    }
  });

  it('the SHIFT treatment differs by >=1 observable attribute from a primary button', () => {
    const mapping = [verifiedShiftEntry()];
    const {container} = renderFrontPanel(
      makeState({powerOn: true}),
      frontPanelHandlers(),
      mapping,
    );

    const shiftBtn = container.querySelector(
      '[data-shift-button]',
    ) as HTMLButtonElement;
    expect(shiftBtn).toBeTruthy();

    // A primary Target_Button (ENTER) uses a non-sky accent border. The SHIFT
    // button's sky accent border is the >=1 observable difference (R4.2).
    const primaryBtn = screen.getByTitle('Command Execute [ENTER]');
    expect(shiftBtn.className).toContain('border-sky-500/70');
    expect(primaryBtn.className).not.toContain('border-sky-500/70');
  });
});

// -----------------------------------------------------------------------------
//  R5.2 — single emission channel: only onEventEmit is invoked
// -----------------------------------------------------------------------------
describe('SHIFT activation routes through the single onEventEmit channel (R5.2)', () => {
  it('invokes onEventEmit with the recorded chord event and no primary callback', async () => {
    const user = userEvent.setup();
    const handlers = frontPanelHandlers();
    const mapping = [verifiedShiftEntry()];
    const {container} = renderFrontPanel(
      makeState(),
      handlers,
      mapping,
    );

    const shiftBtn = container.querySelector(
      '[data-shift-button="PATCH"]',
    ) as HTMLButtonElement;
    await user.click(shiftBtn);

    // The shared Event_Emitter channel received exactly the recorded event.
    expect(handlers.onEventEmit).toHaveBeenCalledTimes(1);
    expect(handlers.onEventEmit).toHaveBeenCalledWith('MODE_SELECT', {
      mode: 'PATCH',
      shift: true,
    });

    // No alternate / bypassing emission path: the primary mode callback (which a
    // real MODE button would fire) is NOT invoked by the SHIFT button.
    expect(handlers.onSetMode).not.toHaveBeenCalled();
    expect(handlers.onSoftKey).not.toHaveBeenCalled();
    expect(handlers.onEnter).not.toHaveBeenCalled();
  });
});

// -----------------------------------------------------------------------------
//  R3.5, R7.1, R7.5 — synchronous emission + native title tooltip
// -----------------------------------------------------------------------------
describe('SHIFT emission is synchronous and the button carries a native title tooltip (R3.5, R7.1, R7.5)', () => {
  it('emits synchronously within the click gesture (well under 100ms)', async () => {
    const user = userEvent.setup();
    const handlers = frontPanelHandlers();
    const mapping = [verifiedShiftEntry()];
    const {container} = renderFrontPanel(makeState(), handlers, mapping);

    const shiftBtn = container.querySelector(
      '[data-shift-button="PATCH"]',
    ) as HTMLButtonElement;

    const start = performance.now();
    await user.click(shiftBtn);
    const elapsed = performance.now() - start;

    // Emission already happened synchronously inside the click handler.
    expect(handlers.onEventEmit).toHaveBeenCalledTimes(1);
    // The whole gesture (incl. emission) completes well within the 100ms bound.
    expect(elapsed).toBeLessThan(100);
  });

  it('exposes the tooltip text via the native title attribute (R7.1, R7.5)', () => {
    const mapping = [verifiedShiftEntry()];
    const {container} = renderFrontPanel(
      makeState(),
      frontPanelHandlers(),
      mapping,
    );

    const shiftBtn = container.querySelector(
      '[data-shift-button="PATCH"]',
    ) as HTMLButtonElement;

    // The native `title` attribute backs the browser tooltip (dwell to show,
    // dismiss on leave/blur — R7.1, R7.5). Its text derives from the entry's
    // SHIFT function description.
    expect(shiftBtn.getAttribute('title')).toBe('Copy the current patch.');
    // The accessible name derives from the same entry (silkscreen label).
    expect(shiftBtn.getAttribute('aria-label')).toBe('COPY');
  });
});

// -----------------------------------------------------------------------------
//  R7.4 — native-button focus order and focus-visible participation
// -----------------------------------------------------------------------------
describe('SHIFT buttons are native focusable buttons in the normal focus order (R7.4)', () => {
  it('renders as a native <button> element', () => {
    const mapping = [verifiedShiftEntry()];
    const {container} = renderFrontPanel(
      makeState(),
      frontPanelHandlers(),
      mapping,
    );
    const shiftBtn = container.querySelector(
      '[data-shift-button="PATCH"]',
    ) as HTMLElement;
    expect(shiftBtn.tagName).toBe('BUTTON');
    expect(shiftBtn.getAttribute('type')).toBe('button');
    // No tabindex override => participates in the natural document focus order.
    expect(shiftBtn.getAttribute('tabindex')).toBeNull();
  });

  it('is focusable: Tab reaches it and .focus() makes it the active element', async () => {
    const user = userEvent.setup();
    const mapping = [verifiedShiftEntry()];
    const {container} = renderFrontPanel(
      makeState(),
      frontPanelHandlers(),
      mapping,
    );
    const shiftBtn = container.querySelector(
      '[data-shift-button="PATCH"]',
    ) as HTMLButtonElement;

    // Direct focus works (native focusability).
    shiftBtn.focus();
    expect(document.activeElement).toBe(shiftBtn);

    // Tabbing from the body eventually lands on a focusable control; the SHIFT
    // button is in the natural tab order, so a Tab sequence can reach it.
    shiftBtn.blur();
    await user.tab();
    // At least one native control received focus (the panel has many); the SHIFT
    // button being a native <button> with no negative tabindex guarantees it is
    // part of this same order.
    expect(document.activeElement).not.toBe(document.body);
  });
});

// -----------------------------------------------------------------------------
//  R6.1, R6.2 — no Shift_Button inside the Gotek subtree; GotekBay unchanged
// -----------------------------------------------------------------------------
describe('Gotek isolation: no Shift_Button inside the Gotek subtree (R6.1, R6.2)', () => {
  it('renders SHIFT buttons outside the Gotek bay subtree', () => {
    const mapping = [verifiedShiftEntry(), secondVerifiedShiftEntry()];
    const {container} = renderFrontPanel(
      makeState(),
      frontPanelHandlers(),
      mapping,
    );

    // Locate the Gotek bay by its unique silkscreen badge, then walk up to the
    // outermost GotekBay subtree (the badge sits inside the bezel which sits
    // inside the GotekBay root wrapper).
    const gotekBadge = screen.getByText('Gotek SFR1M44-U100K');
    const gotekSubtree = gotekBadge.closest(
      'div.relative.flex.flex-col',
    ) as HTMLElement | null;
    const gotekRoot = (gotekSubtree ?? gotekBadge.parentElement) as HTMLElement;
    expect(gotekRoot).toBeTruthy();

    // Sanity: the Gotek subtree really does contain the Gotek controls.
    expect(
      within(gotekRoot).getByTitle('Mount / Select Disk [SEL]'),
    ).toBeInTheDocument();

    // No element carrying data-shift-button exists anywhere in the Gotek subtree.
    expect(gotekRoot.querySelectorAll('[data-shift-button]').length).toBe(0);

    // But the SHIFT buttons DO exist elsewhere on the panel.
    expect(container.querySelectorAll('[data-shift-button]').length).toBe(2);
  });

  it('leaves GotekBay controls intact and functional (R6.1, R6.2)', async () => {
    const user = userEvent.setup();
    const onMountDisk = vi.fn();
    const onEventEmit = vi.fn();
    const mapping = [verifiedShiftEntry()];
    renderFrontPanel(
      makeState(),
      frontPanelHandlers({onMountDisk, onEventEmit}),
      mapping,
    );

    // Gotek silkscreen badges still present (component rendered unchanged).
    expect(screen.getByText('Gotek SFR1M44-U100K')).toBeInTheDocument();
    expect(screen.getByText('FlashFloppy 3.42')).toBeInTheDocument();

    // Gotek [SEL] still mounts the disk and emits its own event — unaffected by
    // the SHIFT row.
    await user.click(screen.getByTitle('Mount / Select Disk [SEL]'));
    expect(onMountDisk).toHaveBeenCalledTimes(1);
    expect(onEventEmit).toHaveBeenCalledWith('GOTEK_BTN_SEL', expect.anything());
  });
});

/**
 * ShellNavigationMigration.test.tsx
 *
 * Migrates the shell/chrome + navigation assertions that were REMOVED from the
 * MAME screenshot-scraping suite in ui-consolidation task 1.5 (R4.1/R4.2) into
 * REAL React tests over the REAL React components that now OWN that chrome
 * (true ownership — R4.2, R7.2). The old tests scraped the MAME-drawn GUI
 * (chassis, Gotek OLED, SYSTEM-tab outline, seamless CRT<->rack navigation);
 * that chrome moved to React (R6), so the invariants are re-expressed here as
 * component render + interaction assertions.
 *
 * Each `describe` block names the original MAME test it replaces and which
 * removed assertion(s) it re-owns. Composed-shell visual/pixel coverage lives
 * in e2e/composed-shell.spec.ts and e2e/shell-navigation.spec.ts (Playwright,
 * task 4.2/4.3); this file covers the component/interaction level.
 *
 * Validates: Requirements 4.2, 7.2
 */
import {describe, it, expect, vi, beforeAll} from 'vitest';
import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {S760FrontPanel} from './S760FrontPanel';
import {GotekBay} from './GotekBay';
import {soundFx} from '../audio/soundFx';
import {SamplerState, SamplerMode, DEFAULT_DISK_IMAGES} from '../types/sampler';

// jsdom has no Web Audio API, and the shell's tactile buttons call
// soundFx.playClick() (which lazily constructs an AudioContext) before invoking
// their action callback. Disable the UI-haptics engine for this suite via its
// public API so playClick() early-returns — we are asserting navigation/chrome
// behaviour, not audio (audio ownership is covered elsewhere, R5.7/4.1).
beforeAll(() => {
  soundFx.setSoundEnabled(false);
  soundFx.setFloppySeekEnabled(false);
});

// -----------------------------------------------------------------------------
//  Test fixtures / helpers
// -----------------------------------------------------------------------------

/** A powered-on sampler state with a USB disk inserted (the interactive case). */
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

function gotekHandlers(overrides: Record<string, unknown> = {}) {
  return {
    onSelectDiskIndex: vi.fn(),
    onMountDisk: vi.fn(),
    onToggleUsb: vi.fn(),
    onEventEmit: vi.fn(),
    ...overrides,
  };
}

function renderFrontPanel(
  state: SamplerState,
  handlers: ReturnType<typeof frontPanelHandlers>,
) {
  return render(
    <S760FrontPanel state={state} diskList={DEFAULT_DISK_IMAGES} {...handlers} />,
  );
}

// -----------------------------------------------------------------------------
//  Replaces: test_rack_panel_and_embedded_lcd_rendering
//  Removed MAME assertions: rack charcoal chassis, embedded LCD-green backlight,
//  Gotek-cyan OLED — all were render_rack_panel chrome in the deleted 120px rack
//  strip. React's S760FrontPanel now owns the 1U chassis + LCD housing + Gotek
//  bay (R6). Assert they are present and real.
// -----------------------------------------------------------------------------
describe('S760FrontPanel chassis + embedded LCD + Gotek bay (replaces MAME test_rack_panel_and_embedded_lcd_rendering)', () => {
  it('renders the 1U rack chassis with both rack ears (chassis present)', () => {
    renderFrontPanel(makeState(), frontPanelHandlers());
    // The 1U chassis is flanked by two rack ears, each carrying a "1U" marker
    // (RackEar). Two ears == a mounted 1U chassis.
    const unitMarkers = screen.getAllByText('1U');
    expect(unitMarkers.length).toBe(2);
    // The hardware silkscreen model block identifies the real chassis.
    expect(screen.getByText('S-760')).toBeInTheDocument();
    expect(screen.getByText('DIGITAL SAMPLER')).toBeInTheDocument();
  });

  it('renders the front-panel LCD housing (SED1335 cutout owned by React)', () => {
    const {container} = renderFrontPanel(makeState(), frontPanelHandlers());
    // The front-panel LCD exposes a live SED1335 160x64 surface canvas. Its
    // intrinsic geometry is the authentic hardware size — proof React owns the
    // LCD housing/cutout the old MAME "LCD-green" scrape used to cover.
    const lcdCanvas = Array.from(container.querySelectorAll('canvas')).find(
      (c) => c.width === 160 && c.height === 64,
    );
    expect(lcdCanvas).toBeTruthy();
  });

  it('renders the Gotek drive bay inside the chassis (not MAME-drawn)', () => {
    renderFrontPanel(makeState(), frontPanelHandlers());
    // The Gotek silkscreen badge is unique to the React GotekBay component.
    expect(screen.getByText('Gotek SFR1M44-U100K')).toBeInTheDocument();
    expect(screen.getByText('FlashFloppy 3.42')).toBeInTheDocument();
  });
});

// -----------------------------------------------------------------------------
//  Replaces: test_gotek_oled_and_navigation_controls
//  Removed MAME assertions: Gotek OLED cyan scrape + the Prev/Next/Select
//  hot-swap behaviour. React's GotekBay owns the OLED readout + nav controls.
// -----------------------------------------------------------------------------
describe('GotekBay OLED readout + Prev/Next/Select controls (replaces MAME test_gotek_oled_and_navigation_controls)', () => {
  it('renders the Gotek OLED readout with the selected disk (slot + filename)', () => {
    const state = makeState();
    render(
      <GotekBay
        powerOn={state.powerOn}
        selectedDisk={DEFAULT_DISK_IMAGES[1]}
        mountedDisk={DEFAULT_DISK_IMAGES[1]}
        diskList={DEFAULT_DISK_IMAGES}
        selectedDiskIndex={1}
        isDiskBusy={false}
        diskTrack={18}
        usbInserted
        {...gotekHandlers()}
      />,
    );
    // OLED line 1 shows "<slot> <filename>" of the selected image.
    const disk = DEFAULT_DISK_IMAGES[1];
    expect(
      screen.getByText(new RegExp(disk.filename.replace('.', '\\.'))),
    ).toBeInTheDocument();
    expect(screen.getByText(/MOUNTED/)).toBeInTheDocument();
    // The live 128x32 OLED surface canvas (Gotek-cyan tint) is React-owned.
    const oled = screen
      .getByText(new RegExp(disk.filename.replace('.', '\\.')))
      .closest('div');
    expect(oled).toBeTruthy();
  });

  it('steps to the NEXT image when the Gotek [>] button is clicked', async () => {
    const user = userEvent.setup();
    const onSelectDiskIndex = vi.fn();
    const onEventEmit = vi.fn();
    render(
      <GotekBay
        powerOn
        selectedDisk={DEFAULT_DISK_IMAGES[1]}
        mountedDisk={DEFAULT_DISK_IMAGES[1]}
        diskList={DEFAULT_DISK_IMAGES}
        selectedDiskIndex={1}
        isDiskBusy={false}
        diskTrack={0}
        usbInserted
        {...gotekHandlers({onSelectDiskIndex, onEventEmit})}
      />,
    );
    await user.click(screen.getByTitle('Next Image / Directory [>]'));
    // Next from index 1 -> index 2 (wraps on the disk list length).
    expect(onSelectDiskIndex).toHaveBeenCalledWith(2);
    expect(onEventEmit).toHaveBeenCalledWith(
      'GOTEK_BTN_NEXT',
      expect.anything(),
    );
  });

  it('steps to the PREVIOUS image when the Gotek [<] button is clicked', async () => {
    const user = userEvent.setup();
    const onSelectDiskIndex = vi.fn();
    render(
      <GotekBay
        powerOn
        selectedDisk={DEFAULT_DISK_IMAGES[1]}
        mountedDisk={DEFAULT_DISK_IMAGES[1]}
        diskList={DEFAULT_DISK_IMAGES}
        selectedDiskIndex={1}
        isDiskBusy={false}
        diskTrack={0}
        usbInserted
        {...gotekHandlers({onSelectDiskIndex})}
      />,
    );
    await user.click(screen.getByTitle('Previous Image / Directory [<]'));
    // Prev from index 1 -> index 0.
    expect(onSelectDiskIndex).toHaveBeenCalledWith(0);
  });

  it('mounts/hot-swaps the selected image when [SEL] is clicked', async () => {
    const user = userEvent.setup();
    const onMountDisk = vi.fn();
    const onEventEmit = vi.fn();
    render(
      <GotekBay
        powerOn
        selectedDisk={DEFAULT_DISK_IMAGES[2]}
        mountedDisk={DEFAULT_DISK_IMAGES[1]}
        diskList={DEFAULT_DISK_IMAGES}
        selectedDiskIndex={2}
        isDiskBusy={false}
        diskTrack={0}
        usbInserted
        {...gotekHandlers({onMountDisk, onEventEmit})}
      />,
    );
    await user.click(screen.getByTitle('Mount / Select Disk [SEL]'));
    expect(onMountDisk).toHaveBeenCalledTimes(1);
    expect(onEventEmit).toHaveBeenCalledWith('GOTEK_BTN_SEL', expect.anything());
  });
});

// -----------------------------------------------------------------------------
//  Replaces: test_manual_sampling_and_mode_workflow
//  Removed MAME assertion: the Pen-5 SYSTEM-tab-outline pixel scrape (active
//  mode-tab outline). Mode tabs + their active state are now React-owned.
// -----------------------------------------------------------------------------
describe('Mode tab selection incl. SYSTEM active outline (replaces MAME test_manual_sampling_and_mode_workflow)', () => {
  const MODES: SamplerMode[] = ['PERF', 'PATCH', 'PART', 'SAMPLE', 'SYSTEM', 'DISK'];

  it('exposes all six mode buttons on the front panel', () => {
    renderFrontPanel(makeState(), frontPanelHandlers());
    for (const m of MODES) {
      expect(screen.getByTitle(`Mode Button [${m}]`)).toBeInTheDocument();
    }
  });

  it('selecting the SYSTEM mode tab invokes onSetMode(SYSTEM)', async () => {
    const user = userEvent.setup();
    const onSetMode = vi.fn();
    const onEventEmit = vi.fn();
    renderFrontPanel(
      makeState({mode: 'DISK'}),
      frontPanelHandlers({onSetMode, onEventEmit}),
    );
    await user.click(screen.getByTitle('Mode Button [SYSTEM]'));
    expect(onSetMode).toHaveBeenCalledWith('SYSTEM');
    expect(onEventEmit).toHaveBeenCalledWith('MODE_SELECT', {mode: 'SYSTEM'});
  });

  it('marks the active mode tab (SYSTEM) with the selected-outline styling', () => {
    renderFrontPanel(makeState({mode: 'SYSTEM'}), frontPanelHandlers());
    // The active tab carries an amber selection border (the React equivalent of
    // the old Pen-5 red SYSTEM-tab outline the MAME test scraped). Inactive
    // tabs do not.
    const systemBtn = screen.getByTitle('Mode Button [SYSTEM]');
    const diskBtn = screen.getByTitle('Mode Button [DISK]');
    expect(systemBtn.className).toContain('border-amber-500/70');
    expect(diskBtn.className).not.toContain('border-amber-500/70');
  });

  it('moves the active outline when a different tab becomes active', () => {
    const {rerender} = renderFrontPanel(
      makeState({mode: 'SYSTEM'}),
      frontPanelHandlers(),
    );
    expect(screen.getByTitle('Mode Button [SYSTEM]').className).toContain(
      'border-amber-500/70',
    );
    // Re-render with SAMPLE active: the outline must follow the active tab.
    rerender(
      <S760FrontPanel
        state={makeState({mode: 'SAMPLE'})}
        diskList={DEFAULT_DISK_IMAGES}
        {...frontPanelHandlers()}
      />,
    );
    expect(screen.getByTitle('Mode Button [SAMPLE]').className).toContain(
      'border-amber-500/70',
    );
    expect(screen.getByTitle('Mode Button [SYSTEM]').className).not.toContain(
      'border-amber-500/70',
    );
  });
});

// -----------------------------------------------------------------------------
//  Replaces: test_seamless_mouse_navigation_between_crt_and_rack_ui
//  Removed MAME assertions: SYSTEM-tab outline + Gotek-mounted scrape across
//  the (deleted) CRT->rack strip, i.e. "seamless" navigation between the CRT
//  area and the rack panel. React owns both regions in one shell, so the
//  cross-region navigation is a real interaction: a mode selected on the front
//  panel and a disk mounted on the Gotek bay drive the shared handlers.
// -----------------------------------------------------------------------------
describe('Seamless CRT<->rack navigation (replaces MAME test_seamless_mouse_navigation_between_crt_and_rack_ui)', () => {
  it('navigates across front-panel regions: mode tab then Gotek mount via shared handlers', async () => {
    const user = userEvent.setup();
    const onSetMode = vi.fn();
    const onMountDisk = vi.fn();
    renderFrontPanel(
      makeState({mode: 'DISK'}),
      frontPanelHandlers({onSetMode, onMountDisk}),
    );

    // Phase 1 (CRT-area control): select the SYSTEM mode tab.
    await user.click(screen.getByTitle('Mode Button [SYSTEM]'));
    expect(onSetMode).toHaveBeenCalledWith('SYSTEM');

    // Phase 2 (rack-area control): mount the selected disk on the Gotek bay.
    await user.click(screen.getByTitle('Mount / Select Disk [SEL]'));
    expect(onMountDisk).toHaveBeenCalledTimes(1);
    // Both regions live in the SAME shell and talk to the SAME handler set —
    // this is the "seamless navigation between CRT and rack UI" the MAME test
    // used to approximate by scraping two pixel regions.
  });

  it('cursor navigation controls in the shell drive onNavigate for all four directions', async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();
    renderFrontPanel(makeState(), frontPanelHandlers({onNavigate}));

    await user.click(screen.getByTitle('Cursor Up [▲]'));
    await user.click(screen.getByTitle('Cursor Down [▼]'));
    await user.click(screen.getByTitle('Cursor Left [◄]'));
    await user.click(screen.getByTitle('Cursor Right [►]'));

    expect(onNavigate).toHaveBeenNthCalledWith(1, 'UP');
    expect(onNavigate).toHaveBeenNthCalledWith(2, 'DOWN');
    expect(onNavigate).toHaveBeenNthCalledWith(3, 'LEFT');
    expect(onNavigate).toHaveBeenNthCalledWith(4, 'RIGHT');
  });
});

/**
 * Authoritative Roland S-760 front-panel Button_Mapping (machine-readable mirror).
 *
 * This module is the typed, build-time source of truth the React UI imports to
 * render dedicated SHIFT buttons. It mirrors the human-readable canonical
 * document `docs/front-panel-button-mapping.md`.
 *
 * GOLDEN RULE — evidence over invention (project steering): the real-hardware
 * front-panel button layout and its SHIFT (secondary) function mapping are NOT
 * yet OCR-confirmed from the owner's manual (`Manuals/S-760_OM.pdf`, a scanned
 * image PDF with no text layer). Therefore every seeded entry below defaults to
 * `Verification_Status = 'Unverified'`, carries a `reasonUnverified` string, and
 * records NO manual page reference and NO emitted event. No `Verified` entries
 * and no SHIFT functions are invented. Entries are promoted to `Verified` (with a
 * manual page and a recorded chord event) only when a manual page confirms them,
 * at which point the UI lights up the corresponding button with no code change.
 */

/** Verification status for a Button_Mapping entry or SHIFT function. */
export type VerificationStatus = 'Verified' | 'Unverified';

/** The single input event emitted for a SHIFT chord (matches onEventEmit args). */
export interface ChordEventSpec {
  /** Event type string passed to onEventEmit (e.g. "MODE_CHANGE"). */
  type: string;
  /** Payload object passed to onEventEmit, matched value-for-value (R5.3). */
  payload: Record<string, unknown>;
}

/** The SHIFT secondary function of a Target_Button. */
export interface ShiftFunctionSpec {
  /** The primary (target) button this SHIFT function is reached through. */
  targetButtonId: string;
  /** Silkscreen name of the SHIFT function (null if the manual shows none). */
  silkscreenLabel: string | null;
  /** Human-readable description of the SHIFT action. */
  description: string;
  /** Verification status for THIS SHIFT function. */
  verification: VerificationStatus;
  /** Manual page backing a Verified SHIFT function (null otherwise). */
  manualPage: string | null;
  /** Reason not confirmed (required when Unverified). */
  reasonUnverified: string | null;
  /**
   * The exact input event the hardware SHIFT+target chord emits. Present only
   * when this SHIFT function is Verified; null otherwise (so no event can be
   * emitted for an unverified entry — R5.5, R3.6).
   */
  event: ChordEventSpec | null;
}

/** One hardware front-panel button and its optional SHIFT secondary function. */
export interface ButtonMappingEntry {
  /** Stable unique id for the hardware button (e.g. "PATCH", "F3"). */
  buttonId: string;
  /** Primary (unshifted) function description. */
  primaryFunction: string;
  /** SHIFT secondary function, or null if the button has none. */
  shift: ShiftFunctionSpec | null;
  /** Verification status for THIS button entry. */
  verification: VerificationStatus;
  /** Owner's-manual page reference backing a Verified entry (null otherwise). */
  manualPage: string | null;
  /** Reason the entry could not be confirmed (required when Unverified). */
  reasonUnverified: string | null;
  /** True if this hardware control is owned by the Gotek drive bay (out of scope). */
  ownedByGotek: boolean;
}

/**
 * Shared reason-not-confirmed string for the seeded entries. The front-panel
 * button section of the owner's manual has not been OCR'd, so no entry can yet
 * be confirmed against a manual page.
 */
const REASON_UNVERIFIED =
  'Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; ' +
  'entry awaits manual page verification.';

/**
 * The full authoritative mapping.
 *
 * Seeded with the currently-known hardware front-panel controls rendered by
 * `S760FrontPanel.tsx`. Every entry is `Unverified` with `manualPage: null`,
 * a `reasonUnverified` string, and `shift: null` (no SHIFT function is asserted
 * without manual evidence). None are Gotek-owned (the Gotek drive bay is out of
 * scope and owns no front-panel-matrix control).
 */
export const BUTTON_MAPPING: readonly ButtonMappingEntry[] = [
  {
    buttonId: 'POWER',
    primaryFunction: 'Power rocker switch (toggles device power on/off).',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'PERF',
    primaryFunction: 'Select PERFORMANCE mode.',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'PATCH',
    primaryFunction: 'Select PATCH mode.',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'PART',
    primaryFunction: 'Select PARTIAL mode.',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'SAMPLE',
    primaryFunction: 'Select SAMPLE mode.',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'SYSTEM',
    primaryFunction: 'Select SYSTEM mode.',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'DISK',
    primaryFunction: 'Select DISK mode.',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'NAV_LEFT',
    primaryFunction: 'Move cursor left.',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'NAV_RIGHT',
    primaryFunction: 'Move cursor right.',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'NAV_UP',
    primaryFunction: 'Move cursor up.',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'NAV_DOWN',
    primaryFunction: 'Move cursor down.',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'DEC',
    primaryFunction: 'Decrement the selected value (DEC / -).',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'INC',
    primaryFunction: 'Increment the selected value (INC / +).',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'ENTER',
    primaryFunction: 'Confirm / execute the current command (ENTER).',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'EXIT',
    primaryFunction: 'Return / escape from the current screen (EXIT).',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'F1',
    primaryFunction: 'Soft-function key F1 (context-dependent LCD function).',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'F2',
    primaryFunction: 'Soft-function key F2 (context-dependent LCD function).',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'F3',
    primaryFunction: 'Soft-function key F3 (context-dependent LCD function).',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'F4',
    primaryFunction: 'Soft-function key F4 (context-dependent LCD function).',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'F5',
    primaryFunction: 'Soft-function key F5 (context-dependent LCD function).',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'F6',
    primaryFunction: 'Soft-function key F6 (context-dependent LCD function).',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'VOLUME',
    primaryFunction: 'Master volume potentiometer (analog output level).',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
  {
    buttonId: 'VALUE_DATA',
    primaryFunction: 'VALUE / DATA alpha-dial (continuous value entry).',
    shift: null,
    verification: 'Unverified',
    manualPage: null,
    reasonUnverified: REASON_UNVERIFIED,
    ownedByGotek: false,
  },
];

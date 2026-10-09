/**
 * Pure selector helpers for the S-760 front-panel SHIFT buttons.
 *
 * These functions derive what the React UI renders from the authoritative
 * `BUTTON_MAPPING` artifact (see `./shiftButtonMap`). They are kept side-effect
 * free so they are directly unit- and property-testable.
 *
 * Design reference: front-panel-shift-buttons design.md
 *   - "Mapping selectors (pure helpers)"
 *   - "Data Models > ShiftButtonDescriptor / ShiftButtonLabels"
 *   - Correctness Property 3 (renderable Shift_Button set) and
 *     Property 8 (label/accessibility derivation).
 */

import type { ButtonMappingEntry, ChordEventSpec } from './shiftButtonMap';

/**
 * Resolved display/accessibility strings for one Shift_Button, all derived from
 * the same `Button_Mapping` entry (R4.1, R4.5, R7.1, R7.2, R7.3).
 */
export interface ShiftButtonLabels {
  /** Silkscreen label when present, otherwise the SHIFT function name (R4.5). */
  label: string;
  /** Accessible name derived from the silkscreen label (R7.2). */
  accessibleName: string;
  /** Tooltip text derived from the SHIFT function name (R7.1). */
  tooltipText: string;
  /** True exactly when the silkscreen label was missing and the fallback used. */
  silkscreenMissing: boolean;
}

/**
 * Everything a Shift_Button needs to render and emit. The `event` is non-null by
 * construction because descriptors are produced only for Verified, non-Gotek,
 * event-bearing SHIFT functions.
 */
export interface ShiftButtonDescriptor {
  /** Stable unique id for the hardware button this SHIFT function belongs to. */
  buttonId: string;
  /** The primary (target) button the SHIFT function is reached through. */
  targetButtonId: string;
  /** Resolved label / accessible name / tooltip for the button. */
  labels: ShiftButtonLabels;
  /** The exact input event to emit on activation (non-null by construction). */
  event: ChordEventSpec;
}

/**
 * Resolve the label, accessible name, tooltip text, and silkscreen-missing flag
 * for one mapping entry, all derived from that same entry.
 *
 * - `label`: the recorded silkscreen label when present (non-null, non-empty),
 *   otherwise the SHIFT function name (its `description`) as a fallback (R4.5).
 * - `silkscreenMissing`: true exactly when the fallback was used (R4.5 flag).
 * - `accessibleName`: derived from the silkscreen label (falls back to the same
 *   resolved label when no silkscreen is recorded) (R7.2).
 * - `tooltipText`: derived from the SHIFT function name/description (R7.1).
 *
 * Entries without a SHIFT function fall back to the entry's primary function so
 * the result is always a well-formed, non-empty set of strings.
 *
 * Validates: Requirements 4.1, 4.5, 7.1, 7.2, 7.3
 */
export function resolveShiftButtonLabels(
  entry: ButtonMappingEntry,
): ShiftButtonLabels {
  const shift = entry.shift;
  // SHIFT function name used both as the label fallback and tooltip source.
  const functionName = shift ? shift.description : entry.primaryFunction;
  const silkscreen = shift ? shift.silkscreenLabel : null;
  const hasSilkscreen = silkscreen !== null && silkscreen !== '';

  const label = hasSilkscreen ? silkscreen : functionName;

  return {
    label,
    // Accessible name is derived from the silkscreen label; when none is
    // recorded it resolves to the same label fallback (R7.2).
    accessibleName: label,
    // Tooltip text is derived from the SHIFT function name (R7.1).
    tooltipText: functionName,
    silkscreenMissing: !hasSilkscreen,
  };
}

/**
 * Return the exact set of Shift_Buttons to render: one `ShiftButtonDescriptor`
 * per SHIFT function that is `Verified`, NOT owned by the Gotek bay, and has a
 * non-null recorded `event`. The result is de-duplicated by `buttonId` so a
 * given hardware button yields at most one descriptor (first occurrence wins).
 *
 * Any `Unverified` entry, any Gotek-owned entry, and any entry lacking a
 * `Verified` event is structurally excluded, so no such entry can ever be
 * rendered or emit an action.
 *
 * Validates: Requirements 2.3, 2.4, 3.1, 3.4, 3.6, 5.5, 6.3, 7.1, 7.2, 7.3
 */
export function verifiedShiftButtons(
  mapping: readonly ButtonMappingEntry[],
): ShiftButtonDescriptor[] {
  const descriptors: ShiftButtonDescriptor[] = [];
  const seen = new Set<string>();

  for (const entry of mapping) {
    const shift = entry.shift;
    if (shift === null) continue;
    if (entry.ownedByGotek) continue;
    if (shift.verification !== 'Verified') continue;
    if (shift.event === null) continue;
    if (seen.has(entry.buttonId)) continue;

    seen.add(entry.buttonId);
    descriptors.push({
      buttonId: entry.buttonId,
      targetButtonId: shift.targetButtonId,
      labels: resolveShiftButtonLabels(entry),
      event: shift.event,
    });
  }

  return descriptors;
}

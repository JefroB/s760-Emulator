/**
 * Property-based tests for the Shift_Button label/accessibility derivation.
 *
 * Property 8: Labels, accessible name, and tooltip derive consistently from the
 * entry.
 *
 * For any Button_Mapping entry, `resolveShiftButtonLabels(entry)` resolves the
 * `label`, `accessibleName`, `tooltipText`, and `silkscreenMissing` flag from
 * that same entry:
 *   - The resolved SHIFT function name is `shift.description` when a SHIFT
 *     function is present, otherwise the entry's `primaryFunction` fallback.
 *   - The recorded silkscreen is `shift.silkscreenLabel` when a SHIFT function
 *     is present, otherwise `null`.
 *   - A silkscreen "is present" exactly when it is non-null AND non-empty; so
 *     `silkscreenMissing` is true exactly when there is no non-empty silkscreen.
 *   - `label` equals the silkscreen when present, otherwise the function name.
 *   - `accessibleName` is derived from the same entry and equals the resolved
 *     `label`.
 *   - `tooltipText` is derived from the SHIFT function name.
 *
 * This test independently (re-)derives the expected strings from the raw
 * generated fields and asserts `resolveShiftButtonLabels` agrees on every
 * generated entry, pinning the selector to the Property 8 definition rather than
 * to its own implementation.
 *
 * Validates: Requirements 4.1, 4.5, 7.1, 7.2, 7.3
 */
import {describe, it, expect} from 'vitest';
import fc from 'fast-check';
import {resolveShiftButtonLabels} from './shiftButtonSelectors';
import type {
  ButtonMappingEntry,
  ShiftFunctionSpec,
  ChordEventSpec,
  VerificationStatus,
} from './shiftButtonMap';

/** Both legal statuses, so the generator exercises Verified and Unverified. */
const statusArb: fc.Arbitrary<VerificationStatus> = fc.constantFrom(
  'Verified',
  'Unverified',
);

/** A chord event (present variant), so `event` sometimes carries a value. */
const chordEventArb: fc.Arbitrary<ChordEventSpec> = fc.record({
  type: fc.string(),
  payload: fc.dictionary(fc.string(), fc.anything()),
});

/**
 * silkscreenLabel generator mixing the three cases Property 8 distinguishes:
 * null (no label), '' (empty => treated as missing), and a non-empty string
 * (present). The non-empty branch is weighted so present-silkscreen entries are
 * well represented.
 */
const silkscreenArb: fc.Arbitrary<string | null> = fc.oneof(
  fc.constant(null),
  fc.constant(''),
  fc.string({minLength: 1}),
);

/**
 * A SHIFT function arbitrary. `silkscreenLabel` uses the three-way generator so
 * both the silkscreen-present and silkscreen-missing branches are exercised.
 * `description` is non-empty so the function-name fallback is observable.
 */
const shiftArb: fc.Arbitrary<ShiftFunctionSpec> = fc.record({
  targetButtonId: fc.string(),
  silkscreenLabel: silkscreenArb,
  description: fc.string({minLength: 1}),
  verification: statusArb,
  manualPage: fc.option(fc.string({minLength: 1}), {nil: null}),
  reasonUnverified: fc.option(fc.string({minLength: 1}), {nil: null}),
  event: fc.option(chordEventArb, {nil: null}),
});

/**
 * An entry arbitrary. `shift` is null vs a generated SHIFT function so both the
 * with-shift and no-shift (primaryFunction fallback) branches are exercised.
 * `primaryFunction` is non-empty so the no-shift fallback is observable.
 */
const entryArb: fc.Arbitrary<ButtonMappingEntry> = fc.record({
  buttonId: fc.string(),
  primaryFunction: fc.string({minLength: 1}),
  shift: fc.option(shiftArb, {nil: null}),
  verification: statusArb,
  manualPage: fc.option(fc.string({minLength: 1}), {nil: null}),
  reasonUnverified: fc.option(fc.string({minLength: 1}), {nil: null}),
  ownedByGotek: fc.boolean(),
});

describe('resolveShiftButtonLabels — Property 8 (label/aria/tooltip derivation)', () => {
  it('derives label, accessibleName, tooltipText, and silkscreenMissing consistently from the entry', () => {
    fc.assert(
      fc.property(entryArb, (entry) => {
        // Reference derivation from the raw generated fields (R4.5, R7.1-R7.3).
        const shift = entry.shift;
        const expectedFunctionName = shift
          ? shift.description
          : entry.primaryFunction;
        const silkscreen = shift ? shift.silkscreenLabel : null;
        const hasSilkscreen = silkscreen !== null && silkscreen !== '';
        const expectedLabel = hasSilkscreen
          ? (silkscreen as string)
          : expectedFunctionName;

        const result = resolveShiftButtonLabels(entry);

        // silkscreenMissing is true exactly when there is no non-empty silkscreen.
        expect(result.silkscreenMissing).toBe(!hasSilkscreen);

        // label == silkscreen when present, else the SHIFT function name (R4.5).
        expect(result.label).toBe(expectedLabel);

        // accessibleName derives from the same entry and resolves to the label (R7.2).
        expect(result.accessibleName).toBe(expectedLabel);

        // tooltipText derives from the SHIFT function name (R7.1).
        expect(result.tooltipText).toBe(expectedFunctionName);

        // All resolved strings are well-formed strings derived from one entry (R4.1, R7.3).
        expect(typeof result.label).toBe('string');
        expect(typeof result.accessibleName).toBe('string');
        expect(typeof result.tooltipText).toBe('string');
      }),
      {numRuns: 100},
    );
  });
});

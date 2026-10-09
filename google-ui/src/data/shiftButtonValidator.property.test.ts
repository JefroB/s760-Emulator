/**
 * Property-based tests for the Button_Mapping schema validator.
 *
 * Property 1: Verification implies a manual page, and vice versa.
 *
 * For any Button_Mapping and any entry (and any nested SHIFT function) in it,
 * the entry/shift is `Verified` IFF it has a non-null owner's-manual page
 * reference, and every `Unverified` entry/shift has a non-null
 * reason-not-confirmed. Additionally, a `Verified` SHIFT function must carry a
 * non-null chord event. The validator (`validateButtonMapping` /
 * `isValidButtonMapping`) MUST accept EXACTLY the invariant-holding mappings and
 * reject every mapping that breaks any invariant.
 *
 * This test independently (re-)derives the invariant predicate from the raw
 * generated fields and asserts the validator agrees with it on every generated
 * mapping, so the validator is pinned to the Property 1 definition rather than
 * to its own implementation.
 *
 * Validates: Requirements 1.4, 1.5, 1.6
 */
import {describe, it, expect} from 'vitest';
import fc from 'fast-check';
import {
  validateButtonMapping,
  isValidButtonMapping,
} from './shiftButtonValidator';
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

/** null vs a present string, to mix both halves of each invariant. */
const nullableStringArb = (present: fc.Arbitrary<string>) =>
  fc.option(present, {nil: null});

/** A chord event (present variant). */
const chordEventArb: fc.Arbitrary<ChordEventSpec> = fc.record({
  type: fc.string(),
  payload: fc.dictionary(fc.string(), fc.anything()),
});

/**
 * An UNCONSTRAINED SHIFT function arbitrary: verification, manualPage,
 * reasonUnverified, and event are each generated INDEPENDENTLY so the generator
 * produces both invariant-holding and invariant-violating combinations. This is
 * essential: the property is that the validator accepts EXACTLY the holding
 * ones, which can only be checked if violations are also generated.
 */
const shiftArb: fc.Arbitrary<ShiftFunctionSpec> = fc.record({
  targetButtonId: fc.string(),
  silkscreenLabel: nullableStringArb(fc.string()),
  description: fc.string(),
  verification: statusArb,
  manualPage: nullableStringArb(fc.string({minLength: 1})),
  reasonUnverified: nullableStringArb(fc.string({minLength: 1})),
  event: fc.option(chordEventArb, {nil: null}),
});

/**
 * An UNCONSTRAINED entry arbitrary. The entry's own verification/manualPage/
 * reasonUnverified are generated independently, and `shift` is null vs an
 * unconstrained SHIFT function, so the full cross-product of invariant states is
 * explored.
 */
const entryArb: fc.Arbitrary<ButtonMappingEntry> = fc.record({
  buttonId: fc.string(),
  primaryFunction: fc.string(),
  shift: fc.option(shiftArb, {nil: null}),
  verification: statusArb,
  manualPage: nullableStringArb(fc.string({minLength: 1})),
  reasonUnverified: nullableStringArb(fc.string({minLength: 1})),
  ownedByGotek: fc.boolean(),
});

const mappingArb: fc.Arbitrary<readonly ButtonMappingEntry[]> = fc.array(
  entryArb,
  {maxLength: 8},
);

/**
 * Reference predicate: does a single verification/manualPage/reasonUnverified
 * triple satisfy the Property 1 invariants?
 *   - Verified   ⇒ manualPage !== null           (R1.5)
 *   - manualPage === null ⇒ Unverified           (R1.6, contrapositive of R1.5)
 *   - Unverified ⇒ reasonUnverified !== null      (R1.4)
 *   - Unverified must NOT record a manualPage      (R1.6 forward)
 */
function verificationInvariantsHold(
  verification: VerificationStatus,
  manualPage: string | null,
  reasonUnverified: string | null,
): boolean {
  if (verification === 'Verified') {
    return manualPage !== null;
  }
  // Unverified
  return manualPage === null && reasonUnverified !== null;
}

/** Reference predicate for a whole entry, including its nested SHIFT function. */
function entryInvariantsHold(entry: ButtonMappingEntry): boolean {
  if (
    !verificationInvariantsHold(
      entry.verification,
      entry.manualPage,
      entry.reasonUnverified,
    )
  ) {
    return false;
  }
  const shift = entry.shift;
  if (shift === null) {
    return true;
  }
  if (
    !verificationInvariantsHold(
      shift.verification,
      shift.manualPage,
      shift.reasonUnverified,
    )
  ) {
    return false;
  }
  // R5.5 — a Verified SHIFT function must carry a non-null event.
  if (shift.verification === 'Verified' && shift.event === null) {
    return false;
  }
  return true;
}

/** Reference predicate for the whole mapping. */
function mappingInvariantsHold(
  mapping: readonly ButtonMappingEntry[],
): boolean {
  return mapping.every(entryInvariantsHold);
}

describe('validateButtonMapping — Property 1 (verification ⇔ manual page)', () => {
  it('accepts EXACTLY the invariant-holding mappings (and rejects the rest)', () => {
    fc.assert(
      fc.property(mappingArb, (mapping) => {
        const expectValid = mappingInvariantsHold(mapping);
        const actualValid = isValidButtonMapping(mapping);
        expect(actualValid).toBe(expectValid);

        // When invalid, there must be at least one reported violation; when
        // valid, there must be none.
        const violations = validateButtonMapping(mapping);
        expect(violations.length === 0).toBe(expectValid);
      }),
      {numRuns: 100},
    );
  });
});

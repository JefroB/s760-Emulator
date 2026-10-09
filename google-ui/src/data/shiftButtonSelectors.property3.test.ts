/**
 * Property-based test for the renderable Shift_Button set (design Property 3).
 *
 * Property 3: The renderable Shift_Button set is exactly the Verified,
 *   non-Gotek, event-bearing SHIFT functions.
 *
 *   For any Button_Mapping, the set of rendered Shift_Buttons
 *   (`verifiedShiftButtons(mapping)`) equals EXACTLY the set of SHIFT functions
 *   that are `Verified`, NOT owned by the Gotek bay, and have a non-null
 *   recorded event — with exactly one descriptor per such entry (one
 *   `targetButtonId` and one `event` each), de-duplicated by `buttonId`
 *   (first occurrence wins), and no duplicate `buttonId`. Consequently no
 *   `Unverified` entry, no Gotek-owned entry, and no entry lacking a `Verified`
 *   event is ever renderable.
 *
 * This test independently (re-)derives the expected descriptor set from the raw
 * generated fields and asserts `verifiedShiftButtons` agrees with it on every
 * generated mapping, so the selector is pinned to the Property 3 definition
 * rather than to its own implementation.
 *
 * Validates: Requirements 2.3, 2.4, 3.1, 3.4, 3.6, 5.5, 6.3
 *
 * Test tooling: Vitest + fast-check (design "Testing Strategy > Tooling").
 */
import {describe, it, expect} from 'vitest';
import fc from 'fast-check';
import {verifiedShiftButtons} from './shiftButtonSelectors';
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

/**
 * Small shared button-id alphabet so DUPLICATE `buttonId`s are generated
 * frequently (the dedup-by-buttonId / first-wins behavior under test only
 * triggers when ids collide).
 */
const buttonIdArb: fc.Arbitrary<string> = fc.constantFrom(
  'PATCH',
  'PART',
  'SAMPLE',
  'SYSTEM',
  'F1',
  'F2',
  'F3',
);

/** A chord event (present variant). */
const chordEventArb: fc.Arbitrary<ChordEventSpec> = fc.record({
  type: fc.string(),
  payload: fc.dictionary(fc.string(), fc.anything()),
});

/**
 * An UNCONSTRAINED SHIFT function arbitrary: `verification` is Verified vs
 * Unverified and `event` is null vs present, generated INDEPENDENTLY, so the
 * generator produces renderable and non-renderable SHIFT functions in every
 * combination.
 */
const shiftArb: fc.Arbitrary<ShiftFunctionSpec> = fc.record({
  targetButtonId: fc.string(),
  silkscreenLabel: fc.option(fc.string(), {nil: null}),
  description: fc.string(),
  verification: statusArb,
  manualPage: fc.option(fc.string(), {nil: null}),
  reasonUnverified: fc.option(fc.string(), {nil: null}),
  event: fc.option(chordEventArb, {nil: null}),
});

/**
 * A `ButtonMappingEntry` arbitrary mixing all axes that affect renderability:
 *   - `shift` null vs present,
 *   - `shift.verification` Verified vs Unverified,
 *   - `shift.event` null vs present,
 *   - `ownedByGotek` true vs false,
 *   - duplicate `buttonId`s (small shared alphabet).
 */
const entryArb: fc.Arbitrary<ButtonMappingEntry> = fc.record({
  buttonId: buttonIdArb,
  primaryFunction: fc.string(),
  shift: fc.option(shiftArb, {nil: null}),
  verification: statusArb,
  manualPage: fc.option(fc.string(), {nil: null}),
  reasonUnverified: fc.option(fc.string(), {nil: null}),
  ownedByGotek: fc.boolean(),
});

const mappingArb: fc.Arbitrary<readonly ButtonMappingEntry[]> = fc.array(
  entryArb,
  {maxLength: 12},
);

/** Does a single entry qualify as a renderable Shift_Button? (Property 3.) */
function isRenderable(entry: ButtonMappingEntry): boolean {
  const shift = entry.shift;
  return (
    shift !== null &&
    !entry.ownedByGotek &&
    shift.verification === 'Verified' &&
    shift.event !== null
  );
}

/**
 * Reference derivation of the expected descriptor set: the qualifying entries,
 * de-duplicated by `buttonId` with the FIRST occurrence winning (mirrors the
 * selector contract, derived here independently of its implementation).
 */
function expectedDescriptors(mapping: readonly ButtonMappingEntry[]): Array<{
  buttonId: string;
  targetButtonId: string;
  event: ChordEventSpec;
}> {
  const out: Array<{
    buttonId: string;
    targetButtonId: string;
    event: ChordEventSpec;
  }> = [];
  const seen = new Set<string>();
  for (const entry of mapping) {
    if (!isRenderable(entry)) continue;
    if (seen.has(entry.buttonId)) continue;
    seen.add(entry.buttonId);
    // isRenderable guarantees shift and shift.event are non-null.
    const shift = entry.shift as ShiftFunctionSpec;
    out.push({
      buttonId: entry.buttonId,
      targetButtonId: shift.targetButtonId,
      event: shift.event as ChordEventSpec,
    });
  }
  return out;
}

describe('Property 3: verifiedShiftButtons renders exactly the Verified, non-Gotek, event-bearing SHIFT functions', () => {
  it('equals exactly the qualifying entries, one descriptor each, de-duplicated by buttonId (first-wins)', () => {
    fc.assert(
      fc.property(mappingArb, (mapping) => {
        const descriptors = verifiedShiftButtons(mapping);
        const expected = expectedDescriptors(mapping);

        // Exactly one descriptor per qualifying entry (same count, same order
        // because both derive from the mapping in order with first-wins dedup).
        expect(descriptors.length).toBe(expected.length);

        // No duplicate buttonId in the rendered set.
        const ids = descriptors.map((d) => d.buttonId);
        expect(new Set(ids).size).toBe(ids.length);

        // Each descriptor matches the expected qualifying entry value-for-value:
        // one buttonId, one targetButtonId, one event (same reference/value).
        for (let i = 0; i < expected.length; i++) {
          const d = descriptors[i];
          const e = expected[i];
          expect(d.buttonId).toBe(e.buttonId);
          expect(d.targetButtonId).toBe(e.targetButtonId);
          expect(d.event).toEqual(e.event);
        }

        // Conversely: NOTHING non-renderable leaks in. Every rendered buttonId
        // corresponds to at least one qualifying entry, and NO rendered id
        // belongs to a buttonId whose qualifying occurrences are all excluded.
        const renderedIds = new Set(ids);
        for (const id of renderedIds) {
          const hasQualifying = mapping.some(
            (entry) => entry.buttonId === id && isRenderable(entry),
          );
          expect(hasQualifying).toBe(true);
        }

        // And every qualifying buttonId is represented exactly once.
        const qualifyingIds = new Set(
          mapping.filter(isRenderable).map((e) => e.buttonId),
        );
        expect(renderedIds).toEqual(qualifyingIds);
      }),
      {numRuns: 100},
    );
  });
});

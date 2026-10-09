/**
 * Property-based test for front-panel Button_Mapping reconciliation set
 * differences (design Property 2).
 *
 * Property 2: Reconciliation computes correct set differences
 *   For any Button_Mapping and any set of Front_Panel button ids, the
 *   reconciliation result's `missingFromUi` equals exactly the mapping's
 *   hardware button ids that are NOT in the Front_Panel set, and `extraInUi`
 *   equals exactly the Front_Panel ids that are NOT in the mapping.
 *
 * Set equality is asserted ignoring order and duplicates (both outputs are
 * de-duplicated by `reconcile`).
 *
 * Validates: Requirements 2.1, 2.2
 *
 * Test tooling: Vitest + fast-check (design "Testing Strategy > Tooling").
 */
import {describe, it, expect} from 'vitest';
import fc from 'fast-check';
import {reconcile} from './shiftButtonReconcile';
import type {ButtonMappingEntry, VerificationStatus} from './shiftButtonMap';

/**
 * Button-id arbitrary drawn from a small shared alphabet so the generated
 * mapping-id set and the Front_Panel-id set overlap meaningfully (mix of
 * overlapping and disjoint ids) rather than being almost-always disjoint.
 */
const buttonIdArb: fc.Arbitrary<string> = fc.constantFrom(
  'POWER',
  'PATCH',
  'PART',
  'SAMPLE',
  'SYSTEM',
  'DISK',
  'F1',
  'F2',
  'F3',
  'NAV_LEFT',
  'ENTER',
  'EXIT',
  'FAKE_A',
  'FAKE_B',
  'FAKE_C',
);

const verificationArb: fc.Arbitrary<VerificationStatus> = fc.constantFrom(
  'Verified',
  'Unverified',
);

/**
 * A `ButtonMappingEntry` arbitrary. Only `buttonId` affects the set-difference
 * logic under test; the remaining fields are generated with plausible values so
 * the generator exercises mixed shapes without constraining Property 2.
 */
const entryArb: fc.Arbitrary<ButtonMappingEntry> = fc.record({
  buttonId: buttonIdArb,
  primaryFunction: fc.string(),
  shift: fc.constant(null),
  verification: verificationArb,
  manualPage: fc.option(fc.string(), {nil: null}),
  reasonUnverified: fc.option(fc.string(), {nil: null}),
  ownedByGotek: fc.boolean(),
});

/** Compare two id lists as sets (order- and duplicate-insensitive). */
function sameSet(actual: readonly string[], expected: Iterable<string>): void {
  expect(new Set(actual)).toEqual(new Set(expected));
}

describe('Property 2: reconcile computes correct set differences', () => {
  it('missingFromUi = mapping ids \\ ui ids; extraInUi = ui ids \\ mapping ids', () => {
    fc.assert(
      fc.property(
        fc.array(entryArb),
        fc.array(buttonIdArb),
        (mapping, frontPanelButtonIds) => {
          // preservedPrimaryIds / gotekOwnedIds do not affect the two set
          // differences this property checks; use empty sets.
          const result = reconcile(mapping, frontPanelButtonIds, [], []);

          const mappingIds = new Set(mapping.map((e) => e.buttonId));
          const uiIds = new Set(frontPanelButtonIds);

          const expectedMissing = [...mappingIds].filter((id) => !uiIds.has(id));
          const expectedExtra = [...uiIds].filter((id) => !mappingIds.has(id));

          // Set equality: missingFromUi is exactly mapping ids absent from UI.
          sameSet(result.missingFromUi, expectedMissing);
          // Set equality: extraInUi is exactly UI ids absent from the mapping.
          sameSet(result.extraInUi, expectedExtra);

          // Outputs are de-duplicated (sets): list length == unique count.
          expect(result.missingFromUi.length).toBe(
            new Set(result.missingFromUi).size,
          );
          expect(result.extraInUi.length).toBe(
            new Set(result.extraInUi).size,
          );
        },
      ),
      {numRuns: 100},
    );
  });
});

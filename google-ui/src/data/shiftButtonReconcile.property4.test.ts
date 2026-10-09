/**
 * Property 4: Reconciliation is idempotent after adding missing buttons.
 *
 * For any Button_Mapping and any Front_Panel button id set:
 *   - `toAdd` equals exactly the `Verified` entries missing from the UI, AND
 *   - after those ids are added to the Front_Panel set, reconciling again
 *     yields an empty `toAdd` (adding a button never introduces a duplicate on
 *     subsequent reconciliations).
 *
 * **Validates: Requirements 2.3**
 *
 * Design reference: `.kiro/specs/front-panel-shift-buttons/design.md`
 *   — "Correctness Properties > Property 4".
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';

import type {
  ButtonMappingEntry,
  VerificationStatus,
} from './shiftButtonMap';
import { reconcile } from './shiftButtonReconcile';

/**
 * A small pool of button ids so that the UI id set and the mapping ids overlap
 * meaningfully (otherwise every "missing" test would be trivially disjoint).
 * This constrains the input space intelligently per the testing guidance.
 */
const BUTTON_ID_POOL = [
  'POWER',
  'PERF',
  'PATCH',
  'PART',
  'SAMPLE',
  'SYSTEM',
  'DISK',
  'F1',
  'F2',
  'F3',
  'ENTER',
  'EXIT',
  'FAB_A',
  'FAB_B',
  'SHIFT_X',
  'SHIFT_Y',
] as const;

const buttonIdArb: fc.Arbitrary<string> = fc.constantFrom(...BUTTON_ID_POOL);

const verificationArb: fc.Arbitrary<VerificationStatus> = fc.constantFrom(
  'Verified',
  'Unverified',
);

/**
 * Build a mapping entry that honors the schema invariant used by reconcile:
 * a `Verified` entry carries a non-null `manualPage`; an `Unverified` entry
 * carries a `reasonUnverified`. (reconcile only reads `buttonId`,
 * `verification`, `ownedByGotek`, and `primaryFunction`, but we keep entries
 * well-formed so the generator mirrors real data.)
 */
function entryArb(): fc.Arbitrary<ButtonMappingEntry> {
  return fc
    .record({
      buttonId: buttonIdArb,
      verification: verificationArb,
      ownedByGotek: fc.boolean(),
    })
    .map(({ buttonId, verification, ownedByGotek }) => {
      const verified = verification === 'Verified';
      const entry: ButtonMappingEntry = {
        buttonId,
        primaryFunction: `Primary function of ${buttonId}.`,
        shift: null,
        verification,
        manualPage: verified ? 'p.42' : null,
        reasonUnverified: verified ? null : 'awaiting manual OCR confirmation',
        ownedByGotek,
      };
      return entry;
    });
}

/** Arbitrary mapping (may contain duplicate buttonIds, mixed statuses). */
const mappingArb: fc.Arbitrary<ButtonMappingEntry[]> = fc.array(entryArb(), {
  minLength: 0,
  maxLength: 10,
});

/** Arbitrary Front_Panel id set (may overlap the mapping ids, may duplicate). */
const uiIdsArb: fc.Arbitrary<string[]> = fc.array(buttonIdArb, {
  minLength: 0,
  maxLength: 12,
});

describe('Property 4: reconciliation is idempotent after adding missing buttons', () => {
  it('toAdd equals exactly the Verified entries missing from the UI, and a second reconcile adds nothing', () => {
    fc.assert(
      fc.property(mappingArb, uiIdsArb, (mapping, uiIds) => {
        // reconcile reads only the mapping + UI ids for toAdd; preserved/gotek
        // sets do not influence toAdd, so empty sets are a valid, general input.
        const preservedPrimaryIds: string[] = [];
        const gotekOwnedIds: string[] = [];

        const result = reconcile(
          mapping,
          uiIds,
          preservedPrimaryIds,
          gotekOwnedIds,
        );

        // --- Part 1: toAdd == exactly the Verified ids absent from the UI. ---
        const uiSet = new Set(uiIds);
        const expectedToAddSet = new Set<string>();
        for (const entry of mapping) {
          if (entry.verification === 'Verified' && !uiSet.has(entry.buttonId)) {
            expectedToAddSet.add(entry.buttonId);
          }
        }

        // toAdd carries no duplicates and matches the expected set exactly.
        expect(new Set(result.toAdd)).toEqual(expectedToAddSet);
        expect(result.toAdd.length).toBe(expectedToAddSet.size);

        // --- Part 2: idempotence — add toAdd ids, reconcile again, no new adds.
        const uiIds2 = [...uiIds, ...result.toAdd];
        const result2 = reconcile(
          mapping,
          uiIds2,
          preservedPrimaryIds,
          gotekOwnedIds,
        );

        expect(result2.toAdd).toEqual([]);
      }),
      { numRuns: 100 },
    );
  });
});

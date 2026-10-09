import { describe, expect, it } from 'vitest';
import fc from 'fast-check';

import { reconcile } from './shiftButtonReconcile';
import type { ButtonMappingEntry, VerificationStatus } from './shiftButtonMap';

/**
 * Property 5: Verified primary that conflicts with a preserved primary is
 * recorded, not removed.
 *
 * **Validates: Requirements 2.6**
 *
 * Implemented contract (see shiftButtonReconcile.ts JSDoc + design.md
 * "Property 5"): there is no separate preserved-primary function string to diff
 * against, so a conflict is recorded whenever a `Verified` mapping entry shares
 * an id with a preserved primary. Concretely:
 *   - every `Verified` entry whose `buttonId` is in the preserved-primary set
 *     appears in `conflicts` (as { buttonId, mappingPrimaryFunction }); and
 *   - no preserved primary id ever appears in `toRemove` /
 *     `fabricationCandidates` (preserved primaries always persist).
 */

// A small, bounded id space so overlaps between the mapping, preserved-primary,
// UI, and Gotek sets occur frequently (the interesting cases for this property).
const idArb: fc.Arbitrary<string> = fc.constantFrom(
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
  'FAB_C',
  'GOTEK_EJECT',
);

const verificationArb: fc.Arbitrary<VerificationStatus> = fc.constantFrom(
  'Verified',
  'Unverified',
);

/**
 * Smart generator for a mapping entry. Mixes Verified/Unverified status and
 * varies the primary function so that Verified entries sharing an id with a
 * preserved primary are plentiful. Keeps the invariant that a Verified entry
 * carries a manual page (not strictly required by `reconcile`, but keeps the
 * generated mappings realistic).
 */
const entryArb: fc.Arbitrary<ButtonMappingEntry> = fc
  .record({
    buttonId: idArb,
    primaryFunction: fc.constantFrom(
      'Select PATCH mode.',
      'Select SAMPLE mode.',
      'A DIFFERENT primary function.',
      'Move cursor left.',
    ),
    verification: verificationArb,
    ownedByGotek: fc.boolean(),
  })
  .map(({ buttonId, primaryFunction, verification, ownedByGotek }) => {
    const verified = verification === 'Verified';
    const entry: ButtonMappingEntry = {
      buttonId,
      primaryFunction,
      shift: null,
      verification,
      manualPage: verified ? 'p.42' : null,
      reasonUnverified: verified ? null : 'awaiting manual OCR',
      ownedByGotek,
    };
    return entry;
  });

const mappingArb: fc.Arbitrary<readonly ButtonMappingEntry[]> = fc.array(
  entryArb,
  { maxLength: 12 },
);

// Preserved-primary set: a subset of the id space, with overlaps onto mapping
// entry ids expected. Use a uniqueArray so the set has no dupes.
const idSetArb: fc.Arbitrary<string[]> = fc.uniqueArray(idArb, {
  maxLength: 10,
});

describe('reconcile — Property 5: conflict recording of preserved primaries', () => {
  it('records every Verified entry whose id is a preserved primary, and never removes a preserved primary', () => {
    fc.assert(
      fc.property(
        mappingArb,
        idSetArb, // frontPanelButtonIds
        idSetArb, // preservedPrimaryIds
        idSetArb, // gotekOwnedIds
        (mapping, frontPanelButtonIds, preservedPrimaryIds, gotekOwnedIds) => {
          const result = reconcile(
            mapping,
            frontPanelButtonIds,
            preservedPrimaryIds,
            gotekOwnedIds,
          );

          const preservedSet = new Set(preservedPrimaryIds);

          // (a) Every Verified entry whose id is a preserved primary is recorded
          //     as a conflict with the mapping's primary function.
          const expectedConflicts = mapping.filter(
            (e) => e.verification === 'Verified' && preservedSet.has(e.buttonId),
          );
          expect(result.conflicts.length).toBe(expectedConflicts.length);
          for (const entry of expectedConflicts) {
            const matching = result.conflicts.filter(
              (c) =>
                c.buttonId === entry.buttonId &&
                c.mappingPrimaryFunction === entry.primaryFunction,
            );
            expect(matching.length).toBeGreaterThanOrEqual(1);
          }

          // (b) Every recorded conflict corresponds to a Verified, preserved
          //     entry (no spurious conflicts for Unverified or non-preserved).
          for (const conflict of result.conflicts) {
            expect(preservedSet.has(conflict.buttonId)).toBe(true);
            const backing = mapping.some(
              (e) =>
                e.verification === 'Verified' &&
                e.buttonId === conflict.buttonId &&
                e.primaryFunction === conflict.mappingPrimaryFunction,
            );
            expect(backing).toBe(true);
          }

          // (c) No preserved primary id is ever produced for removal — preserved
          //     primaries always persist.
          for (const id of result.toRemove) {
            expect(preservedSet.has(id)).toBe(false);
          }
          for (const id of result.fabricationCandidates) {
            expect(preservedSet.has(id)).toBe(false);
          }
        },
      ),
      { numRuns: 100 },
    );
  });
});

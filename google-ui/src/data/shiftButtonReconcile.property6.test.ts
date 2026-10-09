/**
 * Property-based test for front-panel Button_Mapping fabrication removal and
 * retention (design Property 6).
 *
 * Property 6: Fabricated buttons are removed; preserved, Unverified-but-mapped,
 * and Gotek-owned buttons are never removed.
 *
 *   For any Button_Mapping (mixing Verified/Unverified entries), any set of
 *   preserved primary control ids, any set of Gotek-owned ids, and any
 *   Front_Panel button id set, the reconciliation `toRemove`
 *   (≡ `fabricationCandidates`) equals EXACTLY the Front_Panel button ids that
 *   are simultaneously (a) NOT a Preserved_Primary_Control, (b) NOT present as
 *   ANY Button_Mapping entry under ANY Verification_Status, and (c) NOT owned by
 *   the Gotek_Bay. Conversely: no preserved primary (even when its mapping entry
 *   is absent or Unverified), no mapped button (including Unverified-but-mapped),
 *   and no Gotek-owned id is ever removed.
 *
 * **Validates: Requirements 2.7, 2.8, 2.9, 2.10, 2.11**
 *
 * Test tooling: Vitest + fast-check (design "Testing Strategy > Tooling").
 *
 * Generator design (per task 3.6 + design "Testing Strategy"): a shared bounded
 * id pool is used across the mapping, the Front_Panel id set, the preserved set,
 * and the Gotek-owned set so overlaps between all removal/retention classes
 * occur frequently. The pool is partitioned into id families that naturally
 * exercise each class — genuinely-fabricated ids, preserved-primary ids
 * (including some whose mapping entry is absent or Unverified),
 * Unverified-but-mapped ids, and Gotek-owned ids — while still letting the
 * generator freely overlap them to probe edge cases.
 */
import { describe, it, expect } from 'vitest';
import fc from 'fast-check';

import { reconcile } from './shiftButtonReconcile';
import type { ButtonMappingEntry, VerificationStatus } from './shiftButtonMap';

/**
 * Shared bounded id pool. Prefixes hint at the id's typical class but the
 * generator does NOT rely on them — every set is drawn from the SAME pool so
 * any id can land in the mapping, the UI, the preserved set, and/or the Gotek
 * set simultaneously, exercising all overlap combinations.
 */
const idArb: fc.Arbitrary<string> = fc.constantFrom(
  // preserved-primary family
  'POWER',
  'ENTER',
  'EXIT',
  'F1',
  'F2',
  // genuinely-mappable (hardware) family
  'PATCH',
  'SAMPLE',
  'SYSTEM',
  'DISK',
  // fabrication family (not real hardware; prior-AI invented)
  'FAB_A',
  'FAB_B',
  'FAB_C',
  // Gotek-owned family
  'GOTEK_EJECT',
  'GOTEK_PREV',
  'GOTEK_NEXT',
);

const verificationArb: fc.Arbitrary<VerificationStatus> = fc.constantFrom(
  'Verified',
  'Unverified',
);

/**
 * A mapping-entry arbitrary mixing Verified/Unverified status (so the pool
 * contains Unverified-but-mapped ids), and mixing ownedByGotek true/false. Only
 * `buttonId` (presence under ANY status) and `ownedByGotek` affect removal
 * classification; the remaining fields are given plausible values.
 */
const entryArb: fc.Arbitrary<ButtonMappingEntry> = fc
  .record({
    buttonId: idArb,
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
      reasonUnverified: verified ? null : 'awaiting manual OCR',
      ownedByGotek,
    };
    return entry;
  });

const mappingArb: fc.Arbitrary<readonly ButtonMappingEntry[]> = fc.array(
  entryArb,
  { maxLength: 12 },
);

/** An id-set arbitrary (unique, drawn from the shared pool). */
const idSetArb: fc.Arbitrary<string[]> = fc.uniqueArray(idArb, {
  maxLength: 12,
});

describe('reconcile — Property 6: fabrication removal and retention', () => {
  it('toRemove equals exactly the non-preserved, unmapped, non-Gotek UI ids; and toRemove === fabricationCandidates', () => {
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

          const mappingIds = new Set(mapping.map((e) => e.buttonId));
          const preservedSet = new Set(preservedPrimaryIds);
          const gotekSet = new Set(gotekOwnedIds);

          // Independently recompute the EXACT expected fabrication set directly
          // from the Property-6 definition: a Front_Panel id is removed IFF it
          // is (a) not preserved, (b) absent from EVERY mapping entry under ANY
          // status, and (c) not Gotek-owned.
          const expectedRemoval = new Set(
            frontPanelButtonIds.filter(
              (id) =>
                !preservedSet.has(id) &&
                !mappingIds.has(id) &&
                !gotekSet.has(id),
            ),
          );

          // toRemove is EXACTLY the expected fabrication set (order/dupe-insensitive).
          expect(new Set(result.toRemove)).toEqual(expectedRemoval);

          // toRemove and fabricationCandidates are the same set.
          expect(new Set(result.toRemove)).toEqual(
            new Set(result.fabricationCandidates),
          );

          // Conversely (defensive restatement of the retention guarantees):
          //  - no preserved primary is ever removed (R2.9), even if its mapping
          //    entry is absent or Unverified;
          //  - no mapped button (incl. Unverified-but-mapped) is removed (R2.10);
          //  - no Gotek-owned id is removed (R2.11).
          for (const id of result.toRemove) {
            expect(preservedSet.has(id)).toBe(false);
            expect(mappingIds.has(id)).toBe(false);
            expect(gotekSet.has(id)).toBe(false);
            // And it must genuinely be a rendered Front_Panel button (R2.7, R2.8).
            expect(frontPanelButtonIds.includes(id)).toBe(true);
          }

          // Every preserved primary that is on the panel is retained.
          for (const id of frontPanelButtonIds) {
            if (preservedSet.has(id)) {
              expect(result.toRemove.includes(id)).toBe(false);
            }
            // Every Unverified-but-mapped (and any mapped) panel button retained.
            if (mappingIds.has(id)) {
              expect(result.toRemove.includes(id)).toBe(false);
            }
            // Every Gotek-owned panel button retained.
            if (gotekSet.has(id)) {
              expect(result.toRemove.includes(id)).toBe(false);
            }
          }

          // Output is de-duplicated (a set): list length == unique count.
          expect(result.toRemove.length).toBe(new Set(result.toRemove).size);
        },
      ),
      { numRuns: 100 },
    );
  });
});

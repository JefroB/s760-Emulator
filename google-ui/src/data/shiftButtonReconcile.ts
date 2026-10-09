/**
 * Pure reconciliation logic for the Roland S-760 front-panel Button_Mapping.
 *
 * `reconcile` compares the authoritative `Button_Mapping` (the hardware button
 * set) against the current React Front_Panel button id set and produces a
 * recorded `ReconciliationResult`: the set differences (missing / extra), the
 * subset of extra buttons that are prior-AI fabrications to remove, the
 * `Verified`-primary-vs-preserved-primary conflicts, the Gotek-owned entries
 * that are out of scope, and the `Verified` entries to add.
 *
 * This module is intentionally kept separate from `shiftButtonMap.ts` (it only
 * imports the types from there) and contains no React / rendering concerns, so
 * the classification logic stays pure and directly unit/property-testable.
 *
 * Design reference: `.kiro/specs/front-panel-shift-buttons/design.md`
 *   — "Reconciliation flow (Requirement 2)" and "Data Models > ReconciliationResult".
 */

import type { ButtonMappingEntry } from './shiftButtonMap';

/**
 * A `Verified` mapping entry whose primary function conflicts with an existing
 * preserved primary control of the same id (R2.6). Recorded for human
 * resolution; the preserved primary control is never auto-removed.
 */
export interface ConflictRecord {
  /** The id shared by the mapping entry and the preserved primary control. */
  buttonId: string;
  /** The primary function the (Verified) mapping entry documents. */
  mappingPrimaryFunction: string;
}

/**
 * The recorded outcome of reconciling the `Button_Mapping` against the current
 * Front_Panel button id set. See design "Data Models > ReconciliationResult".
 */
export interface ReconciliationResult {
  /** In mapping (hardware) but absent from the Front_Panel (R2.1). */
  missingFromUi: string[];
  /**
   * On the Front_Panel but absent from the mapping (R2.2). The raw "extra in UI"
   * set BEFORE classification. Preserved-primary and Gotek-owned ids may appear
   * here but are NEVER promoted to `fabricationCandidates`.
   */
  extraInUi: string[];
  /**
   * The subset of `extraInUi` identified as prior-AI fabrications to REMOVE:
   * Front_Panel buttons that are not a preserved primary, absent from EVERY
   * mapping entry (any Verification_Status), and not Gotek-owned (R2.7, R2.8).
   * `fabricationCandidates === toRemove`.
   */
  fabricationCandidates: string[];
  /** Alias of `fabricationCandidates`: the exact ids removed from the Front_Panel. */
  toRemove: string[];
  /** Verified entries whose primary conflicts with a preserved primary (R2.6). */
  conflicts: ConflictRecord[];
  /** Entries excluded because they belong to the Gotek bay (R6.3, R2.11). */
  outOfScope: string[];
  /** Verified+missing entries that SHOULD be added (one each, R2.3). */
  toAdd: string[];
}

/**
 * Reconcile the authoritative `Button_Mapping` against the current Front_Panel
 * button id set.
 *
 * @param mapping              The authoritative `Button_Mapping` entries.
 * @param frontPanelButtonIds  The ids of buttons currently rendered on the Front_Panel.
 * @param preservedPrimaryIds  Ids of the Preserved_Primary_Control set (never removed).
 * @param gotekOwnedIds        Front_Panel ids owned by the Gotek_Bay (never removed).
 *
 * Classification of an "extra" (present in UI, absent from mapping) button as a
 * `Fabrication_Candidate` holds IFF the button is simultaneously:
 *   (a) NOT a preserved primary (R2.9),
 *   (b) absent from EVERY mapping entry under ANY Verification_Status (R2.7, R2.10),
 *   (c) NOT owned by the Gotek_Bay (R2.11).
 */
export function reconcile(
  mapping: readonly ButtonMappingEntry[],
  frontPanelButtonIds: readonly string[],
  preservedPrimaryIds: readonly string[],
  gotekOwnedIds: readonly string[],
): ReconciliationResult {
  // Lookup sets. Mapping membership keys off presence under ANY status.
  const mappingIds = new Set<string>(mapping.map((entry) => entry.buttonId));
  const uiIds = new Set<string>(frontPanelButtonIds);
  const preservedSet = new Set<string>(preservedPrimaryIds);
  const gotekSet = new Set<string>(gotekOwnedIds);

  // missingFromUi: mapping ids not present on the Front_Panel (R2.1).
  // Preserve mapping order and de-duplicate.
  const missingFromUi: string[] = [];
  const seenMissing = new Set<string>();
  for (const entry of mapping) {
    const id = entry.buttonId;
    if (!uiIds.has(id) && !seenMissing.has(id)) {
      seenMissing.add(id);
      missingFromUi.push(id);
    }
  }

  // extraInUi: Front_Panel ids absent from the mapping (R2.2).
  // Preserve UI order and de-duplicate.
  const extraInUi: string[] = [];
  const seenExtra = new Set<string>();
  for (const id of frontPanelButtonIds) {
    if (!mappingIds.has(id) && !seenExtra.has(id)) {
      seenExtra.add(id);
      extraInUi.push(id);
    }
  }

  // fabricationCandidates: extra buttons that are neither a preserved primary
  // nor Gotek-owned (and, by virtue of being in `extraInUi`, already absent from
  // every mapping entry) (R2.7, R2.8, R2.9, R2.10, R2.11).
  const fabricationCandidates = extraInUi.filter(
    (id) => !preservedSet.has(id) && !gotekSet.has(id),
  );

  // conflicts: Verified mapping entries whose documented primary differs from an
  // existing preserved primary control of the same id (R2.6). The preserved
  // primary is recorded for resolution, never removed.
  const conflicts: ConflictRecord[] = [];
  for (const entry of mapping) {
    if (entry.verification === 'Verified' && preservedSet.has(entry.buttonId)) {
      conflicts.push({
        buttonId: entry.buttonId,
        mappingPrimaryFunction: entry.primaryFunction,
      });
    }
  }

  // outOfScope: mapping entries owned by the Gotek bay (R6.3, R2.11).
  const outOfScope: string[] = [];
  const seenOutOfScope = new Set<string>();
  for (const entry of mapping) {
    if (entry.ownedByGotek && !seenOutOfScope.has(entry.buttonId)) {
      seenOutOfScope.add(entry.buttonId);
      outOfScope.push(entry.buttonId);
    }
  }

  // toAdd: Verified entries missing from the UI, de-duplicated by id (R2.3).
  const toAdd: string[] = [];
  const seenToAdd = new Set<string>();
  for (const entry of mapping) {
    const id = entry.buttonId;
    if (
      entry.verification === 'Verified' &&
      !uiIds.has(id) &&
      !seenToAdd.has(id)
    ) {
      seenToAdd.add(id);
      toAdd.push(id);
    }
  }

  return {
    missingFromUi,
    extraInUi,
    fabricationCandidates,
    // `toRemove` is the imperative alias the UI consumes; identical set/order.
    toRemove: [...fabricationCandidates],
    conflicts,
    outOfScope,
    toAdd,
  };
}

/**
 * Button_Mapping schema validator.
 *
 * Enforces the Property 1 invariants from the design document across a
 * `Button_Mapping` and the nested SHIFT functions it contains:
 *
 *   - `verification === 'Verified'`  ⇒ `manualPage !== null`            (R1.5)
 *   - `manualPage === null`          ⇒ `verification === 'Unverified'`  (R1.6)
 *   - `verification === 'Unverified'` ⇒ `reasonUnverified !== null`     (R1.4)
 *   - exactly one `VerificationStatus` (`'Verified' | 'Unverified'`)     (R1.3)
 *   - a `Verified` SHIFT function requires a non-null `event`            (R5.5)
 *
 * These invariants apply BOTH to each entry's own
 * verification/manualPage/reasonUnverified fields AND to the nested
 * `ShiftFunctionSpec`'s own verification/manualPage/reasonUnverified/event
 * fields.
 *
 * ERROR-HANDLING CONTRACT (design "Error Handling"): this validator is used in
 * tests and optionally at module load in development. It MUST NOT throw at
 * render time — it always returns a structured, possibly-empty list of
 * violations so authoring mistakes surface as data rather than as exceptions.
 */

import type {
  ButtonMappingEntry,
  ShiftFunctionSpec,
  VerificationStatus,
} from './shiftButtonMap';

/** The two legal verification-status values. */
const VALID_STATUSES: readonly VerificationStatus[] = ['Verified', 'Unverified'];

/**
 * Which part of an entry a violation refers to: the hardware button entry
 * itself, or its nested SHIFT function.
 */
export type MappingViolationScope = 'entry' | 'shift';

/** The specific invariant rule a violation breaks. */
export type MappingViolationRule =
  /** `verification` is not exactly one of 'Verified' | 'Unverified' (R1.3). */
  | 'invalid-verification-status'
  /** `Verified` but `manualPage === null` (R1.5). */
  | 'verified-missing-manual-page'
  /** `manualPage === null` but not `Unverified` (R1.6). */
  | 'manual-page-null-must-be-unverified'
  /** `Unverified` but `reasonUnverified === null` (R1.4). */
  | 'unverified-missing-reason'
  /** `Verified` SHIFT function but `event === null` (R5.5). */
  | 'verified-shift-missing-event';

/** One structured mapping-schema violation. */
export interface MappingViolation {
  /** The `buttonId` of the entry the violation was found on. */
  buttonId: string;
  /** Whether the violation is on the entry itself or its nested SHIFT function. */
  scope: MappingViolationScope;
  /** The entry/shift field most responsible for the violation. */
  field: 'verification' | 'manualPage' | 'reasonUnverified' | 'event';
  /** The specific invariant rule that was broken. */
  rule: MappingViolationRule;
  /** Human-readable explanation of the violation. */
  message: string;
}

/**
 * Validate the verification/manualPage/reasonUnverified invariants shared by an
 * entry and its nested SHIFT function. Appends any violations to `violations`.
 */
function validateVerificationInvariants(
  buttonId: string,
  scope: MappingViolationScope,
  verification: VerificationStatus,
  manualPage: string | null,
  reasonUnverified: string | null,
  violations: MappingViolation[],
): void {
  const scopeLabel = scope === 'entry' ? 'entry' : 'SHIFT function';

  // R1.3 — exactly one valid VerificationStatus.
  if (!VALID_STATUSES.includes(verification)) {
    violations.push({
      buttonId,
      scope,
      field: 'verification',
      rule: 'invalid-verification-status',
      message:
        `${scopeLabel} "${buttonId}" has verification ` +
        `"${String(verification)}", which is not exactly one of ` +
        `'Verified' | 'Unverified'.`,
    });
    // Without a valid status the remaining invariants are not meaningful.
    return;
  }

  if (verification === 'Verified') {
    // R1.5 — Verified ⇒ manualPage !== null.
    if (manualPage === null) {
      violations.push({
        buttonId,
        scope,
        field: 'manualPage',
        rule: 'verified-missing-manual-page',
        message:
          `${scopeLabel} "${buttonId}" is Verified but has no owner's-manual ` +
          `page reference (manualPage === null).`,
      });
    }
  } else {
    // verification === 'Unverified'

    // R1.6 — manualPage === null ⇒ Unverified. Contrapositive guard: an
    // Unverified entry that nonetheless records a page is contradictory, since
    // a recorded page should promote it to Verified.
    if (manualPage !== null) {
      violations.push({
        buttonId,
        scope,
        field: 'manualPage',
        rule: 'manual-page-null-must-be-unverified',
        message:
          `${scopeLabel} "${buttonId}" is Unverified but records a manual ` +
          `page ("${manualPage}"); a recorded page must accompany a Verified ` +
          `status (R1.5/R1.6).`,
      });
    }

    // R1.4 — Unverified ⇒ reasonUnverified !== null.
    if (reasonUnverified === null) {
      violations.push({
        buttonId,
        scope,
        field: 'reasonUnverified',
        rule: 'unverified-missing-reason',
        message:
          `${scopeLabel} "${buttonId}" is Unverified but records no ` +
          `reasonUnverified.`,
      });
    }
  }
}

/**
 * Validate one entry's nested SHIFT function (if any). Appends violations.
 */
function validateShiftFunction(
  buttonId: string,
  shift: ShiftFunctionSpec,
  violations: MappingViolation[],
): void {
  validateVerificationInvariants(
    buttonId,
    'shift',
    shift.verification,
    shift.manualPage,
    shift.reasonUnverified,
    violations,
  );

  // R5.5 — a Verified SHIFT function requires a non-null event (so no event can
  // ever be emitted for an unverified entry).
  if (shift.verification === 'Verified' && shift.event === null) {
    violations.push({
      buttonId,
      scope: 'shift',
      field: 'event',
      rule: 'verified-shift-missing-event',
      message:
        `SHIFT function "${buttonId}" is Verified but records no chord event ` +
        `(event === null); a Verified SHIFT function must carry the exact ` +
        `input event it emits.`,
    });
  }
}

/**
 * Validate a `Button_Mapping` against the Property 1 schema invariants.
 *
 * Never throws. Returns a structured list of all violations found across every
 * entry and nested SHIFT function. An empty array means the mapping satisfies
 * all invariants.
 *
 * @param mapping the mapping to validate.
 * @returns the (possibly empty) list of violations.
 */
export function validateButtonMapping(
  mapping: readonly ButtonMappingEntry[],
): MappingViolation[] {
  const violations: MappingViolation[] = [];

  for (const entry of mapping) {
    // Entry-level verification/manualPage/reasonUnverified invariants.
    validateVerificationInvariants(
      entry.buttonId,
      'entry',
      entry.verification,
      entry.manualPage,
      entry.reasonUnverified,
      violations,
    );

    // Nested SHIFT-function invariants (including the Verified ⇒ event rule).
    if (entry.shift !== null) {
      validateShiftFunction(entry.buttonId, entry.shift, violations);
    }
  }

  return violations;
}

/**
 * Convenience predicate: true when the mapping satisfies every Property 1
 * invariant (i.e. `validateButtonMapping` found no violations).
 */
export function isValidButtonMapping(
  mapping: readonly ButtonMappingEntry[],
): boolean {
  return validateButtonMapping(mapping).length === 0;
}

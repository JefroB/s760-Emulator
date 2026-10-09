/**
 * Schema-validation example test for the Button_Mapping artifacts.
 *
 * Task 2.3 — asserts the shape and basic invariants of the authored
 * `BUTTON_MAPPING` entries and the existence of the canonical human-readable
 * mapping document under `docs/`.
 *
 * Validates: Requirements 1.1, 1.2, 1.3, 1.7
 */
import {describe, it, expect} from 'vitest';
import {existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

import {BUTTON_MAPPING, type VerificationStatus} from './shiftButtonMap';

const VALID_STATUSES: readonly VerificationStatus[] = ['Verified', 'Unverified'];

// Resolve this test file's directory robustly (ESM — no __dirname).
const here = path.dirname(fileURLToPath(import.meta.url));

/**
 * Resolve the repo root from this test file's location, then locate the mapping
 * doc under `docs/`. This file lives at:
 *   <repoRoot>/google-ui/src/data/shiftButtonMap.example.test.ts
 * so the repo root is three directories up from `data/`
 * (data -> src -> google-ui -> <repoRoot>).
 */
const MAPPING_DOC_PATH = path.resolve(
  here,
  '../../../docs/front-panel-button-mapping.md',
);

describe('Button_Mapping artifact schema (example test)', () => {
  it('has at least one authored BUTTON_MAPPING entry', () => {
    // R1.1 — the mapping enumerates hardware front-panel buttons.
    expect(BUTTON_MAPPING.length).toBeGreaterThan(0);
  });

  it('every entry has a non-empty buttonId (R1.1)', () => {
    for (const entry of BUTTON_MAPPING) {
      expect(typeof entry.buttonId).toBe('string');
      expect(entry.buttonId.trim().length).toBeGreaterThan(0);
    }
  });

  it('every entry records a non-empty primaryFunction (R1.1, R1.2)', () => {
    for (const entry of BUTTON_MAPPING) {
      expect(typeof entry.primaryFunction).toBe('string');
      expect(entry.primaryFunction.trim().length).toBeGreaterThan(0);
    }
  });

  it('every entry has exactly one verification status in {Verified, Unverified} (R1.3)', () => {
    for (const entry of BUTTON_MAPPING) {
      expect(VALID_STATUSES).toContain(entry.verification);
    }
  });

  it('buttonIds are unique across the mapping (R1.1)', () => {
    const ids = BUTTON_MAPPING.map((entry) => entry.buttonId);
    const unique = new Set(ids);
    expect(unique.size).toBe(ids.length);
  });

  it('stores the canonical mapping document under docs/ (R1.7)', () => {
    expect(existsSync(MAPPING_DOC_PATH)).toBe(true);
  });
});

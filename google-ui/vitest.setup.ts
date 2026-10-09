// Global test setup for Vitest.
// - jest-dom adds custom matchers (toBeInTheDocument, etc.).
// - afterEach cleanup unmounts React trees between tests so DOM state does not leak.
import '@testing-library/jest-dom/vitest';
import {cleanup} from '@testing-library/react';
import {afterEach} from 'vitest';

afterEach(() => {
  cleanup();
});

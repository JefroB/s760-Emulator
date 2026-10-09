import {describe, expect, it} from 'vitest';

// Minimal sanity test proving the Vitest runner + jsdom environment load.
// Real component/unit tests are added in task 4.1.
describe('vitest smoke', () => {
  it('runs the test runner', () => {
    expect(1 + 1).toBe(2);
  });

  it('has a jsdom document available', () => {
    expect(typeof document).toBe('object');
    expect(document.createElement('div')).toBeTruthy();
  });
});

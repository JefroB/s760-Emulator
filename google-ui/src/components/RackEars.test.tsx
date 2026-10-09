/**
 * Component render test for RackEar — a small, well-scoped, dependency-free
 * shell/chrome component. Verifies React Testing Library + jsdom mounting works
 * and that the component renders its "1U" marker and side-specific styling.
 *
 * Covers task 4.1 item 4 (a representative control component render test).
 *
 * Validates: Requirements 7.1
 */
import {describe, it, expect} from 'vitest';
import {render, screen} from '@testing-library/react';
import {RackEar} from './RackEars';

describe('RackEar', () => {
  it('renders the 1U rack-unit marker', () => {
    render(<RackEar side="left" />);
    expect(screen.getByText('1U')).toBeInTheDocument();
  });

  it('applies a right border on the left ear', () => {
    const {container} = render(<RackEar side="left" />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toContain('border-r');
    expect(root.className).not.toContain('border-l');
  });

  it('applies a left border on the right ear', () => {
    const {container} = render(<RackEar side="right" />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toContain('border-l');
    expect(root.className).not.toContain('border-r');
  });

  it('renders two screw slots (top and bottom)', () => {
    const {container} = render(<RackEar side="left" />);
    // Two screw-head cross slots: each slot has one horizontal + one vertical bar.
    const horizontalBars = container.querySelectorAll('.w-2.h-\\[1px\\]');
    expect(horizontalBars.length).toBe(2);
  });
});

import React from 'react';
import type { ShiftButtonDescriptor } from '../data/shiftButtonSelectors';

/**
 * Signature of the `S760FrontPanel.triggerButton` helper this component reuses so
 * a SHIFT button's press animation, click sound, and emission path are identical
 * to a primary front-panel button (R5.2).
 *
 * It stamps the pressed-button state (for the tactile press animation), plays the
 * click sound, then runs `action` (which performs the single `onEventEmit`).
 */
export type TriggerButtonFn = (
  id: string,
  action: () => void,
  soundType?: 'button' | 'rubber',
) => void;

/**
 * Props for the {@link ShiftButton} sub-component.
 *
 * Design reference: front-panel-shift-buttons design.md
 *   - "Components and Interfaces > 4. Shift_Button (sub-component or inlined
 *     element)"
 *   - Correctness Property 7 (single-event emission on activation) and
 *     Property 8 (label/accessibility derivation).
 */
export interface ShiftButtonProps {
  /**
   * The descriptor for exactly one Verified, non-Gotek, event-bearing SHIFT
   * function. Produced by `verifiedShiftButtons(BUTTON_MAPPING)`. Its `event` is
   * non-null by construction, so a rendered Shift_Button always has an action.
   */
  descriptor: ShiftButtonDescriptor;
  /**
   * The existing Event_Emitter path used by primary front-panel buttons
   * (`onEventEmit(type, payload)`). Shift_Button events MUST flow through this
   * same handler with no alternate, additional, or bypassing emission path
   * (R5.2).
   */
  onEventEmit: (type: string, payload: unknown) => void;
  /**
   * The host panel's `triggerButton` helper. When provided, activation runs the
   * emit through it so the press animation + click sound match primary buttons
   * exactly (R5.2). When omitted, activation performs the single emit directly so
   * the component is independently renderable/testable.
   */
  triggerButton?: TriggerButtonFn;
  /** True while the host panel currently marks this button as pressed. */
  pressed?: boolean;
}

/**
 * One pressed-tactile class string shared by every SHIFT button so the active
 * press state matches the existing front-panel buttons (R4.4).
 */
const PRESSED_CLASS = 'tactile-btn-pressed';

/**
 * Shared SHIFT visual treatment. It reuses the existing front-panel design
 * system (Tailwind palette, `tactile-btn` conventions) used by primary buttons,
 * but applies a single, identical-across-all-SHIFT-buttons accent border
 * (`border-sky-500/70` + a subtle sky glow) that differs by at least one
 * observable attribute (border color) from a primary Target_Button, whose border
 * is `border-neutral-600` / amber / emerald / rose (R4.2, R4.3, R4.4).
 */
const SHIFT_BASE_CLASS =
  'px-2 h-6 rounded-[2px] text-[7.5px] font-mono font-bold text-sky-200 ' +
  'bg-gradient-to-b from-neutral-700 to-neutral-850 border border-sky-500/70 ' +
  'shadow-[0_0_5px_rgba(14,165,233,0.25)]';

const SHIFT_IDLE_CLASS = 'tactile-btn hover:brightness-110 active:scale-95';

/**
 * A dedicated, mouse-clickable button that reproduces one hardware SHIFT
 * (secondary) function. It is a native `<button type="button">` so it joins the
 * existing keyboard focus order and focus-visible indication with no extra work
 * (R7.4) and natively fires `onClick` on Enter/Space (R7.6).
 *
 * On activation it re-checks the descriptor's `event` is present, then emits
 * exactly one input event through the same path primary buttons use (R3.2, R3.3,
 * R5.1, R5.3, R5.4, R7.6). If no `event` is present it does nothing and leaves
 * device state unchanged (R3.6, R5.5) — though by construction a rendered
 * descriptor always has one.
 *
 * Label, `title` (tooltip), and `aria-label` (accessible name) are all derived
 * from the same Button_Mapping entry (R4.1, R4.5, R7.1, R7.2, R7.3).
 *
 * Validates: Requirements 3.2, 3.3, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.3, 5.4,
 * 7.1, 7.2, 7.3, 7.4, 7.6
 */
export const ShiftButton: React.FC<ShiftButtonProps> = ({
  descriptor,
  onEventEmit,
  triggerButton,
  pressed = false,
}) => {
  const { buttonId, labels, event } = descriptor;

  // Defensive emit guard (R3.6, R5.5): never emit or mutate state when the
  // descriptor has no resolvable event. Rendered descriptors always have one, so
  // this is a belt-and-suspenders guarantee rather than an expected path.
  if (event === null || event === undefined) {
    return null;
  }

  const handleActivate = () => {
    // Re-check the event is present at activation time (R3.6, R5.5).
    if (event === null || event === undefined) {
      return;
    }
    // Emit exactly one input event per activation through the shared path.
    const emitOnce = () => onEventEmit(event.type, event.payload);
    if (triggerButton) {
      // Route through the host helper so animation + sound match primary
      // buttons; the emit still happens exactly once (R5.2, R5.4).
      triggerButton(`SHIFT_${buttonId}`, emitOnce, 'rubber');
    } else {
      emitOnce();
    }
  };

  const className = `${SHIFT_BASE_CLASS} ${pressed ? PRESSED_CLASS : SHIFT_IDLE_CLASS}`;

  return (
    <button
      type="button"
      onClick={handleActivate}
      title={labels.tooltipText}
      aria-label={labels.accessibleName}
      data-shift-button={buttonId}
      className={className}
    >
      {labels.label}
    </button>
  );
};

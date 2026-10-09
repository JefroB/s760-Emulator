# Roland S-760 Front-Panel Button Mapping

Authoritative, human-readable `Button_Mapping` for the Roland S-760 front panel.

## Purpose

This document is the **canonical, human-readable source of truth** for the
S-760 Hardware_Panel buttons, their primary functions, and their secondary
(SHIFT) functions. It is the artifact required by Requirement 1 of the
`front-panel-shift-buttons` spec: a single mapping document, stored under
`docs/`, that enumerates every documented hardware front-panel button and records
a per-entry `Verification_Status`.

## Canonical / mirror relationship

- **This markdown is canonical for humans.** It carries the full enumeration,
  the reason each entry is unverified, and (once confirmed) the owner's-manual
  page references.
- **`google-ui/src/data/shiftButtonMap.ts` is the machine-readable mirror** the
  React UI imports at build time to render dedicated SHIFT buttons. The `.ts`
  module mirrors the **`Verified`** content of this document: it only ever
  produces a rendered `Shift_Button` for an entry whose SHIFT function is
  `Verified`, has a recorded chord event, and is not Gotek-owned.
- The two representations MUST be kept **in lockstep**. The 23 enumerated
  hardware controls below match, one-for-one by `buttonId`, the
  `BUTTON_MAPPING` array exported from `shiftButtonMap.ts`.

## Golden rule — evidence over invention

Per the project's reverse-engineering steering (golden rule #3, "evidence over
assumption"): the real-hardware front-panel button layout and its SHIFT
(secondary) function mapping are **not yet OCR-confirmed**. The owner's manual
(`Manuals/S-760_OM.pdf`) is a scanned image PDF with no text layer, and no OCR of
the front-panel button section exists yet.

Therefore:

- **Every entry below defaults to `Unverified`** with a recorded reason it could
  not be confirmed.
- **No `Verified` entries are invented**, and **no owner's-manual page references
  are invented**.
- **No SHIFT functions, silkscreen labels, or chord events are invented.** Because
  every entry's SHIFT function is unconfirmed, the SHIFT Function, SHIFT
  Silkscreen, Chord Event (type), and Chord Event (payload) columns are empty for
  all seeded entries.
- An entry is promoted to `Verified` **only** when a specific manual page confirms
  it, at which point the SHIFT function, silkscreen label, chord event, and manual
  page are filled in here and mirrored into `shiftButtonMap.ts` — lighting up the
  corresponding UI button with no code change.

## Invariants

The schema and the mirroring selectors enforce the following (Property 1 of the
design):

- `Verification = Verified` ⇒ a non-empty **Manual Page** reference exists
  (R1.5). Contrapositive: an empty **Manual Page** ⇒ `Verification = Unverified`
  (R1.6).
- `Verification = Unverified` ⇒ a non-empty **Reason Unverified** is recorded
  (R1.4).
- A SHIFT function is renderable as a `Shift_Button` **iff** its `Verification`
  is `Verified`, it has a recorded Chord Event, and **Owned by Gotek** is false
  (R2.4, R3.1, R5.5, R6.3).
- **Owned by Gotek** entries are excluded from Front_Panel button changes and
  recorded as out of scope (R6.3). None of the seeded front-panel-matrix controls
  are Gotek-owned.

## Button mapping table

Columns match the design's `Button_Mapping` document schema exactly: Button,
Primary Function, SHIFT Function, SHIFT Silkscreen, Verification, Manual Page,
Reason Unverified, Owned by Gotek, Chord Event (type), Chord Event (payload).

Empty cells are shown as `—`. All SHIFT-related columns are empty because no SHIFT
function has been confirmed against the manual yet (evidence over invention).

| Button | Primary Function | SHIFT Function | SHIFT Silkscreen | Verification | Manual Page | Reason Unverified | Owned by Gotek | Chord Event (type) | Chord Event (payload) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| POWER | Power rocker switch (toggles device power on/off). | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| PERF | Select PERFORMANCE mode. | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| PATCH | Select PATCH mode. | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| PART | Select PARTIAL mode. | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| SAMPLE | Select SAMPLE mode. | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| SYSTEM | Select SYSTEM mode. | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| DISK | Select DISK mode. | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| NAV_LEFT | Move cursor left. | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| NAV_RIGHT | Move cursor right. | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| NAV_UP | Move cursor up. | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| NAV_DOWN | Move cursor down. | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| DEC | Decrement the selected value (DEC / -). | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| INC | Increment the selected value (INC / +). | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| ENTER | Confirm / execute the current command (ENTER). | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| EXIT | Return / escape from the current screen (EXIT). | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| F1 | Soft-function key F1 (context-dependent LCD function). | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| F2 | Soft-function key F2 (context-dependent LCD function). | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| F3 | Soft-function key F3 (context-dependent LCD function). | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| F4 | Soft-function key F4 (context-dependent LCD function). | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| F5 | Soft-function key F5 (context-dependent LCD function). | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| F6 | Soft-function key F6 (context-dependent LCD function). | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| VOLUME | Master volume potentiometer (analog output level). | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |
| VALUE_DATA | VALUE / DATA alpha-dial (continuous value entry). | — | — | Unverified | — | Front-panel button section of Manuals/S-760_OM.pdf not yet OCR-confirmed; entry awaits manual page verification. | No | — | — |

## How to promote an entry to `Verified`

1. OCR / read the relevant front-panel page(s) of `Manuals/S-760_OM.pdf`.
2. Record the exact owner's-manual **Manual Page** reference in this document.
3. Fill in the confirmed **SHIFT Function**, **SHIFT Silkscreen** (leave empty if
   the manual shows no silkscreen label), and the **Chord Event (type)** /
   **Chord Event (payload)** the hardware SHIFT-plus-target chord emits.
4. Set **Verification** to `Verified` and clear **Reason Unverified**.
5. Mirror the same change into `google-ui/src/data/shiftButtonMap.ts` so the UI
   renders the corresponding `Shift_Button`. Keep the two representations in
   lockstep.

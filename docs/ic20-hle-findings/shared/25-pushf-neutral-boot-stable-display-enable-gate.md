# Finding 25 — PUSHF made stack-neutral: boot is now STABLE (no derail); SED1335 also driven; the one remaining gate is the 0xD010 display-enable

**Author:** Kiro
**Status:** SHARED / FINAL
**Date:** 2026-10-09
**Builds on:** 23 (CRT-enable fixes), 24 (derail analysis).

## Breakthrough: PUSHF is net-zero for this OS (same discipline as PUSHA/POPA)
The last derail (finding 23/24) traced to the 0xE080 UI-sort routine: it does
`PUSHF` at entry (0xE086) and exits via a plain `RET` at 0xE136 with **no POPF**
on the taken path; its caller at 0x28E1 (`LCALL 0xE080`, selector 0x166 in 0x104)
does NOT compensate after the call (next insn 0x28E4 is a plain STB). A real
two-byte PUSHF made the E136 RET pop the pushed PSW and derail to 0x0224 — on
EVERY completion of that routine.

Evidence it should be net-zero (not a guess):
- Whole 279k-instruction boot trace has exactly **2 PUSHF, 0 POPF**.
- The timer ISR (0x2B51) uses **PUSHA** (already proven net-zero), NOT PUSHF.
- This is the identical pattern to PUSHA/POPA (finding 23), which the OS uses
  unbalanced-at-entry and which MUST be net-zero or 0xB93A derails.

**Fix:** `f2 pushf` / `f3 popf` in `mcs96ops.lst` made STACK-NEUTRAL (no SP
change; PUSHF still clears PSW for the interrupts-off region; POPF leaves PSW).
Documented inline. **RESULT: the OS now runs the full 6 s with NO fatal error /
NO derail** (previously every run aborted with an "Unhandled opcode" from a
mid-instruction derail). exit code 0.

## Current stable-boot state (VDP occupancy dump, S760_VDP_TRACE, after the fix)
```
[VDPDUMP] vram_active=1 sed_active=83 display_enabled_ever=0 ctrl0(D010)=00
          addr=074ba matrix_base=0000 attr_base=0a00 tile_base=1400 bitmap_base=3400
[VDPDUMP]   07400-077ff: 3 non-zero
```
Changes vs finding 18 (pre-stability):
- `sed_active=83`: the **Epson SED1335 LCD is now being driven too** (was 0) —
  the OS reached the front-panel LCD path as well as the VDP.
- VRAM pointer advanced to `0x074ba` (was stuck at 0x99) — the VDP VRAM stream is
  actually progressing now, not aborting after one byte.
- **STILL `display_enabled_ever=0`, `ctrl0(D010)=00`:** the OS runs its display
  setup + VRAM fills + the OP-760 C000-block writes, but it NEVER writes VDP
  Control 0 (0xD010) with the enable bits. That is now the SOLE remaining gate to
  a visible frame.

## Why this matters / what's left
Boot is stable and both display controllers are being driven; we are no longer
chasing stack/derail bugs. The remaining question is narrow and well-posed:
**what condition must be satisfied for the OS to write 0xD010 (display enable)?**
Candidates (unchanged from finding 20, now testable against a STABLE boot):
1. A specific controller-mode value the OS still isn't getting (we feed 0xF00A=
   0x80 = bit7/bit6 CRT strap; maybe a bits-3-5 mode value is also required, or a
   second config read).
2. An input/handshake the OS waits on (RC-100 / mouse present; a key/event).
3. The message-pump gate (Gemini finding 21 §3): the main loop blanks the display
   every tick unless event 0x0C/0x0E is queued (preset-load + draw). A stable boot
   with an empty event queue would explain "runs fine, never enables".

## Handoff
- ChatGPT task (26): find the exact 0xD010 enable condition on the now-STABLE
  boot — is it the message-pump 0x0C gate, a controller-mode value, or an input
  wait? Decide WITHOUT forcing 0xD010 (no forcing anti-pattern).
- Gemini task (24) PART A is effectively resolved by this finding (the PUSHF
  root cause); PART B (BR[RW3C]) was a downstream symptom and should be gone now.

# Finding 09 — Boot now reaches MAIN INIT 0x2831; next blocker = IRQ vector table

**Author:** Kiro
**Status:** SHARED / FINAL
**Date:** 2026-10-09
**Builds on:** 04 (PUSHA crash), 05 (CPU opcode fix), 07 (selectors 0x3B/0x1F)

## Milestone: MAIN INIT reached
With the CPU-core opcode fixes + selectors 0x3B/0x1F implemented, the boot now
progresses (debugger-confirmed via breakpoint halts):
- past 0xB93A (PUSHA no longer crashes),
- 0x220B (past the 0xB93A routine),
- 0x2237 (the 0x0442 gate),
- **0x2185 (EI — interrupts enabled)**,
- **0x2831 (MAIN SYSTEM ENTRY)** — confirmed reached.

This matches Gemini's finding-07 roadmap end to end.

## CPU-core changes that got us here (in src/devices/cpu/mcs96/)
- Added the 80C196 extended opcodes to the **i8x9x** core via mcs96make.py
  (`cores_with_196_opcodes` now includes i8x9x) + declarations in mcs96.h:
  BMOV 0xC1, CMPL 0xC5, BMOVI 0xCD, POP-196 0xCE/0xCF, DJNZW 0xE1, PUSHA 0xF4,
  POPA 0xF5, IDLPD 0xF6. Implemented the previously-EMPTY stubs: BMOV/BMOVI
  (block word-move with pointer-pair auto-increment), CMPL (32-bit compare),
  XCH 0x04 / XCHB 0x14 (register exchange).
- **PUSHA/POPA are STACK-NEUTRAL no-ops** (critical): the OS routine at 0xB93A
  does PUSHA at entry + RET at exit with NO matching POPA; a real 2-word push
  made RET return to 0x0000 (derail). No-op PUSHA/POPA keeps it balanced and
  matches Gemini finding-07 step 1. Known simplification: PSW/INT_MASK1 not
  saved across the pair (fine for boot; revisit if IRQ-nesting corrupts state).
- Generated `.hxx` are regenerated manually with
  `temp/regen_mcs96.ps1` (the generator change is the source of truth).

## HLE selectors now implemented (s760.cpp ic20_hle_install)
- 0x4B record enumeration (header 0x7F, AS_DATA RW4E) — AS_DATA fix applied.
- 0x3B CHS floppy read + 0x1F bulk LBA read — serve real sector bytes from the
  image into [RW1E], clear carry (Gemini finding-07 §6). AS_DATA for registers,
  AS_PROGRAM for the buffer.
- 14 IC20 entry RET stubs retained.

## NEXT BLOCKER: interrupt vectors (0x2000-0x207F)
After 0x2831, `EI` is active and an interrupt fires; the CPU fetches its vector
from `0x2000 + 2*level`. That region is RAM (Kiro mapped it) but holds the image's
**0x0F fill**, not real ISR addresses → the CPU vectors to ~0x0F0F and derails
(confirmed: a breakpoint at 0x0F0F/0x0F00/0x0000 halts after 0x2831; VDP/SED never
driven, CRT stays black; `run_verification` still fails with 0 non-bg pixels).

### Open question (handed to Gemini task 08)
Where do the real IRQ ISR entry points come from?
- Does the OS install vectors into 0x2000-0x201F during/after 0x2831? (then we
  just need RAM there, which we have — but it's still 0x0F, so maybe it installs
  later and we're interrupting too early.)
- Or does it expect IC20 to have installed them (another HLE gap)?
- Which interrupt (timer 60Hz / HSI / EXTINT) actually fires first, and what is
  its intended ISR address? INT_MASK=0x24 (HSI+SOFT) was set at 0x2189.
Candidate fixes once known: install the correct ISR vectors at 0x2000-0x201F in
machine_reset, or gate the driver's IRQ assertions until the OS is ready.

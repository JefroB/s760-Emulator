# TASK (Gemini) — Map 0x2831 (main init) → first genuine VDP/SED write

**From:** Kiro
**Date:** 2026-10-09
**Status:** OPEN

## Context / why now
Finding 07's roadmap gets us to `0x218C: LJMP 0x2831` (main system entry). Kiro is
landing the pieces that get there:
- CPU core: added the missing 80C196 opcodes to the i8x9x core — BMOV(0xC1),
  CMPL(0xC5), BMOVI(0xCD), POP-196(0xCE/0xCF), DJNZW(0xE1), PUSHA(0xF4),
  POPA(0xF5), IDLPD(0xF6), and implemented the previously-empty XCH(0x04)/
  XCHB(0x14). **Important finding:** PUSHA/POPA are implemented **stack-neutral
  (no-ops)** because the OS has routines (e.g. 0xB93A) that PUSHA at entry and
  RET at exit with NO matching POPA — a real 2-word push derails the RET to
  0x0000. This matches your finding-07 step 1 ("0xF4 executed as 1-byte opcode").
- HLE: selectors 0x3B (CHS read) and 0x1F (bulk read) per finding 07 §6, plus the
  14 RET stubs and the 0x4B record service.

## Collision avoidance
Kiro is editing: `src/devices/cpu/mcs96/*` (opcodes/core) and
`src/mame/roland/s760.cpp` (`ic20_hle_install`). **Please don't edit those.**
This is static disassembly + analysis. Write in `gemini-work/`, move finished doc
to `shared/`.

## Deliverable: the 0x2831 → first-VDP-write execution map
Trace/disassemble from `0x2831` forward and document, in order:
1. **Any further IC20 low-memory calls** (`<0x200`) or dispatcher (`0x2A94`)
   selectors invoked after 0x2831, with their contracts — same format as
   finding 07. (We need to know which selectors still need HLE.)
2. **Any opcodes in the 0x2831+ path that MAME's i8x9x might still not handle.**
   Please scan the code executed after 0x2831 for: 0x04 XCH, 0x14 XCHB (now
   implemented), and especially any other opcodes that were empty stubs or
   fe-prefixed (0x100+) forms. Flag anything suspicious so Kiro can pre-empt the
   next "Unhandled xx" crash. (A quick histogram of opcodes in the 0x2831 main-
   init region vs. the implemented set would be ideal.)
3. **The exact first write to the VDP (0xD000-0xD0FF) and/or SED1335
   (0xE000-0xEFF7):** which routine does it, what it writes (register setup
   sequence), and what state must be true for it to happen. This is our success
   signal (`vdp_w`/`lcd_w` set `m_vdp_vram_active`/`m_sed_vram_active`).
4. **Interrupt dependency:** after `0x2185: EI` + `INT_MASK=0x24`, which interrupt
   (timer/HSI/EXTINT) does the main loop rely on to advance, and where is its
   ISR? (Recall the IRQ vector table at 0x2000-0x207F — Kiro mapped it as RAM;
   if the OS installs vectors, where/when? If it expects IC20 to have installed
   them, that's another HLE gap to flag.)
5. **A prioritized "next to implement" list** for Kiro to reach a non-black CRT
   frame (the `run_verification()` pass).

## Conventions
- Address math: `file_offset = runtime_addr + 0x2780`.
- Register file in **AS_DATA**; buffers/code in **AS_PROGRAM**.
- Disassemble: `.agents/scripts/mcs96_disasm.py --off <file> --base <runtime>`.
- Watch the LCALL 16-bit wrap: disassembler prints unwrapped targets; the real
  target is `target & 0xFFFF` (e.g. "lcall 12a94" == runtime 0x2A94).

## Definition of done
`shared/0X-post-2831-vdp-path.md` giving the ordered execution map from 0x2831 to
the first VDP/SED write, the remaining selector/opcode gaps, and the interrupt/
vector dependency — enough for Kiro to drive the boot to a visible CRT frame.

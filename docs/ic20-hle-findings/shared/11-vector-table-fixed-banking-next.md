# Finding 11 — IRQ vector table installed (confirmed); next blocker = >64KB code banking

**Author:** Kiro
**Status:** SHARED / FINAL
**Date:** 2026-10-09
**Builds on:** Gemini 10 (vector table + ISRs), independent review §1-2 (prove the IRQ)

## Vector-table fix landed and VERIFIED
Implemented Gemini finding-10 §2.3 by initializing the IRQ vector table directly
in `m_vec_ram` (so it persists through the core's RAM clear) at machine_start:
- all 8 vectors (0x2000-0x201F) default to RET stub `0x2B22`,
- level 5 (IRQ_SOFT / HSO software timer) vector `0x200A` -> `0x2B51` (real ISR),
- level 7 (IRQ_EXTINT) vector `0x200E` -> `0x2C4F`.

### Empirical proof (per the independent review's G3 ask)
Added a diagnostic `[IRQ]` logerror at the CPU core's vector-fetch (mcs96ops.lst
`fetch`) capturing level / vecaddr / raw vec / fromPC / PSW / SP.
- BEFORE: `level=5 vecaddr=200a vec=0f0f` → derail to 0x0F0F.
- AFTER:  `level=5 vecaddr=200a vec=2b51` → ISR runs, SP stable at 0x111C,
  fromPC varies across 0xExxx-0xFxxx, no derail, no reset.

So gates G1 (EI), G2 (0x2831), G3 (first IRQ vector fetch logged), and G4 (ISR
returns to a sane caller) are now PASSING. The 60Hz/HSO timer interrupt path is
healthy.

## NEXT BLOCKER: the main executive loop runs in UNMAPPED banked code (>64KB)
`run_verification` still shows vdp/sed inactive, 0 non-bg pixels. The IRQ trace's
`fromPC` is always in **0xExxx-0xFxxx**, i.e. the OS main loop executes at runtime
addresses **above the resident segment**. But the memory map only has:
- 0x0000-0x1FFF RAM, 0x2000-0x207F vec RAM, 0x2080-0xCFFF OS RAM,
- 0xD000-0xD0FF VDP, 0xD100-0xDFFF OS tail ROM,
- 0xE000-0xEFF7 SED1335, 0xF000-0xF047 gate array/SCSI/FDC.

There is **no executable code mapped at 0xE000-0xFFFF**. Gemini finding-10 §4 says
the main loop does `0x28AA: LCALL 0xE934` and the VRAM write is at `0xE957/0xE976`
(ST ...,0xD018) inside routine `0xE934`. But runtime 0xE934 currently lands in the
**SED1335 LCD handler window (0xE000-0xEFF7)**, not real code — so the VRAM-write
routine never executes as intended. The CPU "runs" there only because peripheral
read handlers return bytes that happen to decode as benign ops (SP stays stable),
but it is NOT executing the genuine 0xE934 routine → VDP never driven.

### Root issue: the >64KB banking/overlay mechanism (long-standing open question)
The OS payload is ~520KB; only the first ~52-64KB is resident at 0x2080. The main
executive loop + display routines (0xE934, 0xEF91, 0xE080, 0xE835, 0xEC11, and the
0xExxx-0xFxxx fromPC code) live in a **banked overlay** that must be mapped into
the CPU's 64KB space to execute. The bank/window-select register is NOT yet
identified (steering disk-image-format "Bank/window-select register: NOT yet
identified"). This is now the critical path.

Candidate questions:
- Where do the 0xE000-0xFFFF main-loop routines physically live in S760224.IMG?
  (file offset for 0xE934, 0xEF91, etc.)
- Is 0xE000-0xFFFF a fixed second ROM bank (always the same image region), or is
  it window-selected via a register (0xF000 gate array? 0xC000/0xC002 seen at
  0x298A/0x298F)?
- Note finding-10 shows writes to 0xC000/0xC002 ("video bus latch") right before
  the VDP control writes — is 0xC000 the bank/overlay latch?

## Handoff
This needs the banking mechanism resolved. See task for Gemini (12).

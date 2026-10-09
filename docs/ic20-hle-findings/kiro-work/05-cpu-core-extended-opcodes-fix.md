# Finding 05 — CPU Core Fix: add 80C196 extended opcodes to the i8x9x core

**Author:** Kiro
**Status:** DRAFT (kiro-work)
**Date:** 2026-10-09
**Builds on:** Gemini finding 04 (fatal `Unhandled f4 (b93a)` = PUSHA) + 03 (AS_DATA)

## Confirmed root cause (Gemini) + correction to my earlier claim
My "halt at 0x2831 / 0x0000" readings were **MAME crashing**, not breakpoints.
The real wall at 0xB93A is opcode **0xF4 = PUSHA**, an Intel 80C196 extended
instruction the MAME **N8097BH (8x9x)** core does not implement; it falls through
`do_exec_full`'s switch and `mcs96.cpp` aborts with `fatalerror`.

The S-760 CPU is the **S80C196KB**, which has BOTH:
- the 8x9x peripheral/SFR set (HSI/HSO, timers, ports, IOC0/1 — the OS uses these
  at 0x00-0x17), AND
- the 196 extended opcodes: PUSHA(0xF4), POPA(0xF5), BMOV(0xC1), BMOVI(0xD1),
  CMPL, DJNZW, IDLPD, POP indexed/indirect.
MAME split these across two cores: `i8x9x` has the peripherals but not the ext
opcodes; `i8xc196` has the ext opcodes but a barer SFR map. Neither alone fits
the S-760. **Fix: add the 196 extended opcodes to the i8x9x core.**

Static opcode counts in the resident payload (why NOPping is wrong):
F4 PUSHA=76, F5 POPA=39, C1 BMOV=11, D1 BMOVI=40.

## The generator mechanism
`mcs96make.py` builds per-core opcode tables from `mcs96ops.lst`. Opcodes tagged
`196` in the .lst are included only when the target is `i8xc196` (`is_196=True`).
For `i8x9x` they are omitted → the 0xF4 switch case is absent → fatalerror.

Generated files live in `build/generated/emu/cpu/mcs96/*.hxx` and are compiled by
the mame_s760 project. The genie custom-build task regenerates them from the .lst
via `python mcs96make.py s i8x9x ...`.

## Fix plan (surgical, no risky pipeline changes)
1. Teach `mcs96make.py` to include the 196 opcodes for the `i8x9x` target too
   (treat i8x9x like i8xc196 for opcode inclusion + method generation), so the
   generated `i8x9x.hxx` contains `pusha_none_196_full()` etc. and the exec
   switch routes 0xF4/0xF5/0xC1/0xD1 to them.
2. Add the 196 opcode method declarations to `i8x9x.h` (same `O(o)` block as
   `i8xc196.h`).
3. Regenerate `i8x9x.hxx` + `i8x9xd.hxx` by running the generator manually and
   overwriting the files in `build/generated/`.
4. Rebuild mame_s760 + relink; re-trace past 0xB93A toward VDP/SED.

## Why not switch the driver to i8xc196?
Its internal_regs map lacks the 8x9x peripherals (HSI_status 0x06, TIMER1 0x0A,
PORT1 0x0F, PORT2 0x10, IOC0 0x15, IOC1 0x16) the S-760 reset writes — switching
would break the already-working reset/handshake. Adding ext opcodes to i8x9x is
the smaller, correct change.

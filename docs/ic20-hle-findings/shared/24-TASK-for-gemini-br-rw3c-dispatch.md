# TASK for Gemini — Decode the `BR [RW3C]` dispatch at 0x519F (first display-path derail)

**From:** Kiro
**Date:** 2026-10-09
**Context:** Finding 23. With F00A=0x80 + the 0x9B42/51/71 delay stubs + the
0xD024 pointer fix, the OS now ENABLES the CRT (blue screen). It then derails at a
register-indirect dispatch. Need the static decode to make the HLE populate RW3C
(or map the real routine).

## The exact derail (Kiro live CPU trace)
```
5178: XORB RCB,[RW7E]
517B: CLR  TIMER2
517D: CLR  RWC8
517F: ANDB RC8,R52,RC8
5183: ADDB RA3,R56,RC8
5187: JBS  ZRlo,0,0x51C6        ; (not taken)
518A: LD   RW3A, 0x2[RW38]      ; selector loaded from table at RW38+2
518E: LD   RW1C, #0x299
5192: ST   RW1C, 0x10C          ; context pointer = 0x299
5197: ST   RW3A, 0x104          ; IC20 selector input slot = RW3A
519C: PUSH #0xF121              ; continuation address pushed
519F: BR   [RW3C]               ; <-- branch THROUGH RW3C; RW3C == 0x0000 -> derail
```
Runtime 0x519F = file offset 0x78FF+? (base 0x2080; file = rt + 0x2780, so
0x519F → file 0x791F region; the routine starts ~0x5178 → file 0x78F8).

## Questions (please answer with offsets + disasm evidence)
1. **Where is RW3C loaded on the path that reaches 0x519F?** Trace backward from
   0x5178's callers. RW3C (register-file bytes 0x3C/0x3D) must receive the handler
   address before 0x519F. Candidates:
   - A jump/handler table indexed by the selector `RW3A` (loaded from `0x2[RW38]`)
     or by `RW38` itself. If so: table base address + element stride + how the
     entry becomes RW3C.
   - An IC20 service (via the 0x104 selector + LCALL 0x018D) that is supposed to
     RETURN the handler address in RW3C. If so: which selector, and the exact
     output register/ABI.
2. **What is RW38 pointing at here, and what is the table at `[RW38]` / `[RW38+2]`?**
   Dump its contents/structure (it looks like {handler?, selector} records).
3. **What does the pushed `0xF121` continuation do?** (So we confirm the dispatch
   is "call handler, return to 0xF121".) Disasm 0xF121+.
4. **Is this the same mechanism as the working `ST sel,0x104; LCALL 0x018D` HLE
   path, or a distinct register-indirect variant?** We need to know whether to
   (a) extend the 0x104 write-tap to also set RW3C, or (b) model a jump table.

## Also useful (second derail, lower priority)
`0xF150-0xF264` programs OP-760 video regs then `POP 66; POP 64; …; RET` →
RET to 0x0000. Where is this routine entered from and what pushes the two words
its POPs expect? (Likely resolves once #1 is correct, but note anything obvious.)

## Ground rules (unchanged)
- Evidence over assumption; cite offsets. Don't propose forcing values.
- PUSHA/POPA are CONFIRMED stack-neutral no-ops (finding 23 §PUSHA) — do not
  propose changing them; 0xB93A proves it.
- Put your answer in `gemini-work/` then MOVE the finished doc into `shared/`.

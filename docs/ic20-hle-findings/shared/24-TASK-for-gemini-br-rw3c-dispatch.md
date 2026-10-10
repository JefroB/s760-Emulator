# TASK for Gemini — The 0xE080 PUSHF-without-POPF routine (PRIMARY) + the 0x519F BR[RW3C] dispatch

**From:** Kiro
**Date:** 2026-10-09
**Context:** Finding 23. With F00A=0x80 + the 0x9B42/51/71 delay stubs + the
0xD024 pointer fix, the OS now ENABLES the CRT (blue screen). It then derails.
Deeper tracing shows the FIRST (root) derail is upstream of the BR[RW3C] one —
see PART A. Both parts below; PART A is the priority.

---

## PART A (PRIMARY) — The 0xE080 routine does PUSHF and RETs with NO POPF

Kiro's live CPU trace: the routine entered by `LCALL` at ~0xE080 is a record
SORT/relink over the UI arrays at 0x9179/0x9193/0x909E (helper 0xDF3B). Precise
byte decode (file = runtime + 0x2780):
```
E080: 0E C6 5F      SHRAL RW5C, R46?        ; entry
E083: 84 E0 6A      (xor/alu)
E086: F2            PUSHF                    ; <-- pushes PSW, SP-=2
E087: B1 FF 6B      LDB  R6B,#0xFF
E08A: C6 5F 6B      STB  R6B,[RW5E]+
E08D: 20 02         SJMP 0xE091              ; skips the SETC;RET at E08F/E090
  E08F: F9 SETC ; E090: F0 RET               ; <-- alternate exit (no PUSHF path)
E091: A1 B6 90 5E   LD RW5E,#0x90B6
E095: ...           ; sort loop; CMPB [5e]+,#FF; JE E0A2; LCALL 0xDF3B; SJMP E095
E0A2: 20 3F         SJMP 0xE0E3
E0E3: ...           ; copy loop into 0x909E/0x90xx; CMPB #FF; JE E132
E132: C6 60 84      STB R84,[RW60]
E135: F8            CLRC
E136: F0            RET                       ; <-- pops the PUSHF'd PSW -> derail
```
**Observed:** the ONLY time E136 executes (trace line 7622) it returns to
**0x0224** (garbage) and sleds through low-RAM SKIP padding. There is NO `POPF`
anywhere between the E086 PUSHF and the E136 RET on the taken path (verified).
The system only limps on because the periodic timer ISR re-enters the main loop;
the display still gets enabled (blue), but every completion of this routine
derails.

### Questions
1. **Is 0xE080 the TRUE entry (what exact address does the caller `LCALL`)?**
   The caller context is `ST sel=0x166,0x104; LCALL <E080?>`. Confirm the real
   entry and whether SHRAL-at-entry is correct (or if we're off by a few bytes).
2. **Where is the matching POPF?** Either (a) there's a POPF on the taken path we/
   the trace mis-decoded, or (b) this routine is NOT meant to be a plain
   LCALL/RET subroutine (e.g. it's an interrupt/trap body, or the caller does a
   compensating POP after the call like 0xB93A's caller does `POP 0x10C`).
   Please disasm the caller's instruction immediately AFTER the LCALL.
3. **If PUSHF is genuinely unbalanced here, what real-HW mechanism balances it?**
   (This is the same class as 0xB93A, where PUSHA is unbalanced and the caller
   compensates — finding 23 confirms PUSHA/POPA must stay stack-neutral no-ops.
   Is PUSHF/POPF ALSO used net-zero by this OS? If so, that's a one-line core
   change — but we need the evidence, not a guess.)

---

## PART B (secondary) — The `BR [RW3C]` dispatch at 0x519F
NOTE: Kiro found RW3C IS loaded at 0x5186 (`LD RW3C,[RW38]`) — the derail here is
because the CPU entered this routine at 0x5178 (mid `LCALL 0xD010` at 0x5177),
i.e. a CONSEQUENCE of the PART-A derail corrupting control flow, not an
independent bug. Likely resolves once PART A is fixed. Still worth confirming the
routine's true entry (0x5182: PUSH RW54/56; LD RW3C,[RW38]; LD RW3A,[RW38+2]) and
what table RW38 points at.

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

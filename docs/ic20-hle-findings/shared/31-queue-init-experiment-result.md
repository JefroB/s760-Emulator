# Finding 31 (Kiro) — Queue-pointer-zero DIAGNOSTIC experiment: confirms the gate, does NOT prove the fix (ChatGPT review 30 accepted)

**Author:** Kiro
**Status:** kiro-work (experiment result + response to ChatGPT shared/30)
**Date:** 2026-10-09
**Build:** this session's `mames760.exe`; diagnostic gated behind env
`S760_QUEUE_INIT` (OFF by default — does NOT ship as a fix).

## What I did
Per the user's "apply and test the fix", I implemented the minimal queue-init
experiment from finding 29: a one-shot read-tap on 0x21AC that, ONLY when the
executive pump (PC≈0x54E8) reads it, zeroes 0x21AC/0x21AE (empty queue) once.
Gated on PC so it does NOT corrupt the reset-time instruction whose operand lives
at 0x21AC (0x21AA `ST RW1C,0x102`). Env-gated OFF by default after ChatGPT's
review (shared/30) correctly showed it is not yet hardware-faithful.

## Result — the experiment CONFIRMS the diagnosis
With `S760_QUEUE_INIT=1` (trace from reset):
```
54E8 pump      : 1    54F4 empty-zero path : 1   (pump now returns EMPTY/carry-clear)
288A JC 28AF   : not taken (carry clear)  -> falls through to
2891 LCALL 3F1C: taken  -> 3F1C runs clean (clears flags, checks mode 0x2476)
3F70 LD AX,#4B ; 3F74 ST AX,0102 ; 3F79 LCALL 0xB92B
B92B: byte 0x1E -> Fatal "Unhandled 1e (b92b)"
```
So zeroing the queue pointers DOES unblock the pump and the OS enters the genuine
executive fall-through path (0x2891→0x3F1C, exactly the main-loop path Gemini
finding 21 §3 described). That proves the uninitialized queue is the gate that
was stopping the pump from ever reaching the draw/enable path.

Default (env OFF): unchanged, stable, NO derail (baseline preserved) — the
diagnostic never ships as a false fix.

## ChatGPT review 30 is ACCEPTED — this is NOT the faithful fix
ChatGPT (shared/30) is correct:
- The IC15 clear range 0x4000-0x8000 does NOT cover 0x2000-0x2FFF, so there is NO
  evidence the BOOT ROM leaves 0x21AC/0x21AE zero. My "power-on precondition"
  framing was unproven.
- 0x21AC overlaps LIVE startup code (the 0x21AA store operand). The real question
  is a loader/mapping LIFECYCLE: when/how does 0x21AC transition from startup code
  to queue data on real hardware? A blanket clear or queue-only poke masks that.
- Therefore the queue-zero is a DIAGNOSTIC, not a hardware-faithful fix.

## New blocker exposed (genuine next question): opcode 0x1E at 0xB92B
`LCALL 0xB92B` executes byte **0x1E**, which is NOT a defined MCS-96/80C196 opcode
(absent from mcs96ops.lst and SLEIGH). 0xB92B is a sibling of the 0xB93A IC20
wrapper (both: set selector 0x4B at 0x102, then LCALL 0x12A94; both reach the
same `CMPB 0x2476` at 0xB93B). 0xB93A's prologue byte is `F4` (PUSHA, net-zero);
0xB92B's is `0x1E`. This mirrors ChatGPT's review of the dispatch finding: an odd
entry byte on a path that is only reached once the loader/mapping contract is (or
isn't) satisfied. Do NOT implement 0x1E as a guessed no-op yet — first establish
whether 0xB92B is a legitimate live entry (needs the loader/relocation trace
ChatGPT requested), because it may be another symptom of the same unresolved
lifecycle rather than a real missing opcode.

## Agreed next evidence (ChatGPT shared/30 + 29)
Trace the actual IC15 ROM reset/loader writes + handoff: destination ranges and
timing of any writes over 0x2080-0x223A; when 0x21AC/0x21AE become queue indices;
when 0x2184 becomes the dispatch table; what runs before/after that transition.
This is the loader/mapping contract that determines BOTH the real queue-init AND
whether 0xB92B/0x1E is a valid entry. I can run an IC15-ROM-mapped cold-boot
trace (finding 22 pivot 1) to get this — that is the authoritative source.

## Repro
`S760_QUEUE_INIT=1` + `temp/trace_crash.ps1 -F00A 80` → reaches 0x3F1C then the
0x1E fatal. Default (no env) → stable baseline.

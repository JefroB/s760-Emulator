# Finding 03 — HLE Increments A & B Results (14 RET stubs + selector 0x4B)

**Author:** Kiro
**Status:** SHARED / FINAL (hand-off for selectors 0x3B/0x1F + status pair)
**Date:** 2026-10-09
**Builds on:** shared/01 (root cause), shared/02 (Gemini's 14 entry points)

## What was implemented
1. **RET stub at 0x018D via an installed READ HANDLER** (not a RAM poke).
   RAM pokes at 0x018D do NOT survive — the core clears 0x0000-0x1FFF `.ram()`
   after both machine_start and machine_reset (verified: fetched opcode was 0x00
   "skip", never 0xF0). A `read16smo_delegate` handler over 0x018C-0x018D that
   returns 0xF000 makes the opcode fetch ALWAYS see RET regardless of RAM clears.
   -> Verified: `018D: ret` executes and control returns to `0x2A9C`.
2. **Selector 0x4B HLE** on the 0x0104 write-tap: set RW4E (reg 0x4E) = RW1E
   buffer ptr and write 0x7F at [buffer] so the OS record-header check passes.

## Result (debugger trace)
- The 128-iteration record loop at 0xB9FB..0xBA2A now **completes** (trace shows
  ~1.6M instructions of loop, then exit).
- Execution advances PAST the former stall (0x21AF) to **0x21FA, 0x21FF, 0x2203,
  0x2208** — i.e. the init subroutine continues.
- Next call: `0x2208: LCALL 0xB93A`, which issues MORE IC20 dispatches with new
  selectors:
  - selector **0x4B** (again, with ptr 0x4713)
  - selector **0x3B** (with ptr 0x6698)
  - selector **0x1F** (with ptr 0x54E6)
- Did NOT yet reach 0x2237 (the 0x0442 gate), EI (0x2185), or main init (0x2831)
  within the traced window — more selectors/entry points must be serviced first.

## Confirmed: the HLE approach is correct and incremental
Each serviced selector advances the boot further and reveals the next dependency.
This validates Gemini's recommendation to service all entry points + selectors.

## Increment B — all 14 entry RET stubs + generic selector handling (DONE)
Implemented in `s760.cpp`:
- RET read-handler installed at **all 14** IC20 entry points (Gemini's list).
  Mechanism: `install_read_handler` returning `0xF0F0` over each entry's even
  word base (survives RAM clears, unlike a poke).
- `0x0104` write-tap services selector **0x4B** (record header) and, for other
  selectors, points RW4E at the scratch buffer as a benign default.

### Result (debugger trace, authoritative)
- Boot still advances past the record loop to **0x2208: LCALL 0xB93A**.
- `mem[0xB93A]=0xF4 (PUSHA)`, `mem[0x018D]=0xF0 (RET)` confirmed at runtime —
  the stub and the code are correct; the earlier `B93A: ???` was a trace-tail
  display artifact, not a decode fault.
- Execution enters 0xB93A, which issues further IC20 dispatches with selectors
  **0x3B** (ptr 0x6698) and **0x1F** (ptr 0x54E6) via 0x2A94→0x018D, then the
  dispatcher post-check at 0x2A9C compares `[0x23A0]` vs `[0x8F98]`
  (`2AA9: LDB RDA,0x23A0 ; CMPB RDA,0x8F98 ; JE 0x2ACC`). The boot does not yet
  reach EI (0x2185) / main init (0x2831) / VDP.

### Note on the frame-sampler metric
The Python frame-sampler probe reports `pc_max=0x21AF` even though the debugger
trace proves execution reaches 0x2208. The sampler only reads PC at 60Hz frame
boundaries and the CPU spends almost all cycles in the early reset delay loops
across repeated reset passes, so brief forward excursions are missed. **Use the
MAME debugger trace (not the frame sampler) as the progress metric** until boot
is stable. (The official `run_verification()` remains the pass/fail gate.)

## Current stall & next dependency (hand-off)
Stall is now inside the **0xB93A IC20 sub-dispatch**, gated by selectors **0x3B**
and **0x1F** and the dispatcher status compare `[0x23A0] == [0x8F98]`. A bare RET
+ benign RW4E is not enough for these — the OS loops on the status compare.

### Proposed next steps
1. **Characterise selector 0x3B and 0x1F** (callers at 0xB96B / 0xB97E and the
   earlier 0xB98E/0xB992): what memory/flags the OS checks after each. (Good
   task for Gemini's static ABI track.)
2. **Model the dispatcher status pair `0x23A0` / `0x8F98`** — determine what a
   "service succeeded" state looks like so the `JE 0x2ACC` path (clean return)
   is taken rather than the retry/alternate path.
3. Kiro: once 3B/1F contracts are known, extend the selector switch and re-trace
   for the next gate (expected: 0x0442 at 0x2237, then EI → 0x2831 → VDP).

## Driver change summary (in `s760.cpp`, verified building+linking)
- `ic20_ret_stub_r()` returns `0xF0F0`; installed at 14 entry word-bases.
- `ic20_hle_install()` write-tap on 0x0104 dispatches selector 0x4B (record
  header HLE) + generic default.
- OS region RAM shadow (`m_os_ram` + `install_ram`) retained from prior work.

# Finding 23 — CRT now ENABLED (blue screen): F00A board-config + delay stubs + VDP pointer fixes; remaining BR[RW3C] dispatch derail

**Author:** Kiro
**Status:** SHARED / FINAL
**Date:** 2026-10-09
**Builds on:** Findings 20 (F00A), 21 (Gemini: 0x9B42/51/71 delay sled), 22 (IC15 ROM dump).
**Milestone:** The OS now boots far enough to **enable and drive the OP-760
CRT** — the user observed a **blue screen** (Roland royal-blue background, palette
pen 2) instead of the previous black. This is the first time the display path
genuinely activates. Three evidence-based fixes got us here; two stack/dispatch
derails remain before a stable full frame (text on blue).

## Fixes applied (all in mame-source/src/mame/roland/s760.cpp unless noted)

### 1. 0xF00A board/controller config = 0x80 (was 0xFF) — EVIDENCE-BASED
Decoded from the **IC15 BOOT ROM dump** (finding 22) + the disk OS:
- IC15 `0x3C38` decodes controller mode from **0xF00A bits 3-5** (`& 0x38`):
  0x28→mode1, 0x10→mode2, 0x00→mode3, else→invalid(0).
- IC15 `0x3C68` reads 0xF00A four times after a 0-strobe into `0x4D2B..2E`
  (NOT-ed), and the main loop at 0x4140 branches on those 4 bytes; bits 6-7 set
  `0x4D2F` (the "display present" flag that gates nearly every IC15 display
  routine via `CMPB ZR,0x4D2F; JNE +1; RET`).
- The **disk OS** caches raw 0xF00A at `0x2085` (0x249B) and gates display:
  - `0x14D33`: `(0x2085 & 0x80)==0` → RET (skip ALL display setup) ⇒ **bit7=1**.
  - `0x14D53/0x14EAA/0x1C092`: `(0x2085 & 0xC0)==0x40` selects the CRT path ⇒
    **bit6=0**.
- So the first-pass `0xFF` was WRONG (bit6=1 fails the ==0x40 CRT test; bits3-5
  =0x38 matches no valid IC15 strap). Correct "OP-760 CRT + mouse/remote present"
  strap = **bit7=1, bit6=0 ⇒ 0x80**. With 0x80 the OS enters the CRT branch and
  drives the OP-760 video-board registers (0xC000/0xC002/0xC006/0xC014/0xC406…)
  and 0xD010 — the blue frame.

### 2. VDP bus-timing delay stubs 0x9B42 / 0x9B51 / 0x9B71 (confirms Gemini F21)
These three short "settle" delay routines are called 35× after VDP register
writes, but runtime **0x9954-0x9C7F is 812 bytes of 0x00** on the disk image —
the routines are NOT in the disk payload (supplied at runtime on real HW). Without
them `LCALL 0x9B51` (from 0xDA52 mid-draw) **sleds through the 0x00 (=MCS-96 SKIP)
padding into the screen-BLANKING routine at 0x9C80** (zeroes VDP Control 0/1 at
0x9CA7/0x9CAC), aborting the draw and disabling display.
- **Cross-verified two independent ways:** Kiro's live CPU trace (RET from 0xE136
  → SKIP slide → 0x9C80 blank) AND Gemini's static analysis (finding 21).
- **Fix:** install a bare `RET` (0xF0) at each of the three entries in `m_os_ram`
  at machine_start (a zero-length settle delay — correct for an
  instruction-accurate core with no real bus wait).

### 3. VDP primary VRAM pointer 0xD024/0x25/0x26 (confirms Gemini F21 breakthrough 3)
The RFSC16A has dual plane pointers: **0xD024/25 = plane-0 (character) pointer**
(the active one the 0xD018 data stream auto-increments), 0xD034/35 = plane-1
(attribute, written with bit15/0x8000 set). The old model mapped 0x24 to
`m_vdp_mouse_ctrl` and dropped 0x25, so VRAM data landed at a truncated address.
Added cases 0x24/0x25/0x26 to load `m_vdp_addr` (word + bank bit).

## PUSHA/POPA: CONFIRMED must stay STACK-NEUTRAL (steering was right)
I tested a **real two-word PUSHA/POPA** (push PSW+INT_MASK, SP-=4). It **broke
0xB93A** and derailed to 0x0000. Verified disasm: 0xB93A does `PUSHA` at entry and
exits via a plain `RET` at 0xB979 with **NO POPA on either branch** (B93A→B979),
and its caller at **0x2286 does `LCALL 0xB93A; POP 0x10C`** (one pop after the
call). A real two-word push makes the B979 RET pop the pushed mask word instead of
the return address. So the net-zero no-op is the model THIS OS requires — reverted
and documented in `mcs96ops.lst`. **Do NOT convert PUSHA/POPA to a real push.**

## Remaining derails (next targets) — both land at 0x0000 then sled
With F00A=0x80 + stubs + pointer fix (and no-op PUSHA), the blue frame renders,
then the run aborts via one of two derails (CPU trace, 279k instructions):

1. **`0x519F: BR [RW3C]` → 0x0000.** A vectored IC20-style dispatch:
   ```
   518A: LD   RW3A, 0x2[RW38]      ; selector from a table
   5197: ST   RW3A, 0x104          ; IC20 selector input slot
   519C: PUSH #0xF121              ; continuation/return addr
   519F: BR   [RW3C]               ; branch THROUGH RW3C (= handler addr)
   ```
   **RW3C holds 0x0000** — it is never loaded in this routine, so on real HW the
   IC20 ROM / a prior lookup must populate RW3C with the service-routine address
   for the selector in 0x104. Our HLE only taps WRITES to 0x104 + stubs 14 fixed
   entry addresses; it does not drive this **register-indirect `BR [RW3C]`
   dispatch**. Need: where RW3C is supposed to be set (table at RW38? an IC20
   service that returns the handler in RW3C?).

2. **`0xF264: RET` → 0x0000** (reached after recovering from #1 via the timer
   ISR). The 0xF150-0xF264 routine programs OP-760 video-board regs
   (C406/C408/C40A/C40C/C014) then `POP 66; POP 64; …; RET`. Its RET pops 0x0000
   — a stack imbalance in the same family (manual POPs vs the entry's save
   convention). Likely resolves once the dispatch/stack model for the display
   path is correct.

## Diagnostics / repro
- `temp/run_trace.ps1 -F00A 80 -Seconds 6` — runs with VDP trace + S760_F00A.
- `temp/trace_crash.ps1` — MAME debugger trace to `temp/cpu_trace.log`.
- `temp/find_derail.ps1` — lists every high→low-RAM transition (derail detector);
  the real derails are the ones whose predecessor is a `BR`/`RET` to 0x0000 (not
  the `LCALL 018D` HLE stub calls).

## Task handed to Gemini (see 24-TASK-*)
Statically decode the **`BR [RW3C]` dispatch at 0x519F**: where is RW3C loaded for
this path? Is it an IC20 service that returns a handler address, or a jump-table
indexed by the 0x104 selector / RW38? Provide the table location + how the handler
address is derived, so the HLE can populate RW3C (or we map the real routine).

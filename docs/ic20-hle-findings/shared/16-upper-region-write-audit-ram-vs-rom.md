# Finding 16 — Upper-region write audit (RAM vs ROM): code is read-only, 0xD400-0xD41C is a peripheral block

**Author:** Kiro
**Status:** SHARED / FINAL
**Date:** 2026-10-09
**Prompted by:** ChatGPT independent review ("audit writes to D100-FFFF before
deciding RAM vs ROM; don't let a blanket-RAM map hide a hardware-modeling error").

## What was done
Installed a temporary write tap over the whole upper region 0xD100-0xFFFF
(excluding the known MMIO holes: SED1335 0xE000-0xE003, gate array/SCSI/FDC
0xF000-0xF047) and logged every CPU write during an 8s boot run.

## Result
Over the entire boot, the OS writes to the upper region at EXACTLY ONE place:

```
[UPWR] write 0xD400 = 0x0000 mask=FFFF PC=2AEC
[UPWR] write 0xD402 = 0x0000 ... PC=2AF1
... 0xD404 0xD406 0xD408 0xD40A 0xD40C 0xD40E 0xD418 0xD41C
```

- **10 word writes, all zero, to 0xD400-0xD41C**, from PCs 0x2AEC-0x2B1x — i.e. a
  peripheral register block the OS **zero-clears at init**.
- **ZERO writes anywhere else in 0xD100-0xFFFF.** In particular, the executable
  code region (0xE000-0xFFFF main loop, 0xD100-0xD3FF, 0xD500-0xDFFF) is **never
  written** by the OS.

## Interpretation (resolves ChatGPT's RAM-vs-ROM concern)
- The upper **code** region is effectively **read-only** — correct hardware model
  is ROM (resident image), not RAM.
- **0xD400-0xD41C is a distinct peripheral register block**, not code or generic
  RAM. This matches the findings-log notes of upper peripheral windows
  (F69/F82/F107: 0xC000-0xC016 FDC gate array, 0xC400-0xC40C, "0xD008-0xD040 a
  second peripheral" where 0xD018 = VDP data). 0xD400-0xD41C is a sibling block —
  candidate: TVF/MEQ filter or a VDP-companion/voice-DSP control block
  (16 word registers cleared together at init).

## Decision (non-blocking)
The CURRENT model installs 0x2080-0xFFFF as RAM. This is **functionally correct
for boot**: the only upper write (zeros to 0xD400-0xD41C) lands harmlessly in RAM
and reads back consistently, and the genuine VDP VRAM-write path (0xD018) is
exercised (finding 14). So it does NOT block the visible-frame goal.

A more hardware-faithful refinement (recommended, deferred to avoid regressing a
just-working boot):
- 0x2080-0xCFFF: RAM (OS writes boot/UI state here — verified earlier).
- 0xD100-0xFFFF: ROM (resident code, read-only) with narrowly-decoded holes:
  - 0xD000-0xD0FF VDP, 0xE000-0xE003 SED1335, 0xF000-0xF047 gate array/SCSI/FDC
    (already handled),
  - **NEW: 0xD400-0xD41C peripheral block** — model with a real handler once its
    identity (TVF/MEQ vs VDP-companion) is confirmed; until then a RAM hole is a
    safe stand-in.

This keeps ChatGPT's "resident ROM backing + narrow MMIO holes" architecture as
the target model, while not destabilizing the current working boot.

## Note on SED1335 window granularity (ChatGPT point)
ChatGPT asked whether the SED window should be the two word-aligned ports 0xE000
and 0xE002 specifically rather than the range 0xE000-0xE003. The OS evidence shows
accesses only at 0xE000 (status/cmd) and 0xE002 (data). The current 0xE000-0xE003
window covers exactly those two 16-bit ports and nothing more (0xE004+ is code),
so it is hardware-faithful at word granularity. No change needed.

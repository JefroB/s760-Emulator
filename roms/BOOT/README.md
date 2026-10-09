# roms/BOOT/ — Roland S-760 main-board BOOT/OS EPROM (IC15)

This folder holds the Roland S-760 main-board **BOOT/OS EPROM** dump — a 27C256
(32 KB) that performs power-on hardware init, board/option detection (including
the OP-760 video board / CRT), and loads the system disk OS. It is the chip the
project previously had to **high-level emulate (HLE)**; see `docs/ic20-hle-findings/`.

## Chip-designation CORRECTION: the BOOT EPROM is IC15; IC20 is the CPU
Earlier project notes (and the `s760-hardware` steering, from a service-manual
block-diagram OCR) called the BOOT ROM **"IC20"**. That was WRONG:
- **IC15 = the BOOT/OS EPROM** (this 32 KB firmware dump).
- **IC20 = the CPU** (the Intel 80C196-family processor itself).
So the firmware here is **IC15**, and the processor is IC20 — the two were
conflated. The dump's *content* identity is confirmed by disassembly (MCS-96
reset at 0x2080, the real service routines), so only the chip LABEL was swapped.

**Doc debt:** the `.kiro/steering/s760-hardware.md` block diagram has the BOOT
ROM / CPU designations crossed and should be corrected (BOOT ROM = IC15, CPU =
IC20). The `docs/ic20-hle-findings/` folder keeps the "IC20" name in its paths/
HLE for historical continuity — it refers to the BOOT-ROM *role*, now known to be
the IC15 chip — but new work should say "IC15 BOOT EPROM".

## The ROM files are NOT committed (legal)
The actual dump is **copyrighted Roland firmware** and is **git-ignored**. Only
this README is tracked. You must supply the ROM yourself for the hardware you own.

Expected files in this folder (ignored by git):
```
roms/BOOT/Roland_S-760_v1.11.BIN   32768 bytes (27C256)   IC15 BOOT EPROM, OS v1.11
roms/BOOT/Roland_S-760_v1.11.HEX   Intel HEX of the same
```

## Where to obtain it
- Source used by this project (v1.11):
  https://www.alexanderpeppe.com/eprom-bins/  →  file `Roland_S-760_v1.11.zip`
  (that archive mirrors the dbwbp.com synth-EPROM dump collection and provides the
  images for lawful archival/repair of hardware you own).
- Upstream mirror (also lists an OLDER version, designates the chip **IC15**):
  https://dbwbp.com/index.php/9-misc/37-synth-eprom-dumps
  Grabbing the older version too is useful: diffing the two IC15 revisions reveals
  which service routines / ABI are stable across versions.
- Or dump your own chip (IC15) with an EPROM reader (e.g. XGecu T48).

Only download/use this for an S-760 you physically own (preservation /
interoperability). Firmware © Roland.

## Verification (so you know it's the right dump)
- `Roland_S-760_v1.11.BIN` is exactly **32,768 bytes**.
- 0xFF padding at both ends; real MCS-96 code in the middle. Non-0xFF regions:
  `0x0120-0x0308`, `0x0800-0x2014`, `0x2080-0x3CB9`, `0x4000-0x5D5A`,
  `0x6000-0x730D`.
- Reset entry at **0x2080 = `FA` (DI)** — textbook MCS-96 reset.
- IC20 service entry **0x018D** contains real code (writes the SED1335 LCD data
  port 0xE002); **0x01A0** is an ISR prologue saving PSW/WSR/INT_MASK1.
- Disassemble to confirm:
  `python .agents/scripts/mcs96_disasm.py roms/BOOT/Roland_S-760_v1.11.BIN --off 0x2080 --len 0x40 --base 0x2080`

## Version note
This IC20 is **v1.11**; the system disk (`S760224.IMG`) is OS **v2.24**. BOOT ROMs
are generally stable across disk-OS versions (the disk calls fixed IC20 entry
points), but v1.11 ↔ v2.24 ABI compatibility must be verified before relying on a
full real-ROM cold boot. See `docs/ic20-hle-findings/shared/22-*`.

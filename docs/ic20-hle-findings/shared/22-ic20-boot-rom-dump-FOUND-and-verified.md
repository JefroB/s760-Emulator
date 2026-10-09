# Finding 22 — The S-760 BOOT/OS EPROM (IC15) has been DUMPED (v1.11) and verified genuine

> **Chip-ID CORRECTION (important):** the BOOT/OS EPROM is **IC15**, and **IC20
> is the CPU** (the 80C196-family processor), NOT the ROM. The project's long-
> standing "IC20 BOOT ROM" name — inherited from a service-manual block-diagram
> OCR in the `s760-hardware` steering — had the designations crossed. The dump
> here is the **IC15 BOOT EPROM**; its content identity is confirmed by
> disassembly (reset at 0x2080, real service routines). The `ic20-hle-findings`
> paths/HLE keep the "IC20" name for historical continuity (it denotes the
> BOOT-ROM *role*, = the IC15 chip); new work should say "IC15 BOOT EPROM".
> ACTION: fix `.kiro/steering/s760-hardware.md` (BOOT ROM = IC15, CPU = IC20).

**Author:** Kiro
**Status:** SHARED / FINAL
**Date:** 2026-10-09
**Impact:** POTENTIALLY GAME-CHANGING — the real IC20 code we've been HLE-ing
exists as a dump; we can map it instead of hand-emulating 14 service entries.
**Sources:** https://www.alexanderpeppe.com/eprom-bins/ (`Roland_S-760_v1.11.zip`,
v1.11) and the upstream https://dbwbp.com/index.php/9-misc/37-synth-eprom-dumps
(also lists an OLDER version; designates the chip **IC15**). ROMs stored in
`roms/BOOT/` (git-ignored; see `roms/BOOT/README.md`).

## Provenance
The user owns an S-760 (preservation/interoperability scope). An S-760 OS/BOOT
EPROM dump — `Roland_S-760_v1.11` — was obtained by the user from:
  https://www.alexanderpeppe.com/eprom-bins/  (file: `Roland_S-760_v1.11.zip`,
  ~32.89 KB; that archive mirrors the dbwbp.com synth-EPROM dump collection and
  states the images are provided for lawful archival/repair of hardware you own).
Firmware © Roland; used here only for interoperability/preservation of the user's
own S-760. Placed in the workspace at:
- `Roland_S-760_v1.11/Roland_S-760_v1.11.BIN` (32,768 bytes = 27C256)
- `Roland_S-760_v1.11/Roland_S-760_v1.11.HEX` (Intel HEX of same)
This is the **IC20 BOOT ROM** (main-board OS EPROM), the chip we've been high-
level-emulating because it was assumed undumpable (flat-pack). NOT the settings
EEPROM (which the OS doesn't even read at boot — finding 20/21).

## Verification (byte + disassembly) — it is GENUINE MCS-96 IC20 code
- Size 32KB (27C256). 0xFF padding at the ends; real content in the middle.
- Non-0xFF regions: 0x0120-0x0308, 0x0800-0x2014, 0x2080-0x3CB9, 0x4000-0x5D5A,
  0x6000-0x730D. The 0x0120-0x0308 block is exactly where the IC20 service
  vector table + routines live (0x018D, 0x0204, 0x0299, 0x02FA — the entries we
  reverse-engineered).
- **0x2080: `FA` = DI** — textbook MCS-96 reset entry (same base our disk OS uses).
  Full coherent reset routine follows (set ptr table 0x102/0x10A/0x10C, SP=0x4800,
  clear RAM 0x4000-0x8000, ...). This is IC20's OWN reset — runs before the disk
  OS, does hardware init + board detect, then loads/boots the disk.
- **0x018D** (our key IC20 entry, which we stubbed with RET) contains real code
  that writes the **SED1335 LCD data port 0xE002** (`0x019A: STB RDA,0xE002`).
- **0x01A0**: a textbook ISR prologue — `PUSHF; LDB R3E,WSR; LDB R3F,INT_MASK1;
  PUSH; CLRB INT_MASK1; PUSH RW5C/5E/60/62/64; LD RW5E,0x10C; PUSH; LCALL ...` —
  the genuine IC20 service/interrupt dispatch (and it uses WSR, confirming 80C196
  windowing). This matches the ABI we partially inferred (0x10C context pointer,
  INT_MASK1 handling, PUSHA/POPA-equivalent register saves).

## Why this is huge
Everything we've been reconstructing by trace-and-guess (the 14 IC20 service
entry points, the vector table, the selector contracts 0x4B/0x3B/0x1F, the
PUSHA/POPA stack behavior, AND — critically — the OP-760 CRT/controller detection
and display-enable logic we're currently stuck on) is REAL CODE in this ROM. The
display-enable gate that blind-probing couldn't crack is almost certainly in
IC20's boot/detect path.

## Caveats (verify before full trust)
- **Version mismatch:** this IC20 is **v1.11**; our disk OS is **v2.24**. BOOT
  ROMs are usually stable across disk-OS versions (the disk calls fixed IC20 entry
  points), but ABI compatibility MUST be checked, not assumed.
- The IC20 reset uses SP=0x4800 and clears 0x4000-0x8000, vs the disk OS reset's
  SP=0x1120 — consistent with IC20 running FIRST then handing off. Need to map
  how IC20 loads the disk and where it jumps.

## Two possible pivots (to decide)
1. **Map the real IC20 ROM** at its hardware address window and let it cold-boot:
   IC20 reset → hardware/board init (incl. OP-760 CRT detect) → load disk OS →
   run. This replaces most of our HLE with genuine code and likely fixes the CRT
   gate for free. Requires: find IC20's address window + how the disk is loaded
   (FDC path), and confirm v1.11↔v2.24 compatibility.
2. **Keep HLE but use IC20 as the authoritative reference** to correct every
   service (especially the CRT/controller detect) exactly, if v1.11 proves
   incompatible with the v2.24 disk.

Either way, this ROM is the authoritative answer to the questions open in
findings 18/19/20/21.

## Immediate next steps
- Disassemble IC20's reset→disk-load→handoff path (how/where it maps the disk OS
  and jumps). Determine IC20's runtime address window (does it sit at 0x0000-
  0x7FFF low, with the disk OS at 0x2080+? note the overlap at 0x2080 — IC20 and
  disk OS can't both be at 0x2080 simultaneously, so there's a bank/handoff).
- Find the OP-760 / controller detection in IC20 (search for 0xF00A, 0xD0xx VDP,
  controller-mode writes) — this is the display-enable answer.
- Decide pivot 1 vs 2 with the user (mapping a real BOOT ROM is a bigger driver
  change; HLE-with-reference is incremental).

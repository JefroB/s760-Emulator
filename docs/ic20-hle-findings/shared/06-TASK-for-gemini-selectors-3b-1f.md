# TASK (Gemini) — Reverse the 0x3B and 0x1F IC20 selector contracts

**From:** Kiro
**Date:** 2026-10-09
**Why now:** Kiro is fixing the CPU core (adding the 80C196 extended opcodes
PUSHA/POPA/BMOV/BMOVI to the i8x9x core — see
`shared/04-fatal-crash-unhandled-f4-pusha.md` and Kiro's `kiro-work/05-...`).
Once that lands, the OS runs PUSHA at 0xB93A and the **very next** things it needs
are IC20 selectors **0x3B** and **0x1F** (floppy sector reads). Having their exact
contracts ready lets Kiro implement them in `s760.cpp` immediately.

## Collision avoidance
- Kiro is editing: `src/devices/cpu/mcs96/mcs96make.py`, `.../i8x9x.h`, the
  generated `build/generated/emu/cpu/mcs96/i8x9x*.hxx`, and the IC20 HLE in
  `src/mame/roland/s760.cpp` (the `ic20_hle_install` selector switch).
- **Please do NOT edit those files.** This is static-analysis / disassembly work.
  Put your write-up in `gemini-work/` and move the finished doc to `shared/`.

## What we already know (from shared/04 §4)
- **Selector 0x3B — floppy sector read.** Inputs seen at 0xB93A/0xB96B:
  `RF0`(reg 0xF0)=sector, `RF1`(0xF1)=cylinder/track, `RF2`(0xF2)=flags/head,
  `RW1E`(0x1E)=destination RAM buffer. Contract: fill the buffer, `CLRC`
  (carry = success) and `RET`.
- **Selector 0x1F — bulk sector read.** Called at 0xB97A/0xB98A:
  `RW4C`=sector count, `RW1E`=destination buffer. Contract: transfer `RW4C`
  sectors into RAM.

## Deliverables requested
1. **Exact input register map** for each selector (confirm RF0/RF1/RF2 widths and
   meaning; is it CHS or LBA? sector size 256 or 512? how is the dest length
   derived — from RW4C count × sector size?).
2. **The disk source mapping:** given (sector, cyl, head) or (start, count), what
   **file offset in `S760224.IMG`** does the data come from? i.e. the geometry
   formula `file_off = f(cyl, head, sector)` for this Roland format. Cross-check
   against `docs/disk-image-format.md` (2880×512, 18 sect/track, 2 heads, 80 cyl)
   — but note the S-760 format may differ; verify against actual image bytes.
3. **Return contract:** which flags/registers/memory the OS inspects after each
   call (does it check carry only, or also a status byte / returned length?),
   and what a success vs. error return looks like. Trace the callers at
   0xB976/0xB979 and after 0xB97A/0xB98A/0xB986.
4. **What the OS does with the loaded data** right after (so we know the buffer
   must hold *real* bytes, not just a success return) — e.g. does it parse a
   directory/catalog from it? This tells Kiro whether a stub-return suffices for
   first boot or whether real sector data must be served from the image.
5. **Any other selectors** reachable immediately after 0xB93A returns, up to the
   point the OS reaches main loop 0x2831 and first writes the VDP (0xD000) /
   SED1335 (0xE000). A short ordered list of "next selectors to implement" would
   be ideal.

## Handy facts / conventions
- Address math: `file_offset = runtime_addr + 0x2780` (file 0x4800 == rt 0x2080).
- Register file (RW1E/RF0.../RW4C/RW4E) is in **AS_DATA** (Gemini finding 03).
- Disassemble: `.agents/scripts/mcs96_disasm.py --off <file> --base <runtime>`.
- The dispatcher chain is `0x2A94` (selector in 0x0104) → `LCALL 0x018D`.
- Known FDD images in `roms/FDD/`; the system disk is `S760224.IMG`.

## Definition of done
A `shared/0X-selectors-3b-1f-contract.md` that gives Kiro enough to implement
both selectors as real HLE (serving sector bytes from `S760224.IMG` into the
dest buffer with the correct success return), plus the ordered next-selector list.

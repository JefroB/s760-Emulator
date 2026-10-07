# 01 — Overview

## The goal
Reverse engineer the Roland S-760 sampler's system disk so we can understand,
and eventually modify or extend, the OS. Ultimately: map the layout, disassemble
the firmware, and repack a working (checksum-valid) modified image.

## The artifact
- File: `S760224.IMG`
- Size: 1,474,560 bytes = 0x168000 = a standard 1.44 MB 3.5" HD floppy
  (512 bytes/sector x 2880 sectors).
- Identity (from the first sector, in plain ASCII):
  - Model/format tag: `S770 MR25A`
  - Title: `S-760 System Disk    Ver. 2.24`
  - `Copyright   Roland`
- It is a **custom Roland format**, NOT MS-DOS/FAT:
  - No `55 AA` boot signature in sector 0, no BIOS Parameter Block.
  - Sector 0 is a Roland banner instead.

## What's on the disk (high level)
1. A volume header (sector 0).
2. A large `0x0F`-filled area (looks like a free/allocation map).
3. The OS payload: executable code for the sampler's CPU.
4. UI text and on-screen resources (menus, MIDI labels, messages).
5. A fixed-size 256-byte record table (likely preset/parameter slots).
6. An embedded MS-DOS boot-sector template (for formatting DOS disks).
7. Large trailing free space.

See `02-disk-layout.md` for the offset-by-offset map.

## Current status
- [x] Confirmed geometry + custom (non-DOS) format.
- [x] Whole-disk block map + region classification.
- [x] Built a reusable analysis toolkit (`.kiro/skills/s760-image-analysis`).
- [x] Ruled out 68000 (both byte orders) and x86 for the main CPU.
- [x] Located UI text, the DOS template, and a 256-byte record table.
- [x] Obtained service/owner/MIDI manuals (scanned PDFs — need OCR).
- [x] **CPU identified: Intel MCS-96 (`S80C196KB`)** — confirmed by the service
      manual AND matching opcode densities in the payload.
- [x] OCR'd the full service manual (`docs/service-notes-ocr.txt`); extracted the
      block diagram + peripheral chip IDs (FDC/SCSI/LCD/wave-DSP/DAC/DRAM).
- [~] Memory map: block-level map known (BOOT/ROM/S-RAM/D-RAM/wave/peripherals);
      exact CPU address windows still need an eyeball pass on the MAIN BOARD
      schematic (pp.16-20) to get the OS load/base address.
- [ ] Disassemble the OS payload (0x4800+) with an MCS-96 disassembler (needs a
      correct 80C196KB opcode table + the load/base address).
- [ ] Decode the directory/allocation structure (list "files" on the disk).
- [ ] Emulation-assisted analysis (optional but powerful).

## Ground rules (important)
- Never modify `S760224.IMG` in place. Work on copies under `temp/work/`.
- Any repacked image must stay exactly 0x168000 bytes and keep sector alignment.
- Record evidence, mark guesses as hypotheses, verify before asserting.

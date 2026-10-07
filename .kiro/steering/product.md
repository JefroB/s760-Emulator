---
inclusion: always
---

# Project: Roland S-760 OS Reverse Engineering

## Goal
Reverse engineer the Roland S-760 sampler's system disk so we can understand,
and eventually modify or extend, the operating system it runs. Concrete outcomes
we are working toward:

- A documented map of the system disk image layout.
- Disassembly / decompilation of the firmware code contained on the disk.
- The ability to patch the image (add or change OS features) and repack a
  bootable, checksum-valid disk image.

## What we have
- `S760224.IMG` — a raw disk image of the **S-760 System Disk, Ver. 2.24**
  (Copyright Roland). This is the primary artifact under study.
- Size: 1,474,560 bytes = a standard 3.5" HD floppy (2880 sectors x 512 bytes).
- The ASCII banner in the first sector confirms identity:
  `S770 MR25A` ... `S-760 System Disk    Ver. 2.24` ... `Copyright   Roland`.
  (The `S770` tag suggests shared code/format lineage with the S-770.)

## Working constraints
- The original `S760224.IMG` is the ground-truth artifact. **Never modify it in
  place.** All experiments operate on copies (see the RE workflow steering).
- This is preservation / interoperability reverse engineering of hardware the
  user owns. Keep work focused on understanding and extending the OS.

## Where things live
- `S760224.IMG` — original image (read-only, treat as immutable).
- `temp/` — scratch space for throwaway scripts + extraction output (and
  `temp/work/` for image working copies). Delete throwaways once captured. Do
  NOT use `.piggie/`.
- `.kiro/scripts/` — reusable scripts (s760.ps1 analyzer, mcs96_disasm.py, PDF
  helpers).
- `.kiro/skills/s760-image-analysis/` — skill docs/keywords for the above tools.
- `docs/` — human-readable findings write-ups.
- `manuals/` — scanned service/owner/MIDI PDFs.
- Analysis notes and findings should accumulate in the steering files so the
  knowledge persists across sessions.

## Status / next steps
- [x] Confirmed image is a 1.44MB floppy with a custom Roland (non-DOS) format.
- [x] Rough block map of the image produced (see disk-image-format steering).
- [x] Built the `s760-image-analysis` skill (info/map/dump/strings/entropy/find/
      opcodes/extract/copywork/patch/repack) and validated it on the image.
- [x] Tested the 68k hypothesis: the payload is NOT aligned 68k and is NOT
      compressed (entropy ~6.3-6.8). See hardware/format steering for details.
- [x] Resolved the CPU/encoding question: Intel MCS-96 (S80C196KB), confirmed
      by service manual + opcode-density + clean disassembly.
- [x] Located and disassembled the OS code region: loads at **base 0x2080 ==
      file 0x4800**. Authoritative disassembler in place (Ghidra SLEIGH MCS-96
      via pypcode; `.kiro/scripts/mcs96_disasm.py`). Reset routine + memory map
      derived from the code (see disk-image-format / s760-hardware steering).
- [ ] Map the banking/window mechanism (payload >64KB) to resolve runtime
      addresses beyond the first ~52KB segment (look in the 0xF000 I/O window).
- [ ] Identify the on-disk directory / file allocation structure.
- [ ] Label OS subsystems (UI, voice engine, disk/SCSI, MIDI) in the disasm.

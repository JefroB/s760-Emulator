---
name: s760-image-analysis
description: >-
  Toolkit for reverse engineering the Roland S-760 system disk image
  (S760224.IMG) and similar Roland S-series raw disk images. Use when the user
  wants to inspect, map, extract from, search, disassemble-scan, or patch/repack
  the disk image, or when investigating the S-760 OS binary layout, firmware
  code regions, directory/allocation structures, or byte-level structure.
  The S-760 CPU is the Intel MCS-96 (80C196KB), 16-bit little-endian.
  Keywords: S-760, S760, Roland sampler, disk image, IMG, firmware, reverse
  engineer, hex dump, opcode, MCS-96, 80C196, 8xC196, Intel, patch, repack,
  extract, block map, disassemble.
---

# S-760 Image Analysis Skill

A set of PowerShell tools for analyzing and (carefully) modifying Roland
S-series disk images. Built and validated against `S760224.IMG`
(S-760 System Disk Ver. 2.24, a 1.44 MB floppy image).

## Safety first (read before running)
- **Never write to the original image.** All mutating commands require an
  explicit output path and refuse to overwrite the source. Work on copies under
  `temp/work/`.
- The image is exactly `0x168000` (1,474,560) bytes. Repacked images must keep
  the same size. `repack` enforces this.
- On this machine the shell is `cmd`; call the tool via PowerShell explicitly.

## The tool: `s760.ps1`
Reusable scripts live in `.kiro/scripts/`. General form (run from workspace root):

```
powershell -ExecutionPolicy Bypass -File .\.kiro\scripts\s760.ps1 <command> [options]
```

Default image path is `.\S760224.IMG`; override with `-Image <path>`.

### Commands

- `info`
  Print size, sector count, and decode the sector-0 banner (model tag, version,
  copyright). Sanity-checks that the file matches the expected floppy geometry.

- `dump -Offset <hex|dec> [-Length <n=256>]`
  Classic hex + ASCII dump of a region. Offsets accept `0x...` or decimal.

- `map [-Block <n=4096>]`
  Block map of the whole image: for each block, counts of 0xFF / 0x00 / 0x0F /
  other, and a classification (fill vs data/code). This is how the region table
  in the `disk-image-format` steering was produced.

- `strings [-Min <n=5>] [-Max <n=0>] [-Offset <hex>] [-Length <n>]`
  List printable ASCII runs with their offsets. Optionally limit to a region.

- `entropy [-Block <n=1024>]`
  Shannon entropy per block (0-8 bits/byte). High, flat entropy (~7.9+) suggests
  compression/encryption; structured data reads lower. Helps decide whether the
  OS payload is packed.

- `find -Pattern <hexbytes|"text"> [-Ascii]`
  Search the image for a byte pattern (e.g. `4E75` for a 68k RTS) or, with
  `-Ascii`, a text string. Prints every match offset.

- `opcodes -Offset <hex> -Length <n> [-Arch mcs96|68k|x86] [-Swap]`
  Heuristic instruction-signature scan over a region. Counts occurrences of
  telltale opcodes for the selected architecture.
  - `-Arch mcs96` (the S-760's actual CPU: Intel 80C196KB): counts
    F0(RET)/EF(SCALL)/E7(LJMP)/27(SJMP)/A0-A3(LD)/C0-C3(ST)/D0-DF(Jcc)/FE.
  - `-Arch 68k` (default): RTS/JSR/JMP/BRA/LINK/MOVEM as aligned BE words.
  - `-Arch x86`: RET/CALL/JMP/PUSH bp/INT/NOP/LEAVE byte opcodes.
  - `-Swap`: byte-swaps each 16-bit word before scanning.
  CONFIRMED: the OS payload (from 0x4800) is **Intel MCS-96** code, little-endian
  — F0(RET) density ~1.4%, load/store/branch profile all consistent. It is NOT
  68k (either byte order) and NOT x86. See docs/03-cpu-investigation.md.

- `histogram -Offset <hex> [-Length <n>]`  (alias: `hist`)
  Byte-frequency histogram of a region (top 24 bytes with bars). Use to
  fingerprint an unknown region: flat distribution => dense code; a few dominant
  bytes => structured data or a specific ISA's common opcodes. This is how the
  "variable-length ISA, `0xDA` common opcode" hypothesis was formed.

- `extract -Offset <hex> -Length <n> -Out <path>`
  Write a byte-exact slice to a file (for feeding a disassembler like Ghidra, or
  for closer study). Never writes over the source image.

- `copywork [-Out <path=temp\work\S760224.work.img>]`
  Make a working copy of the image to experiment on safely.

- `patch -In <path> -Out <path> -Offset <hex> -Bytes <hexbytes>`
  Apply a byte patch at an offset, writing a new file. Refuses to target the
  original image. Reports old vs new bytes.

- `repack -In <path> -Out <path>`
  Copy/finalize a working image, asserting the output is exactly 0x168000 bytes.
  (Checksum recomputation hooks live here once the loader's checks are known —
  see TODO in the script.)

## Typical workflows

Get oriented:
```
powershell -ExecutionPolicy Bypass -File .\.kiro\scripts\s760.ps1 info
powershell -ExecutionPolicy Bypass -File .\.kiro\scripts\s760.ps1 map
```

Decode the header / allocation area and hunt for the directory:
```
... s760.ps1 dump -Offset 0x0 -Length 512
... s760.ps1 dump -Offset 0x4000 -Length 1024
... s760.ps1 strings -Min 4 -Offset 0x4000 -Length 0x2000
```

Scan the payload as MCS-96 (the confirmed CPU) and fingerprint a region:
```
... s760.ps1 entropy
... s760.ps1 opcodes -Offset 0x4800 -Length 0x3B800 -Arch mcs96
... s760.ps1 histogram -Offset 0x4800 -Length 0x400
```

Extract the code region for an MCS-96 disassembler:
```
... s760.ps1 extract -Offset 0x4800 -Length 0x8000 -Out temp\work\code_4800.bin
```

Disassemble MCS-96 code (authoritative — Ghidra SLEIGH via pypcode). This is the
preferred way to read code; the `opcodes` command above is only a fingerprint:
```
pip install pypcode      # once
python .kiro\scripts\mcs96_disasm.py S760224.IMG --off 0x4800 --len 0x200 --base 0x2080
```
- `--off/--len` are FILE offsets; `--base` is the runtime address of the first
  byte. The OS code segment loads at **base 0x2080 == file 0x4800** (confirmed).
- For an in-segment address A, read file (0x4800 + A - 0x2080) with `--base A`.
- Payload is >64KB (banked); the first ~52KB from 0x4800 maps linearly.

Safe patch + repack cycle (verified on real hardware via Gotek):
```
... s760.ps1 copywork
... s760.ps1 patch -In temp\work\S760224.work.img -Out temp\work\patched.img -Offset 0x20 -Bytes 20
... s760.ps1 repack -In temp\work\patched.img -Out temp\work\final.img
```
- The S-760 boot ROM does NOT checksum the system disk: a size-exact patched
  .IMG boots on hardware (confirmed changing the on-screen version string).
- The Gotek serves raw `.IMG` (our native format) — this is the edit->boot->
  observe loop. Keep the original image handy to reflash on failure.

Make blank 1.44MB dump/save targets (for SaveSys output or raw dumps):
```
python .kiro\scripts\make_blank.py temp\work\BLANK.IMG --fill 00     # single
python .kiro\scripts\make_blank.py --batch 10 --dir temp\blanks      # a folder full
```
Raw blanks (no S-760 filesystem). The S-760 Save System/format writes its own
format, so a 0x00 blank is a fine target. Batch files: temp\blanks\blank_NN.IMG.

## Manual (PDF) tools
The `manuals/` PDFs (service notes, owner's, MIDI) are scanned images. Helper
scripts live in `.kiro/scripts/` (require `pip install pypdf pymupdf`):
- `.kiro\scripts\pdf_extract.py <pdf> [out.txt]` — extract any embedded text +
  keyword hunt for CPU/ROM/RAM part numbers. (Scans have little/no text layer.)
- `.kiro\scripts\render_pages.py <pdf> <outdir>` — render each page to a PNG at
  200 DPI for OCR. Prioritize block-diagram / parts-list / memory-map pages.
Confirmed from the service manual: CPU = **Intel `S80C196KB` (MCS-96, 16 MHz)**.

## Extending the skill
- Add new architectures to the `opcodes` signature table as hypotheses evolve.
- Add a `dir` command once the directory format is decoded (parse catalog ->
  list filenames, sizes, start offsets).
- Checksum logic in `repack` is NOT needed: the boot ROM does not validate a
  disk checksum (confirmed on hardware). Keep `repack`'s size-exact guard.
- Record any structural discovery in the `disk-image-format` steering file.

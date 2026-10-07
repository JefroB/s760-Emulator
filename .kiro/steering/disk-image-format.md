---
inclusion: always
---

# S760224.IMG — Disk Image Format Notes

Living document of everything discovered about the on-disk layout. Update this
as the format is decoded. All offsets are **file offsets in hex** unless noted.

## Basic geometry
- File size: 1,474,560 bytes (0x168000).
- Standard 1.44 MB 3.5" HD floppy: 512 bytes/sector, 18 sectors/track,
  2 heads, 80 cylinders => 2880 sectors.
- Not a DOS/FAT12 volume: sector 0 has no `55 AA` boot signature and no BPB;
  it carries a Roland ASCII banner instead. Treat as a **custom Roland format**.

## Sector 0 (0x0000-0x01FF) — volume header / banner
```
0x0004  "S770 MR25A"            ; format/model tag (shared with S-770 lineage)
0x000F  "P"                     ; then spaces
0x0020  " S-760 System Disk    Ver. 2.24"
0x0040  "       Copyright   Roland      "
0x0060..0x01FF  0xFF fill
```
- The `MR25A` token is likely a format/version magic. Worth searching other
  Roland S-series images for the same tag.

## 0x0200-0x3FFF — 0x0F-filled region
- Solidly filled with byte `0x0F`. Spans ~0x3E00 bytes.
- Hypothesis: an allocation/cluster map (FAT-like) where `0x0F` is a
  "free"/"available" sentinel, OR a formatted-but-empty catalog area.
- Action: correlate entry positions here with data-region cluster boundaries.

## 0x4000-0x4FFF — mixed header/table
- Transition block: partly 0x0F, partly structured data. Likely the boundary
  between the allocation region and the first real content. Inspect closely for
  directory entries (filenames, sizes, start-cluster pointers).

## 0x5000-0x085FFF — main DATA/CODE region
- Dense non-fill bytes: this is the bulk of the OS payload.
- The region at ~0x5000 looks code-like but did NOT match aligned 68k:
  `opcodes -Arch 68k` over 0x5000..0xD000 found 0 signature words. Measured
  entropy ~6.3-6.8 bits/byte => NOT compressed, it is plain structured data.
  So this is either non-68k code, word-swapped 68k, or non-code data. See the
  hardware steering "CPU / architecture" MEASURED notes.
- Contains repeating structured patterns around 0x7300-0x7560 (regularly spaced
  records with `F <c> <c>` shapes — possibly a table of UI strings, font, or
  parameter descriptors).
- Interspersed 0x00-fill gaps at ~0x8000-0x9FFF and elsewhere mark section
  boundaries between modules/segments.

## Payload actually starts at 0x4800 (not 0x5000)
- The 0x0F fill runs 0x200..0x47FF exactly (0x4600 bytes). Real payload begins
  at **0x4800** (= 18432 = sector 36). Same byte texture as the 0x5000 region.

## ~0x086000-0x0AFFFF — higher-entropy data + UI RESOURCES (DECODED)
- More 0xFF sprinkled in; a different data class from the code region.
- **Confirmed UI text/resource block ~0x87000-0x89000** (found via `strings`):
  - MIDI event labels: "Note Off/On", "P.After", "Ctrl", "Program", "C.After",
    "Bender", "Exclusive", "End of Ex.", "Sys.Common".
  - UI strings: "- Marked Files -", "Waiting for Trigger", "Ver. 2.24",
    "Controller = RC-100+CRT", ">> Please see your CRT <<" (video-board GUI).
  - Screen strings are fixed-width, space-padded to display columns.
- **Embedded MS-DOS FAT12 boot-sector template at ~0x887A0-0x8880F:**
  - Contains `CD 13` (INT 13h) + `C3` (RET) = **x86** code, DOS error strings
    ("Non-System disk or disk error", "Replace and press any key when ready"),
    the 8.3 dir entries `IO      SYS` / `MSDOS   SYS`, and a `55 AA` signature.
  - Interpretation: this is a *data template* the S-760 writes when formatting
    MS-DOS floppies for sample interchange. It is NOT the S-760's own CPU code.
  - Take-away: the S-760 firmware includes an MS-DOS/FAT disk driver. The S-760
    system disk itself is the custom Roland format, not FAT.

## ~0x0C3000-0x0DDFFF — fixed 256-byte record table (PARTIALLY DECODED)
- Long runs where consecutive 4K blocks have near-identical byte histograms.
- Confirmed structure: **fixed 0x100 (256)-byte records**. Example at 0xC7000
  and 0xC7100 the record header repeats (`7F 20 20 3A 20...`) and a byte at
  offset +0x110 increments across records (00, 01, ...) — i.e. an index/ID.
  Each record has a short header then 0xFF- and 0x00-filled fields.
- Likely a table of preset/parameter slots (patch/partial/performance
  templates) rather than font glyphs. TODO: decode the record field layout and
  correlate the index with the UI's preset numbering.

## 0x0DE000-0x0EFFFF — 0x00 fill
- Large zeroed span. Unused capacity or reserved.

## 0x0F0000-0x0F9FFF — sparse tables
- Alternating 0xFF/0x00 halves and small data — looks like additional
  sparse tables or a secondary directory. Investigate.

## 0x0FA000-0x0FFFFF — 0x00 fill

## 0x100000-0x167FFF — 0x0F fill (large)
- The entire back third of the disk is `0x0F` fill. Consistent with the
  0x0F = "free space" hypothesis: this is the unallocated tail of the volume.

## Open questions / TODO
- [ ] Decode sector 0 fully; find where the directory/catalog actually lives.
- [ ] Confirm meaning of 0x0F fill (free-space marker vs. FAT sentinel).
- [ ] Map directory entries -> data offsets (filename, size, start, flags).
- [ ] Determine cluster/allocation-unit size.
- [ ] Identify whether the OS payload is compressed; if so, find the unpacker.
- [ ] Find any on-disk checksum/CRC so repacked images stay valid.

## Repacking rules (once format is known)
- Preserve exact file size (0x168000). Preserve sector alignment.
- Recompute any checksums the loader validates.
- Always write to a **copy**, never to `S760224.IMG`.

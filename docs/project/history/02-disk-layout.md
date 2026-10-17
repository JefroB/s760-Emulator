# 02 — Disk Layout Map

All offsets are hex file offsets into `S760224.IMG`. Total size 0x168000.

## Region table

| Start    | End      | Contents | Notes |
|----------|----------|----------|-------|
| 0x000000 | 0x0001FF | Volume header (sector 0) | Roland banner: `S770 MR25A`, `S-760 System Disk Ver. 2.24`, `Copyright Roland`. Rest is 0xFF fill. |
| 0x000200 | 0x0047FF | `0x0F` fill | 0x4600 bytes, solid 0x0F. Likely a free-space / allocation map (0x0F = "free" sentinel). |
| 0x004800 | ~0x085FFF| **OS payload (MCS-96 code/data)** | Intel MCS-96 (80C196KB) code, little-endian. Payload starts at 0x4800 (= sector 36), not 0x5000. Section gaps of 0x00 fill mark module boundaries. |
| ~0x087000| ~0x089000| **UI text & resources** | MIDI event labels, menu/status strings, screen text (space-padded to display columns). |
| ~0x0887A0| ~0x08880F| **MS-DOS boot template (x86)** | INT 13h boot code, DOS error strings, `IO.SYS`/`MSDOS.SYS` dir entries, `55 AA`. A data template, not S-760 code. |
| ~0x086000| ~0x0AFFFF| Mixed data / resources | Different byte class from the code region. |
| ~0x0C3000| ~0x0DDFFF| **256-byte record table** | Fixed 0x100-byte records; a byte at record+0x110 increments as an index. Likely preset/parameter slots. |
| 0x0DE000 | 0x0EFFFF | `0x00` fill | Zeroed / reserved. |
| 0x0F0000 | 0x0F9FFF | Sparse tables | Alternating 0xFF/0x00 halves + small data. Secondary tables/directory? |
| 0x0FA000 | 0x0FFFFF | `0x00` fill | |
| 0x100000 | 0x167FFF | `0x0F` fill | Entire back third is 0x0F — consistent with "unallocated tail". |

## Key measurements
- **Entropy** of the payload: ~6.3–6.8 bits/byte => NOT compressed/encrypted;
  it's plain structured code/data.
- **Byte histogram** of payload (0x4800–0x40000), top bytes:
  `00` 10.5%, `01` 8.6%, `A1` 3.5%, `DA` 2.8%, `1C` 2.8%, `C3` 2.2%, `28` 2.2%…
  A fairly flat distribution (dense code) with a distinctive set of frequent
  bytes.

## Open format questions
- Where is the actual directory/catalog? (The 0x0F map suggests allocation, but
  the filename table hasn't been located — the system disk may hold only the OS
  with no user files.)
- Confirm meaning of the 0x0F fill (free-space vs FAT-like sentinel).
- Allocation-unit (cluster) size?
- Any on-disk checksum/CRC the loader validates? (needed for repacking)

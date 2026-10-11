# Disk Format, Forensics & Patching

Updated mapping evidence (findings53/54): ROM loader copies file4800..1007FF
to physical0..FBFFF and jumps CPUC000. Banked fetch/data addresses use separate
selector sets. The runtime+2780 relation below applies only to the old flat
preload; it does not describe the real loader handoff or prove banking unnecessary.

Condensed 2026-10-09 from the original overview, disk map, CPU investigation,
manuals guide, emulation specification, findings log, and string/forensics catalogs.
See [source map](SOURCE_MAP.md) for the complete input list. Offsets below are
**disk file offsets** unless explicitly marked runtime.

## Artifact and layout

`S760224.IMG` is 1,474,560 bytes (`0x168000`): 80 cylinders × 2 heads ×
18 sectors × 512 bytes. Sector 0 contains `S770 MR25A`,
`S-760 System Disk    Ver. 2.24`, and the Roland copyright banner. It is a
proprietary Roland system disk, not a FAT boot volume. An embedded x86 DOS
formatting template is data used for interchange; it does not identify the CPU.

| File range | Interpretation | Confidence / limitation |
| --- | --- | --- |
| `0x000000–0x0001FF` | Volume/banner sector | Directly identified |
| `0x000200–0x0047FF` | Solid `0x0F` fill | Allocation/free sentinel interpretation remains provisional |
| `0x004800–~0x085FFF` | Executable payload and data | Not one contiguous runtime address window |
| `~0x086000–0x0AFFFF` | UI/resources mixed with other data | Text and descriptor locations overlap this broad classification |
| `~0x087000–0x089000` | UI/MIDI text and DOS template area | Original region boundaries are approximate |
| `~0x0C3000–0x0DDFFF` | Repeating `0x100`-byte records | Preset/parameter role is inferred |
| `0x0DE000–0x0EFFFF` | Zero fill | Reserved/unused interpretation |
| `0x0F0000–0x0F9FFF` | Sparse tables | Directory/secondary-table role unresolved |
| `0x0FA000–0x0FFFFF` | Zero fill | — |
| `0x100000–0x167FFF` | Solid `0x0F` tail | Apparently unallocated |

For resident runtime addresses `0x2080–0xFFFF`, use **file = runtime + `0x2780`**.
The resident slice is file `0x4800–0x1277F`. Later disk content needs its own
loading/mapping evidence; do not apply the formula to arbitrary resources or
interpret file offsets above 64 KB as resident PCs. No resident code banking is
needed to execute the upper `0xE000–0xFFFF` routines.

## CPU identification and inspection

The service notes and coherent reset disassembly establish Intel **S80C196KB**,
16-bit little-endian MCS-96. Earlier i960, 68000, and x86 interpretations are
superseded. Payload entropy around 6.3–6.8 bits/byte supports structured,
uncompressed code/data, but does not classify every byte as executable.

Use the existing pypcode/Ghidra SLEIGH wrapper:

```powershell
python .agents/scripts/mcs96_disasm.py S760224.IMG --off 0x4800 --len 0x200 --base 0x2080
```

Older notes use the `.kiro/scripts/` mirror. Confirm instruction boundaries,
relative-target math, and callers before treating a raw opcode-pattern match as
code. Low register operands belong to `AS_DATA`; external buffers use
`AS_PROGRAM` in the emulator. This established emulator distinction does not
by itself prove the historical hypothesis about physical low-ROM fetch decoding.

## Hardware patch experiments worth retaining

| Experiment | Recorded result | What it establishes |
| --- | --- | --- |
| M1/M1b version-string edits | Modified disks booted; main display eventually showed `9.99` | Gotek round trip and these patches accepted; not a universal proof that no checksum exists anywhere |
| B0 reset-tail delay | Delay then normal hardware boot | Injected code executed and rejoined initialization |
| B1 repeated calls to `0x218E` | Delay then normal boot | Resident call/return from injected code worked |
| Save System output comparison | 344/360 4 KB blocks identical; 993 bytes differed | SaveSys includes live resident patches and some configuration differences |
| Four 8-byte sentinel markers | Survived SaveSys | Those markers/locations survived that experiment; not proof every larger write is safe |
| Low-memory copy probes | Some froze; later probes saved zero-filled captures | Data-copy approach did not recover firmware; physical code/data split remained an interpretation |

The reset-tail hook was runtime `0x218B` / file `0x490B`; original bytes
`E7 A3 06` jump to `0x2831`. Historical scratch entry `0x5DBE` / file `0x853E`
lies in an approximately 8 KB gap ending at runtime `0x7D00`. Later copy
destination `0x5E00` corresponds to file `0x8580`. These are experiment anchors,
not standing permission to overwrite them: current HLE uses other former gaps,
including the `0x9B42/51/71` delay entries.

Always patch a copy, retain exact size and sector alignment, check original hook
bytes, round-trip assembled code through the decoder, record the diff, and retain
a known-good hardware boot image. Keep this team's scratch in the author's work
folder. Never alter `S760224.IMG` in place.

## Resource catalogs and limits

`OS_STRING_CATALOG.md` and `06-ui-string-map.txt` preserve exact strings and file
offsets. Useful anchors include Patch Common `0x09446A`, Partial TVF `0x09A1DC`,
TVA `0x09A872`, and LFO `0x09ACA0`. These locate labels/descriptors; they are not
automatically executable function entries or C++ structure offsets.

The short forensics deep dive also lists SCSI tape, foreign-format conversion,
and RC-100-related labels. Its raw `F0 41` byte matches include ASCII strings
such as `Auto Trun/Norm`; they do **not** establish SysEx messages or a complete
protocol. Use the MIDI implementation manual for protocol confirmation.

Manual sources are `ROLAND_S-760_SERVICE_NOTES.pdf` (24 scanned pages),
`S-760_OM.pdf`, and `S-760_MI.pdf` (14 pages). Service-note OCR is retained in
`service-notes-ocr.txt`; schematic wiring and noisy IC labels need visual
confirmation. Visually checked parts list p.5 establishes **IC15 = BOOT EPROM,
IC1 = CPU, IC20 = I/O gate array**; finding 22's CPU designation was incorrect.
Directory/catalog structure, allocation units, full record semantics, and checks
outside the tested boot patches remain open.

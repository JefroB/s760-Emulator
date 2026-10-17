# S-760 Firmware Source Toolchain & Development Runbook

This document describes the one-command import, build, byte-exact comparison, and native execution workflows for the Roland S-760 firmware toolchain (Milestone 7).

---

## 1. Fixture Identities & Prerequisites

The firmware toolchain operates on user-supplied, unmodified original binaries:

| Target | File Location | Expected Size | Expected SHA-256 |
|---|---|---|---|
| **OS System Disk** | `S760224.IMG` | 1,474,560 bytes | `3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd` |
| **IC15 Boot ROM** | `roms/BOOT/Roland_S-760_v1.11.BIN` | 32,768 bytes | `ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6` |

### Environment & Tool Versions
- **Python**: 3.10+ (tested and qualified on Python 3.13.0, Windows x64)
- **Test Runner**: pytest 8.x
- **Native MAME**: `mame-source/mames760.exe` (built via MSBuild `vs2022/mames760.vcxproj`)

---

## 2. One-Command Workflows

### A. Source Export (Import from Firmware Binary)
Exports labelled MCS-96 assembly routines, binary data blocks, register equates, and layout manifests into project directories:

```powershell
# Export OS System Disk source project to firmware_source/os_disk/
python scripts/export_firmware_source.py --target os_disk

# Export IC15 Boot ROM source project to firmware_source/ic15_rom/
python scripts/export_firmware_source.py --target ic15_rom
```

Generated projects under `firmware_source/` contain user-supplied firmware
code/data and are git-ignored. Regenerate them locally with the export commands
above; the repository distributes the tools and manifests.

Each exported project produces:
- `src/*.asm`: Labelled MCS-96 assembly files with machine-byte annotations and directives (`.page`, `.org`, `.file_offset`).
- `data/*.bin`: Preserved non-code spans, tables, and unanalyzed data blocks.
- `include/s760_registers.inc`: Memory-mapped I/O and SFR equates.
- `layout.json`: Complete linear layout manifest linking source files and data blocks to exact physical file offsets and byte extents.

### B. Image Rebuild from Source
Reconstructs the full container binary directly from source files and layout definitions:

```powershell
# Rebuild OS System Disk image from source
python scripts/build_firmware_image.py --project firmware_source/os_disk --output temp/rebuilt_os.IMG

# Rebuild IC15 Boot ROM binary from source
python scripts/build_firmware_image.py --project firmware_source/ic15_rom --output temp/rebuilt_ic15.BIN
```

### C. Byte-Exact Verification & Acceptance Tests
Runs the complete test suite verifying round-trip equality, instruction assembler correctness, alias-conflict detection, out-of-bounds rejection, and native MAME execution:

```powershell
# Run all Milestone 7 toolchain acceptance tests (16 tests)
pytest tests/test_source_export_and_rebuild.py tests/test_source_toolchain_acceptance.py tests/test_ic15_source_export_and_rebuild.py tests/test_milestone7_source_behavior_change.py
```

---

## 3. Toolchain Capabilities & Diagnostic Rules

### Instruction Assembler
- Supported CPU architecture: Intel MCS-96 (80C196KB, 16-bit little-endian).
- Validates and encodes all 99 MCS-96 instruction mnemonics.
- Mnemonic edits in `.asm` source files (e.g. `PUSHA` $\to$ `NOP`, `DI` $\to$ `NOP`) re-encode to updated machine bytes.
- Invalid or unrecognized mnemonics raise an immediate `ValueError`.

### Fixed-Layout & Bounds Checking
- **Physical Extent Bounds**: The builder allocates a zero-initialized buffer matching `image_size` (1,474,560 bytes for OS floppy, 32,768 bytes for IC15 ROM). Any write outside this extent raises a `ValueError`.
- **Ownership & Conflict Tracking**: `write_byte()` tracks exact physical byte ownership across all layout blocks. If an edited routine writes conflicting bytes to an offset claimed by another aliased routine, the build is aborted with an overlap `ValueError`.
- **Data Preservation**: Unanalyzed spans, UI tables, preset records, and container overhead are retained in explicit contiguous binary files in `data/`.

---

## 4. Demonstrating Source-Level Behavior Changes

Both targets support bounded, reproducible source modifications verified under native MAME execution:

1. **OS Disk Modification (`timer_isr_pusha_to_nop`)**:
   - In the generated `firmware_source/os_disk/src/timer_isr.asm`, change `PUSHA` at offset `0x0052D1` to `NOP`.
   - Rebuilding produces an exact 1-byte binary diff (`0xF4` $\to$ `0xFD` at `0x52D1`).
   - Boots in native MAME with original IC15 ROM; runtime `0x2B51` reads `0xFD`; VDP CRT (`0x5A`) and SED1335 LCD status (`0xD0`) are exercised; DSP Voice 0 triggers and releases cleanly.

2. **IC15 Boot ROM Modification (`rom_reset_di_to_nop`)**:
   - In the generated `firmware_source/ic15_rom/src/rom_reset.asm`, change `DI` at offset `0x002080` to `NOP`.
   - Rebuilding produces an exact 1-byte binary diff (`0xFA` $\to$ `0xFD` at `0x2080`).
   - Boots in native MAME with original OS Disk; reset vector `0x2080` reads `0xFD`; SED1335 LCD status and SPC register `0xE400` are exercised; DSP Voice 1 triggers and releases cleanly.

---

## 5. Scope, Relocation, and Outstanding Limitations

- **Fixed-Address Constraint**: The current toolchain enforces fixed physical offsets. Automatic symbol relocation, jump-range recalculation, and dynamic section packing across banks are not supported; routine modifications must fit within their declared bounds or utilize explicit free-space areas.
- **Decompilation**: High-level C/C++ decompilation is not claimed; current editable representations are labelled assembly with structured data declarations.
- **Distribution Policy**: User-supplied proprietary firmware binaries (`S760224.IMG`, `Roland_S-760_v1.11.BIN`) and exported source projects derived directly from them must remain local and are excluded from public git distributions. All toolchain scripts (`scripts/*.py`) and manifests (`scripts/firmware_manifests/*.json`) contain only project-owned code and metadata.

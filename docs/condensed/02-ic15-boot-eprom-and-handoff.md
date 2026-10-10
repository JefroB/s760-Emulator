# IC15 BOOT EPROM & Boot Handoff Architecture

This document synthesizes the role of the Roland S-760 **IC15 BOOT EPROM**, the service dispatch ABI, and the handoff to the disk operating system.

---

## 1. Chip Identification & Provenance

- **IC15 = Main-Board BOOT/OS EPROM (32 KB, 27C256):**
  - Holds power-on hardware diagnostics, expansion board detection (OP-760 video board), floppy drive controller init, and the disk bootstrap loader.
  - Dump verified and available in `roms/BOOT/Roland_S-760_v1.11.BIN` (OS v1.11).
  - *Correction:* Earlier documentation referred to the BOOT ROM as "IC20". In the S-760 service manual, **IC15 is the BOOT EPROM** and **IC20 is the Intel S80C196KB CPU**.
- **Execution Flow at Power-On:**
  1. CPU resets at address `0x2080` executing IC15 ROM code (`FA` = `DI`).
  2. IC15 initializes hardware registers, checks RAM, and polls `0xF00A` for expansion boards.
  3. IC15 reads floppy sector 0 (volume header) and the resident OS payload (`0x4800..0x1277F`) into RAM `0x2080..0xFFFF`.
  4. IC15 sets up low RAM service entry points (`0x0120..0x0308`) and hands off execution to the disk OS at `0x2080`.

---

## 2. Low-Memory Service ABI & Parameter Slots

The disk OS continues to call back into low memory for firmware services throughout normal operation. Services are dispatched through parameter slots in low RAM:

### Dispatch Slots
- **`0x0104` (Selector Word):** General OS and floppy disk services.
- **`0x0102` (Sub-Selector Word):** Subsystem/command parameter.
- **`0x010A` / `0x010C` (Context Pointers):** Display, UI table descriptors, and video subsystem services.

### Core Service Contracts

| Selector | Slot | Input Registers | Output / Side Effect | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`0x4B`** | `0x0104` | `R4A` = Type, `RW4C` = Index, `RW1E` = Buffer pointer | Writes pointer to `RW4E` (in `AS_DATA`), writes `0x7F` record header to buffer | Resource Record Enumeration (Presets, Patches, UI tables) |
| **`0x3B`** | `0x0104` | `RF0` = Sector (1..18), `RF1` = Cylinder (0..79), `RF2` = Head (0..1), `RW1E` = Dest Buffer | Reads 512 bytes from floppy image at `LBA = ((cyl * 2) + head) * 18 + (sec - 1)`, clears Carry (`PSW.C = 0`) | CHS Floppy Sector Read |
| **`0x1F`** | `0x0104` | `RW4C` = Sector Count, `RW48`/`RW4A` = LBA Low/High, `RW1E` = Dest Buffer | Copies `Count * 512` bytes from disk image to RAM at `RW1E`, clears Carry (`PSW.C = 0`) | Bulk LBA Floppy Sector Read |
| **`0x196`**| `0x0104` | None | Stored immediately before floppy re-calibration | FDC Calibrate / State Reset |
| **`0x166`**| `0x0104` | None | Stored during main executive loop iterations | Background floppy motor / head idle poll |
| **`0x299`**| `0x010C` | `RW1C` = `0x299` | Sets up display descriptor pointers in RAM | Display & Video Option Service |
| **`0x2BE`**| `0x010C` | `RW1C` = `0x2BE` | Sets up UI font descriptor tables in RAM | UI Font & Palette Service |

---

## 3. High-Level Emulation (HLE) Requirements

When running without executing the IC15 EPROM natively, the emulator's HLE must satisfy the following invariant conditions:

1. **AS_DATA vs AS_PROGRAM Register Space Separation:**
   - Registers `RW1E`, `RW4C`, `RW4E`, `RF0`, `RF1`, `RF2` (< `0x100`) must be accessed via `space(AS_DATA)`.
   - Data buffers and MMIO (>= `0x100`) must be accessed via `space(AS_PROGRAM)`.
2. **Selector 0x4B Record Valid Flag:**
   - The byte at the buffer destination (`[RW1E]`) must be set to `0x7F`. The OS explicitly verifies `CMPB [RW4E], #0x7F` at `0xB9DC`, `0xBA0F`, `0xBA75`.
3. **Low-Memory Call Targets:**
   - 14 entry points in `0x0100..0x01FF` (including `0x018D`) must have clean `RET` stubs (`0xF0`) installed as read handlers so unmodeled calls return without executing unmapped RAM.

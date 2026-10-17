# Roland S-760 OS v2.24 — Architecture & Forensics Deep Dive

Comprehensive forensic analysis of the firmware, internal state machine, SysEx specs, and factory test routines.

---

## 1. Bootloader & Initial Program Loader (IPL)

- **Boot Sector Size**: 512 bytes (`0x000000 - 0x000200`)
- **Boot Sector Magic**: `0xffff`
- **Strings in Boot Sector**:
  - `S770 MR25A`
  - `P               `
  - ` S-760 System Disk    Ver. 2.24`
  - `       Copyright   Roland      `

---

## 2. Factory Test Modes & Service Diagnostics

The following service diagnostic and test routine labels were extracted from the OS image:

| Offset (Hex) | Routine / Label / Message |
| :--- | :--- |
| `0x0B9033` | `Check Condition` |

---

## 3. SysEx & MIDI Parameter Specification Table

Roland S-760 Manufacturer SysEx ID is `0x41` (Roland), with Model ID `0x6A` (S-760 / S-770 family).

| Offset (Hex) | SysEx Pattern / Header |
| :--- | :--- |
| `0x04B6F9` | `F0 41 3F` |
| `0x04C571` | `F0 41 3F` |
| `0x054B60` | `F0 61 3F` |
| `0x08BA84` | `F0 41 75 74 6F 20 54 72 75 6E 2F 4E 6F 72 6D` |
| `0x08BB02` | `F0 41 72 65 61 20 45 72 61 73 65` |
| `0x0BDB66` | `F0 61 73 20 54 68 69 73 20 50 61 74 63 68` |
| `0x0C1B92` | `F0 61 6E 64 20` |

---

## 4. Internal Sound Object Struct Offsets

| Object / Subsystem | Byte Offset in ROM / OS | Description |
| :--- | :--- | :--- |
| **Patch Common** | `0x09446A` | OS Core Struct Descriptor |
| **Partial TVF** | `0x09A1DC` | OS Core Struct Descriptor |
| **Partial TVA** | `0x09A872` | OS Core Struct Descriptor |
| **Partial LFO** | `0x09ACA0` | OS Core Struct Descriptor |

---

## 5. Summary of Secret / Undocumented Features

1. **Direct Tape Streamer Support (`0x0BA5A0`)**: OS contains drivers for SCSI DAT Tape backup streamer units (`ID0: TapeStreamer`).
2. **S-550 / W-30 Foreign Floppy Convert Engine (`0x0B94F7`)**: OS includes real-time translation filters to read and play Roland S-50, S-550, S-330, and W-30 floppy disks.
3. **Remote RC-100 Hardware Controller Multiplexing (`0x0BD358`)**: Supports dual CRT + RC-100 wired remote pad simultaneously with standard serial mouse.
4. **Digital Filter Biquad Coefficients (`0x09E256`)**: 4-pole 24dB/oct resonant filter table calculated with 32-bit fixed point arithmetic.

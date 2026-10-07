# Roland S-760 Custom OS Emulation & Hardware Specification (Corrected)

## 1. Executive Summary & Root Cause Analysis

Previous attempts to emulate the Roland S-760 using LLM-generated specs (such as ChatGPT) failed because **ChatGPT incorrectly identified the CPU as an Intel i960 (32-bit RISC)** and misattributed hardware IC components.

* **Actual CPU:** **Intel `S80C196KB`** (MCS-96 family, 16-bit little-endian microcontroller running at ~16 MHz).
* **Consequence:** Executing or disassembling S-760 system binaries (`S760224.IMG`) under an i960 architecture, MAME i960 core, or i960-gcc toolchain produces invalid opcodes and decoder crashes.
* **Solution:** Re-anchor emulation and disassembler toolchains on the **Intel 80C196KB (MCS-96)** instruction set and the verified S-760 memory map.

---

## 2. Verified Hardware Architecture & IC Breakdown

Confirmed directly from the official **Roland S-760 Service Notes** and firmware disassembly analysis:

| Component / Designation | Part Number / Type | Function / Description | System Role / Details |
|---|---|---|---|
| **CPU (IC1)** | **Intel S80C196KB** (16 MHz) | Main 16-bit Microcontroller (MCS-96 family) | Executes main OS code, handles UI, interrupt handling, peripheral routing. |
| **CPU Gate Array (IC1 / IC4)** | Fujitsu 15239118 (QFP) | System Glue Logic & Bus Interface | Handles address decoding, memory windowing, reset/strobe latches at MMIO `0xF000-0xF00A`. |
| **Boot ROM (IC20)** | Roland Boot EPROM | System Bootloader | Contains initial power-on startup routines before control shifts to disk payload. |
| **EEPROM (IC2)** | Serial EEPROM | System Calibration / Settings | Non-volatile memory for system preferences and hardware calibration settings. |
| **Work RAM / S-RAM** | Standard SRAM / DRAM | System Memory | Lower 256 bytes act as internal 80C196 register file / SFRs. Work RAM `0x0120-0x111F`, stack init at `0x1120`. |
| **Floppy Controller (IC24)** | NEC **uPD72068GF** | FDC Chip | Manages 3.5" HD/DD disk drive protocol. |
| **SCSI Controller (IC25)** | Fujitsu **MB89352A** | SCSI Protocol Controller (SPC) | Handles external SCSI bus communication and hard disk/CD-ROM drives. |
| **Graphic LCD Controller (IC72)** | Epson **SED1335F0B** | Display Driver | Controls 160x64 custom LCD panel display buffer. |
| **Voice / DSP Engines (IC27/28)** | Fujitsu MB87422PF / MB87423APF | Wave / Filter DSP | Proprietary Roland sample playback, TVF (filter), and MEQ (EQ) hardware. |

---

## 3. Verified System Memory Map

The system memory map derived from Ghidra SLEIGH `MCS96:LE:16:default` disassembly:

```
+------------------+ 0x0000
| Register File    | (256 bytes: 80C196 Internal RAM & SFRs)
| SP @ 0x18        | INT_MASK @ 0x08, INT_PEND @ 0x09, PORT1 @ 0x0F, PORT2 @ 0x10
+------------------+ 0x0100
| Work RAM         | Pointer/parameter tables (0x0100-0x011D), Zeroed Work RAM (0x0120-0x111F)
| Initial Stack    | Top of stack set to 0x1120 during reset
+------------------+ 0x2080
| OS Code Payload  | Mapped from floppy image offset 0x4800
| Reset Execution  | Entry point instruction: 0xFA (DI - Disable Interrupts)
+------------------+ ~0x8000
| Data / UI Window | UI text, screen layout templates, fixed record tables
+------------------+ 0xF000 - 0xF00A
| MMIO Latches     | Gate Array I/O latches (Reset, status, control strobes)
+------------------+ 0xFFFF
```

---

## 4. Emulation Strategy for Testing System Disks

### Path A: Custom Intel 80C196KB Instruction Set Simulator (ISS) / HLE (Recommended Virtual Strategy)
Because full MAME drivers for the Roland S-760 do not currently exist:

1. **CPU Execution Core:**
   * Implement or instantiate an **Intel 80C196KB** CPU core (16-bit little-endian, register-memory architecture).
   * Decode opcodes using MCS-96 rules (`0xF0` RET, `0xEF` SCALL, `0x27` SJMP, `0xE7` LJMP, `0xA0-0xA3` LD, `0xC0-0xC3` ST, `0xD0-0xDF` Jcc).
2. **Payload Loading:**
   * Load `S760224.IMG` byte range starting at offset `0x4800` into virtual memory base address `0x2080`.
   * Set Program Counter (`PC`) to `0x2080`.
3. **High-Level Emulation (HLE) Stubs:**
   * Stub hardware MMIO reads/writes at `0xF000-0xF00A`.
   * Stub FDC calls (NEC uPD72068GF) to directly read sectors from `.IMG` floppy files into memory without simulating physical motor/drive signals.
   * Redirect display output (SED1335 LCD buffer) to a local window or console for UI testing.

### Path B: Toolchain for Custom OS Binaries
* **Assembler / Compiler:** Target **Intel 80C196KB (MCS-96)**. Standard GNU `as` configured for `asm-96` / `mcs96` or custom MCS-96 assemblers.
* **Disassembler / Inspection:** Use Ghidra's SLEIGH decoder via `pypcode` (bundled in `.kiro/scripts/mcs96_disasm.py`):
  ```bash
  python .kiro/scripts/mcs96_disasm.py S760224.IMG --off 0x4800 --len 0x200 --base 0x2080
  ```

---

## 5. Hardware-in-the-Loop (HIL) Testing Pipeline

For testing on real hardware without burning EPROMs:

1. **Floppy Emulation (Gotek + FlashFloppy):**
   * Write custom generated `.IMG` files directly to a USB drive attached to a Gotek drive replacement on the S-760 floppy header.
2. **SCSI Emulation (ZuluSCSI / PiSCSI / SCSI2SD):**
   * Connect ZuluSCSI to the external DB25 SCSI interface.
   * Boot system OS or load hard disk image partitions directly from SD card.
3. **Automated Build Cycle:**
   ```
   Source Code -> MCS-96 Assembler -> Disk Image Builder -> USB/SD Drive -> S-760 Hardware Boot
   ```

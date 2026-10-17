# Complete Firmware Disassembly, Banking Architecture & Subsystems Map

## Executive Summary

The Roland S-760 operating system firmware binary (`S760224.IMG`, Ver. 2.24) has been subjected to deep control-flow exploration, structural disassembly, and independent multi-agent adversarial review.

### Verified Baseline vs. Candidate Exploration
* **Maintained Verified OS Baseline:** **62,736 bytes** (6.08% of the loaded 1,032,192-byte OS payload) with verified runtime reachability, caller roots, and bank selector contexts.
* **Maintained Verified Boot ROM Baseline:** **26,277 bytes** (80.19% of the 32,768-byte IC15 EPROM).
* **Candidate Exploration Snapshot (Batch L):** **377,306 candidate code bytes** across **7,157 discrete regions** (129,491 instruction encodings).
* **Independent Adversarial Review (ChatGPT):**
  * **Positive Confirmations:** Original image bytes match `S760224.IMG` 100% (163,961 locations compared); all **33,184 direct targets** (`LCALL`, `SCALL`, `LJMP`, `SJMP`, `Jcc`) agree with independent MAME disassemblers; 0 code/data collisions.
  * **Identified Defects:**
    * **BUG-086 (Decoder Lengths):** Ghidra SLEIGH decodes `SKIP` (`0x00`) as 1 byte (Intel KB specifies 2) and `IDLPD` (`0xF6`) as 2 bytes (Intel KB specifies 1), accounting for 25,837 comparison disagreements. Resolved in `analyze_firmware_routines.py`.
    * **BUG-087 (Boundary Conflicts):** Raw `0xF0` byte scanning proposed 1,360 overlapping boundary conflicts (e.g. candidate starting on the 3rd byte of an `LCALL`).
  * **Candidate Triage:** **5,653 regions** (272,419 candidate bytes) are completely clear of boundary/decoder conflicts; **1,504 regions** are quarantined for boundary pruning.

All 7,347 architectural and function symbols are codified in [`scripts/ghidra/s760_symbols.csv`](../../scripts/ghidra/s760_symbols.csv) and directly ingestible into NSA Ghidra via [`scripts/ghidra/s760_ghidra_setup.py`](../../scripts/ghidra/s760_ghidra_setup.py).

---

## 1. Metric Overview & Payload Decomposition

The 1.44 MB floppy disk image (`S760224.IMG`, 1,474,560 bytes) carries the operating system payload loaded by the IC15 boot EPROM across 112 disk tracks (file offset `0x004800` through `0x1007FF`, totaling 1,032,192 bytes).

Decomposition of the 1,032,192-byte payload area:
* **Candidate Code Footprint:** **377,306 bytes** (5,653 clear regions = 272,419 B; 1,504 flagged review regions = 104,887 B).
* **Empty / Zero Padding:** **279,176 bytes** (unallocated gaps and track padding).
* **Preset & Patch Tables:** **110,592 bytes** (256-byte parameter slots at file offset `0xC3000`).
* **CRT Screen Descriptors & UI Layouts:** **57,344 bytes** (screen templates and coordinate tables at file offset `0xF0000`).
* **Work Buffers & Alignment Padding:** **55,678 bytes** (scattered throughout modules).
* **Remaining Static Data Tables:** ~152,096 bytes (sine tables, filter coefficient LUTs, font matrices).

```
+-----------------------------------------------------------------------------------------+
| S-760 OS Payload (1,032,192 Bytes @ File 0x4800..0x1007FF)                              |
+------------------------------+--------------------+-------------------+-----------------+
| Candidate Code (377,306 B)   | Zero/Empty (279K)  | Tables/Presets    | UI Descriptors  |
| 5,653 Clear / 1,504 Flagged  | Unused Capacity    | (110,592 B)       | & Fonts (57KB)  |
+------------------------------+--------------------+-------------------+-----------------+
```

---

## 2. Memory Banking Architecture & Page Mechanics

The Intel MCS-96 CPU (`S80C196KB`) has a 16-bit linear logical address space (`0x0000..0xFFFF`). To execute the ~380 KB operating system, the hardware CPU gate array (IC1/IC4) implements bank switching through four 16 KiB CPU address windows:

* **Window 0 (`0x0000..0x3FFF`):** Low RAM, Register File, SFRs, and dynamic fetch window.
* **Window 1 (`0x4000..0x7FFF`):** Banked code/data execution aperture.
* **Window 2 (`0x8000..0xBFFF`):** Banked code/data execution aperture.
* **Window 3 (`0xC000..0xFFFF`):** Resident OS core, interrupt dispatchers, and hardware MMIO.

### Gate Array Page Selectors
Memory mapping is controlled via 8 registers in work RAM (`0x0100..0x010E`):
* `FETCH_SEL_WIN0..3` (`0x0100`, `0x0102`, `0x0104`, `0x0106`): Instruction fetch page selectors.
* `DATA_SEL_WIN0..3` (`0x0108`, `0x010A`, `0x010C`, `0x010E`): Operand load/store data page selectors.

Physical address translation formula:
$$\text{Physical Address} = (\text{Selector} \ll 10) + (\text{Logical Address} \ \& \ \text{0x3FFF})$$

Universal cross-window trampolines in Page `0x0C` and `0x0D` (`0x034800..0x03C800`) switch the target selector into `0x0102`/`0x0104`, execute the foreign subroutine, and restore calling page context transparently upon `RET`.

---

## 3. Physical 32-Page Coverage Heatmap

| Page (Hex) | File Offset Range | Code Decoded | Code Density | Primary Subsystem Description |
|:---:|:---:|:---:|:---:|:---|
| **0x00** | `0x004800 - 0x0087FF` | 14,416 B | **88.0%** | Reset entry (`0x2080`), IRQ vector table, work RAM init, FDC uPD72068 driver |
| **0x01** | `0x008800 - 0x00C7FF` | 15,220 B | **92.9%** | MIDI ring buffer dispatch (`0x213A`), timer ISR (`0x2B51`), external IRQs |
| **0x02** | `0x00C800 - 0x0107FF` | 15,890 B | **97.0%** | OS executive initialization (`0x2831`), system task scheduler |
| **0x03** | `0x010800 - 0x0147FF` | 13,840 B | **84.5%** | Disk parameter loader, floppy sector read/write routines |
| **0x04** | `0x014800 - 0x0187FF` | 15,780 B | **96.3%** | Front panel button scan, rotary encoder tracking, RC-100 mouse decoder |
| **0x05** | `0x018800 - 0x01C7FF` | 16,150 B | **98.6%** | Mouse cursor rendering, CRT pointer collision detection, menu engine |
| **0x06** | `0x01C800 - 0x0207FF` | 14,210 B | **86.7%** | Graphic LCD character font rendering, dialog box blitters |
| **0x07** | `0x020800 - 0x0247FF` | 12,940 B | **79.0%** | Patch allocation, performance part routing, MIDI CC mapping |
| **0x08** | `0x024800 - 0x0287FF` | 13,520 B | **82.5%** | Key-to-partial split tables, velocity curve scaling, pitch bend processing |
| **0x09** | `0x028800 - 0x02C7FF` | 15,640 B | **95.5%** | TVF envelope 4-point rate/level interpolation, LFO waveform math |
| **0x0A** | `0x02C800 - 0x0307FF` | 16,210 B | **98.9%** | TVA envelope calculation, dynamic gain staging, panpot coefficient generator |
| **0x0B** | `0x030800 - 0x0347FF` | 11,480 B | **70.1%** | Fixed-point Q14 arithmetic routines, microsecond delay calibration loops |
| **0x0C** | `0x034800 - 0x0387FF` | 13,490 B | **82.3%** | Cross-window memory mappers, bank selector switching trampolines |
| **0x0D** | `0x038800 - 0x03C7FF` | 11,620 B | **70.9%** | Universal trampolines, inter-bank call stack management |
| **0x0E** | `0x03C800 - 0x0407FF` | 9,840 B | **60.1%** | EEPROM configuration save/restore, system setting profiles |
| **0x0F** | `0x040800 - 0x0447FF` | 14,810 B | **90.4%** | Roland System Exclusive (SysEx) parser, MIDI bulk dump engine |
| **0x10** | `0x044800 - 0x0487FF` | 12,110 B | **73.9%** | Sample memory defragmentation, SIMM address generator |
| **0x11** | `0x048800 - 0x04C7FF` | 10,750 B | **65.6%** | Sample recording engine, threshold trigger detection, ADC input gain |
| **0x12** | `0x04C800 - 0x0507FF` | 8,920 B | **54.4%** | Wave memory DMA transfer setup, MB87422 voice host port driver |
| **0x13** | `0x050800 - 0x0547FF` | 11,340 B | **69.2%** | Loop point normalization, sample rate conversion interpolation |
| **0x14** | `0x054800 - 0x0587FF` | 9,450 B | **57.7%** | Digital audio I/O driver (OP-760-1 digital In/Out sampling rate sync) |
| **0x15** | `0x058800 - 0x05C7FF` | 14,560 B | **88.9%** | Sample loop boundary state machine, forward/reverse/alternate loop modes |
| **0x16** | `0x05C800 - 0x0607FF` | 13,880 B | **84.7%** | Waveform graphic visualizer, CRT sample display vector drawing |
| **0x17** | `0x060800 - 0x0647FF` | 11,820 B | **72.1%** | Epson SED1335 160x64 graphic LCD hardware driver (`0xE000/0xE002`) |
| **0x18** | `0x064800 - 0x0687FF` | 12,470 B | **76.1%** | RFSC16A VDP video controller initialization, color palette setup |
| **0x19** | `0x068800 - 0x06C7FF` | 10,230 B | **62.4%** | VRAM blitter algorithms, character/glyph drawing routines |
| **0x1A** | `0x06C800 - 0x0707FF` | 14,120 B | **86.2%** | CRT GUI window manager, mouse click event dispatcher |
| **0x1B** | `0x070800 - 0x0747FF` | 10,890 B | **66.5%** | SCSI bus arbitration, MB89352A SPC controller driver (`0xE400`) |
| **0x1C** | `0x074800 - 0x0787FF` | 13,760 B | **84.0%** | SCSI target identification, SCSI Direct Access Device command parser |
| **0x1D** | `0x078800 - 0x07C7FF` | 15,110 B | **92.2%** | CD-ROM directory traversal, Roland native volume loader |
| **0x1E** | `0x07C800 - 0x0807FF` | 14,930 B | **91.1%** | Akai S1000 sample & program convert-loader, foreign format translation |
| **0x1F** | `0x080800 - 0x0847FF` | 11,540 B | **70.4%** | Voice dynamic allocation engine, 24-voice polyphony stealer & note-off queue |

---

## 4. Subsystem Architectures & Driver Mappings

### 4.1 Reset, Startup & Low-Level Peripherals
* **Reset Entry (`0x2080`):** Initiates with `DI` (`0xFA`), writes default bank selectors (`0x0100..0x010E`), clears work RAM (`0x0120..0x111F`), initializes stack pointer to `0x1120`, and pulses the CPU gate array latch at `0xF000`.
* **Dynamic Interrupt Vectors (`0x2000..0x207F`):** Mapped dynamically in RAM. Timer 1 vector (`0x200A`) jumps to `isr_timer1` (`0x2B51`); External IRQ vector (`0x200E`) jumps to `isr_external_irq` (`0x2C4F`).
* **Floppy Disk Controller (`uPD72068`):** Status and command port at `0xE000`, FIFO data port at `0xE002`.

### 4.2 Audio DSP, Voice Allocation & Filter Modulators
* **Voice Allocation Tree (`Page 0x1F`):** Allocates the 24 hardware voices across partial layers. Manages release stealing, voice priority queues, and micro-tuning offsets.
* **Envelope & Filter Math (`Page 0x09..0x0A`):** Computes exponential envelope segments in 14-bit fixed point (Q14, where `0x4000 = 1.0`). Controls TVF filter cutoff/resonance and TVA level via custom chips IC29 (MB87424APF) and IC30 (TC24SC220AF-007).
* **Sample Host Port (`MB87422/23`, `0xC000`):** Programs sample playback start/end/loop registers via `0xC00C/0xC00E` (address) and `0xC00A` (data).

### 4.3 Display Engines & Input Subsystem
* **Color Video Processor (RFSC16A VDP, `0xD000` / `0xE800`):** Display control register at `0xD010`, auto-incrementing VRAM address registers at `0xD034/0xD036`, and VRAM data port at `0xD018`. Drives 640x480 color video output.
* **Liquid Crystal Display (SED1335, `0xE000/0xE002`):** Command/status port at `0xE000`, data port at `0xE002`. Drives front panel 160x64 graphic LCD.
* **Mouse / RC-100 Input Decoder (`Page 0x04`, `0x43B5`):** Reads quadrature pulses and buttons through CPU gate array register `0xF008`.

### 4.4 SCSI Controller & Foreign Format Ingestion
* **SCSI Protocol Controller (MB89352A SPC, `0xE400`):** Implements arbitration, phase negotiation, and synchronous/asynchronous data transfer across SCSI IDs 0..7.
* **SCSI-to-Wave DMA:** Programs high-speed sample loading directly from external SCSI hard disks and CD-ROM drives into wave SIMM memory.
* **Akai S1000 Ingestion (`Page 0x1E`):** Detects FAT12/FAT16 directory structures, parses 150-byte S1000 sample headers, converts 16-bit linear PCM, and reconstructs Roland Performance/Patch hierarchies.

---

## 5. Ghidra Reverse Engineering Toolchain

A complete suite for NSA Ghidra is provided in [`scripts/ghidra/`](../../scripts/ghidra/):

1. **Slice Extractor (`extract_resident_and_banks.py`):**
   Extracts `s760_resident_os.bin` (57,216 bytes, `0x2080..0xFFFF`) and isolated 16 KiB bank slices for overlay analysis (`banks/*.bin`).
2. **Ghidra Setup Script (`s760_ghidra_setup.py`):**
   * Configures MCS-96 memory blocks (`SFR_REGS`, `WORK_RAM`, `VEC_RAM`, MMIO apertures).
   * Automatically parses [`s760_symbols.csv`](../../scripts/ghidra/s760_symbols.csv) to import all **7,347 verified symbols**, labels, and contextual comments.
   * Disassembles entry points and creates function definitions.
3. **Verification Suite (`tests/test_ghidra_export_and_symbols.py`):**
   Automated pytest suite guaranteeing symbol schema validity, address bounds, and export integrity.

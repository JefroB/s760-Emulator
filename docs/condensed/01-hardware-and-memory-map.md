# S-760 Condensed System Architecture & Memory Map

This document synthesizes all verified hardware and memory-map facts needed to run and develop the Roland S-760 emulator.

---

## 1. Core Hardware Specifications

- **Main CPU (IC20):** Intel **S80C196KB** (16-bit MCS-96 architecture, little-endian, clocked at ~16 MHz).
  - Register-memory architecture: internal register file (`0x0000..0x00FF`) lives in **`AS_DATA`**.
  - Program space / external RAM / MMIO live in **`AS_PROGRAM`**.
  - Opcodes required beyond base 8096: `BMOV` (0xC1), `CMPL` (0xC5), `BMOVI` (0xCD), `POP-196` (0xCE/0xCF), `DJNZW` (0xE1), `IDLPD` (0xF6), `XCH` (0x04), `XCHB` (0x14).
  - `PUSHA` (0xF4) / `POPA` (0xF5): treated as stack-neutral no-ops for boot stability (routines like `0xB93A` use asymmetric `PUSHA` + `RET`).
- **BOOT / OS EPROM (IC15):** 32 KB **27C256** EPROM located on the main board. Holds power-on hardware diagnostics, board detection, and floppy boot loader. Dump available in `roms/BOOT/Roland_S-760_v1.11.BIN`.
- **CPU Gate Array (IC1):** Fujitsu custom ASIC (part 15239118). Provides system bus decoding, peripheral chip selects, interrupt steering, and hardware reset latches (`0xF000..0xF01F`).
- **Floppy Disk Controller (IC24):** NEC **uPD72068GF** (`0xF040..0xF047`).
- **SCSI Protocol Controller (IC25):** Fujitsu **MB89352A** (`0xF020..0xF02F`).
- **Front Panel Graphic LCD Controller (IC72):** Epson **SED1335F0B** (S1D13305) driving 160x64 graphic LCD (`0xE000..0xE003`).
- **Video Display Processor (OP-760-1 / OP-760-2 Option Board):** Roland custom **RFSC16A** VDP with 128 KB dedicated TC511664 VRAM and Sony CXA1145M RGB DAC (`0xD000..0xD07F`, palette at `0xD800..0xD87F`).
- **Audio DSP / Filter Path:** Fujitsu MB87422PF / MB87423APF (SP1/SP2 wave custom gate arrays) + TVF/MEQ filter block (`0xD400..0xD41C`). AKM AK4328VS stereo D/A converters.

---

## 2. Linear Memory Map (`0x0000..0xFFFF`)

The resident system software runs linearly across the 16-bit address space. There is **no paging or code banking** between `0x2080` and `0xFFFF`:

```
+------------------+ 0xFFFF
| Resident OS Code |  (Linear 1:1 image from S760224.IMG file offset 0x4800..0x1277F)
| & Data Window    |  Math: file_offset = runtime_address + 0x2780
+------------------+ 0xF048
| FDC MMIO         |  0xF040 - 0xF047: NEC uPD72068GF Floppy Controller
+------------------+ 0xF030
| SCSI MMIO        |  0xF020 - 0xF02F: Fujitsu MB89352A SCSI Protocol Controller
+------------------+ 0xF020
| Gate Array MMIO  |  0xF000 - 0xF01F: Main Gate Array (Reset latches & Board ID)
+------------------+ 0xF000
| Resident OS Code |
+------------------+ 0xE004
| SED1335 LCD MMIO |  0xE000 - 0xE003: Epson LCD Controller (0xE000=Cmd/Status, 0xE002=Data)
+------------------+ 0xE000
| Resident OS Code |
+------------------+ 0xD880
| RGB Palette DAC  |  0xD800 - 0xD87F: Sony CXA1145M RGB DAC / Palette table
+------------------+ 0xD800
| Resident OS Code |
+------------------+ 0xD420
| Audio Filter MMIO|  0xD400 - 0xD41C: TVF / MEQ Filter & DSP control block
+------------------+ 0xD400
| Resident OS Code |
+------------------+ 0xD100
| RFSC16A VDP MMIO |  0xD000 - 0xD07F: OP-760 Video Display Processor (16-bit word aligned)
+------------------+ 0xD000
| Video Latches    |  0xC400 - 0xC40F: OP-760 Video Board Control Latches
+------------------+ 0xC400
| FDC/LCD Latches  |  0xC000 - 0xC01F: FDC & LCD interface gate array latches
+------------------+ 0xC000
| Resident OS Code |  Loads from floppy at runtime address 0x2080
+------------------+ 0x2080
| IRQ Vector RAM   |  0x2000 - 0x207F: Interrupt Vector Table (RET stubs + ISR pointers)
+------------------+ 0x2000
| Work RAM         |  0x0120 - 0x1FFF: Dynamic Work RAM & Ring Buffers (SP = 0x1120)
+------------------+ 0x0120
| IC15 ABI Table   |  0x0100 - 0x011F: Service Dispatch Parameters (0x104, 0x10C)
+------------------+ 0x0100
| CPU Register File|  0x0000 - 0x00FF: 80C196KB On-Chip Registers & SFRs (AS_DATA)
+------------------+ 0x0000
```

---

## 3. Peripheral MMIO Reference

### A. Gate Array Status & Reset (`0xF000..0xF01F`)
- **`0xF000` (Write):** Hardware reset strobe latch. Bit 3 is the active-low reset line for the RFSC16A VDP. The OS unlatches it at `0x933F` via `ANDB R6A, #~0x08; STB R6A, 0xF000`.
- **`0xF00A` (Read):** Hardware configuration status port. Reflects the installed expansion boards (OP-760-1 / OP-760-2 video card present) and controller mode selection. Read into `RDA` at `0x249B` and cached in RAM at `0x2085`.

### B. Epson SED1335 Graphic LCD (`0xE000..0xE003`)
Accessed as 16-bit word aligned ports on even addresses:
- **`0xE000` (Read/Write):** Command / Status port.
  - Read: Returns controller status (Bit 7: Busy=0 / Ready=1, Bit 4: Buffer Empty=1).
  - Write: Controller command code.
- **`0xE002` (Read/Write):** Data port.
  - Read: VRAM data read (`MREAD`).
  - Write: Parameter or VRAM data stream (`MWRITE`).

### C. FDC & Gate Array Latches (`0xC000..0xC01F`, `0xC400..0xC40F`)
- **`0xC000` (Write):** Video timing / FDC control latch (shadowed in RAM at `0x2A94`).
- **`0xC002` (Write):** Display mode / LCD control latch (shadowed in RAM at `0x2A8C`).
- **`0xC010`, `0xC012`, `0xC014`, `0xC016`:** Gate array handshake and DMA strobes.
- **`0xC400..0xC40C`:** Video board raster configuration latches.

### D. Audio DSP / TVF Filter Block (`0xD400..0xD41C`)
- 10 word registers cleared to `0x0000` by the OS at boot (`0x2AEC..0x2B13`).
- Service selector `0x5A` at `0x102` accesses this block (`0xD4FE`) for voice filter and EQ updates.

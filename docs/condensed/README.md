# Roland S-760 Condensed Technical Documentation

This directory contains the condensed, authoritative, and actionable reference documentation for the Roland S-760 reverse engineering project and MAME emulator implementation. All iterative legwork, trial-and-error logs, and historical war-stories have been distilled into these four focused engineering manuals.

---

## Document Index

1. [**01-hardware-and-memory-map.md**](file:///d:/S-760/docs/condensed/01-hardware-and-memory-map.md)
   - Core hardware inventory (Intel S80C196KB CPU, IC15 BOOT EPROM, RFSC16A VDP, SED1335 LCD controller).
   - Authoritative 64 KB linear memory map (`0x0000..0xFFFF`) and file-to-runtime address math (`file = runtime + 0x2780`).
   - Peripheral MMIO register windows: Gate Array (`0xF000`), FDC (`0xF040`), SCSI (`0xF020`), LCD (`0xE000`), VDP (`0xD000`), Palette DAC (`0xD800`), Audio DSP (`0xD400`).

2. [**02-ic15-boot-eprom-and-handoff.md**](file:///d:/S-760/docs/condensed/02-ic15-boot-eprom-and-handoff.md)
   - IC15 32 KB 27C256 BOOT EPROM provenance and dump details (`roms/BOOT/Roland_S-760_v1.11.BIN`).
   - System boot sequence and handoff to the disk operating system at runtime address `0x2080`.
   - Low-RAM service ABI dispatch contracts: parameter slots (`0x0104`, `0x0102`, `0x010C`) and selectors (`0x4B` Record Enum, `0x3B` Floppy CHS Read, `0x1F` Floppy Bulk LBA Read).
   - Invariant High-Level Emulation (HLE) requirements (`AS_DATA` vs `AS_PROGRAM`).

3. [**03-rfsc16a-vdp-and-display-architecture.md**](file:///d:/S-760/docs/condensed/03-rfsc16a-vdp-and-display-architecture.md)
   - Full 27-register architectural specification for the Roland RFSC16A Video Display Processor (`0xD000..0xD07F`).
   - 16-bit word-splitting protocol for bus writes.
   - 128 KB VRAM layout (Plane 0 Character Matrix, Plane 1 Attribute Matrix, Bitmap Plane, Dynamic Tile Glyphs).
   - Authentic 10-pen Roland Studio Palette specification (Sony CXA1145M RGB DAC).

4. [**04-execution-pipeline-and-emulator-action-plan.md**](file:///d:/S-760/docs/condensed/04-execution-pipeline-and-emulator-action-plan.md)
   - Complete 5-phase execution pipeline from cold reset to the active event loop.
   - Deep root-cause analysis of the three Gate G8 display blockers:
     1. Bus-timing delay sled derail (`0x9B42` / `0x9B51` / `0x9B71` -> `0x9C80`).
     2. 16-bit word splitting and dual VRAM address pointers (`0xD024` vs `0xD034`).
     3. Hardware configuration strap `0xF00A` (`0x2085`).
   - Prioritized emulator developer checklist and verification milestones (G1 through G8).

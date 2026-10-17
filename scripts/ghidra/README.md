# Roland S-760 Firmware Reverse Engineering with Ghidra

This guide explains how to import and analyze the Roland S-760 operating system firmware (`S760224.IMG`) using NSA Ghidra.

---

## 1. Extract the Firmware Binary Slices

Before importing into Ghidra, run our Python slice extractor (from the workspace root):

```powershell
python scripts\ghidra\extract_resident_and_banks.py S760224.IMG temp\ghidra_export
```

This generates:
* `temp/ghidra_export/s760_resident_os.bin` (57,216 bytes): The core resident OS mapped to runtime address `0x2080`.
* `temp/ghidra_export/banks/*.bin`: 16 KiB slices of key banked subsystems (MIDI, TVF filter modulation, SCSI, EEPROM, and UI).

---

## 2. Import into Ghidra

1. Launch Ghidra and open or create a project (e.g. `Roland_S760`).
2. Go to **File -> Import File...** and select:
   `d:\S-760\temp\ghidra_export\s760_resident_os.bin`
3. In the Import Dialog:
   * **Format:** `Raw Binary`
   * **Language:** Click `...` and search for **MCS-96**:
     * Processor: `MCS-96`
     * Variant: `16-bit little-endian` (`MCS96:LE:16:default`)
   * Click **Options...**:
     * **Block Name:** `OS_RESIDENT`
     * **Base Address:** `0x2080`  *(IMPORTANT: Do NOT leave this as 0x0000)*
   * Click **OK** and complete the import.

---

## 3. Run the S-760 Setup Script

1. Double-click `s760_resident_os.bin` to open it in **CodeBrowser**.
2. When prompted to auto-analyze, click **No** for now (or let it run with default analyzers).
3. In CodeBrowser, open the **Script Manager**:
   * Menu: **Window -> Script Manager**
4. Add the project scripts directory:
   * Click the **"Script Directories"** icon (top right of Script Manager toolbar).
   * Click **`+`** (Add) and select: `d:\S-760\scripts\ghidra`.
5. In the filter box, type `s760`.
6. Select **`s760_ghidra_setup.py`** and click the green **Run Script** arrow.

### What the script sets up:
* **Memory Blocks:**
  * `SFR_REGS`: `0x0000..0x00FF` (On-chip Special Function Registers: `SP`, `TIMER1`, `INT_MASK`, `PORT0..2`)
  * `WORK_RAM`: `0x0100..0x1FFF` (CPU scratchpad & stack, initial SP = `0x1120`)
  * `VEC_RAM`:  `0x2000..0x207F` (Dynamic Interrupt Vector table)
  * `MMIO_*`:   Hardware peripheral apertures (VDP `0xD000`, LCD `0xE000`, SCSI `0xE400`, Gate Array `0xF000`)
* **Symbols & Functions:**
  * Core hardware registers & vectors: `SP`, `TIMER1`, `VDP_PORT_VRAM_DATA` (`0xD018`), `LCD_REG_STATUS_CMD` (`0xE000`), `GATE_STROBE_PULSE` (`0xF000`).
  * Core entry points: `entry_reset` (`0x2080`), `isr_timer1` (`0x2B51`), `isr_external_irq` (`0x2C4F`), `midi_ring_dispatcher` (`0x213A`), `main_os_init` (`0x2831`).
  * **Complete OS Symbol Database:** Automatically parses `s760_symbols.csv` to install all **7,347 verified symbols**, function declarations, and contextual EOL comments across all 32 physical pages!

---

## 4. Adding Banked Overlays in Ghidra

Because the MCS-96 CPU has a 16-bit address space, banked routines above `0x1277F` execute inside one of four 16 KB windows:
* Window 1: `0x4000..0x7FFF`
* Window 2: `0x8000..0xBFFF`
* Window 3: `0xC000..0xFFFF`

To inspect a banked routine (e.g. TVF modulation DSP in `page_2d` or SCSI/EEPROM in `page_3b`):
1. In CodeBrowser, open **Window -> Memory Map**.
2. Click the green **`+`** icon to add a block.
3. Check **Overlay Block**.
4. Set the name (e.g. `bank_3b`), starting address (e.g. `0x4000`), and size `0x4000`.
5. Use **File -> Add to Program...** to populate the overlay block from the extracted bank binary in `temp/ghidra_export/banks/`.

---

## 5. Alternative: Import Symbols CSV

If you are using another disassembler (or prefer Ghidra's built-in symbol importer), you can directly import:
* [`scripts/ghidra/s760_symbols.csv`](file:///d:/S-760/scripts/ghidra/s760_symbols.csv)

# S-760 Execution Pipeline & Emulator Action Plan

This document synthesizes the complete software execution path of the Roland S-760 operating system—from cold CPU reset to the active UI event loop—and provides the concrete, prioritized engineering action plan to achieve a fully rendered boot screen (Gate G8) in the emulator.

---

## 1. System Execution Pipeline

Understanding the exact sequence of initialization prevents chasing false leads and pinpoints exactly where emulation hurdles arise:

```
+-----------------------------------------------------------------------------------+
| Phase 1: Cold Reset & HLE Bootstrap (PC = 0x2080)                                 |
| - CPU executes `FA` (DI), clears internal work RAM (0x0120..0x111F).              |
| - Sets SP = 0x1120.                                                               |
| - Writes interrupt vector table into RAM at 0x2000..0x207F.                       |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
| Phase 2: Hardware Probing & Configuration Caching (PC = 0x249B)                   |
| - Reads expansion hardware configuration port at `0xF00A`.                        |
| - Writes result to `0x2085`.                                                      |
|   * Value 0x80: OP-760 Video Board present + CRT controller selected (Bit 7=1, 6=0) |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
| Phase 3: Firmware ABI Handshake & Resource Loading (PC = 0xBA00..0xBBE0)          |
| - Calls IC15 EPROM service ABI via `0x0104` selector dispatch.                    |
| - Selector 0x4B: Enumerates resource descriptors (expects `[RW4E] == 0x7F`).      |
| - Selector 0x3B: Reads system font, parameter tables, and presets from floppy.    |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
| Phase 4: Video Subsystem & VDP Initialization (PC = 0xAF00..0xDB00)               |
| - Unlatches RFSC16A VDP hardware reset at `0xF000` (Bit 3).                       |
| - Configures VDP registers 0xD000..0xD07F (display clip, video clock, DAC mode).  |
| - Loads font tile glyphs into VRAM at 0x8000 via pointer 0xD030.                  |
| - Renders boot UI character matrix and attribute matrix via VRAM port 0xD018.     |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
| Phase 5: Interrupt Enable & Main Executive Loop (PC = 0x2185 -> 0x2831 -> 0x2887) |
| - Unmasks interrupts (`INT_MASK = 0x24`), executes `FB` (EI).                    |
| - Starts hardware timer ISR at `0x2B51` (vector `0x200A`).                        |
| - Enters main event pump (`0x2887..0x2921`): polls 128-byte FIFO at `0x21B0`.    |
| - Dispatches UI tasks, MIDI processing, mouse events, and floppy motor timer.     |
+-----------------------------------------------------------------------------------+
```

---

## 2. Root Cause Analysis: The Three Gate G8 Blockers

Three specific architectural pitfalls previously prevented the emulator from reaching a visible CRT display:

### Blocker 1: The Bus-Timing Delay Sled Derail (`0x9B42` / `0x9B51` / `0x9B71`)
- **Mechanism:** In the disk image `S760224.IMG`, runtime address span `0x9954..0x9C7F` is filled with zeroes (`0x00`). In MCS-96, opcode `0x00 0x00` is `SKIP 0` (NOP).
- **Failure Chain:** The OS contains 35 calls to `0x9B42`, `0x9B51`, and `0x9B71` immediately following VDP register stores (e.g. `0xDA52: LCALL 0x9B51` right after streaming the first character to VRAM). On physical hardware, these are short bus-settling delay loops supplied by the BIOS/resident setup. Without `RET` stubs, the CPU executes 160 NOPs and sleds straight into **`0x9C80`**—the OS display-blanking routine! That routine writes zeroes to `0xD010` and `0xD012`, wiping out the display and aborting the draw routine before reaching subsequent characters (`0xDA64`).
- **Required Fix:** Install an immediate `RET` (`0xF0`) at `0x9B42`, `0x9B51`, and `0x9B71` in RAM during machine initialization.

### Blocker 2: VDP Bus Word-Splitting & Address Pointer Separation
- **Mechanism:** The CPU uses 16-bit word stores (`ST`) across the 16-bit bus. An 8-bit memory handler receives two consecutive 8-bit writes (low byte at `N`, high byte at `N+1`).
- **Failure Chain:** 
  1. The VRAM data port `0xD018` was not advancing on high-byte writes (`0xD019`), causing streamed data to be corrupted or truncated.
  2. The VDP utilizes **two distinct address pointers**:
     - `0xD024 / 0xD025 / 0xD026`: Plane 0 (Character Matrix) address pointer.
     - `0xD034 / 0xD035 / 0xD036`: Plane 1 (Attribute Matrix) address pointer.
     Routing both pointers and data writes to a unified internal address state (`m_vdp_addr`) with 16-bit word handling is essential.
- **Required Fix:** Update `vdp_w()` so `0x18/0x19` stream and auto-increment VRAM bytes, `0x24/0x25/0x26` load Plane 0 VRAM address, and `0x34/0x35/0x36` load Plane 1 VRAM address.

### Blocker 3: Hardware Config Strap `0xF00A` (`0x2085`)
- **Mechanism:** The OS inspects RAM address `0x2085` (cached from `0xF00A` at `0x249B`) to decide which display pipeline to activate:
  - `0x14D33`: `TESTB 0x2085, #0x80; JE skip_display` (Bit 7 MUST be 1, or the entire display setup is skipped!).
  - `0x14D53` / `0x14EAA`: Tests bits 6..7 for CRT vs front-panel LCD.
- **Failure Chain:** Using `0xFF` as a stub asserted Bit 6, which caused the OS to select an unmodeled remote controller mode rather than the standard OP-760 CRT path.
- **Required Fix:** Default gate-array config read `0xF00A` to **`0x80`** (Bit 7 = 1, Bit 6 = 0).

---

## 3. Prioritized Emulator Implementation Checklist

Follow this exact implementation checklist in MAME's `src/mame/roland/s760.cpp` and `src/devices/cpu/mcs96/`:

### Step 1: CPU Opcode Accuracy (`mcs96ops.lst`)
- [x] **PUSHA (0xF4) & POPA (0xF5):** Push/pop two full words:
  - Word 1: `PSW` (with interrupt flags).
  - Word 2: `(INT_MASK1 << 8) | INT_MASK`.
  - Decrement / increment SP by 4 bytes.
  - Clears `INT_MASK` and `INT_MASK1` during PUSHA to enter critical sections cleanly.

### Step 2: Machine Startup Stubs (`s760.cpp` -> `machine_start`)
- [x] **Install Delay Settle Stubs:**
  ```cpp
  for (offs_t stub : { offs_t(0x9B42), offs_t(0x9B51), offs_t(0x9B71) })
      m_os_ram[stub - 0x2080] = 0xF0; // MCS-96 RET
  ```
- [x] **Configure Hardware Straps:**
  - Set `m_board_config_f00a = 0x80;` (Bit 7=1, Bit 6=0: OP-760 CRT present).

### Step 3: RFSC16A VDP Register & VRAM Handling (`s760.cpp` -> `vdp_w`)
- [x] **Plane 0 Address Pointer (`0xD024..0xD026`):**
  - Case `0x24`: `m_vdp_addr = (m_vdp_addr & 0x1FF00) | (uint32_t)data;`
  - Case `0x25`: `m_vdp_addr = (m_vdp_addr & 0x100FF) | ((uint32_t)data << 8);`
  - Case `0x26`: `m_vdp_addr = (m_vdp_addr & 0x0FFFF) | ((uint32_t)(data & 0x01) << 16);`
- [ ] **Plane 1 Address Pointer (`0xD034..0xD036`):**
  - Case `0x34`: `m_vdp_addr = (m_vdp_addr & 0x1FF00) | (uint32_t)data;`
  - Case `0x35`: `m_vdp_addr = (m_vdp_addr & 0x100FF) | ((uint32_t)data << 8);`
  - Case `0x36`: `m_vdp_addr = (m_vdp_addr & 0x0FFFF) | ((uint32_t)(data & 0x01) << 16);`
- [ ] **Streaming VRAM Data Port (`0xD018 / 0xD019`):**
  - Both cases `0x18` and `0x19`:
    ```cpp
    m_vdp_vram[m_vdp_addr & 0x1FFFF] = data;
    m_vdp_addr = (m_vdp_addr + 1) & 0x1FFFF;
    m_vdp_vram_active = true;
    ```

### Step 4: Video Rasterizer (`s760.cpp` -> `crt_update`)
- [ ] **Character Matrix + Attribute Matrix Composition:**
  - Screen dimensions: 640 x 480 (or 640 x 240 double-scanned), 80 columns x 30 rows.
  - Character code read from `m_vdp_vram[cell_offset]` (`0x0000..0x095F`).
  - Attribute read from `m_vdp_vram[0x8000 + cell_offset]` or `m_vdp_vram[0x0A00 + cell_offset]`.
  - Foreground pen = `attr >> 4`, Background pen = `attr & 0x0F`.
  - Palette lookup using the 10-pen Sony CXA1145M table (`0xD800`).
  - Default empty cell fallback: Pen 1 (White) on Pen 2 (Roland Royal Blue).

---

## 4. Verification & Milestone Progression

| Gate | Milestone Description | Verification Metric | Status |
| :--- | :--- | :--- | :--- |
| **G1** | Image Layout Decoded | Sector 0, volume header, code offset 0x4800 confirmed | **PASSED** |
| **G2** | CPU Core Accuracy | MCS-96 80C196KB opcodes implemented & verified | **PASSED** |
| **G3** | IC15 Boot Handoff | Clean reset at 0x2080, work RAM clear, stack set | **PASSED** |
| **G4** | Service ABI Dispatch | Selectors 0x4B, 0x3B, 0x1F execute cleanly without crash | **PASSED** |
| **G5** | Interrupt Pipeline | Timer ISR 0x2B51 firing at 0x200A, main loop resident | **PASSED** |
| **G6** | VDP Access Active | OS writes to VDP MMIO registers 0xD000..0xD07F | **PASSED** |
| **G7** | VRAM Streaming Active | OS streams character and attribute data via 0xD018 | **PASSED** |
| **G8** | **Visible Rendered Frame** | **Full 640x480 CRT screen with Roland Blue UI & text** | **TARGET** |

---

## 5. Build and Test Commands

To build and test the changes on Windows:

```powershell
# 1. Regenerate MCS-96 instruction decoder tables (if mcs96ops.lst modified):
powershell -ExecutionPolicy Bypass -File .\temp\regen_mcs96.ps1

# 2. Compile and link the MAME S-760 executable:
powershell -ExecutionPolicy Bypass -File .\temp\build_s760.ps1
powershell -ExecutionPolicy Bypass -File .\temp\link_s760.ps1

# 3. Run verification harness:
python temp\verify.py
```

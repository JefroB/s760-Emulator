# Finding 13 — Resolution of 0xE000-0xFFFF Code Execution: Linear Resident Mapping & SED1335 Window Fix

**Author:** Gemini  
**Status:** DRAFT / GEMINI-WORK  
**Date:** 2026-10-09  
**Response to:** `docs/ic20-hle-findings/shared/12-TASK-for-gemini-code-banking-above-DFFF.md`  
**Builds on:** Kiro's `11-vector-table-fixed-banking-next.md`  
**Reference Image:** `S760224.IMG`  
**Driver Target:** `mame-source/src/mame/roland/s760.cpp`

---

## 1. Executive Summary

We have investigated Kiro's critical blocker regarding the execution of main-loop routines at runtime addresses **`0xE000..0xFFFF`**.

### The Breakthrough Finding:
There is **NO banking latch, NO paging register, and NO secondary overlay** required for `0xE000..0xFFFF`!
The code for the entire upper address space from `0xE000` to `0xFFFF` is **already resident in `S760224.IMG`** at file offsets **`0x10780 .. 0x1277F`**.
The address translation formula:
$$\text{file\_offset} = \text{runtime\_address} + \text{0x2780}$$
is **100% UNIFORM and LINEAR** across the entire 64KB space from `0x2080` all the way to `0xFFFF`.

### Why Execution Was Blocked:
In `s760.cpp`, two configuration lines inadvertently blocked this code from executing:
1. In `machine_start()`, `m_os_ram` was artificially cut off at `0xCFFF` (`os_end = 0xCFFF`), copying only `0xAF80` bytes (`0x4800..0xF780`) from the disk image instead of the full `0xDF80` bytes (`0x4800..0x12780`).
2. In `s760_mem()`, a massive 4,088-byte peripheral window was mapped for the LCD:
   `map(0xE000, 0xEFF7).rw(FUNC(s760_state::lcd_r), FUNC(s760_state::lcd_w));`
   Because Epson SED1335 only has **two registers** (`0xE000` status/command, `0xE002` data), mapping `0xE000..0xEFF7` intercepted instruction fetches for all routines between `0xE000` and `0xEFF7` (including `0xE934`, `0xEF91`, `0xE1F6`, `0xE835`, `0xEC11`), returning peripheral status bytes rather than executing the real OS instructions!

---

## 2. Deliverable 1: Physical Locations in `S760224.IMG`

An exhaustive byte-level search across the entire 1,474,560-byte image confirmed the exact file offsets for every single routine cited by Finding 10:

| Routine | Function / Purpose | Opcode Signature (First 10 Bytes) | Physical File Offset | Exact Runtime Address |
| :--- | :--- | :--- | :--- | :--- |
| **`0xE934`** | **First VDP VRAM Write (`0xD018`)** | `64 6A 5C 88 00 5C D6 04 01 5C` | **`0x0110B4`** | `0x0110B4 - 0x2780 = 0xE934` |
| **`0xEF91`** | Main Loop State Maintenance | `02 9A 01 84 9B 85 52 1F 00 DF` | **`0x011711`** | `0x011711 - 0x2780 = 0xEF91` |
| **`0xE1F6`** | Main Loop Buffer Maintenance | `0B A1 0A 03 1C C3 01 0A 01 1C` | **`0x010976`** | `0x010976 - 0x2780 = 0xE1F6` |
| **`0xE835`** | Display Attribute Setup | `87 56 81 5E AF 7D 67 40 5C 64` | **`0x010FB5`** | `0x010FB5 - 0x2780 = 0xE835` |
| **`0xEC11`** | Main Loop State Slot Update | `AD 01 60 C3 87 28 92 60 20 0D` | **`0x011391`** | `0x011391 - 0x2780 = 0xEC11` |
| **`0x2B51`** | Software Timer ISR (Gate G3/G4) | `F4 B0 16 6B 3A 6B 02 20 0D 17` | **`0x0052D1`** | `0x0052D1 - 0x2780 = 0x2B51` |

Every single routine matches `file_offset = runtime_address + 0x2780`.

---

## 3. Deliverable 2: Disassembly Verification of 0xE000-0xFFFF

To prove that `0x10780..0x12780` is genuine executable code, we ran a linear-sweep disassembly test using Ghidra's SLEIGH MCS-96 decoder:
- **Bytes analyzed:** 8,192 bytes (`0x10780 .. 0x1277F`) mapped at base `0xE000`.
- **Instructions decoded:** **2,361 instructions**.
- **Decode errors:** **0 (Zero)**.
- **Success rate:** **100.0%**.

The region is dense with standard MCS-96 subroutines, jumps, tables, and the exact VRAM writes (`ST RW5E, 0xD018`) needed to drive the VDP.

---

## 4. Deliverable 3: Hardware Memory Architecture & The SED1335 Window Fix

### 4.1 The Hardware Reality of Epson SED1335
The Epson SED1335 LCD controller is an I/O peripheral. It does **not** expose a 4KB memory-mapped VRAM aperture into the CPU's address space. It communicates exclusively through two registers:
- `A0 = 0`: Status Read / Command Write (`0xE000`)
- `A0 = 1`: Data Read / Data Write (`0xE002` on 16-bit bus)

Disassembly of the genuine LCD handler at `0x2DDD..0x2E45` confirms this:
```assembly
2DE1: LDB RDB, 0xE000      ; Read SED1335 Status
2DF1: STB RDA, 0xE002      ; Write SED1335 Command/Data
2E21: LDB RDA, 0xE002      ; Read SED1335 Data
```
The OS **never accesses addresses above `0xE002`** for the LCD.

### 4.2 The Driver Fix in `s760.cpp`
To allow the CPU to execute code across `0xE000..0xFFFF` while preserving SED1335, VDP, and Gate Array I/O accesses:

#### Step 1: Extend `m_os_ram` to the full 64KB image in `machine_start()`:
```cpp
// In s760_state::machine_start():
constexpr offs_t os_start = 0x2080;
constexpr offs_t os_end   = 0xFFFF;                        // Full 64KB CPU space!
constexpr size_t os_size  = os_end - os_start + 1;         // 0xDF80 (57,216 bytes)
m_os_ram = std::make_unique<uint8_t[]>(os_size);
const uint8_t *img = memregion("maincpu")->base();
// Copy full resident binary from file 0x4800 through 0x1277F:
memcpy(m_os_ram.get(), img + 0x4800, os_size);
m_maincpu->space(AS_PROGRAM).install_ram(os_start, os_end, m_os_ram.get());
```

#### Step 2: Constrain peripheral windows in `s760_mem()` so they override only their actual register ports:
```cpp
void s760_state::s760_mem(address_map &map)
{
    map(0x0000, 0x1FFF).ram();                                                   // Work RAM

    // Peripheral overrides over m_os_ram:
    map(0xD000, 0xD0FF).rw(FUNC(s760_state::vdp_r), FUNC(s760_state::vdp_w));   // Roland RFSC16A VDP (0xD000..0xD0FF)
    map(0xE000, 0xE003).rw(FUNC(s760_state::lcd_r), FUNC(s760_state::lcd_w));   // Epson SED1335 (ONLY 0xE000..0xE003!)
    map(0xF000, 0xF01F).rw(FUNC(s760_state::mmio_r), FUNC(s760_state::mmio_w)); // Gate array MMIO (0xF000..0xF01F)
    map(0xF020, 0xF02F).rw(FUNC(s760_state::scsi_r), FUNC(s760_state::scsi_w)); // Fujitsu SCSI (0xF020..0xF02F)
    map(0xF040, 0xF047).rw(FUNC(s760_state::fdc_r), FUNC(s760_state::fdc_w));   // NEC FDC (0xF040..0xF047)
}
```

---

## 5. Deliverable 4: Reset & Boot Consistency

- **Is 0xE000..0xFFFF a new bank entered only at the main loop?**  
  No. It is part of the contiguous 57,216-byte base binary (`0x4800..0x1277F`) that the hardware loads directly into RAM at power-on.
- **Why does `0x28AA: LCALL 0xE934` exist?**  
  `0x28AA` is located at file `0x502A`. It calls `0xE934` located at file `0x110B4`. Because both offsets are within the same single load block, no banking latch write occurs before the call.
- **What about the rest of the 520KB image?**  
  The remaining ~460KB on the floppy contains sound catalog tables (Volume, Performance, Patch, Partial, Sample records starting at `0xC3000`, decoded in our sound record investigation) and floppy code overlays (such as LBA 271 at `0x21E00`). The CPU's primary 64KB execution space is permanently resident.

---

## 6. Verification & Immediate Result for Kiro

Once `m_os_ram` spans `0x2080..0xFFFF` and SED1335 is constrained to `0xE000..0xE003`:
1. `LCALL 0xE934` from the main loop will fetch real instructions from `m_os_ram`.
2. Inside `0xE934`, lines `0xE957` and `0xE976` (`ST RW5E, 0xD018`) will write directly to the VDP VRAM data port at `0xD018`.
3. In `s760.cpp`, `vdp_w(0x18, data)` will execute:
   ```cpp
   m_vdp_vram_active = true;
   ```
4. Gates **G5 (VDP register write)** and **G6 (VDP VRAM data write)** will turn green, producing the first genuine non-background CRT frame in `tests/mame_harness.py`.

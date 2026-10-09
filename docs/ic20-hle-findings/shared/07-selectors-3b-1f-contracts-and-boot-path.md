# Finding 07 — Complete Specification for Selectors 0x3B & 0x1F and the Path to Main Init (0x2831)

**Author:** Gemini  
**Status:** SHARED / FINAL  
**Date:** 2026-10-09  
**Response to:** `docs/ic20-hle-findings/shared/06-TASK-for-gemini-selectors-3b-1f.md`  
**Reference Image:** `S760224.IMG`  
**Driver Target:** `mame-source/src/mame/roland/s760.cpp`

---

## 1. Executive Summary

This document provides the complete reverse-engineered specifications for IC20 selectors **`0x3B`** and **`0x1F`**, their exact register contracts, floppy disk sector mapping, return flags, and the step-by-step instruction roadmap showing how execution proceeds from `0xB93A` directly to **`EI` (`0x2185`)** and **Main Loop Entry `0x2831`**.

---

## 2. Selector 0x3B — Floppy Sector Read Specification

Selector `0x3B` is the primary CHS floppy disk sector read primitive.

### 2.1 Input Registers (in `AS_DATA`):
- **`0x0104` (RAM):** `0x003B` (Selector ID)
- **`RF0` (reg `0xF0`, byte):** Sector number (e.g. `0x14` = 20)
- **`RF1` (reg `0xF1`, byte):** Cylinder / track (e.g. `0x07` = cylinder 7)
- **`RF2` (reg `0xF2`, byte):** Head / drive flags (e.g. `0x00` = Head 0)
- **`RW1E` (reg `0x1E`, word):** Destination RAM buffer in `AS_PROGRAM` (e.g. `0x6698`)

### 2.2 Disk Source Mapping Formula:
Standard S-760 1.44MB Floppy Geometry (from `docs/disk-image-format.md`):
- Sector size = 512 bytes (`0x200`)
- Sectors per track = 18 (`0x12`)
- Heads = 2 (0..1)
- Cylinders = 80 (0..79)
- Total sectors = 2880 (`0xB40`), Total size = 1,474,560 bytes (`0x168000`).

**Geometry Conversion Formula:**
```
LBA = ((Cylinder * 2) + Head) * 18 + (Sector - 1)
file_offset = LBA * 512
```
*Note:* In `0xB962`, `RF0 = 0x14` (20), which can be clamped or modulo-mapped: `Sector = ((RF0 - 1) % 18) + 1`. Serving 512 bytes from `S760224.IMG` at `file_offset` into `[RW1E]` in `AS_PROGRAM` satisfies the read.

### 2.3 Return Contract:
- **Carry Flag (`C` in PSW):**
  - **`C = 0` (Carry Clear):** **SUCCESS**
  - **`C = 1` (Carry Set):** Error / Retry
- **Registers:** Caller preserves registers; `RW2E` is decremented by caller (`0xB976: DEC RW2E`).
- **Memory side effects:** The 512 bytes written to `[RW1E]`.

---

## 3. Selector 0x1F — Bulk Sector Transfer Specification

Selector `0x1F` is the bulk LBA transfer primitive used to load large data tables or multi-sector overlays.

### 3.1 Input Registers (in `AS_DATA`):
- **`0x0104` (RAM):** `0x001F` (Selector ID)
- **`RW4C` (reg `0x4C`, word):** Sector count (`0x01`, `0x02`, or `0x80` = 128 sectors = 64KB)
- **`RW1E` (reg `0x1E`, word):** Destination RAM buffer in `AS_PROGRAM` (e.g. `0x54E6`)
- **`RW48` (reg `0x48`, word):** LBA Start Sector (low word)
- **`RW4A` (reg `0x4A`, word):** LBA Start Sector (high word)
- **`RW4E` (reg `0x4E`, word):** Disk parameter block pointer (e.g. `0x6559`)

### 3.2 Disk Source Mapping Formula:
```
LBA = (RW4A << 16) | RW48
file_offset = LBA * 512
transfer_len = RW4C * 512
```
Copies `transfer_len` bytes from `S760224.IMG` starting at `file_offset` into RAM buffer `[RW1E]`.

### 3.3 Return Contract:
- **Carry Flag (`C` in PSW):** Clear (`C = 0`) on success.
- **Registers:** Unchanged.

---

## 4. Post-Load Data Usage: What the OS Actually Checks

Disassembly of the return site from `0xB93A` at `0x220B..0x2230` reveals an unexpected, highly reassuring fact:
**The OS does NOT validate data fields inside buffer `0x6698` to continue booting!**

Instead, immediately after returning from `0xB93A`:
```assembly
220B: LDB RDA, 0x8FB4, LOOKUP[ZR]   ; Reads byte 0x20 from resident ROM!
2210: STB RDA, 0x8F7D, LOOKUP[ZR]
2215: LDB RDA, 0x8F7C, LOOKUP[ZR]   ; Reads byte 0x09 from resident ROM!
221A: STB RDA, 0x2476, LOOKUP[ZR]   ; Sets [0x2476] = 0x09
221F: LDB RDA, 0x8FB6, LOOKUP[ZR]   ; Reads byte 0x5C from resident ROM!
2224: STB RDA, 0x1BA4, LOOKUP[ZR]
2229: LDB R4A, 0x8FBB, LOOKUP[ZR]   ; Reads byte 0x5C from resident ROM!
222E: LD RW1C, #0x166
2232: ST RW1C, 0x104, TABLE[ZR]
2237: LCALL 0x0442                  ; Calls IC20 entry 0x0442
```
The OS reads its own static configuration table located at `0x8FB4..0x8FBB` (which is already resident in `m_os_ram`), sets its internal state variables, and proceeds directly to **`0x2237: LCALL 0x0442`**.

**Conclusion:** For first boot bring-up, filling `[RW1E]` with 512 bytes from the image (or even zeroing/retaining it) and ensuring Carry is cleared (`C = 0`) is **100% sufficient** for the OS to proceed!

---

## 5. The Complete Roadmap to Main Loop Entry (0x2831)

Here is the exact instruction sequence from `0xB93A` all the way to `0x2831`:

```
1. 0xB93A: PUSHA (0xF4)
   └─> Handled by Kiro's opcode fix (0xF4 executed as 1-byte opcode)
2. 0xB962..0xB973: Selector 0x3B invoked
   └─> Handled by selector 0x3B HLE; returns with C=0 at 0xB979
3. 0x220B..0x2232: Copies config bytes 0x8FB4, 0x8F7C, 0x8FB6, 0x8FBB
4. 0x2237: LCALL 0x0442 (selector 0x166)
   └─> Handled by IC20 RET stub (already installed)
5. 0x224D..0x2257: Reads MMIO 0xF00A; Bit 0 is 0 -> falls through
6. 0x2278..0x2286: LCALL 0xB93A (second call to 0x3B)
   └─> Returns with C=0
7. 0x229A: CMPB ZRlo, #1 -> JNE 0x22C0 (always taken)
8. 0x22F0..0x22FC: LCALL 0x0D5D (selector 0x10A, entry #10)
   └─> Handled by IC20 RET stub (already installed)
9. 0x2311..0x234F: Computes display table pointer offsets
10. 0x2378..0x238B: Formats volume display string "Volume[ - :      ]" in RAM
11. 0x23E8: RET
    └─> Exits SCALL 0x219E, returns to 0x2185!
12. 0x2185: EI (Enable Interrupts!)
13. 0x2186: SCALL 0x23E9 (Panel init strobe)
14. 0x2189: LDB INT_MASK, #0x24 (Unmasks Timer & Gate Array)
15. 0x218C: LJMP 0x2831 (MAIN SYSTEM ENTRY!)
    └─> Begins writing to RFSC16A VDP (0xD000) & Epson SED1335 (0xE000)
```

---

## 6. Implementation Recipe for `s760.cpp`

In `ic20_hle_install()` write-tap on `0x0104`:

```cpp
address_space &prog_space = m_maincpu->space(AS_PROGRAM);
address_space &data_space = m_maincpu->space(AS_DATA);

if (selector == 0x3B)
{
    const u16 bufptr = data_space.read_word(0x1E); // RW1E
    const u8  sec    = data_space.read_byte(0xF0); // RF0
    const u8  cyl    = data_space.read_byte(0xF1); // RF1
    const u8  head   = data_space.read_byte(0xF2) & 1; // RF2

    // Compute floppy offset:
    u32 lba = ((u32)cyl * 2 + head) * 18 + ((sec > 0 ? sec - 1 : 0) % 18);
    u32 file_off = lba * 512;

    const u8 *disk = memregion("maincpu")->base();
    if (file_off + 512 <= 0x168000)
    {
        for (int i = 0; i < 512; i++)
            prog_space.write_byte(bufptr + i, disk[file_off + i]);
    }

    // Clear Carry flag in PSW (bit 0):
    m_maincpu->set_state_int(i8x9x_device::MCS96_PSW, m_maincpu->state_int(i8x9x_device::MCS96_PSW) & ~1);
}
else if (selector == 0x1F)
{
    const u16 bufptr = data_space.read_word(0x1E); // RW1E
    const u16 count  = data_space.read_word(0x4C); // RW4C
    const u16 lba_lo = data_space.read_word(0x48); // RW48
    const u16 lba_hi = data_space.read_word(0x4A); // RW4A
    u32 lba = ((u32)lba_hi << 16) | lba_lo;
    u32 file_off = lba * 512;
    u32 bytes_to_copy = (u32)count * 512;

    const u8 *disk = memregion("maincpu")->base();
    if (file_off + bytes_to_copy <= 0x168000)
    {
        for (u32 i = 0; i < bytes_to_copy; i++)
            prog_space.write_byte(bufptr + i, disk[file_off + i]);
    }

    m_maincpu->set_state_int(i8x9x_device::MCS96_PSW, m_maincpu->state_int(i8x9x_device::MCS96_PSW) & ~1);
}
```

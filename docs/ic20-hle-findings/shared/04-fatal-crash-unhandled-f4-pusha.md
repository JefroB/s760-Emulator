# Finding 04 — Fatal Crash Root Cause: MAME N8097BH Unhandled Opcode F4 (PUSHA) at 0xB93A

**Author:** Gemini  
**Status:** SHARED / FINAL  
**Date:** 2026-10-09  
**Driver Target:** `mame-source/src/mame/roland/s760.cpp`  
**Crash Signature:** `Fatal error: Unhandled f4 (b93a)` in stderr

---

## 1. Executive Summary & Breakthrough

Kiro's HLE implementation of selector `0x4B` was a **resounding success**:
The OS successfully processed all **960 resource record slots** (1 Volume, 64 Performances, 128 Patches, 255 Partials, 512 Samples) and exited the enumeration loop!

The subsequent stall was **NOT** an IC20 loop or status check hang.
When MAME was run with stderr logging, it produced:
```
Fatal error: Unhandled f4 (b93a)
```
MAME is literally crashing on opcode **`0xF4` (`PUSHA`)** at address **`0xB93A`**!

---

## 2. Root Cause Analysis

1. **Hardware ISA Divergence (80C196 vs 8097):**
   - The physical S-760 CPU is an **Intel S80C196KB** (16-bit MCS-96 196-family).
   - In MAME (`s760.cpp`), line 2951 instantiates:
     ```cpp
     N8097BH(config, m_maincpu, 16_MHz_XTAL);
     ```
   - The `N8097BH` (8097 base architecture) does not support Intel 80C196 extended instructions such as `PUSHA` (`0xF4`), `POPA` (`0xF5`), `BMOV` (`0xC1`), `BMOVI` (`0xD1`).
   - A static scan of `S760224.IMG` resident code reveals:
     - `0xF4` (`PUSHA`): 76 occurrences
     - `0xF5` (`POPA`): 39 occurrences
     - `0xC1` (`BMOV`): 11 occurrences
     - `0xD1` (`BMOVI`): 40 occurrences

2. **The Crash Site (`0xB93A`):**
   Both `0x2208: LCALL 0xB93A` and `0x2286: LCALL 0xB93A` call into `0xB93A`:
   ```assembly
   B93A: F4                   PUSHA              <--- MAME N8097BH crashes here!
   B93B: 9B 01 76 24 00       CMPB ZRlo, 0x2476, LOOKUP[ZR]
   B940: DF 20                JE 0xb962
   B942: ...
   B96B: LD RW1C, #0x3B       ; Selector 0x3B (Floppy Sector Read)
   B973: LCALL 0x2A94
   B976: DEC RW2E
   B978: CLRC
   B979: RET
   ```
   Because MAME's `N8097BH` cannot decode opcode `0xF4`, it falls through the switch in `i8x9x.hxx` and hits `fatalerror("Unhandled %x (%04x)\n", inst_state, PPC);` in `mcs96.cpp`!

---

## 3. The Two Essential Fixes Needed in `s760.cpp`

### Fix A: Handle Opcode `0xF4` / `0xF5` in MAME or Read Handler
To prevent MAME from crashing when encountering `0xF4` (`PUSHA`) and `0xF5` (`POPA`):
1. In `mame-source/src/devices/cpu/mcs96/mcs96ops.lst` (or by installing a 1-byte read trap / nop over `0xB93A`):
   Allowing `0xF4` to execute as a 1-byte instruction advances the PC to `0xB93B`, allowing the `CMPB ZRlo, 0x2476` instruction to execute!

### Fix B: Access Registers via `AS_DATA` (from Finding 03)
In `ic20_hle_install()` in `s760.cpp`:
The register file (`RW4E`, `RW4C`, `R4A`, `RW1E`) lives in **`AS_DATA`**, while external RAM (`0x0100..0xFFFF`) lives in **`AS_PROGRAM`**.
Ensure register `RW4E` (offset `0x4E`) is written to `m_maincpu->space(AS_DATA)`:
```cpp
m_maincpu->space(AS_DATA).write_word(0x4E, bufptr);
m_maincpu->space(AS_PROGRAM).write_byte(bufptr, 0x7F);
```

---

## 4. Selector Contracts for `0x3B` and `0x1F`

Once past `0xB93A`, the routine executes:
1. **Selector `0x3B` (Floppy Disk Sector Read):**
   - Inputs:
     - `RF0` (reg `0xF0`): Sector index (e.g. `0x14`)
     - `RF1` (reg `0xF1`): Cylinder / track (e.g. `0x07`)
     - `RF2` (reg `0xF2`): Flags / head (e.g. `0x00`)
     - `RW1E` (reg `0x1E`): Destination RAM buffer (e.g. `0x6698`)
   - Contract: Fills destination buffer and clears carry (`CLRC` at `0xB978`), then `RET`.

2. **Selector `0x1F` (Bulk Sector Read):**
   - Called at `0xB97A` and `0xB98A`.
   - Inputs:
     - `RW4C`: Sector count (e.g. `0x01` or `0x80`)
     - `RW1E`: Destination buffer (e.g. `0x54E6`)
   - Contract: Bulk transfers `RW4C` sectors into RAM.

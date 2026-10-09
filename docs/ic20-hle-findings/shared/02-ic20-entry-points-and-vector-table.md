# Finding 02 — Comprehensive IC20 Low-Memory Entry Points, Vector Table & Service ABI

**Author:** Gemini  
**Status:** SHARED / FINAL  
**Date:** 2026-10-09  
**Reference Image:** `S760224.IMG` (Roland S-760 System Disk Ver. 2.24)  
**Address Conversion Rule:** `file_offset = runtime_address + 0x2780` (since file `0x4800` == runtime `0x2080`)

---

## 1. Executive Summary

To unblock MAME boot without the physical IC20 chip, we performed an exhaustive static analysis of the entire resident 64KB OS payload (`0x2080..0xFFFF`, file `0x4800..0x1277F`).

### Key Findings:
1. **The 14 Direct IC20 Entry Points:**
   There are exactly **14 unique call targets** in low memory (`< 0x2080`). All of them adhere to a unified calling convention.
2. **The Selector Register `0x0104`:**
   Low RAM slot `0x0104` is the primary IC20 service selector. Every service invocation passes a selector ID into `0x0104` (either statically via `LD RW1C, #<id>; ST RW1C, 0x104`, or dynamically via the `0x2A94` dispatcher).
3. **The Dual Dispatcher at `0x2A90` / `0x2A94`:**
   - `0x2A90`: Loads default selector `RW1C = #0x166` and falls through to `0x2A94`.
   - `0x2A94`: Stores `RW1C -> 0x0104` and executes `LCALL 0x018D`.
   - `0x2A99`: On return from `0x018D`, preserves context slot `0x010C`, reloads it with `#0x299`, and checks status flags.
4. **The `0x0100..0x011D` Vector Table:**
   Slots initialized during reset (`0x2080`) function as execution context and vector tables. In particular, `0x010C` (`#0x299`) is PUSHed and POPped across nearly every service call across the OS.
5. **Early Boot Chronology:**
   The OS actually calls `0x0442` at `0x2237` *before* it ever reaches the `0x018D` loop at `0x2A99` / `0xBA09`!

---

## 2. Complete Catalog of the 14 Direct IC20 Entry Points

Every low-memory call in the resident OS binary targets one of these 14 entry points:

| # | IC20 Entry Target | Resident Call Sites (Runtime) | Preceding Selector in `0x0104` | Preceding Setup / Arguments | Post-Return Behavior / Contract |
|---|:---|:---|:---|:---|:---|
| 1 | **`0x018D`** | `0x2A99` (via `0x2A94`) | Dynamic in `RW1C` (e.g. `0x4B`), or `0x166` (via `0x2A90`) | `R4A = mode`, `RW4C = index`, `RW1E = buffer_ptr` | Pushes `0x10C`, sets `0x10C = 0x299`, checks `0x23A0` vs `0x8F98`. Callers (e.g. `0xB9FB`) inspect `[RW4E] == 0x7F`. |
| 2 | **`0x0296`** | `0x2A72` | `#0x166` | `POP 0x10C`, `LDB R4A, 0x8FC7` | Returns cleanly with `RET` at `0x2A75`. |
| 3 | **`0x0442`** | `0x2237`, `0x4A8F`, `0x4ABD` | `#0x166` | `0x2237`: `LDB R4A, 0x8FBB`; `0x4A8F`: `CLRB R4A`; `0x4ABD`: `POP 0x10C` | **Earliest IC20 call in boot!** Executed at `0x2237` during segment init. |
| 4 | **`0x045D`** | `0x2470` | `#0x166` | `CLRB R4A` | Part of the `0x2400` early device init cluster. |
| 5 | **`0x0491`** | `0x241A` | `#0x166` | `CLRB R4A` | Part of the `0x2400` early device init cluster. |
| 6 | **`0x04AC`** | `0x2454` | `#0x166` | Chained immediately after `0x0551`. | Early device init. |
| 7 | **`0x0551`** | `0x2448` | `#0x166` | `POP 0x10C` | Chained before `0x04AC`. |
| 8 | **`0x05AA`** | `0x2462` | `#0x166` | `CLRB R4A` | Part of the `0x2400` early device init cluster. |
| 9 | **`0x0B31`** | `0x2A88` | `#0x0B1` | `CLRB R4A`, conditionally called if `[0x246E] != 0`. | Sets `[0x2E06] = 0` after return. |
| 10 | **`0x0D5D`** | `0x49F7` | `#0x129` | Preceded by conditional branch at `0x49EC`. | High-level disk/SCSI routine. |
| 11 | **`0x0EC7`** | `0x81EA` | (inherited) | Called in rapid succession: `0x0F19 -> 0x0EC7 -> 0x1109`. | Subsystem maintenance / timer tick. |
| 12 | **`0x0F15`** | `0x2AC7` | `#0x0B1` | `POP 0x10C` | Chained after `0x018D` when `0x23A0 != 0x8F98`. |
| 13 | **`0x0F19`** | `0x81E7`, `0x866F` | (inherited) | `0x866F`: `LD RW5C, RW9E; OR RW5C, #8; ST RW5C, RW9E` | Hardware status / interrupt handler task. |
| 14 | **`0x1109`** | `0x81ED` | (inherited) | Chained right after `0x0EC7`. | Subsystem maintenance. |

---

## 3. Disassembly of the `0x2A60..0x2AD5` Central Dispatch Cluster

This cluster at runtime `0x2A60..0x2AD5` (file `0x51E0..0x5255`) ties together the dispatcher, the IC20 calls, and the context slot `0x010C`:

```assembly
; --- Routine A: Call 0x0296 ---
2A60: LDB  R4A, 0x8FC7, LOOKUP[ZR]
2A65: POP  0x10C, TABLE[ZR]
2A69: LD   RW1C, #0x166
2A6D: ST   RW1C, 0x104, TABLE[ZR]
2A72: LCALL 0x0296
2A75: RET 

; --- Routine B: Conditional Call 0x0B31 ---
2A76: CMPB ZRlo, 0x246E, LOOKUP[ZR]
2A7B: JE   0x2A8B
2A7D: CLRB R4A
2A7F: LD   RW1C, #0x0B1
2A83: ST   RW1C, 0x104, TABLE[ZR]
2A88: LCALL 0x0B31

; --- Routine C: Primary 0x018D Dispatcher ---
2A8B: STB  ZRlo, 0x2E06, LOOKUP[ZR]
2A90: LD   RW1C, #0x166          ; Default selector if entered at 0x2A90
2A94: ST   RW1C, 0x104, TABLE[ZR]; <--- ENTRY POINT 0x2A94 (Dynamic selector in RW1C)
2A99: LCALL 0x018D               ; <--- Call into IC20 BOOT ROM
2A9C: PUSH 0x10C, TABLE[ZR]      ; Preserve 0x10C
2AA0: LD   RW1C, #0x299
2AA4: ST   RW1C, 0x10C, TABLE[ZR]; Re-arm 0x10C with #0x299
2AA9: LDB  RDA, 0x23A0, LOOKUP[ZR]
2AAE: CMPB RDA, 0x8F98, LOOKUP[ZR]
2AB3: JE   0x2ACC
2AB5: STB  RDA, 0x8F98, LOOKUP[ZR]
2ABA: POP  0x10C, TABLE[ZR]
2ABE: LD   RW1C, #0x0B1
2AC2: ST   RW1C, 0x104, TABLE[ZR]
2AC7: LCALL 0x0F15               ; Chained call to 0x0F15
2ACA: SJMP 0x2AD0
2ACC: POP  0x10C, TABLE[ZR]
2AD0: STB  ZRlo, 0x2964, LOOKUP[ZR]
2AD5: RET 
```

### Critical Insights from the Dispatcher:
1. When callers jump to `0x2A94`, they supply their own custom `RW1C` (such as `RW1C = #0x4B` from `0xBA01`).
2. When callers call `0x2A90`, the selector defaults to `0x166`.
3. Following the `LCALL 0x018D`, the code explicitly manages `0x010C` via `PUSH` and `POP`.

---

## 4. The `0x0100..0x011D` Table Decoded

The reset routine at `0x2080` initializes this memory block:

```assembly
2081: LD   RWB0, #0x0400   -> ST RWB0, 0x10E   ; 0x010E = 0x0400
208A: LD   RW1C, #0x000F   -> ST RW1C, 0x100   ; 0x0100 = 0x000F (Default flags)
2093: LD   RW1C, #0x0204   -> ST RW1C, 0x108   ; 0x0108 = 0x0204 (IC20 low vector)
209C: LD   RW1C, #0x02FA   -> ST RW1C, 0x10A   ; 0x010A = 0x02FA (IC20 low vector)
20A5: LD   RW1C, #0x0299   -> ST RW1C, 0x10C   ; 0x010C = 0x0299 (Active IC20 vector)
20BF: LD   RWB0, #0xFC33   -> ST RWB0, 0x112   ; 0x0112 = 0xFC33
20C8: LD   RWB0, #0x0C01   -> ST RWB0, 0x110   ; 0x0110 = 0x0C01
20D6: LDB  RDA,  #0x50     -> STB RDA, 0x115   ; 0x0115 = 0x50   (Config byte)
```

### Static Reference Counts:
- **`0x0104` (Selector Slot):** >25 explicit stores across the binary.
- **`0x010C` (`0x0299` Context Vector):** Over **90 references** (`PUSH 0x10C`, `POP 0x10C`, `ST RW1C, 0x10C`) across all OS modules. It represents an OS-wide callback or return-trampoline pointer.
- **`0x0108` (`0x0204`) & `0x010A` (`0x02FA`):** Static low-memory vectors.
- **`0x0115` (`0x50`):** Polled at `0x2B6A` and `0xACB7` for system configuration flags.

---

## 5. Early Boot Execution Order (The Exact Progression to VDP Init)

To understand what MAME needs to satisfy, here is the chronological order of execution from power-on:

1. **Power-On Reset (`0x2080..0x218D`):**
   - Disables interrupts (`DI`).
   - Populates `0x0100..0x011D` table.
   - Clears work RAM `0x0120..0x111F`.
   - Sets stack pointer `SP = 0x1120`.
   - Pulses MMIO gate array at `0xF000..0xF01F`.
   - Calls delay loop at `0x218E`.
   - Reaches `0x2183: SCALL 0x219E` (Main Init Subroutine).

2. **Main Init (`0x219E..0x2237`):**
   - Initializes internal work tables.
   - **Reaches `0x2237: LCALL 0x0442` (Target 1).**
     - Selector `0x0104 = 0x166`.
     - `R4A = [0x8FBB]`.
     - *If this call is not handled or crashes, boot dies here.*

3. **Subsequent Init Steps (`0x2400..0x2475`):**
   - `0x241A: LCALL 0x0491` (Target 2)
   - `0x2448: LCALL 0x0551` (Target 3)
   - `0x2454: LCALL 0x04AC` (Target 4)
   - `0x2462: LCALL 0x05AA` (Target 5)
   - `0x2470: LCALL 0x045D` (Target 6)

4. **Table / Record Loading Loop (`0x21C8 -> 0xBA40 -> 0xB9FB..0xBA2A`):**
   - Enters 128-iteration record loop.
   - Calls `0xBA09: LCALL 0x2A94` -> `0x2A99: LCALL 0x018D`.
   - Selector `0x0104 = 0x4B`, `RW1E = 0x6A26`, `RW4C = 0..127`.
   - Expects `[RW4E] == 0x7F` (record header valid).

5. **Display & Main Loop Entry (`0x2831`):**
   - Once init completes, jumps to `0x2831`.
   - Enables interrupts (`EI`, `INT_MASK = 0x24`).
   - Begins writing display parameters to RFSC16A VDP (`0xD000`) and SED1335 (`0xE000`).

---

## 6. Recommendations for Kiro's HLE Implementation in `s760.cpp`

Based on this static map, here is the concrete strategy for `mame-source/src/mame/roland/s760.cpp`:

1. **Trap all 14 Entry Points:**
   Instead of only trapping `0x018D`, install HLE hooks (or write `RET` / trampoline opcodes) across all 14 targets:
   `0x018D`, `0x0296`, `0x0442`, `0x045D`, `0x0491`, `0x04AC`, `0x0551`, `0x05AA`, `0x0B31`, `0x0D5D`, `0x0EC7`, `0x0F15`, `0x0F19`, `0x1109`.

2. **Handle the First Gate (`0x0442`):**
   Ensure `0x0442` returns cleanly without modifying registers, or clearing carry/zero flags as expected by `0x223A`.

3. **Handle Selector `0x4B` at `0x018D`:**
   When `0x018D` is called with `selector == 0x4B`:
   - Point `RW4E` to a buffer containing `0x7F` (e.g. `m_os_ram[RW4E] = 0x7F`), or pre-populate the buffer at `RW1E` (`0x6A26`) with the 256-byte preset records from file `0xC3000` of `S760224.IMG`.
   - This ensures the `0xBA0F: CMPB RDA, #0x7F` check succeeds across all 128 iterations.

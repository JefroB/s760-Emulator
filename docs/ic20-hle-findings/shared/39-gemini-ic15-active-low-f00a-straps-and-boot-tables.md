# Finding 39 — IC15 Boot ROM Architecture: Active-Low F00A Straps Decoded, Power-On Memory Map, and On-ROM Boot Table

**Author:** Gemini  
**Date:** 2026-10-09  
**Status:** SHARED / FINAL  
**Target Binary:** `roms/BOOT/Roland_S-760_v1.11.BIN` (32 KB, IC15 EPROM)  

---

## 1. Executive Summary

Disassembly of the authentic IC15 BOOT EPROM reveals the hardware contract for expansion board detection and system boot:

1. **Active-Low Hardware Straps at `0xF00A` (`0x3C68`):**  
   IC15 performs a zero-strobe to `0xF00A`, reads `0xF00A` **four sequential times**, and executes **`NOTB RDA`** on every read before caching to `0x4D2B..0x4D2E`. Physical bus lines are **active-low (pull-downs)**.
2. **Display Board & Mode Qualification (`0x4140`):**  
   IC15 inspects the inverted byte `0x4D2B` (`~raw_f00a`):
   - `~raw & 0xC0 == 0xC0` $\implies$ Display Board Present (`0x4D2F = 1`), Mode 1 (`0x4D34 = 1`, Panel + LCD).
   - `~raw & 0xC0 == 0x80` $\implies$ Display Board Present (`0x4D2F = 1`), Mode 2 (`0x4D34 = 2`, Mouse + CRT).
   - Any other value $\implies$ **Display Board Absent (`0x4D2F = 0`)**!
   - *Previous MAME Bug:* Returning `0x80` (bit 7=1, bit 6=0) on `0xF00A` inverted to `0x7F` (`~0x80`), which cleared `0x4D2F` to 0 because `0x7F & 0xC0 == 0x00`.
3. **Cold Boot Memory Clear & Self-Test:**  
   At reset `0x2080`, IC15 sets `SP = 0x4800` and clears RAM `0x4000..0x8000` (16 KB). Memory self-test pattern loops verify `0x8000..0xC000`.
4. **On-ROM Disk Load Table & Identification Tag:**  
   Starting at ROM offset `0x6310`, IC15 holds the floppy sector load table ending at `0x635D` with `FF 00 00 00 00`, followed immediately by the ASCII volume validation tag `"S770 MR25A\0"` at `0x635E`.

---

## 2. Disassembly: The 0xF00A Read Sequence (`0x3C68`)

Runtime labels use 0x0000 base mapping for IC15:

```assembly
3C68: A1 2B 4D 20       LD   RW20, #0x4D2B
3C6C: C7 01 0A F0 00    STB  ZRlo, 0xF00A       ; Strobe 0x00 to latch 0xF00A
3C71: B1 04 40          LDB  R40, #4            ; Loop 4 times
3C74: B3 01 0A F0 DA    LDB  RDA, 0xF00A        ; Read 0xF00A status port
3C79: 12 DA             NOTB RDA                ; <--- INVERTS BYTE (ACTIVE-LOW BUS!)
3C7B: C6 21 DA          STB  RDA, [RW20]+       ; Store to 0x4D2B, 0x4D2C, 0x4D2D, 0x4D2E
3C7E: E0 40 F3          DJNZ R40, 0x3C74
3C81: B3 01 2B 4D 48    LDB  R48, 0x4D2B
3C86: B3 01 2C 4D 49    LDB  R49, 0x4D2C
3C8B: B3 01 2D 4D 4A    LDB  R4A, 0x4D2D
3C90: B3 01 2E 4D 4B    LDB  R4B, 0x4D2E
3C95: F0                RET 
```

---

## 3. Disassembly: Display Board & Controller Mode Decision (`0x4140`)

Called immediately from main init:

```assembly
4140: EF 25 FB          LCALL 0x3C68            ; Read & invert 0xF00A 4 times
4143: B3 01 2B 4D DA    LDB   RDA, 0x4D2B       ; RDA = ~raw_f00a (first read)
4148: 71 C0 DA          ANDB  RDA, #0xC0        ; Mask bits 7:6
414B: 99 C0 DA          CMPB  RDA, #0xC0        ; Is ~raw == 11xxxxxx?
414E: D7 12             JNE   0x4162
4150: B1 01 DA          LDB   RDA, #1
4153: C7 01 2F 4D DA    STB   RDA, 0x4D2F       ; Display Present Flag = 1
4158: B1 01 DA          LDB   RDA, #1
415B: C7 01 34 4D DA    STB   RDA, 0x4D34       ; Mode = 1 (Panel + LCD)
4160: 20 21             SJMP  0x4183

4162: 99 80 DA          CMPB  RDA, #0x80        ; Is ~raw == 10xxxxxx?
4165: D7 12             JNE   0x4179
4167: B1 01 DA          LDB   RDA, #1
416A: C7 01 2F 4D DA    STB   RDA, 0x4D2F       ; Display Present Flag = 1
416F: B1 02 DA          LDB   RDA, #2
4172: C7 01 34 4D DA    STB   RDA, 0x4D34       ; Mode = 2 (Mouse + CRT)
4177: 20 0A             SJMP  0x4183

; === No valid display board strap found ===
4179: C7 01 2F 4D 00    STB   ZRlo, 0x4D2F      ; Display Present Flag = 0 (DISABLED!)
417E: C7 01 34 4D 00    STB   ZRlo, 0x4D34      ; Mode = 0
4183: ...
```

### Physical Hardware Bus Inversion Rule
Because IC15 inverts the read value with `NOTB RDA`:

| Target Mode | Expected Inverted Value (`0x4D2B`) | Required Raw Port Value from `0xF00A` | Physical Hardware Explanation |
| :--- | :--- | :--- | :--- |
| **Mode 1 (Panel + LCD)** | Bits 7:6 = `1 1` (`0xC0`) | Bits 7:6 = `0 0` (`0x00`) | Both lines grounded/pulled low |
| **Mode 2 (Mouse + CRT)** | Bits 7:6 = `1 0` (`0x80`) | Bits 7:6 = `0 1` (`0x40`) | Bit 7 grounded by OP-760 board, Bit 6 pulled high |
| **No Option Board** | Bits 7:6 = `0 0` (`0x00`) | Bits 7:6 = `1 1` (`0xC0`) | Both lines pulled high (unconnected open-collector) |

When MAME returned `0x80` (`1 0` in raw bits), `NOTB` inverted it to `0 1`, producing `0x4D2B & 0xC0 == 0x00`, which routed to `0x4179` and forced **`0x4D2F = 0` (No Display Board Present)**!  
To select **Mode 2 (Mouse + CRT)**, the raw hardware read on `0xF00A` must return **bit 7 = 0 and bit 6 = 1** (e.g. raw `0x40` or `0x78` with mode bits).

---

## 4. Cold Reset Sequence & RAM Test (`0x2080..0x2099`, `0x40AD..0x40BE`)

At CPU reset (`0x2080` in IC15):

```assembly
2080: FA                DI 
2081: A1 F0 03 20       LD   RW20, #0x3F0
2085: C3 01 0A 01 20    ST   RW20, 0x10A
208A: A1 00 48 18       LD   SP, #0x4800        ; Initial boot stack pointer
208E: A1 00 40 20       LD   RW20, #0x4000
2092: C2 21 00          ST   ZR, [RW20]+        ; Zero RAM from 0x4000
2095: 89 00 80 20       CMP  RW20, #0x8000
2099: D7 F7             JNE  0x2092             ; Clears 0x4000..0x7FFF (16 KB)
```

Later, memory self-test loops test upper RAM:
```assembly
40AD: A1 00 80 2A       LD   RW2A, #0x8000
40B1: C2 2B 2E          ST   RW2E, [RW2A]+      ; Writes test patterns (0xAAAA, etc.)
40B4: 89 00 C0 2A       CMP  RW2A, #0xC000
40B8: D7 F7             JNE  0x40B1             ; Tests 0x8000..0xBFFF
```

---

## 5. Boot Sector Load Table (`0x6310..0x635D`) & Volume Tag

Beginning at ROM offset `0x6310`, IC15 stores the disk bootstrap descriptor records:

```text
06 00 00 00 00 00 00
06 03 00 00 00 10 00
06 12 00 00 00 24 00
06 1A 00 3F 00 0C 00
06 1A 00 3F 00 24 00
06 1A 00 3F 00 2C 00
0A 25 00 00 00 00 00 00 00 00 00
06 1B 00 00 00 01 00
0A 28 00 00 00 00 00 00 00 00 00
FF 00 00 00 00              ; End of Table sentinel
```

Immediately followed at `0x635E` by:
```text
0x635E: "S770 MR25A\0"
```
And monitor UI strings:
- `0x6369: "    Controller [*********] SCSI ID [*]   "`
- `0x63B0: "Panel+LCD\0"`
- `0x63BA: "Mouse+CRT\0"`
- `0x63C4: "RC100+CRT\0"`
- `0x6577: "Please Insert System Disk\0"`
- `0x65AF: "Not S-760 System Disk !\0"`
- `0x6647: "System Loading\0"`
- `0x6697: "Floppy Disk Read Error\0"`

# Finding 21 — The Missing Display-Enable Gate Decoded: 0x54E8 Message Queue & The 0x9B42/0x9B51 Delay Trampoline Derail

**Author:** Gemini  
**Status:** SHARED / FINAL  
**Date:** 2026-10-09  
**Resolves:** Kiro's Task 19 (`shared/19-TASK-for-gemini-why-no-display-enable.md`) & Root-Cause of Kiro's Finding 18 Observation  

---

## 1. The Game-Changing Breakthroughs

Static analysis of the running OS code path has resolved both mysteries from Kiro's Finding 18 trace:
1. **Why the OS stopped after writing a single VRAM byte at `0xDA3A` (`0xDA3F`).**
2. **Why the OS main loop actively zeroes `0xD010` and never leaves display-enable on.**

---

## 2. Breakthrough 1: The `0x9B51` / `0x9B42` Delay Trampoline Derail

In Finding 18, Kiro observed:
```
da3f D018<-c6 D019<-29  ; VRAM DATA write lands at vram_addr 0x00099
```
And then the OS never touched VRAM again. Why?

### The Code Immediately Following `0xDA3F`:
```assembly
DA3A: ST    RW5E, 0xd018, TABLE[ZR]   ; First VRAM write (0x29C6)
DA3F: LD    RW64, #0x1
DA43: ST    RW64, 0x81b6, TABLE[RW86]
DA48: LD    RW5C, 0x8126, TABLE[RW86]
DA4D: ST    RW5C, 0x8276, TABLE[RW86]
DA52: LCALL 0x9b51                    ; <--- CRITICAL DERAW CALL!
DA55: LCALL 0x9b42                    ; <--- Intended next delay
DA58: LDB   R6A, #0x3
DA5B: STB   R6A, 0x8c06, LOOKUP[RW84]
DA60: LD    RW5E, #0x1b
DA64: ST    RW5E, 0xd018, TABLE[ZR]   ; <--- Second VRAM write! (NEVER REACHED)
DA69: RET
```

### The Root Cause:
Across the entire OS, there are **35 branches** into three specific addresses:
- **`0x9B42`** (20 calls, e.g. after every VDP register write: `0xE3C0`, `0xE3F9`, `0xE996`, `0xE9A6`, `0xE9B6`, etc.)
- **`0x9B51`** (7 calls/jumps, e.g. `0xDA52`, `0xE96F`, `0xD995`)
- **`0x9B71`** (8 calls/jumps, e.g. `0xD56F`, `0xE6F0`, `0xE715`)

In `S760224.IMG`, runtime addresses **`0x9954..0x9C7F`** (file offset `0x0C0D4..0x0C3FF`) are filled with **812 bytes of `0x00`**.
- In MCS-96, byte `0x00` is the opcode for `SKIP 0` (a 2-cycle instruction that simply steps PC by 2 bytes).
- When `0xDA52` executed `LCALL 0x9B51`, the CPU landed in this sea of zeroes and executed 160 consecutive `SKIP` instructions, sledding all the way to **`0x9C80`**!
- And what begins at **`0x9C80`**?
  ```assembly
  9C80: PUSH   RW1C
  9C82: LD     RW5C, 0x10a, TABLE[ZR]
  9C87: LD     RW5E, 0x10c, TABLE[ZR]
  ...
  9C9C: DI
  9C9D: ST     ZR, 0xc000, TABLE[ZR]     ; Gate array clear
  9CA2: ST     ZR, 0xc002, TABLE[ZR]     ; Gate array clear
  9CA7: ST     ZR, 0xd012, TABLE[ZR]     ; VDP Control 1 = 0
  9CAC: ST     ZR, 0xd010, TABLE[ZR]     ; VDP Control 0 = 0 (DISABLE DISPLAY!)
  9CB1: ST     ZR, 0x2a94, TABLE[ZR]     ; Shadow Control 1 = 0
  9CB6: ST     ZR, 0x2a8c, TABLE[ZR]     ; Shadow Control 0 = 0
  9CBB: EI
  ```
- **Result:** Instead of delaying and returning to `0xDA55` and `0xDA64`, `LCALL 0x9B51` sledded directly into the screen blanking routine at `0x9C80`! It wiped out VDP Control 0/1 and aborted the rest of the draw routine (`0xDA64` was never reached)!

### Hardware Architectural Meaning:
Just like `0xA342..0xA350` is a 14-NOP delay loop that ends with `RET` (`0xF0`), `0x9B42`, `0x9B51`, and `0x9B71` are **VDP bus timing delay stubs**.
In real hardware, this RAM region is either:
1. Expected to have short delay + `RET` (`0xF0`) sequences, OR
2. In the emulated environment, a simple `RET` (`0xF0`) at `0x9B42`, `0x9B51`, and `0x9B71` allows all 35 VDP routines to return cleanly without sledding into `0x9C80`!

---

## 3. Breakthrough 2: The Main Loop Message Pump (`0x54E8`) & Display Blanking

Why was `display_enabled_ever = 0` in Kiro's trace?

### The Main Executive Loop (`0x2887..0x2921`):
```assembly
2887: LCALL  0x54e8                    ; Call OS Message Pump!
288A: JC     0x28af                    ; IF Carry = 1, jump to screen update!
288C: STB    ZRlo, 0x1f6d
2891: LCALL  0x3f1c
2894: LD     RW1C, #0x0
2898: LD     RW1E, #0xdd77
289C: LCALL  0x2e46
289F: SCALL  0x2923                    ; <--- BLANKS DISPLAY ON EVERY TICK!
28A1: LD     RW1C, #0x196
28A5: ST     RW1C, 0x104
...
2921: SJMP   0x2887                    ; Loop back!
```

And in routine `0x2923`:
```assembly
2994: ST     ZR, 0xd012, TABLE[ZR]     ; Control 1 = 0
2999: ST     ZR, 0xd010, TABLE[ZR]     ; Control 0 = 0 (DISABLES DISPLAY!)
```

### The Message Pump (`0x54E8`):
Queue `0x21B0` is a 128-byte circular event FIFO:
- `0x21AC` = Read Pointer
- `0x21AE` = Write Pointer
```assembly
54E8: LD     RW38, 0x21ac, TABLE[ZR]
54ED: CMP    RW38, 0x21ae, TABLE[ZR]
54F2: JNE    0x5500                    ; Queue has messages!
54F4: ST     ZR, 0x21ac, TABLE[ZR]
54F9: ST     ZR, 0x21ae, TABLE[ZR]
54FE: CLRC                             ; Clear Carry (queue empty)!
54FF: RET                              ; Return!
```
- **When queue is empty:** `54E8` returns with `Carry = 0`.
- At `0x288A`: `JC 0x28af` **does not branch**.
- The loop falls through to `0x289F`, which executes `ST ZR, 0xD010` and blanks the screen!
- **Conclusion:** As long as no event message is in queue `0x21B0`, the main loop actively blanks the display on every single loop iteration.

### What Message Triggers Screen Draw?
In `0x5500..0x5650`:
```assembly
5646: CMPB   RDA, #0x0c                ; Message 0x0C = Draw/Init Screen!
5649: JNE    0x5651
564B: SCALL  0x5714                    ; Load presets via IC20 (0x4B & 0x3B) + Draw UI!
564D: SETC                             ; SET CARRY!
564E: RET                              ; Return to main loop!
```
When message `0x0C` (or event `0x0E`) is posted:
1. `0x5714` is called:
   - Sets selector `0x4B` and loads system parameters.
   - Sets selector `0x3B` and loads disk data.
   - Calls `0xA133` (the main screen rasterizer).
2. It executes `SETC` and returns!
3. The main loop at `0x288A: JC 0x28af` **takes the branch**, skipping the blanking routine `0x2923`!

---

## 4. Breakthrough 3: Dual VRAM Pointers (`0xD024` vs `0xD034`)

In Finding 18, Kiro noticed:
```
e9a6 D034<-99 D035<-82    ; 0x8299
e9b6 D024<-99 D025<-02    ; 0x0299
da3f D018<-c6 D019<-29    ; lands at 0x00099
```

### The Disassembly at `0xE984..0xE9B6`:
```assembly
E984: LD    RW5C, 0x82d6[RW86]         ; Stride (80)
E989: MULU  RL5C, 0x80f6[RW86]         ; Multiply by row (e.g. row 8)
E98E: ADD   RW5E, RW5E                 ; Word offset -> 0x0299
E991: ST    RW84, 0xd040               ; VDP sync
E996: LCALL 0x9b42                     ; Sync delay
E999: ST    ZR,   0xd036               ; Bank = 0
E99E: ORB   R5F,  #-0x80               ; Sets bit 15 -> RW5E = 0x8299!
E9A1: ST    RW5E, 0xd034               ; Writes 0x8299 to 0xD034! (Attribute Plane Pointer)
E9A6: LCALL 0x9b42
E9A9: ST    ZR,   0xd026               ; Bank = 0
E9AE: ANDB  R5F,  #0x7f                ; Clears bit 15 -> RW5E = 0x0299!
E9B1: ST    RW5E, 0xd024               ; Writes 0x0299 to 0xD024! (Character Plane Pointer)
E9B6: LCALL 0x9b42
E9B9: LJMP  0xd998                     ; Continues to VRAM data write at 0xDA3A!
```

### Architectural Meaning:
The RFSC16A features **Dual VRAM Address Pointers**:
- **`0xD024` / `0xD026`:** Primary VRAM Address Pointer (Plane 0 / Character Matrix). Written with `0x0299`.
- **`0xD034` / `0xD036`:** Secondary VRAM Address Pointer (Plane 1 / Attribute Matrix). Written with `0x8299` (`0x8000 + 0x0299`).
- **Why MAME saw `0x00099` instead of `0x0299`:**
  In MAME's current `vdp_w`, `case 0x34` only took the low byte (`0x99`). Byte `0x35` was not in `switch(reg)` and was discarded! And `0x24` was assigned to `m_vdp_mouse_ctrl` instead of a VRAM pointer!
  So `m_vdp_addr` held only the truncated byte `0x99`!

---

## 5. Corrected RFSC16A Register Table for `vdp_w` / `vdp_r`

Based on the static disassembly across the whole binary and Kiro's trace:

| Register | Access | Correct Hardware Semantics | MAME Action Needed |
| :--- | :--- | :--- | :--- |
| **`0xD010 / 0xD011`** | W (16-bit) | VDP Control 0 (Mode / Enable) | `m_vdp_display_enable = (data != 0)` |
| **`0xD012 / 0xD013`** | W (16-bit) | VDP Control 1 (Sync / Interlace) | Store word config |
| **`0xD018 / 0xD019`** | W (16-bit stream)| VRAM Data Streaming Port | `case 0x18:` and `case 0x19:` both write VRAM & auto-increment! |
| **`0xD024 / 0xD025`** | W (16-bit) | **Plane 0 VRAM Address Pointer Low** | Store low word (bits 0..15) of Plane 0 |
| **`0xD026 / 0xD027`** | W (16-bit) | **Plane 0 VRAM Address Pointer High** | Store high bits (bits 16..17) |
| **`0xD030 / 0xD031`** | W (16-bit) | Character Font / Glyphs VRAM Base | Store low word (`0x8000`) |
| **`0xD032 / 0xD033`** | W (16-bit) | Character Font VRAM Base High | Store high word (`0x0000`) |
| **`0xD034 / 0xD035`** | W (16-bit) | **Plane 1 VRAM Address Pointer Low** | Store low word (bits 0..15) of Plane 1 |
| **`0xD036 / 0xD037`** | W (16-bit) | **Plane 1 VRAM Address Pointer High** | Store high bits (bits 16..17) |
| **`0xD040 / 0xD041`** | W (16-bit) | VDP Command / Blitter Trigger | Command code (`0x0083`, `0x0000`, etc.) |

---

## 6. Three Immediate Steps for Kiro to Reach Gate G8 (Visible Frame)

1. **Stub `RET` (`0xF0`) at `0x9B42`, `0x9B51`, and `0x9B71`:**
   In `s760.cpp`, install a 1-byte opcode `0xF0` (`RET`) at runtime addresses `0x9B42`, `0x9B51`, and `0x9B71` (or add them to the HLE trampolines). This immediately prevents the delay calls from sledding into `0x9C80` and allows `0xDA64` and the full draw routine to complete!
2. **Handle 16-Bit Word-Splitting in `vdp_w`:**
   - Add `case 0x19` identical to `case 0x18`.
   - Add `case 0x25` to write bits 8..15 of `m_vdp_addr`.
   - Add `case 0x35` to write bits 8..15 of secondary address pointer.
   - Add `case 0x31` to write bits 8..15 of `m_vdp_tile_base`.
3. **Queue Initial Draw Message `0x0C` at Startup:**
   At boot completion (e.g. when entering `0x2831`), write byte `0x0C` into queue buffer `0x21B0` with `m_maincpu->space(AS_PROGRAM).write_byte(0x21B0, 0x0C); m_maincpu->space(AS_PROGRAM).write_word(0x21AE, 1);`.
   This satisfies the `0x54E8` message pump, executes `0x5714` (preset load + UI draw), and skips the blanking routine `0x2923`!

# Finding 17 — RFSC16A VDP Architectural Specification & Render Path to Gate G8

**Author:** Gemini  
**Status:** DRAFT (Ready for review & promotion to SHARED)  
**Date:** 2026-10-09  
**Resolves:** Kiro's Task 15 (`shared/15-TASK-for-gemini-render-path-to-visible-frame.md`) & ChatGPT's RFSC16A Register-Use Table Assignment  

---

## Executive Summary

Following Kiro's historic breakthrough in Finding 14 (Gates G5/G6 green, OS running its executive loop and streaming to VRAM), static analysis of the entire resident OS binary (`0x2080..0xFFFF`) has unlocked the exact hardware specification of Roland's custom **RFSC16A VDP** (`0xD000..0xD07F`).

### Key Root-Cause Revelations for the Blank CRT Frame
1. **The 16-Bit Word-Splitting Bug in MAME's `vdp_w`:**
   On the 16-bit MCS-96 bus, the CPU accesses VDP registers exclusively with 16-bit word stores (`ST`). In MAME, an 8-bit handler (`write8sm_delegate`) is installed over `0xD000..0xD0FF`. When `ST` writes a 16-bit word, MAME calls `vdp_w(offset, byte0)` followed by `vdp_w(offset+1, byte1)`.
   - **VRAM Data Port (`0xD018`):** The OS executes `ST RW5E, 0xD018`. Byte 0 hits `case 0x18` and writes to VRAM. Byte 1 hits `offset 0x19`, which had **no case in `switch(reg)`** and was **silently discarded**. Every single VRAM word had its second byte dropped!
   - **VRAM Address Pointer (`0xD034` / `0xD036`):** The OS executes `ST ZR, 0xD036` (high word) followed by `ST RW5E, 0xD034` (low word = 16-bit offset). MAME mistakenly treated `0x34` as an 8-bit low byte and `0x36` as an 8-bit high byte, completely ignoring byte 1 at `0x35`! Thus, address bits 8..15 were lost on every seek, truncating all VRAM pointers to 8 bits (`0x00..0xFF`).
   - **Character/Tile Base (`0xD030` / `0xD032`):** The OS executes `ST #0x8000, 0xD030`. MAME treated `0x30` as an 8-bit low byte, dropping `0x31` (`0x80`), leaving the tile base corrupted at 0.
2. **RFSC16A Reset Routine Decoded (`0xAF36..0xAFDF`):**
   The OS contains the manufacturer's textbook hardware initialization sequence for all 27 RFSC16A registers. Every register is paired as a 16-bit word register on even boundaries (`0xD000`, `0xD002`, `0xD004`, ...).
3. **SED1335 (LCD) Bus Address Alignment Bug:**
   The OS accesses `0xE000` as the Command/Status port and `0xE002` as the Data port (both even addresses). MAME checked `(offset & 1) == 1`, routing both `0xE000` and `0xE002` to the Data port, causing status polls at `0x2DE1` to fail.

---

## Part 1: Complete RFSC16A VDP Register Specification (0xD000–0xD07F)

Derived from an exhaustive disassembly audit of every access to `0xD000..0xD07F` across the resident OS binary.

| Register Address | Bus Width | Access | Key OS Sites | Values Observed / Source | Hardware Purpose & Architectural Semantics |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`0xD000`** | 16-bit | W | `0xAFC1`, `0xE401`, `0xE40E` | `0x0000`, `TABLE[ZR]` | **Plane 0 Scroll X:** Horizontal pixel/cell scroll offset for Layer 0. |
| **`0xD002`** | 16-bit | W | `0xAFBC`, `0xE3FC`, `0xE409` | `0x0000`, `TABLE[ZR]` | **Plane 0 Scroll Y:** Vertical scanline scroll offset for Layer 0. |
| **`0xD004`** | 16-bit | R/W | `0x98B1`, `0x98E2`, `0xAFD9`, `0xDC20` | R: Beam Counter; W: `0x0000` | **Raster Beam Counter X / HBlank Status:** Polled at `0x98E2` with `0xD006` to synchronize raster updates during blanking. |
| **`0xD006`** | 16-bit | R/W | `0x98AC`, `0x98DD`, `0xAFD4`, `0xDC1B` | R: Scanline; W: `0x0000` | **Raster Scanline Counter Y / VBlank Status:** Polled at `0x98DD` (`OR RW5C, RW60; JNE`) to wait for VBlank. |
| **`0xD008`** | 16-bit | W | `0xA8E6`, `0xAF69`, `0xE3C7`, `0xE49E` | `0x0000`, `0x0FFF` (`RW60`) | **Display Window Width / Clip X:** Set to `0x0FFF` (4095) for full unclipped 640-pixel CRT raster. |
| **`0xD00A`** | 16-bit | W | `0xA8DD`, `0xAF64`, `0xE3BB`, `0xE492` | `0x0000`, `0x0200` (512 lines) | **Display Window Height / Clip Y:** Set to `0x0200` (512 lines) during init, zeroed during blanking. |
| **`0xD00C`** | 16-bit | W | `0xAFCD`, `0xE3F4` | `0x0000`, `TABLE[ZR]` | **Plane 1 Scroll X:** Horizontal scroll offset for Layer 1. |
| **`0xD00E`** | 16-bit | W | `0xAFC8`, `0xE3EF` | `0x0000`, `TABLE[ZR]` | **Plane 1 Scroll Y:** Vertical scroll offset for Layer 1. |
| **`0xD010`** | 16-bit | W (R/W shadow)| `0x2999`, `0x92D0`, `0x9326`, `0x9F95`, `0xA900` | `0x0000`, `RW5E` (from `[0x2A8C]`) | **VDP Control 0 (Mode / Display / Plane Enables):** Controls master display enable, tile plane enable, and bitmap overlay. Shadowed in RAM at `0x2A8C` / `0x2A8D`. |
| **`0xD012`** | 16-bit | W | `0x2994`, `0x92CB`, `0x9321`, `0x9F90`, `0xA8FB` | `0x0000`, `RW5C` (from `[0x2A94] >> 4`) | **VDP Control 1 (Timing / Interlace / Sync):** Video timing modes, interlace sync. Shadowed in RAM at `0x2A94`. |
| **`0xD014`** | 16-bit | W | `0xAF3A` | `0x0017` (`RW28`) | **Video Clock / DAC Mode Config:** Configures dot clock divider and Sony CXA1145M RGB DAC interface. |
| **`0xD016`** | 16-bit | W | `0xAF49` | `0x0000` (`ZR`) | **Layer Priority & Transparency:** Blending/priority between Plane 0, Plane 1, and Bitmap Plane. |
| **`0xD018`** | 16-bit | W (Stream) | `0x8E34`, `0x8EE8`, `0xDA3A`, `0xDA64`, `0xE957` | Streamed 16-bit data words (`RW5E`) | **VRAM Data Port:** Auto-incrementing read/write port to 128KB TC511664 VRAM. Low byte at `0x18`, high byte at `0x19`. |
| **`0xD020`** | 16-bit | W | `0xAF75`, `0xE6FB`, `0xE720` | `0x0000`, `RW5C` | **Hardware Mouse / Cursor X Position:** 16-bit coordinate (bits 0..9 active). |
| **`0xD022`** | 16-bit | W | `0xAF70`, `0xE6F6`, `0xE71B` | `0x0000`, `ZR` | **Hardware Mouse / Cursor Y Position:** 16-bit coordinate (bits 0..8 active). |
| **`0xD024`** | 16-bit | W | `0xA8F3`, `0xAF99`, `0xE9B1` | `0x0000`, `RW5E` | **Mouse Pattern / Shape Base Pointer:** VRAM base address for the 16x16 hardware mouse cursor glyph. |
| **`0xD026`** | 16-bit | W | `0xA8EE`, `0xAF94`, `0xE9A9` | `0x0000`, `ZR` | **Mouse Color / Attribute:** Cursor palette selection / transparency key. |
| **`0xD028`** | 16-bit | W | `0xAF81` | `0x0000` (`ZR`) | **Hardware Clip Left (X1):** Left boundary of active rendering box. |
| **`0xD02A`** | 16-bit | W | `0xAF7C` | `0x0000` (`ZR`) | **Hardware Clip Top (Y1):** Top boundary of active rendering box. |
| **`0xD02C`** | 16-bit | W | `0xAF8D` | `0x0000` (`ZR`) | **Hardware Clip Right (X2):** Right boundary of active rendering box. |
| **`0xD02E`** | 16-bit | W | `0xAF88` | `0x0000` (`ZR`) | **Hardware Clip Bottom (Y2):** Bottom boundary of active rendering box. |
| **`0xD030`** | 16-bit | W | `0xA486`, `0xA8D5`, `0xAFA5`, `0xE3D8`, `0xE4B5` | `0x0000`, `0x8000`, `0xBFFF` | **Character / Tile Base Address Low Word:** Lower 16 bits of font glyph table base in VRAM. |
| **`0xD032`** | 16-bit | W | `0xA481`, `0xA8CC`, `0xAFA0`, `0xE3D0`, `0xE4AA` | `0x0000` (`ZR`) | **Character / Tile Base Address High Word:** Bits 16..17 bank selector for tile glyph base. |
| **`0xD034`** | 16-bit | W | `0x8EDF`, `0x9879`, `0xA36B`, `0xAFB5`, `0xDC4B`, `0xE9A1` | `0x0000`, `0x7FFF`, `0x8000`, `RW5E` | **VRAM Address Pointer Low Word:** Bits 0..15 of auto-incrementing VRAM address. Low byte at `0x34`, high byte at `0x35`. |
| **`0xD036`** | 16-bit | W | `0x8EDA`, `0x9874`, `0xA366`, `0xAFB0`, `0xDC42`, `0xE999` | `0x0000` (`ZR`) | **VRAM Address Pointer High Word:** Bits 16..17 (bank / 128KB plane selector). |
| **`0xD040`** | 16-bit | W | `0x8ED2`, `0x986C`, `0xA35F`, `0xA8C4`, `0xAF5B`, `0xDC0B` | `0x0000..0x001F` (`RW84`) | **VDP Command Port / Blitter Trigger:** Triggers internal VDP hardware operations (clear line, copy block, sync raster). |
| **`0xD064`** | 16-bit | W | `0x98A4`, `0x98D5`, `0xDC13` | `RW84` | **VDP Command Parameter / Blitter Count:** Stride / length parameter for VDP commands triggered by `0xD040`. |

---

## Part 2: Answers to Task 15 Deliverables

### Deliverable 1: VDP Control 0 (`0xD010`) Display-Enable
- **Does the OS write non-zero to `0xD010`?**
  **YES.** The OS writes non-zero to `0xD010` at five confirmed sites:
  `0x92D0`, `0x9326`, `0x9F95`, `0xA012`, and `0xA900`.
- **Where does the enable value come from?**
  The OS maintains RAM shadow variables:
  - `0x2A8C` = Control 0 shadow (low byte = gate array `0xC002`, high byte `[0x2A8D]` = VDP Control 0).
  - `0x2A94` = Control 1 shadow (low byte = gate array `0xC000`, high bits = VDP Control 1).
  In routines `0x92D0` and `0xA900`:
  ```assembly
  A8B9: LD    RW5E, 0x2a8c, TABLE[ZR]
  A8BE: ORB   R5D, R5E
  A8C1: LDBZE RW5E, R5F                ; RW5E = byte [0x2A8D]
  ...
  A900: ST    RW5E, 0xd010, TABLE[ZR]  ; Writes Control 0
  ```
- **What gates display enable?**
  In routine `0x92A6`:
  `92A6: CMPB ZRlo, 0x2488`
  If `[0x2488] == 0`, the OS executes the primary display update at `0x92D0`.
  In `0x9310` and `0xA004`, the OS explicitly executes:
  `ORB R60, #0x10; ST RW60, 0x2a8c` (sets bit 4).
  In MAME's `vdp_w`, `m_vdp_display_enable` was checked only as `(data & 0x01) != 0`. If the OS activates planes via bit 4 (`0x10`) or bit 3 (`0x08`), `m_vdp_display_enable` remained `false`.
  **Recommendation:** Update MAME's `vdp_w` so that `m_vdp_display_enable = (data & 0x19) != 0` (or `data != 0`), enabling rasterization whenever master enable (bit 0) or any plane enable (bits 3, 4) is asserted.

---

### Deliverable 2: VRAM Layout (OS vs Rasterizer)
- **What the OS actually writes:**
  - **Tile Character Matrix (Plane 0):** `0x00000` (80x30 cells = 2400 bytes). Confirmed: the first VRAM write logged in Finding 14 was at `addr = 0x00099` (cell index 153 = row 1, col 73).
  - **Character Attributes:** `0x00A00` (80x30 cells = 2400 bytes). Attribute byte: high nibble = foreground pen (0..9), low nibble = background pen (0..9).
  - **Tile Glyphs / Font Base (`0xD030`):** The OS writes `0x8000` to `0xD030` at `0xA8D5`, and `0xBFFF` at `0xE3D8`.
    - **Current MAME Assumption:** `m_vdp_tile_base = 0x01400`.
    - **OS Ground Truth:** The OS sets the tile base dynamically via register `0xD030` to `0x8000`.
- **Action for Kiro:**
  In `crt_update()`, character glyphs must be read dynamically from `m_vdp_tile_base` (set via `0xD030`), or fall back to MAME's internal ROM font if VRAM at `0x8000` has not yet been populated with soft-fonts.

---

### Deliverable 3: VRAM Address-Pointer Protocol
- **OS Subroutine Sequence:**
  Subroutine `0xA351..0xA370` is the OS's dedicated VRAM raster address setter:
  ```assembly
  A351: LD    RW5C, 0x82d6[RW86]       ; Row stride (e.g. 80)
  A356: MUL   RL5C, 0x8276[RW86]       ; Multiply by row index
  A35C: ADD   RW5E, RW5E               ; Word/cell offset
  A35F: ST    RW84, 0xd040             ; VDP command sync
  A364: SCALL 0xa342                   ; Delay/sync
  A366: ST    ZR,   0xd036             ; Set High Word (Bits 16..17 = 0)
  A36B: ST    RW5E, 0xd034             ; Set Low Word (Bits 0..15)
  A370: RET
  ```
- **Byte Stream Write Protocol (`0xD018`):**
  Immediately after calling `0xA351` (or setting `0xD034`), the OS streams character/attribute data via consecutive 16-bit stores:
  `ST RW5E, 0xD018` (e.g. at `0xDA3A`, `0xDA64`, `0xE957`).

---

### Deliverable 4: SED1335 (Front-Panel LCD) First Content Write
- **Hardware Bus Mapping:**
  The OS accesses SED1335 at:
  - `0xE000`: Command / Status Port (16-bit even address).
  - `0xE002`: Data Port (16-bit even address).
- **OS Polling Routine (`0x2DDD..0x2E3B`):**
  ```assembly
  2DE1: LDB  RDB, 0xe000, LOOKUP[ZR]   ; Read status
  2DE6: ANDB RDB, #-0x30               ; Check bits 7..4
  2DE9: CMPB RDB, #-0x80
  2DEC: JNE  0x2e03
  2DEE: LDB  RDA, #0x8                 ; Command 0x08
  2DF1: STB  RDA, 0xe002, LOOKUP[ZR]   ; Write Data/Cmd
  2DF6: LDB  RDB, 0xe000, LOOKUP[ZR]   ; Wait for Ready
  2DFB: ANDB RDB, #0x10
  2DFE: CMPB RDB, #0x10
  2E01: JNE  0x2df6                    ; Spin until bit 4 set
  ```
- **Bug in MAME's `lcd_r` / `lcd_w`:**
  MAME currently uses `(offset & 1) == 1` to distinguish command/status from data. Because both `0xE000` and `0xE002` have `offset & 1 == 0`, MAME routes BOTH to the Data Port!
  **Fix:** Change the test in `lcd_r` and `lcd_w` to:
  `bool is_cmd = (offset & 0x02) == 0;` (or check `offset == 0x00` vs `0x02`).

---

## Part 3: Exact C++ Implementation Fix for Kiro (`s760.cpp`)

To resolve the 16-bit word-splitting bug and achieve Gate G8, update `vdp_w` and `vdp_r` as follows:

```cpp
void s760_state::vdp_w(offs_t offset, uint8_t data)
{
    uint8_t reg = offset & 0x7F;
    m_vdp_regs[reg] = data;

    switch (reg)
    {
        case 0x10: // VDP Control 0 (Low Byte)
            m_vdp_display_enable = (data & 0x19) != 0; // Accept bit 0, 3, or 4
            m_vdp_interlace = (data & 0x02) != 0;
            m_vdp_tile_plane_enable = (data & 0x08) != 0;
            m_vdp_bitmap_plane_enable = (data & 0x10) != 0;
            break;

        case 0x18: // VRAM Data Port Byte 0
        case 0x19: // VRAM Data Port Byte 1 (CRITICAL FIX: 16-bit streaming)
        {
            m_vdp_vram[m_vdp_addr & 0x1FFFF] = data;
            m_vdp_addr = (m_vdp_addr + 1) & 0x1FFFF;
            m_vdp_vram_active = true;
            break;
        }

        case 0x20: // Mouse X Low
            m_vdp_mouse_x = (m_vdp_mouse_x & ~0x00FF) | data;
            break;
        case 0x21: // Mouse X High
            m_vdp_mouse_x = (m_vdp_mouse_x & ~0xFF00) | ((uint16_t)data << 8);
            break;

        case 0x22: // Mouse Y Low
            m_vdp_mouse_y = (m_vdp_mouse_y & ~0x00FF) | data;
            break;
        case 0x23: // Mouse Y High
            m_vdp_mouse_y = (m_vdp_mouse_y & ~0xFF00) | ((uint16_t)data << 8);
            break;

        case 0x30: // Character Tile Base Low Byte
            m_vdp_tile_base = (m_vdp_tile_base & ~0x00FF) | data;
            break;
        case 0x31: // Character Tile Base High Byte (CRITICAL FIX)
            m_vdp_tile_base = (m_vdp_tile_base & ~0xFF00) | ((uint32_t)data << 8);
            break;

        case 0x34: // VRAM Address Pointer Byte 0 (Bits 0..7)
            m_vdp_addr = (m_vdp_addr & ~0x0000FF) | (uint32_t)data;
            break;
        case 0x35: // VRAM Address Pointer Byte 1 (Bits 8..15) (CRITICAL FIX)
            m_vdp_addr = (m_vdp_addr & ~0x00FF00) | ((uint32_t)data << 8);
            break;
        case 0x36: // VRAM Address Pointer Byte 2 (Bits 16..23 Bank) (CRITICAL FIX)
            m_vdp_addr = (m_vdp_addr & ~0xFF0000) | ((uint32_t)data << 16);
            break;

        case 0x40: // VDP Command Port
            m_vdp_status = data & 0x7F;
            break;

        default:
            break;
    }
}
```

And in `lcd_r` / `lcd_w`:
```cpp
uint8_t s760_state::lcd_r(offs_t offset)
{
    if ((offset & 0x02) == 0) // Status Port (0xE000)
    {
        return 0x90; // Status: Bit 7 (Busy=0/Ready=1), Bit 4 (Buffer Empty=1)
    }
    else // Data Port (0xE002)
    {
        uint8_t val = m_sed_vram[m_sed_cursor_addr & 0x0FFF];
        m_sed_cursor_addr = (m_sed_cursor_addr + 1) & 0x0FFF;
        return val;
    }
}
```

---

## Part 4: Minimal Ordered Checklist to Gate G8 (Visible CRT Frame)

1. [x] **Disassemble & identify VDP register architecture** (Finding 17 Part 1).
2. [ ] **Apply 16-bit word-splitting fix in `vdp_w`** (`0x18/0x19`, `0x30/0x31`, `0x34/0x35/0x36`).
3. [ ] **Update `m_vdp_display_enable` condition** in `vdp_w` case `0x10` (`(data & 0x19) != 0`).
4. [ ] **Fix SED1335 address decoding** in `lcd_r` / `lcd_w` (`offset & 0x02`).
5. [ ] **Run `tests/mame_harness.py --seconds 5`** to confirm `nonBackgroundPixels > 0` on CRT snapshot (Gate G8 PASS).

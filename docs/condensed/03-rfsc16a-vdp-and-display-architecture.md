# RFSC16A VDP & Display Subsystem Architecture

This document synthesizes the hardware specification of the Roland **RFSC16A Video Display Processor (VDP)**, the 128 KB VRAM layout, and the SED1335 LCD interface.

---

## 1. RFSC16A Hardware Register Specification (`0xD000..0xD07F`)

The RFSC16A resides on the OP-760 expansion board and connects to the 16-bit CPU bus. All registers are 16-bit word aligned on even addresses:

| Register Address | Access | Hardware Function & Semantics | Observed Values / Source |
| :--- | :--- | :--- | :--- |
| **`0xD000`** | W (16-bit) | **Plane 0 Scroll X:** Horizontal pixel/cell scroll offset for Layer 0. | `0x0000` |
| **`0xD002`** | W (16-bit) | **Plane 0 Scroll Y:** Vertical scanline scroll offset for Layer 0. | `0x0000` |
| **`0xD004`** | R/W (16-bit) | **Beam Counter X / HBlank:** Polled with `0xD006` to synchronize raster updates. | R: Beam Counter; W: `0x0000` |
| **`0xD006`** | R/W (16-bit) | **Scanline Counter Y / VBlank:** Polled at `0x98DD` (`OR RW5C, RW60; JNE`) to wait for VBlank. | R: Scanline; W: `0x0000` |
| **`0xD008`** | W (16-bit) | **Display Window Width / Clip Right:** Screen clipping boundary. | `0x0FFF` (full unclipped 640px CRT) |
| **`0xD00A`** | W (16-bit) | **Display Window Height / Clip Bottom:** Screen clipping boundary. | `0x0200` (512 scanlines) |
| **`0xD00C`** | W (16-bit) | **Plane 1 Scroll X:** Horizontal scroll offset for Layer 1. | `0x0000` |
| **`0xD00E`** | W (16-bit) | **Plane 1 Scroll Y:** Vertical scroll offset for Layer 1. | `0x0000` |
| **`0xD010`** | W (16-bit) | **VDP Control 0 (Mode / Enable):** Bit 0: Master Display Enable, Bit 3: Tile Plane, Bit 4: Bitmap Plane. | Shadowed in RAM at `0x2A8C` / `0x2A8D` |
| **`0xD012`** | W (16-bit) | **VDP Control 1 (Timing / Sync):** Video timing modes, interlace sync. | Shadowed in RAM at `0x2A94` |
| **`0xD014`** | W (16-bit) | **Video Clock / DAC Mode Config:** Dot clock divider and Sony CXA1145M RGB DAC interface. | `0x0017` at init (`0xAF3A`) |
| **`0xD016`** | W (16-bit) | **Layer Priority & Transparency:** Blending priority between Plane 0, Plane 1, and Bitmap. | `0x0000` at init (`0xAF49`) |
| **`0xD018`** | W (16-bit stream)| **VRAM Data Port:** Auto-incrementing read/write port to 128KB TC511664 VRAM. | Streamed words (`ST RW5E, 0xD018`) |
| **`0xD020`** | W (16-bit) | **Hardware Mouse / Cursor X Position:** Active horizontal screen position. | 16-bit word coordinate |
| **`0xD022`** | W (16-bit) | **Hardware Mouse / Cursor Y Position:** Active vertical screen position. | 16-bit word coordinate |
| **`0xD024`** | W (16-bit) | **Plane 0 VRAM Address Pointer (Low 16 Bits):** Character Matrix pointer. | e.g. `0x0299` (row 8) |
| **`0xD026`** | W (16-bit) | **Plane 0 VRAM Address Pointer (High Word):** Bank bits 16..17. | `0x0000` |
| **`0xD028`** | W (16-bit) | **Hardware Clip Left (X1):** Active bounding box. | `0x0000` |
| **`0xD02A`** | W (16-bit) | **Hardware Clip Top (Y1):** Active bounding box. | `0x0000` |
| **`0xD02C`** | W (16-bit) | **Hardware Clip Right (X2):** Active bounding box. | `0x0000` |
| **`0xD02E`** | W (16-bit) | **Hardware Clip Bottom (Y2):** Active bounding box. | `0x0000` |
| **`0xD030`** | W (16-bit) | **Character Tile Glyphs VRAM Base (Low 16 Bits):** Font glyph table pointer. | `0x8000` (at `0xA8D5`), `0xBFFF` |
| **`0xD032`** | W (16-bit) | **Character Tile Glyphs VRAM Base (High Word):** Bank bits 16..17. | `0x0000` |
| **`0xD034`** | W (16-bit) | **Plane 1 VRAM Address Pointer (Low 16 Bits):** Attribute Matrix pointer. | e.g. `0x8299` (`0x8000 + 0x0299`) |
| **`0xD036`** | W (16-bit) | **Plane 1 VRAM Address Pointer (High Word):** Bank bits 16..17. | `0x0000` |
| **`0xD040`** | W (16-bit) | **VDP Command Port / Blitter Trigger:** Triggers internal line-clear, copy, sync. | `0x0083`, `0x0000` |
| **`0xD064`** | W (16-bit) | **VDP Command Parameter / Blitter Count:** Stride and length for VDP blits. | Stride / block count |

---

## 2. 16-Bit Word-Splitting Protocol

Because the CPU bus is 16-bit, 16-bit stores (`ST`) emit two 8-bit bus cycles (low byte on even address, high byte on odd address). When an 8-bit handler is installed over `0xD000..0xD0FF`, it must handle both bytes:

1. **VRAM Data Stream (`0xD018 / 0xD019`):**
   - Both `case 0x18:` and `case 0x19:` must write data to `m_vdp_vram[m_vdp_addr]` and increment `m_vdp_addr`.
2. **Dual Address Pointers:**
   - **Plane 0 Pointer:** `case 0x24` sets bits 0..7; `case 0x25` sets bits 8..15; `case 0x26` sets bits 16..17.
   - **Plane 1 Pointer:** `case 0x34` sets bits 0..7; `case 0x35` sets bits 8..15; `case 0x36` sets bits 16..17.
3. **Character Base Pointer:**
   - `case 0x30` sets bits 0..7; `case 0x31` sets bits 8..15 (`0x8000`).

---

## 3. VRAM Memory Map (128 KB TC511664)

The OS organizes the 128 KB VRAM surface as follows:

```
0x00000 - 0x0095F: Plane 0 Character Matrix (80 cols x 30 rows = 2,400 bytes, ASCII character codes)
0x00A00 - 0x0135F: Plane 1 Character Attribute Matrix (80 cols x 30 rows = 2,400 bytes)
                   High Nibble = Foreground Pen (0..9)
                   Low Nibble  = Background Pen (0..9)
0x03400 - 0x07FFF: Direct Bitmap / Waveform Overlay Plane (Plane 4)
0x08000 - 0x0BFFF: Dynamic Character Tile Font Glyphs (programmed via 0xD030 = 0x8000)
```

---

## 4. Authentic Roland Studio Palette (Sony CXA1145M RGB DAC)

The VDP character attribute nibble indexes a 10-pen authentic color table configured at `0xD800`:

| Pen Index | RGB Color | Roland UI Purpose |
| :--- | :--- | :--- |
| **0** | `rgb_t(0, 0, 0)` | Blank CRT Background / Black Text |
| **1** | `rgb_t(255, 255, 255)` | Pure White Text & Highlighting |
| **2** | `rgb_t(0, 0, 192)` | **Roland S-760 Royal Blue** (Default Screen Background) |
| **3** | `rgb_t(0, 200, 80)` | Status Green (Top Banner & Activity Indicators) |
| **4** | `rgb_t(255, 230, 0)` | Yellow Cursor & Focus Highlight |
| **5** | `rgb_t(220, 60, 20)` | Red / Orange Parameter Tab Borders |
| **6** | `rgb_t(190, 195, 205)`| Light Gray Panel Background |
| **7** | `rgb_t(0, 0, 96)` | Dark Navy Header Bar |
| **8** | `rgb_t(0, 220, 220)` | Cyan Information Text |
| **9** | `rgb_t(24, 26, 30)` | Dark Slate Outer Frame |

Default attribute for empty text cells: `0x12` (White text on Roland Royal Blue background).

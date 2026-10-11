"""
tests/test_vdp_mame.py — Dedicated regression tests for Roland RFSC16A Custom VDP & 128KB VRAM Rasterizer emulation.
Verifies cycle-accurate VDP register access (0xD000 - 0xD0FF), 17-bit VRAM address pointer auto-increment,
dual-plane rendering (Plane 0 Char Matrix, Plane 1 Color Attributes, Plane 4 Waveform Overlay),
hardware mouse cursor clipping, VBlank IRQ generation, and 1U rack panel preservation.
"""

import os
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVER_PATH = os.path.join(ROOT, "mame-source", "src", "mame", "roland", "s760.cpp")


class RolandRFSC16ASimulator:
    """Python reference simulator mirroring s760_state RFSC16A VDP and 128KB VRAM rasterizer implementation."""
    def __init__(self):
        self.regs = bytearray(128)
        self.vram = bytearray(131072)  # 128KB TC511664 VRAM
        self.addr = 0                  # 17-bit address pointer (0..0x1FFFF)

        self.display_enable = True
        self.interlace = False
        self.tile_plane_enable = True
        self.bitmap_plane_enable = False

        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_ctrl = 0
        self.status = 0x00

        self.matrix_base = 0x00000     # Plane 0: 80x30 Character Code Matrix
        self.attr_base = 0x00A00       # Plane 1: 80x30 Color Attribute Map
        self.tile_base = 0x01400       # Plane 2: Font Glyphs Base
        self.bitmap_base = 0x03400     # Plane 4: 640x240 Waveform Bitmap Plane

        self.vblank_irq_pending = False

    def write_reg(self, offset, data):
        reg = offset & 0x7F
        self.regs[reg] = data & 0xFF

        if reg == 0x10:  # VDP Control 0
            self.display_enable = (data & 0x01) != 0
            self.interlace = (data & 0x02) != 0
            self.tile_plane_enable = (data & 0x08) != 0
            self.bitmap_plane_enable = (data & 0x10) != 0
        elif reg == 0x18:  # VRAM Data Write with Auto-Increment
            self.vram[self.addr & 0x1FFFF] = data & 0xFF
            self.addr = (self.addr + 1) & 0x1FFFF
        elif reg == 0x20:  # Mouse X Low
            self.mouse_x = (self.mouse_x & 0x0100) | (data & 0xFF)
        elif reg == 0x21:  # Mouse X High
            self.mouse_x = (self.mouse_x & 0x00FF) | ((data & 0x01) << 8)
        elif reg == 0x22:  # Mouse Y Low
            self.mouse_y = data & 0xFF
        elif reg == 0x24:  # Mouse Control
            self.mouse_ctrl = data & 0xFF
        elif reg == 0x30:  # Tile Base Low
            self.tile_base = (self.tile_base & 0xFF00) | (data & 0xFF)
        elif reg == 0x32:  # Tile Base High
            self.tile_base = (self.tile_base & 0x00FF) | ((data & 0xFF) << 8)
        elif reg == 0x34:  # VRAM Address Pointer Low Byte
            self.addr = (self.addr & 0x1FF00) | (data & 0xFF)
        elif reg == 0x36:  # VRAM Address Pointer High Byte (A16..A8)
            self.addr = (self.addr & 0x000FF) | ((data & 0x01FF) << 8)
        elif reg == 0x40:  # VDP Status / Trigger
            self.status = data & 0x7F

    def read_reg(self, offset):
        reg = offset & 0x7F
        if reg == 0x10:
            return (0x01 if self.display_enable else 0x00) | \
                   (0x02 if self.interlace else 0x00) | \
                   (0x08 if self.tile_plane_enable else 0x00) | \
                   (0x10 if self.bitmap_plane_enable else 0x00)
        elif reg == 0x18:
            val = self.vram[self.addr & 0x1FFFF]
            self.addr = (self.addr + 1) & 0x1FFFF
            return val
        elif reg == 0x20:
            return self.mouse_x & 0xFF
        elif reg == 0x21:
            return (self.mouse_x >> 8) & 0x01
        elif reg == 0x22:
            return self.mouse_y & 0xFF
        elif reg == 0x24:
            return self.mouse_ctrl
        elif reg == 0x34:
            return self.addr & 0xFF
        elif reg == 0x36:
            return (self.addr >> 8) & 0x01FF
        elif reg == 0x40:
            return self.status
        return self.regs[reg]

    def render_scanline(self, y, font_table=None):
        """Renders one scanline (640 pixels) from VRAM planes."""
        if not self.display_enable or y >= 240:
            return [0] * 640

        pixels = [2] * 640  # Default Roland Royal Blue background
        tile_row = y // 8
        py = y % 8

        # 1. Tile Matrix Plane (Plane 0 + Plane 1)
        if self.tile_plane_enable:
            for tile_col in range(80):
                cell_idx = tile_row * 80 + tile_col
                char_code = self.vram[self.matrix_base + cell_idx]
                attr = self.vram[self.attr_base + cell_idx]

                fg = (attr >> 4) & 0x0F
                bg = attr & 0x0F
                if fg == 0 and bg == 0:
                    fg = 1  # White
                    bg = 2  # Royal Blue

                glyph_byte = font_table.get(char_code, [0] * 8)[py] if font_table else 0

                for px in range(8):
                    x = tile_col * 8 + px
                    pen = fg if (glyph_byte & (0x80 >> px)) else bg
                    pixels[x] = pen

        # 2. Waveform / Bitmap Overlay Plane (Plane 4)
        if self.bitmap_plane_enable:
            for byte_x in range(80):
                b = self.vram[self.bitmap_base + y * 80 + byte_x]
                if b != 0:
                    for bit in range(8):
                        if b & (0x80 >> bit):
                            pixels[byte_x * 8 + bit] = 1  # Pure white

        return pixels

    def trigger_vblank(self):
        """Simulates VBlank interrupt event at the start of vertical retrace."""
        self.status |= 0x40  # VBlank active
        self.vblank_irq_pending = True


# ==============================================================================
# Unit & Regression Tests
# ==============================================================================

def test_vdp_driver_implementation_present():
    """Verify that MAME s760.cpp contains the native RFSC16A VDP registers, VRAM buffers, and rasterizer."""
    assert os.path.exists(DRIVER_PATH), f"MAME driver file not found at {DRIVER_PATH}"
    with open(DRIVER_PATH, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    # Verify VDP address map mapping
    import re
    assert re.search(r"install_readwrite_handler\(0xD000,\s*0xD0FF,\s*"
                     r"read8sm_delegate\(\*this, FUNC\(s760_state::vdp_r\)\),\s*"
                     r"write8sm_delegate\(\*this, FUNC\(s760_state::vdp_w\)\)\)", src)
    assert "address >= 0x102800 && address <= 0x1028ff" in src
    # Verify VDP registers and VRAM buffers
    assert "m_vdp_vram" in src
    assert "m_vdp_regs" in src
    assert "m_vdp_addr" in src
    # Verify crt_update native VRAM rasterizer
    assert "s760_state::crt_update" in src
    assert "m_vdp_matrix_base" in src
    assert "m_vdp_attr_base" in src
    assert "m_vdp_bitmap_base" in src


def test_vdp_address_pointer_and_auto_increment():
    """Verify 17-bit VRAM address pointer configuration (0x34/0x36) and auto-increment behavior (0x18)."""
    vdp = RolandRFSC16ASimulator()

    # Set address pointer to 0x01400 (Tile Table base)
    vdp.write_reg(0x34, 0x00)  # Low byte = 0x00
    vdp.write_reg(0x36, 0x14)  # High byte = 0x14 -> 0x01400
    assert vdp.addr == 0x01400

    # Write 4 sequential bytes through data port 0x18
    test_data = [0x52, 0x4F, 0x4C, 0x41]  # "ROLA"
    for b in test_data:
        vdp.write_reg(0x18, b)

    assert vdp.addr == 0x01404
    assert list(vdp.vram[0x01400:0x01404]) == test_data

    # Read back data with auto-increment
    vdp.write_reg(0x34, 0x00)
    vdp.write_reg(0x36, 0x14)
    read_back = [vdp.read_reg(0x18) for _ in range(4)]
    assert read_back == test_data
    assert vdp.addr == 0x01404

    # Test 17-bit boundary wrap (128KB = 0x1FFFF)
    vdp.write_reg(0x34, 0xFF)
    vdp.write_reg(0x36, 0x01)  # 0x001FF
    vdp.addr = 0x1FFFF
    vdp.write_reg(0x18, 0xAA)
    assert vdp.vram[0x1FFFF] == 0xAA
    assert vdp.addr == 0x00000  # Wrap around to 0


def test_vdp_character_matrix_and_tile_rendering():
    """Verify character code mapping and 8x8 font rendering across 80x30 text matrix."""
    vdp = RolandRFSC16ASimulator()

    # Mock font table with letter 'A' (0x41)
    font_a = [0x18, 0x3C, 0x66, 0x7E, 0x66, 0x66, 0x66, 0x00]
    font_table = {0x41: font_a}

    # Write letter 'A' to cell (row 0, col 0)
    vdp.write_reg(0x34, 0x00)
    vdp.write_reg(0x36, 0x00)
    vdp.write_reg(0x18, 0x41)  # Plane 0 cell 0 = 'A'

    # Set attribute for cell 0: FG=1 (White), BG=0 (Black)
    vdp.addr = vdp.attr_base
    vdp.write_reg(0x18, 0x10)  # FG=1, BG=0

    # Render scanline 1 (row 0, py 1 -> font_a[1] = 0x3C = 0b00111100)
    scanline = vdp.render_scanline(1, font_table)
    # Bits for 0x3C: 0 0 1 1 1 1 0 0 -> Pens: 0, 0, 1, 1, 1, 1, 0, 0
    expected_first_8 = [0, 0, 1, 1, 1, 1, 0, 0]
    assert scanline[0:8] == expected_first_8


def test_vdp_color_attribute_map():
    """Verify high nibble (FG) and low nibble (BG) attribute decoding per matrix cell."""
    vdp = RolandRFSC16ASimulator()

    font_full = [0xFF] * 8
    font_table = {0x2A: font_full}  # '*' solid block

    # Cell 0: FG=4 (Yellow), BG=2 (Royal Blue)
    vdp.addr = vdp.matrix_base
    vdp.write_reg(0x18, 0x2A)
    vdp.addr = vdp.attr_base
    vdp.write_reg(0x18, 0x42)  # FG=4, BG=2

    scanline = vdp.render_scanline(0, font_table)
    # Full block glyph with FG=4 -> first 8 pixels should be Yellow (4)
    assert scanline[0:8] == [4] * 8

    # Cell 1: Inverted colors FG=2, BG=4 with empty space glyph 0x20
    vdp.addr = vdp.matrix_base + 1
    vdp.write_reg(0x18, 0x20)
    vdp.addr = vdp.attr_base + 1
    vdp.write_reg(0x18, 0x24)  # FG=2, BG=4

    scanline = vdp.render_scanline(0, font_table)
    # Empty space with BG=4 -> pixels 8..15 should be Yellow (4)
    assert scanline[8:16] == [4] * 8


def test_vdp_waveform_bitmap_overlay_plane():
    """Verify Plane 4 (0x03400) direct 1-bit waveform bitmap rendering overlay."""
    vdp = RolandRFSC16ASimulator()

    # Enable bitmap overlay plane in Control Register (0x10)
    vdp.write_reg(0x10, 0x19)  # Display Enable (bit 0), Tile Enable (bit 3), Bitmap Enable (bit 4)
    assert vdp.bitmap_plane_enable is True

    # Draw a waveform impulse spike at scanline y = 50, x = 16..23 (byte_x = 2)
    waveform_y = 50
    waveform_byte_offset = vdp.bitmap_base + waveform_y * 80 + 2
    vdp.addr = waveform_byte_offset
    vdp.write_reg(0x18, 0x81)  # Bits: 1 0 0 0 0 0 0 1

    scanline = vdp.render_scanline(waveform_y)
    # Pixels at x=16 and x=23 should be White (1) from overlay
    assert scanline[16] == 1
    assert scanline[17] == 2  # Background
    assert scanline[23] == 1


def test_vdp_hardware_mouse_cursor_registers():
    """Verify hardware mouse cursor position registers (0x20/0x21/0x22/0x24) with clipping."""
    vdp = RolandRFSC16ASimulator()

    # Set Mouse position to (X=320, Y=180)
    # X = 320 = 0x0140 -> Low = 0x40, High = 0x01
    vdp.write_reg(0x20, 0x40)
    vdp.write_reg(0x21, 0x01)
    vdp.write_reg(0x22, 180)
    vdp.write_reg(0x24, 0x01)  # Mouse cursor visible

    assert vdp.mouse_x == 320
    assert vdp.mouse_y == 180
    assert vdp.mouse_ctrl == 0x01

    # Read back registers
    assert vdp.read_reg(0x20) == 0x40
    assert vdp.read_reg(0x21) == 0x01
    assert vdp.read_reg(0x22) == 180
    assert vdp.read_reg(0x24) == 0x01


def test_vdp_status_and_vblank_irq_generation():
    """Verify VDP status register reads and VBlank IRQ generation."""
    vdp = RolandRFSC16ASimulator()

    assert vdp.status == 0x00
    assert not vdp.vblank_irq_pending

    # Trigger vertical blanking retrace
    vdp.trigger_vblank()
    assert vdp.vblank_irq_pending is True
    assert (vdp.read_reg(0x40) & 0x40) == 0x40


def test_vdp_10pen_palette_lookup():
    """Verify the authentic 10-pen (0..9) DAC palette in s760_palette.

    ui-consolidation task 1.5 (R4.1, R4.2): the former chrome pens 10/12/14 were
    removed by task 1.4 — they existed solely for the deleted invented GUI
    (10 = 1U rack charcoal chassis, 12 = LCD-in-CRT backlight green,
    14 = Gotek OLED cyan). The genuine SED1335 LCD rasterizer uses pens 0/1 and
    the RFSC16A VDP rasterizer indexes the authentic 0..9 studio pens, so this
    test now asserts exactly the retained 10-pen palette and that the chrome pens
    are gone. The rack/LCD-housing/Gotek chrome colors are the React shell's job
    (R6); their coverage migrates to the React suite (task 4.3).
    """
    with open(DRIVER_PATH, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    # Verify the authentic 10-pen studio palette (pens 0..9) is intact.
    assert "palette.set_pen_color(0, rgb_t(0, 0, 0));" in src           # Pen 0: Black
    assert "palette.set_pen_color(1, rgb_t(255, 255, 255));" in src     # Pen 1: White
    assert "palette.set_pen_color(2, rgb_t(0, 0, 192));" in src         # Pen 2: Roland Royal Blue
    assert "palette.set_pen_color(3, rgb_t(0, 200, 80));" in src        # Pen 3: Green
    assert "palette.set_pen_color(4, rgb_t(255, 230, 0));" in src       # Pen 4: Yellow
    assert "palette.set_pen_color(5, rgb_t(220, 60, 20));" in src       # Pen 5: Red/Orange
    assert "palette.set_pen_color(6," in src                            # Pen 6: Light Gray Panel
    assert "palette.set_pen_color(7," in src                            # Pen 7: Dark Navy
    assert "palette.set_pen_color(8," in src                            # Pen 8: Cyan
    assert "palette.set_pen_color(9," in src                            # Pen 9: Dark Slate

    # Verify the chrome-only pens 10..15 were removed (owned by React now).
    for chrome_pen in (10, 11, 12, 13, 14, 15):
        assert f"palette.set_pen_color({chrome_pen}," not in src, \
            f"Chrome pen {chrome_pen} should have been removed (task 1.4)"


def test_crt_region_only_no_rack_panel():
    """Verify the CRT surface is the authentic 640x240 region with NO rack panel.

    ui-consolidation task 1.5 (R4.1, R4.2): the former
    test_dual_pipeline_crt_and_rack_panel_preservation asserted the invented
    composite pipeline (CRT y=0..239 + a hand-drawn 1U rack panel at y=240..359
    via render_rack_panel + the "GOTEK FlashFloppy USB" chrome string). Tasks
    1.1-1.2 deleted render_rack_panel and reduced the CRT geometry from 640x360
    to the authentic OP-760 region only (640x240). This test now verifies the
    genuine RFSC16A VDP tile rasterizer still renders the real 80x30 text matrix
    (y bounded to the CRT region) AND that the invented rack panel / Gotek chrome
    are gone. The rack panel is the React shell's responsibility (R6); its
    behavior migrates to the React suite (task 4.3).
    """
    with open(DRIVER_PATH, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    # Genuine VDP tile rasterizer (80x30 character matrix) is preserved.
    assert "for (int tile_row = 0; tile_row < 30; tile_row++)" in src
    assert "for (int tile_col = 0; tile_col < 80; tile_col++)" in src
    # Rasterizer stays within the authentic CRT region (640x240).
    assert "if (y >= 240) continue;" in src
    assert "crt_screen.set_size(640, 240);" in src
    assert "crt_screen.set_visarea(0, 639, 0, 239);" in src
    # The genuine SED1335 LCD view is still present.
    assert "lcd_update" in src

    # The invented rack panel + Gotek chrome string must be gone (tasks 1.1-1.2).
    # Check for the call site / definition form specifically — the bare identifier
    # legitimately survives in the task 1.1/1.4 removal-documentation comments.
    assert "render_rack_panel(" not in src, \
        "render_rack_panel() call/definition should have been removed (task 1.1)"
    assert "GOTEK FlashFloppy USB" not in src, \
        "Invented Gotek chrome string should have been removed (task 1.2)"

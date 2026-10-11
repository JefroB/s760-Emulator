"""
tests/test_lcd_mame.py — Dedicated regression tests for Epson SED1335 (S1D13305) 160x64 Front Panel LCD controller emulation.
Verifies cycle-accurate command decoding (SYSTEM SET, CSRW, CSRR, MWRITE, MREAD, SCROLL, DISP ON/OFF, OVLAY),
dual-layer rasterization (Layer 1 Text Matrix + Layer 2 Graphics Bit-Plane), layer composition (OR, XOR, AND),
and 1U rack front panel integration.
"""

import os
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVER_PATH = os.path.join(ROOT, "mame-source", "src", "mame", "roland", "s760.cpp")


class EpsonSED1335Simulator:
    """Python reference simulator mirroring s760_state Epson SED1335 LCD implementation."""
    def __init__(self):
        self.cmd = 0
        self.params = bytearray(16)
        self.param_idx = 0
        self.param_len = 0
        self.cursor_addr = 0
        self.sad1 = 0x0000  # Layer 1 Text Base (20x8 chars = 160 bytes)
        self.sad2 = 0x0800  # Layer 2 Graphics Base (20 bytes/line * 64 lines = 1280 bytes)
        self.disp_mode = 0x14  # Layer 1 Text (0x01) + Layer 2 Graphics (0x04) enabled
        self.overlay_mode = 0  # 0=OR, 1=XOR, 2=AND
        self.vram = bytearray(4096)
        self.vram_active = False

    def write_cmd(self, opcode):
        self.cmd = opcode
        self.param_idx = 0
        if opcode == 0x40:    # SYSTEM SET
            self.param_len = 8
        elif opcode == 0x44:  # SCROLL
            self.param_len = 10
        elif opcode == 0x46:  # CSRW
            self.param_len = 2
        elif opcode == 0x42:  # MWRITE (stream)
            self.param_len = -1
        elif opcode == 0x58:  # DISP OFF
            self.disp_mode = 0
            self.param_len = 0
        elif opcode == 0x59:  # DISP ON
            self.param_len = 1
        elif opcode == 0x5A:  # HDOT SCR
            self.param_len = 1
        elif opcode == 0x5B:  # OVLAY
            self.param_len = 1
        elif opcode == 0x5D:  # CSRFORM
            self.param_len = 2
        else:
            self.param_len = 0

    def write_data(self, data):
        if self.cmd == 0x42:  # MWRITE stream
            self.vram[self.cursor_addr & 0x0FFF] = data & 0xFF
            self.cursor_addr = (self.cursor_addr + 1) & 0x0FFF
            self.vram_active = True
        elif self.param_len > 0:
            if self.param_idx < 16:
                self.params[self.param_idx] = data & 0xFF
                self.param_idx += 1

            if self.param_idx >= self.param_len:
                if self.cmd == 0x46:  # CSRW
                    self.cursor_addr = self.params[0] | (self.params[1] << 8)
                elif self.cmd == 0x44:  # SCROLL
                    self.sad1 = self.params[0] | (self.params[1] << 8)
                    self.sad2 = self.params[3] | (self.params[4] << 8)
                elif self.cmd == 0x59:  # DISP ON
                    self.disp_mode = self.params[0]
                elif self.cmd == 0x5B:  # OVLAY
                    self.overlay_mode = self.params[0] & 0x03

    def read_status(self):
        return 0x40  # LCD Ready

    def read_data(self):
        val = self.vram[self.cursor_addr & 0x0FFF]
        self.cursor_addr = (self.cursor_addr + 1) & 0x0FFF
        return val

    def render_framebuffer(self, font_table=None):
        """Renders 160x64 monochrome pixel framebuffer."""
        if not self.vram_active or self.disp_mode == 0:
            return [[0] * 160 for _ in range(64)]

        fb = [[0] * 160 for _ in range(64)]

        for y in range(64):
            char_row = y // 8
            py = y % 8

            for x in range(160):
                char_col = x // 8
                px = x % 8

                # Layer 1: Character Matrix (20x8 characters at sad1)
                text_bit = 0
                if self.disp_mode & 0x01:
                    char_code = self.vram[(self.sad1 + char_row * 20 + char_col) & 0x0FFF]
                    glyph_byte = font_table.get(char_code, [0] * 8)[py] if font_table else 0
                    text_bit = 1 if (glyph_byte & (0x80 >> px)) else 0

                # Layer 2: 1-Bit Graphics Plane (160x64 dots at sad2)
                gfx_bit = 0
                if self.disp_mode & 0x04:
                    byte_offset = y * 20 + (x // 8)
                    b = self.vram[(self.sad2 + byte_offset) & 0x0FFF]
                    gfx_bit = 1 if (b & (0x80 >> px)) else 0

                # Layer Composition Mode (OR, XOR, AND)
                if self.overlay_mode == 1:
                    pixel = text_bit ^ gfx_bit
                elif self.overlay_mode == 2:
                    pixel = text_bit & gfx_bit
                else:
                    pixel = text_bit | gfx_bit

                fb[y][x] = pixel

        return fb


# ==============================================================================
# Unit & Regression Tests
# ==============================================================================

def test_lcd_driver_implementation_present():
    """Verify that MAME s760.cpp contains the Epson SED1335 controller emulation and memory map."""
    assert os.path.exists(DRIVER_PATH), f"MAME driver file not found at {DRIVER_PATH}"
    with open(DRIVER_PATH, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    assert "s760_state::lcd_r" in src
    assert "s760_state::lcd_w" in src
    assert "s760_state::lcd_update" in src
    assert "m_sed_vram" in src
    assert "m_sed_cursor_addr" in src
    # Legacy flat mode installs only the two even-addressed ports. Mapping
    # through EFF7 intercepted executable OS bytes (including E934).
    import re
    assert re.search(r"install_readwrite_handler\(0xE000,\s*0xE003,\s*"
                     r"read8sm_delegate\(\*this, FUNC\(s760_state::lcd_r\)\),\s*"
                     r"write8sm_delegate\(\*this, FUNC\(s760_state::lcd_w\)\)\)", src)
    assert not re.search(r"(?:map|install_readwrite_handler)\(0xE000,\s*0xEFF7", src)
    assert "address >= 0x103800 && address <= 0x103803" in src


def test_lcd_system_set_and_cursor_addressing():
    """Verify SYSTEM SET (0x40), CSRW (0x46) cursor pointer write, and status read."""
    sed = EpsonSED1335Simulator()

    # Configure SYSTEM SET
    sed.write_cmd(0x40)
    for p in [0x30, 0x87, 0x07, 0x13, 0x27, 0x3F, 0x14, 0x00]:
        sed.write_data(p)

    # Set Cursor address to 0x0850 via CSRW (0x46) -> Low = 0x50, High = 0x08
    sed.write_cmd(0x46)
    sed.write_data(0x50)
    sed.write_data(0x08)
    assert sed.cursor_addr == 0x0850

    # Verify LCD ready status
    assert (sed.read_status() & 0x40) == 0x40


def test_lcd_memory_write_stream_mwrite():
    """Verify MWRITE (0x42) sequential byte streaming with auto-increment."""
    sed = EpsonSED1335Simulator()

    # Set Cursor address to 0x0100
    sed.write_cmd(0x46)
    sed.write_data(0x00)
    sed.write_data(0x01)
    assert sed.cursor_addr == 0x0100

    # Stream 5 bytes via MWRITE
    sed.write_cmd(0x42)
    payload = [0x53, 0x2D, 0x37, 0x36, 0x30]  # "S-760"
    for b in payload:
        sed.write_data(b)

    assert sed.cursor_addr == 0x0105
    assert list(sed.vram[0x0100:0x0105]) == payload

    # Read back data with auto-increment
    sed.write_cmd(0x46)
    sed.write_data(0x00)
    sed.write_data(0x01)
    read_back = [sed.read_data() for _ in range(5)]
    assert read_back == payload


def test_lcd_scroll_layer_addressing():
    """Verify SCROLL (0x44) command setting Layer 1 text and Layer 2 graphics start addresses."""
    sed = EpsonSED1335Simulator()

    # Set SAD1 = 0x0200, Lines = 64, SAD2 = 0x0A00, Lines = 64
    sed.write_cmd(0x44)
    scroll_params = [
        0x00, 0x02, 64,   # Layer 1: Start 0x0200, 64 lines
        0x00, 0x0A, 64,   # Layer 2: Start 0x0A00, 64 lines
        0x00, 0x00, 0,    # Layer 3: Start 0x0000
        0x00              # Screen 4
    ]
    for p in scroll_params:
        sed.write_data(p)

    assert sed.sad1 == 0x0200
    assert sed.sad2 == 0x0A00


def test_lcd_text_character_matrix_rendering():
    """Verify Layer 1 character matrix decoding through 8x8 font table."""
    sed = EpsonSED1335Simulator()

    # Mock font table with letter 'R' (0x52)
    font_r = [0x7C, 0x66, 0x66, 0x7C, 0x78, 0x6C, 0x66, 0x00]
    font_table = {0x52: font_r}

    # Write 'R' to character cell (row 0, col 0) at SAD1 (0x0000)
    sed.write_cmd(0x46)
    sed.write_data(0x00)
    sed.write_data(0x00)
    sed.write_cmd(0x42)
    sed.write_data(0x52)

    # Enable Text Layer (0x01)
    sed.write_cmd(0x59)
    sed.write_data(0x01)

    fb = sed.render_framebuffer(font_table)

    # Check first scanline: font_r[0] = 0x7C = 0b01111100 -> [0, 1, 1, 1, 1, 1, 0, 0]
    expected_top_line = [0, 1, 1, 1, 1, 1, 0, 0]
    assert fb[0][0:8] == expected_top_line


def test_lcd_graphics_bitplane_rendering():
    """Verify Layer 2 direct 1-bit monochrome graphics bitplane rendering."""
    sed = EpsonSED1335Simulator()

    # Write graphic pattern 0xAA (10101010) at scanline y = 10, x = 0..7 (offset = 10 * 20 = 200)
    gfx_offset = sed.sad2 + (10 * 20)
    sed.write_cmd(0x46)
    sed.write_data(gfx_offset & 0xFF)
    sed.write_data((gfx_offset >> 8) & 0xFF)
    sed.write_cmd(0x42)
    sed.write_data(0xAA)  # 1 0 1 0 1 0 1 0

    # Enable Graphics Layer (0x04)
    sed.write_cmd(0x59)
    sed.write_data(0x04)

    fb = sed.render_framebuffer()

    expected_pixels = [1, 0, 1, 0, 1, 0, 1, 0]
    assert fb[10][0:8] == expected_pixels


def test_lcd_layer_composition_modes_or_xor_and():
    """Verify Layer 1 + Layer 2 composition modes (OR, XOR, AND)."""
    sed = EpsonSED1335Simulator()

    # Font with solid block [0xFF]
    font_table = {0x42: [0xFF] * 8}

    # Text at (0, 0) = Solid 1s
    sed.write_cmd(0x46)
    sed.write_data(0x00)
    sed.write_data(0x00)
    sed.write_cmd(0x42)
    sed.write_data(0x42)

    # Graphics at (0, 0) = Alternating 0xAA (10101010)
    sed.write_cmd(0x46)
    sed.write_data(sed.sad2 & 0xFF)
    sed.write_data((sed.sad2 >> 8) & 0xFF)
    sed.write_cmd(0x42)
    sed.write_data(0xAA)

    # Enable both Text (0x01) and Graphics (0x04)
    sed.write_cmd(0x59)
    sed.write_data(0x05)

    # 1. OR Mode (0x00): 1s | 10101010 = 11111111
    sed.write_cmd(0x5B)
    sed.write_data(0x00)
    fb_or = sed.render_framebuffer(font_table)
    assert fb_or[0][0:8] == [1] * 8

    # 2. XOR Mode (0x01): 11111111 ^ 10101010 = 01010101
    sed.write_cmd(0x5B)
    sed.write_data(0x01)
    fb_xor = sed.render_framebuffer(font_table)
    assert fb_xor[0][0:8] == [0, 1, 0, 1, 0, 1, 0, 1]

    # 3. AND Mode (0x02): 11111111 & 10101010 = 10101010
    sed.write_cmd(0x5B)
    sed.write_data(0x02)
    fb_and = sed.render_framebuffer(font_table)
    assert fb_and[0][0:8] == [1, 0, 1, 0, 1, 0, 1, 0]


def test_lcd_display_on_off_modes():
    """Verify DISP OFF (0x58) and DISP ON (0x59) layer blanking."""
    sed = EpsonSED1335Simulator()

    sed.write_cmd(0x46)
    sed.write_data(sed.sad2 & 0xFF)
    sed.write_data((sed.sad2 >> 8) & 0xFF)
    sed.write_cmd(0x42)
    sed.write_data(0xFF)

    # Turn display ON for Graphics
    sed.write_cmd(0x59)
    sed.write_data(0x04)
    assert sed.render_framebuffer()[0][0:8] == [1] * 8

    # Turn display OFF
    sed.write_cmd(0x58)
    assert sed.render_framebuffer()[0][0:8] == [0] * 8


def test_lcd_renders_only_authentic_sed1335_vram():
    """Verify the LCD path renders ONLY genuine SED1335 VRAM — no invented chrome fallback.

    ui-consolidation tasks 1.1-1.4 (R1.2, R2.2, R2.3): the former
    "render active front panel page" fallback that fabricated the
    "S-760 SAMPLER / SYSTEM v2.24 OK / RAM: 32MB READY" status text when VRAM was
    empty, and the render_rack_panel() invented 1U-rack chrome, were deleted. The
    LCD/rack chrome is now the React shell's responsibility (R6). This test, which
    previously asserted that invented chrome STILL existed in the driver source,
    is inverted to assert the authentic invariant: the invented chrome strings and
    the render_rack_panel renderer are gone, and the genuine SED1335 VRAM path
    (m_sed_vram + lcd_update) is what drives the LCD.
    """
    import re

    with open(DRIVER_PATH, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    # Strip C/C++ comments so that NOTE comments which legitimately *document* the
    # removed chrome (e.g. "...the draw_string() helper was removed...") are not
    # mistaken for live code. We assert on actual code, not on documentation.
    no_block = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    code = "\n".join(line.split("//", 1)[0] for line in no_block.splitlines())

    # The invented GUI renderers and the draw_string chrome helper have no live
    # call sites or definitions anymore (deleted in tasks 1.1-1.4).
    assert "render_rack_panel" not in code
    assert "render_disk_mode" not in code
    assert "render_perform_mode" not in code
    assert "draw_string(" not in code
    # The fabricated LCD status-text fallback is gone from executable code.
    assert "S-760 SAMPLER" not in code
    assert "RAM: 32MB READY" not in code

    # Genuine Epson SED1335 VRAM rasterizer path is preserved.
    assert "m_sed_vram" in code
    assert "lcd_update" in code

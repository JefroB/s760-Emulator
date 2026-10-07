"""
render_lcd.py — Roland S-760 LCD Framebuffer & Screen Visualizer

Renders the Epson SED1335 160x64 monochrome LCD display buffer into ASCII/Unicode console art.
"""
import sys
import os

WIDTH = 160
HEIGHT = 64
BYTES_PER_ROW = WIDTH // 8  # 20 bytes per row

def render_framebuffer(vram_bytes, title="Roland S-760 LCD Display (160x64)"):
    print("=" * (WIDTH + 4))
    print(f"  {title}")
    print("=" * (WIDTH + 4))
    print("+" + "-" * WIDTH + "+")

    for y in range(HEIGHT):
        row_str = ""
        for b_idx in range(BYTES_PER_ROW):
            byte_val = vram_bytes[y * BYTES_PER_ROW + b_idx] if (y * BYTES_PER_ROW + b_idx) < len(vram_bytes) else 0
            for bit in range(7, -1, -1):
                pixel = (byte_val >> bit) & 1
                row_str += "█" if pixel else " "
        print("|" + row_str + "|")

    print("+" + "-" * WIDTH + "+")

def render_sample_boot_screen():
    """Generates a mock preview of the S-760 Ver. 2.24 LCD display header."""
    vram = bytearray(HEIGHT * BYTES_PER_ROW)
    
    # Simple test pattern / border line
    for x in range(BYTES_PER_ROW):
        vram[x] = 0xFF
        vram[(HEIGHT - 1) * BYTES_PER_ROW + x] = 0xFF

    render_framebuffer(vram, "S-760 System Ver. 2.24 Startup Screen")

if __name__ == "__main__":
    render_sample_boot_screen()

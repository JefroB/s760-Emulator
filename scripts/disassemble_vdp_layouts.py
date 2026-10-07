"""
disassemble_vdp_layouts.py — Parses VDP screen layout descriptors & coordinate arrays from S760224.IMG
Extracts screen bounding boxes, text positions (X, Y), field lengths, and color pen assignments.
"""

import os
import struct
import json

OS_IMG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "S760224.IMG"))
OUT_JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "VDP_LAYOUT_DESCRIPTORS.json"))

def analyze_vdp_tables():
    with open(OS_IMG_PATH, "rb") as f:
        data = f.read()

    print(f"Scanning {len(data)} bytes for VDP layout coordinate structures...")

    # Look for characteristic VDP text descriptor records:
    # Typical 80C196 structure: [uint16 string_ptr or offset, uint8 col_x, uint8 row_y, uint8 pen_color, uint8 flags]
    # Screen boundaries: col_x: 0..79 (or 0..639), row_y: 0..29 (or 0..239), pen: 0..9
    
    screen_descriptors = []

    # Search in main code & data segment (0x80000 to 0xC0000)
    for offset in range(0x80000, 0xC0000 - 8, 2):
        col, row, pen, flag = data[offset+4], data[offset+5], data[offset+6], data[offset+7]
        # Check if coordinates match S-760 text grid (80x30 text mode or pixel coords)
        if 0 <= col <= 79 and 0 <= row <= 29 and 0 <= pen <= 9 and flag in (0, 1, 2, 4, 8, 0x80):
            str_ptr = struct.unpack("<H", data[offset:offset+2])[0]
            screen_descriptors.append({
                "table_offset": f"0x{offset:06X}",
                "str_ptr": f"0x{str_ptr:04X}",
                "col": col,
                "row": row,
                "pen": pen,
                "flag": flag
            })

    print(f"Discovered {len(screen_descriptors)} candidate VDP screen field descriptors.")

    with open(OUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(screen_descriptors[:500], f, indent=2)

    print(f"Exported VDP layout descriptors to {OUT_JSON_PATH}")

if __name__ == "__main__":
    analyze_vdp_tables()

#!/usr/bin/env python3
"""
extract_resident_and_banks.py - Extract Roland S-760 OS binary slices for Ghidra.

Reads S760224.IMG (strictly read-only) and exports:
  1. s760_resident_os.bin  - The core resident OS slice (file 0x4800..0x1277F, len 0xDF80 = 57,216 bytes).
     Maps into Ghidra at base address 0x2080.
  2. Selected 16 KiB bank slices for Ghidra overlay analysis (e.g., bank_00, bank_1f, bank_2d, bank_3b, bank_4b).
"""

import sys
from pathlib import Path

PAYLOAD_OFFSET = 0x4800
RESIDENT_LEN = 0xDF80  # 57,216 bytes: from 0x2080 to 0xFFFF inclusive

# Key 16 KiB pages identified in reverse-engineering findings:
# Physical RAM address = page << 10. File offset = 0x4800 + (page << 10).
IMPORTANT_PAGES = {
    "page_00_startup_fdc": 0x00,    # Handoff, FDC & interrupt handling
    "page_0f_resident_midi": 0x0F,  # MIDI parser & dispatch
    "page_1f_pitch_voice": 0x1F,    # Pitch control & voice allocation
    "page_2d_tvf_modulation": 0x2D, # TVF/TVA filter modulation DSP
    "page_3b_scsi_eeprom": 0x3B,    # SCSI driver & EEPROM config
    "page_4b_mouse_ui": 0x4B,       # Mouse handshake & UI services
    "page_68_device_probe": 0x68,   # SCSI device probe
    "page_87_ui_strings": 0x82,     # UI strings & screen descriptors (~0x87000)
}

def extract(img_path: Path, out_dir: Path):
    if not img_path.exists():
        print(f"Error: image file '{img_path}' not found.", file=sys.stderr)
        sys.exit(1)

    data = img_path.read_bytes()
    if len(data) != 1474560:
        print(f"Warning: image size is {len(data)}, expected 1,474,560 bytes.", file=sys.stderr)

    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Resident OS binary
    resident_bytes = data[PAYLOAD_OFFSET : PAYLOAD_OFFSET + RESIDENT_LEN]
    resident_file = out_dir / "s760_resident_os.bin"
    resident_file.write_bytes(resident_bytes)
    print(f"[+] Extracted resident OS: {resident_file} ({len(resident_bytes)} bytes)")
    print(f"    Ghidra load address: 0x2080 (maps 0x2080..0xFFFF)")

    # 2. Key 16 KiB bank slices for overlay analysis
    banks_dir = out_dir / "banks"
    banks_dir.mkdir(exist_ok=True)

    for name, page in IMPORTANT_PAGES.items():
        bank_off = PAYLOAD_OFFSET + (page << 10)
        bank_bytes = data[bank_off : bank_off + 0x4000] # 16 KiB
        bank_file = banks_dir / f"{name}_p{page:02x}.bin"
        bank_file.write_bytes(bank_bytes)
        print(f"[+] Extracted 16K bank: {bank_file.name} (file 0x{bank_off:06X})")

    print("\nExtraction complete! Use these binaries with Ghidra.")

if __name__ == "__main__":
    img = Path("S760224.IMG")
    out = Path("temp/ghidra_export")
    if len(sys.argv) > 1:
        img = Path(sys.argv[1])
    if len(sys.argv) > 2:
        out = Path(sys.argv[2])
    extract(img, out)

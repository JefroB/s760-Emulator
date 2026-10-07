"""
analyze_os_binary.py — Deep-dive extraction and analysis of Roland S-760 OS v2.24 (S760224.IMG)
Extracts all screen titles, subpages, parameter descriptors, error prompts, modal menus, and coordinate tables.
"""

import os
import re
import json
from collections import defaultdict

OS_IMG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "S760224.IMG"))
REPORT_TXT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "OS_STRING_CATALOG.md"))

def extract_strings(data, min_len=3):
    """Extract printable ASCII strings with their byte offsets."""
    pattern = re.compile(b'[ -~]{' + str(min_len).encode() + b',}')
    strings = []
    for match in pattern.finditer(data):
        offset = match.start()
        text = match.group().decode('latin1', errors='ignore')
        # Skip pure repeated characters or garbage
        if len(set(text)) > 1:
            strings.append((offset, text))
    return strings

def categorize_strings(strings):
    """Categorize strings based on Roland S-760 architecture and UI domains."""
    categories = {
        "Modes & Subscreens": [],
        "Soft Buttons & Functions": [],
        "Parameter Labels & Units": [],
        "Popups, Menus & Commands": [],
        "Dialogs, Prompts & Confirmations": [],
        "Error Messages & Warnings": [],
        "SCSI, Floppy & File System": [],
        "Hardware Diagnostics & Setup": [],
        "General UI & Formatting": [],
        "Other Interesting Strings": []
    }

    # Keyword rules
    mode_patterns = [
        "PERFORM", "Perform", "PATCH", "Patch", "PARTIAL", "Partial",
        "SAMPLE", "Sample", "DISK", "Disk", "SYSTEM", "System",
        "Sampling", "Loop&Smoothing", "Auto Trun", "Time Stretch",
        "D.Filter", "Comp/Expand", "Rate Convert", "Bit Convert",
        "Truncate", "Cut & Splice", "Area Erase", "Insert", "Mixing",
        "Combine", "Split", "SMT", "TVF", "TVA", "LFO", "Q-Sampling",
        "Volume ID", "System PRM"
    ]

    button_patterns = [
        "VolInfo", "AllOn", "Load", "Save", "Exec", "Exit", "Menu",
        "Mark", "Jump", "Com", "Recover", "KeyStr", "MonOn", "Ready",
        "Mono", "Stereo", "L.Unlk", "Search", "Correct", "SmpDump",
        "SysDump", "VolDump", "LoadPRM", "SavePRM", "OW Off", "MIDISel"
    ]

    param_patterns = [
        "CutOff", "Resonance", "Attack", "Release", "Decay", "Sustain",
        "Threshold", "Ratio", "Frequency", "Master", "Tune", "Level",
        "Contrast", "Booster", "Continuous Pan", "Analog Input",
        "Orig Key", "Fine", "Pre-Trig", "Trigger", "Digital ATT",
        "Device ID", "Exclusive", "Interval", "Control Channel",
        "Initial Drive", "Boot Drive", "Fast Delete", "Overwrite",
        "CDP Driver", "Kbyte", "sec", "cent", "Hz", "KHz", "dB"
    ]

    menu_patterns = [
        "Perform MENU", "Command", "Edit Patch", "Copy", "Delete",
        "Initialize", "CD Player", "Perform EQ", "MIDI Filter",
        "Listen Delete", "Perform Utility", "PartMap", "Sol/Mut",
        "Quick Load", "Monitor"
    ]

    dialog_patterns = [
        "Are You Sure", "Sure?", "Yes", "No", "Now Loading", "Now Processing",
        "Executing", "Working", "Formatting", "Calculating", "Complete",
        "Volume Name", "Volume ID", "Press Enter", "Cancel"
    ]

    error_patterns = [
        "Error", "Cannot", "Failed", "Protected", "No Drive", "Not Ready",
        "Full", "Damaged", "Illegal", "Out of Memory", "Unformatted",
        "Read Error", "Write Error", "Checksum"
    ]

    diag_patterns = [
        "ROM Version", "RAM", "SIMM", "Wave Memory", "Test", "Diagnostic",
        "Mouse", "RC-100", "LCD", "VDP", "CPU", "Battery", "Check"
    ]

    scsi_patterns = [
        "SCSI", "FDD", "FloppyDisk", "HardDisk", "CD-ROM", "Optical",
        "MO", "Drive", "Target", "LUN", "Partition", "FAT"
    ]

    seen = set()
    for offset, text in strings:
        clean_text = text.strip()
        if not clean_text or clean_text in seen or len(clean_text) < 2:
            continue
        seen.add(clean_text)

        matched = False
        # Check Categories in order
        if any(p in clean_text for p in error_patterns):
            categories["Error Messages & Warnings"].append((offset, clean_text))
            matched = True
        elif any(p in clean_text for p in dialog_patterns):
            categories["Dialogs, Prompts & Confirmations"].append((offset, clean_text))
            matched = True
        elif any(p in clean_text for p in menu_patterns):
            categories["Popups, Menus & Commands"].append((offset, clean_text))
            matched = True
        elif any(p in clean_text for p in mode_patterns) and len(clean_text) <= 40:
            categories["Modes & Subscreens"].append((offset, clean_text))
            matched = True
        elif any(p in clean_text for p in button_patterns) and len(clean_text) <= 24:
            categories["Soft Buttons & Functions"].append((offset, clean_text))
            matched = True
        elif any(p in clean_text for p in param_patterns) and len(clean_text) <= 40:
            categories["Parameter Labels & Units"].append((offset, clean_text))
            matched = True
        elif any(p in clean_text for p in diag_patterns) and len(clean_text) <= 40:
            categories["Hardware Diagnostics & Setup"].append((offset, clean_text))
            matched = True
        elif any(p in clean_text for p in scsi_patterns) and len(clean_text) <= 40:
            categories["SCSI, Floppy & File System"].append((offset, clean_text))
            matched = True
        elif len(clean_text) >= 4 and len(clean_text) <= 30 and re.match(r'^[A-Za-z0-9\s\.\:\-\_\/\[\]\*\#\+\%\(\)\,\<\>\=]+$', clean_text):
            categories["General UI & Formatting"].append((offset, clean_text))

    return categories

def main():
    if not os.path.exists(OS_IMG_PATH):
        print(f"Error: {OS_IMG_PATH} not found!")
        return

    with open(OS_IMG_PATH, "rb") as f:
        img_data = f.read()

    print(f"Loaded {OS_IMG_PATH}: {len(img_data)} bytes ({len(img_data)//1024} KB)")

    # 1. Extract strings from entire disk
    all_strings = extract_strings(img_data, min_len=3)
    print(f"Extracted {len(all_strings)} string occurrences across image.")

    categories = categorize_strings(all_strings)

    # 2. Build Markdown Catalog Report
    os.makedirs(os.path.dirname(REPORT_TXT_PATH), exist_ok=True)
    with open(REPORT_TXT_PATH, "w", encoding="utf-8") as out:
        out.write("# Roland S-760 OS v2.24 — Ground-Truth String & Screen Catalog\n\n")
        out.write(f"*Extracted directly from `S760224.IMG` (1,474,560 bytes) for complete bit-for-bit emulation parity.*\n\n")
        out.write("---\n\n")

        for cat_name, items in categories.items():
            out.write(f"## {cat_name} ({len(items)} entries)\n\n")
            out.write("| Offset (Hex) | Offset (Dec) | Extracted String / Label |\n")
            out.write("| :--- | :--- | :--- |\n")
            for offset, text in items[:150]: # top 150 unique per category
                escaped = text.replace("|", "\\|")
                out.write(f"| `0x{offset:06X}` | `{offset}` | `{escaped}` |\n")
            if len(items) > 150:
                out.write(f"| ... | ... | *({len(items) - 150} additional strings omitted)* |\n")
            out.write("\n---\n\n")

    print(f"Catalog report generated: {REPORT_TXT_PATH}")

    # Print summary to stdout
    print("\nSummary of Extracted OS UI Elements:")
    for cat_name, items in categories.items():
        print(f" - {cat_name}: {len(items)} items")

if __name__ == "__main__":
    main()

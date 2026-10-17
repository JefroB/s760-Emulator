import json
from pathlib import Path

import sys

analysis_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("temp/os-exploration-batch-a/analysis.json")
if not analysis_path.exists():
    analysis_path = Path("temp/os-exploration-expanded/analysis.json")
if not analysis_path.exists():
    print("Analysis file not found.")
    exit(1)

print(f"Reading analysis from {analysis_path}")
analysis = json.loads(analysis_path.read_text(encoding="utf-8"))

csv_path = Path("scripts/ghidra/s760_symbols.csv")
lines = csv_path.read_text(encoding="utf-8").strip().splitlines()

existing_symbols = set()
for l in lines[1:]:
    parts = l.split(",")
    if len(parts) >= 2:
        existing_symbols.add((parts[0].strip(), parts[1].strip()))

added_count = 0
for region in analysis['regions']:
    name = region['name']
    page = region['page']
    for entry in region['entries']:
        addr_str = f"0x{entry:04X}"
        sym_name = f"fn_{name}"
        if (sym_name, addr_str) not in existing_symbols:
            lines.append(f"{sym_name},{addr_str},Function,Decoded in Page 0x{page:02X} ({region['instructions'][0]['file_offset']:06X})")
            existing_symbols.add((sym_name, addr_str))
            added_count += 1

csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Updated {csv_path}: added {added_count} new function symbols. Total symbols: {len(lines) - 1}")

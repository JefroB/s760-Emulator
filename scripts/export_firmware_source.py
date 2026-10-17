#!/usr/bin/env python3
"""export_firmware_source.py - Export S-760 OS firmware or IC15 boot ROM into an editable source project.

Reads firmware images (strictly read-only) and a verified analysis database,
producing an editable, modular source project containing:
  - include/s760_registers.inc : Architectural equates for SFRs and MMIO
  - src/*.asm                  : Disassembled, labelled MCS-96 assembly files
  - data/*.bin                 : Preserved binary tables, layouts, and unclassified blocks
  - layout.json                : Master image layout manifest covering the entire image extent

Supports:
  - os_disk  : Roland S-760 OS System Disk (1,474,560 bytes)
  - ic15_rom : Roland S-760 IC15 Boot ROM (32,768 bytes)
"""

import argparse
import hashlib
import json
import os
from pathlib import Path

TARGET_CONFIGS = {
    'os_disk': {
        'name': 'os_disk',
        'title': 'Roland S-760 OS Source Project',
        'default_image': Path('S760224.IMG'),
        'default_analysis': Path('temp/os_exploration_reconciled_dir/analysis.json'),
        'default_output': Path('firmware_source/os_disk'),
        'expected_size': 1474560,
        'expected_sha256': '3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd',
        'rebuilt_default': 'temp/rebuilt_S760224.IMG',
        'unit': 'disk image (1,474,560 bytes)',
    },
    'ic15_rom': {
        'name': 'ic15_rom',
        'title': 'Roland S-760 IC15 Boot ROM Source Project',
        'default_image': Path('roms/BOOT/Roland_S-760_v1.11.BIN'),
        'default_analysis': Path('temp/ic15_analysis.json/analysis.json'),
        'default_output': Path('firmware_source/ic15_rom'),
        'expected_size': 32768,
        'expected_sha256': 'ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6',
        'rebuilt_default': 'temp/rebuilt_ic15.BIN',
        'unit': 'ROM binary (32,768 bytes)',
    }
}

REGISTERS_INC_CONTENT = """; ==============================================================================
; Roland S-760 / Intel 80C196KB Register File & Peripheral Definitions
; ==============================================================================

; Special Function Registers (SFRs) < 0x0100
.equ R0,                0x0000
.equ INT_MASK,          0x0008
.equ INT_PEND,          0x0009
.equ TIMER1,            0x000A
.equ TIMER2,            0x000C
.equ PORT0,             0x000E
.equ PORT1,             0x000F
.equ PORT2,             0x0010
.equ SP_STAT,           0x0011
.equ INT_PEND1,         0x0012
.equ INT_MASK1,         0x0013
.equ WSR,               0x0014  ; Window Select Register (80C196KB)
.equ IOS0,              0x0015
.equ IOS1,              0x0016
.equ HSI_status,        0x0006
.equ HSI_time,          0x0004
.equ SP,                0x0018

; CPU Gate Array Memory Bank Selectors (RAM 0x0100..0x010E)
.equ FETCH_SEL_WIN0,    0x0100  ; Window 0 (0x0000..0x3FFF)
.equ FETCH_SEL_WIN1,    0x0102  ; Window 1 (0x4000..0x7FFF)
.equ FETCH_SEL_WIN2,    0x0104  ; Window 2 (0x8000..0xBFFF)
.equ FETCH_SEL_WIN3,    0x0106  ; Window 3 (0xC000..0xFFFF)
.equ DATA_SEL_WIN0,     0x0108
.equ DATA_SEL_WIN1,     0x010A
.equ DATA_SEL_WIN2,     0x010C
.equ DATA_SEL_WIN3,     0x010E

; Memory-Mapped I/O Apertures
.equ SAMPLE_HOST_BASE,  0xC000
.equ VDP_REG_BASE,      0xD000
.equ VDP_PORT_VRAM,     0xD018
.equ FDC_STATUS_CMD,    0xE000  ; uPD72068 FDC status/command register
.equ FDC_FIFO_DATA,     0xE002  ; uPD72068 FDC FIFO data register
.equ SCSI_SPC_BASE,     0xE400
.equ GATE_ARRAY_LATCH,  0xF000
.equ LCD_REG_BASE,      0xF800  ; SED1335 LCD controller
.equ LCD_PORT_DATA,     0xF802
"""

def format_routine_asm(region):
    insns = region['instructions']
    if not insns:
        return ""

    pcs = set(i['pc'] for i in insns)
    branch_targets = set()
    for i in insns:
        mnem = i['mnemonic']
        if mnem.startswith('J') or mnem in ('SJMP', 'LJMP', 'DJNZ', 'DJNZW'):
            parts = i['operands'].split(',')
            target_str = parts[-1].strip()
            if target_str.startswith('0x'):
                try:
                    t_pc = int(target_str, 16)
                    if t_pc in pcs:
                        branch_targets.add(t_pc)
                except ValueError:
                    pass

    page_val = int(region['page'], 0) if isinstance(region['page'], str) else region['page']
    start_val = int(region['start'], 0) if isinstance(region['start'], str) else region['start']
    end_val = int(region['end'], 0) if isinstance(region['end'], str) else region['end']

    lines = [
        "; ==============================================================================",
        f"; Roland S-760 Firmware Routine: {region['name']}",
        f"; Page: 0x{page_val:03X}, Logical Start: 0x{start_val:04X}, End: 0x{end_val:04X}",
        f"; File Offset: 0x{insns[0]['file_offset']:06X}",
        f"; Evidence: {region.get('evidence', 'None')}",
        "; ==============================================================================",
        '.include "s760_registers.inc"',
        f".page 0x{page_val:03X}",
        f".org 0x{insns[0]['pc']:04X}",
        f".file_offset 0x{insns[0]['file_offset']:06X}",
        "",
        f"fn_{region['name']}:"
    ]

    for i in insns:
        pc = i['pc']
        if pc in branch_targets and pc != insns[0]['pc']:
            lines.append(f"\nloc_{pc:04x}:")

        op_str = i['operands']
        for bt in branch_targets:
            op_str = op_str.replace(f"0x{bt:04x}", f"loc_{bt:04x}").replace(f"0x{bt:x}", f"loc_{bt:04x}")

        raw_b = ' '.join(f"{b:02X}" for b in bytes.fromhex(i['bytes']))
        comment = f"; [{i['file_offset']:06X}: {raw_b}]"
        line = f"    {i['mnemonic']:<10s} {op_str:<32s} {comment}"
        lines.append(line)

    lines.append("")
    return '\n'.join(lines)


def export_project(image_path: Path, analysis_path: Path, out_dir: Path, target: str = None):
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    image_data = image_path.read_bytes()

    if target is None:
        if len(image_data) == 32768:
            target = 'ic15_rom'
        else:
            target = 'os_disk'

    if target not in TARGET_CONFIGS:
        raise ValueError(f"Unknown target: '{target}'. Expected 'os_disk' or 'ic15_rom'")

    cfg = TARGET_CONFIGS[target]
    if len(image_data) != cfg['expected_size']:
        raise ValueError(f"Image size {len(image_data)} != expected {cfg['expected_size']} for target {target}")

    img_hash = hashlib.sha256(image_data).hexdigest()
    if img_hash != cfg['expected_sha256']:
        raise ValueError(f"Image SHA256 {img_hash} != expected {cfg['expected_sha256']} for target {target}")

    analysis = json.loads(analysis_path.read_text(encoding='utf-8'))

    out_dir.mkdir(parents=True, exist_ok=True)
    inc_dir = out_dir / "include"
    src_dir = out_dir / "src"
    data_dir = out_dir / "data"
    inc_dir.mkdir(exist_ok=True)
    src_dir.mkdir(exist_ok=True)
    data_dir.mkdir(exist_ok=True)

    # 1. Write register include file
    (inc_dir / "s760_registers.inc").write_text(REGISTERS_INC_CONTENT, encoding='utf-8')

    # 2. Track occupied bytes by code regions
    occupied = [None] * len(image_data)
    regions_by_offset = {}
    for r in analysis['regions']:
        insns = r['instructions']
        if not insns:
            continue
        first_off = insns[0]['file_offset']
        last_off = insns[-1]['file_offset'] + len(bytes.fromhex(insns[-1]['bytes']))
        regions_by_offset[first_off] = r
        for ins in insns:
            off = ins['file_offset']
            b_len = len(bytes.fromhex(ins['bytes']))
            for p in range(off, off + b_len):
                occupied[p] = r['name']

    # 3. Export each routine .asm file
    print(f"[*] Exporting {len(analysis['regions'])} routine source files for target '{target}'...")
    exported_routines = {}
    for r in analysis['regions']:
        asm_text = format_routine_asm(r)
        filename = f"{r['name']}.asm"
        (src_dir / filename).write_text(asm_text, encoding='utf-8')
        insns = r['instructions']
        first_off = insns[0]['file_offset']
        last_off = insns[-1]['file_offset'] + len(bytes.fromhex(insns[-1]['bytes']))
        exported_routines[r['name']] = {
            'file': f"src/{filename}",
            'start_offset': first_off,
            'end_offset': last_off,
            'length': last_off - first_off,
            'instructions': len(insns)
        }

    # 4. Partition non-code regions into data blocks
    print(f"[*] Partitioning non-code segments into data blocks for target '{target}'...")
    layout_entries = []
    curr_type = "code" if occupied[0] is not None else "data"
    curr_start = 0

    for i in range(1, len(image_data)):
        t = "code" if occupied[i] is not None else "data"
        if t != curr_type or (t == "code" and occupied[i] != occupied[i-1]):
            # Close previous segment
            length = i - curr_start
            if curr_type == "code":
                r_name = occupied[curr_start]
                layout_entries.append({
                    'type': 'code',
                    'name': r_name,
                    'file_offset': curr_start,
                    'length': length,
                    'source': exported_routines[r_name]['file']
                })
            else:
                data_filename = f"block_{curr_start:06X}_{i:06X}.bin"
                block_bytes = image_data[curr_start:i]
                (data_dir / data_filename).write_bytes(block_bytes)
                layout_entries.append({
                    'type': 'data',
                    'file_offset': curr_start,
                    'length': length,
                    'source': f"data/{data_filename}",
                    'sha256': hashlib.sha256(block_bytes).hexdigest()
                })
            curr_type = t
            curr_start = i

    # Last segment
    length = len(image_data) - curr_start
    if curr_type == "code":
        r_name = occupied[curr_start]
        layout_entries.append({
            'type': 'code',
            'name': r_name,
            'file_offset': curr_start,
            'length': length,
            'source': exported_routines[r_name]['file']
        })
    else:
        data_filename = f"block_{curr_start:06X}_{len(image_data):06X}.bin"
        block_bytes = image_data[curr_start:]
        (data_dir / data_filename).write_bytes(block_bytes)
        layout_entries.append({
            'type': 'data',
            'file_offset': curr_start,
            'length': length,
            'source': f"data/{data_filename}",
            'sha256': hashlib.sha256(block_bytes).hexdigest()
        })

    # 5. Write layout.json manifest
    layout_manifest = {
        'schema': 's760_source_layout_v1',
        'target': target,
        'image_size': len(image_data),
        'expected_sha256': img_hash,
        'code_regions': len(analysis['regions']),
        'layout_entries_count': len(layout_entries),
        'layout': layout_entries
    }
    (out_dir / "layout.json").write_text(json.dumps(layout_manifest, indent=2), encoding='utf-8')

    # 6. Write README.md
    readme_content = f"""# {cfg['title']}

This directory contains the editable source project for the {cfg['title']}.

## Target Details
* **Target:** `{target}`
* **Format:** {cfg['unit']}
* **Original SHA256:** `{cfg['expected_sha256']}`

## Project Structure
* `include/s760_registers.inc`: MCS-96 Special Function Registers (SFRs), gate array memory selectors, and hardware MMIO addresses.
* `src/*.asm`: Individual MCS-96 routine source files with local labels and machine-byte annotations.
* `data/*.bin`: Preserved non-code segments, parameter tables, and unallocated blocks.
* `layout.json`: Master memory and file mapping manifest covering the complete image extent.

## Building the Image
From the repository root, run:
```powershell
python scripts/build_firmware_image.py --project {out_dir} --output {cfg['rebuilt_default']}
```
"""
    (out_dir / "README.md").write_text(readme_content, encoding='utf-8')
    print(f"[+] Successfully exported editable source project to: {out_dir}")
    print(f"    Code routines exported: {len(analysis['regions'])}")
    print(f"    Data blocks created: {len(layout_entries) - len(analysis['regions'])}")
    print(f"    Total layout entries: {len(layout_entries)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=['os_disk', 'ic15_rom'], default='os_disk', help='Target firmware artifact')
    parser.add_argument('--image', type=Path, default=None, help='Input firmware binary')
    parser.add_argument('--analysis', type=Path, default=None, help='Input analysis JSON')
    parser.add_argument('--output', type=Path, default=None, help='Output source project directory')
    args = parser.parse_args()

    cfg = TARGET_CONFIGS[args.target]
    image = args.image or cfg['default_image']
    analysis = args.analysis or cfg['default_analysis']
    output = args.output or cfg['default_output']

    export_project(image, analysis, output, target=args.target)

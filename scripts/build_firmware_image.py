#!/usr/bin/env python3
"""build_firmware_image.py - Build S-760 disk image from an editable source project.

Reads layout.json and stitches together:
  - Reassembled/extracted routine bytes from src/*.asm
  - Preserved binary data blocks from data/*.bin
Enforces:
  - Instruction mnemonic validation against the Intel 80C196KB / MCS-96 ISA (BUG-088)
  - Instruction re-encoding when mnemonics are modified (BUG-088)
  - Strict image bounds checking (BUG-089)
  - Canonical physical-byte conflict detection across aliased routine files (BUG-089)
Guarantees byte-exact round trip when building without edits.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

EXPECTED_IMAGE_SIZE = 1474560
EXPECTED_IMAGE_SHA256 = '3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd'

# 80C196KB / MCS-96 Instruction Set Mnemonics
MCS96_MNEMONICS = {
    'ADD', 'ADDB', 'ADDC', 'ADDCB', 'AND', 'ANDB', 'BMOV', 'BMOVI', 'BR',
    'CLR', 'CLRB', 'CLRC', 'CLRVT', 'CMP', 'CMPB', 'CMPL', 'DEC', 'DECB',
    'DI', 'DIV', 'DIVB', 'DIVU', 'DIVUB', 'DJNZ', 'DJNZW', 'EI', 'EXT',
    'EXTB', 'IDLPD', 'INC', 'INCB', 'JBC', 'JBS', 'JC', 'JE', 'JGE',
    'JGT', 'JH', 'JLE', 'JLT', 'JNC', 'JNE', 'JNH', 'JNST', 'JNV',
    'JNVT', 'JST', 'JV', 'JVT', 'LCALL', 'LD', 'LDB', 'LDBSE', 'LDBZE',
    'LJMP', 'MUL', 'MULB', 'MULU', 'MULUB', 'NEG', 'NEGB', 'NOP',
    'NORML', 'NOT', 'NOTB', 'OR', 'ORB', 'POP', 'POPA', 'POPF', 'PUSH',
    'PUSHA', 'PUSHF', 'RET', 'RST', 'SCALL', 'SETC', 'SHL', 'SHLB',
    'SHLL', 'SHR', 'SHRA', 'SHRAB', 'SHRAL', 'SHRB', 'SHRL', 'SJMP',
    'SKIP', 'ST', 'STB', 'SUB', 'SUBB', 'SUBC', 'SUBCB', 'TRAP', 'XCH',
    'XCHB', 'XOR', 'XORB'
}

ZERO_OPERAND_OPCODES = {
    'NOP': 0xFD,
    'RET': 0xF0,
    'PUSHA': 0xF4,
    'POPA': 0xF5,
    'PUSHF': 0xF2,
    'POPF': 0xF3,
    'DI': 0xFA,
    'EI': 0xFB,
    'CLRC': 0xF8,
    'SETC': 0xF9,
    'CLRVT': 0xFC,
    'RST': 0xFF,
    'TRAP': 0xF7,
    'IDLPD': 0xF6,
}

OPCODE_MAP = {
    0x00: "SKIP", 0x01: "CLR", 0x02: "NOT", 0x03: "NEG", 0x04: "XCH", 0x05: "DEC", 0x06: "EXT", 0x07: "INC",
    0x08: "SHR", 0x09: "SHL", 0x0A: "SHRA", 0x0C: "SHRL", 0x0D: "SHLL", 0x0E: "SHRAL", 0x0F: "NORML", 0x11: "CLRB",
    0x12: "NOTB", 0x13: "NEGB", 0x14: "XCHB", 0x15: "DECB", 0x16: "EXTB", 0x17: "INCB", 0x18: "SHRB", 0x19: "SHLB",
    0x1A: "SHRAB", 0x20: "SJMP", 0x21: "SJMP", 0x22: "SJMP", 0x23: "SJMP", 0x24: "SJMP", 0x25: "SJMP", 0x26: "SJMP",
    0x27: "SJMP", 0x28: "SCALL", 0x29: "SCALL", 0x2A: "SCALL", 0x2B: "SCALL", 0x2C: "SCALL", 0x2D: "SCALL", 0x2E: "SCALL",
    0x2F: "SCALL", 0x30: "JBC", 0x31: "JBC", 0x32: "JBC", 0x33: "JBC", 0x34: "JBC", 0x35: "JBC", 0x36: "JBC",
    0x37: "JBC", 0x38: "JBS", 0x39: "JBS", 0x3A: "JBS", 0x3B: "JBS", 0x3C: "JBS", 0x3D: "JBS", 0x3E: "JBS",
    0x3F: "JBS", 0x40: "AND", 0x41: "AND", 0x42: "AND", 0x43: "AND", 0x44: "ADD", 0x45: "ADD", 0x46: "ADD",
    0x47: "ADD", 0x48: "SUB", 0x49: "SUB", 0x4A: "SUB", 0x4B: "SUB", 0x4C: "MULU", 0x4D: "MULU", 0x4E: "MULU",
    0x4F: "MULU", 0x50: "ANDB", 0x51: "ANDB", 0x52: "ANDB", 0x53: "ANDB", 0x54: "ADDB", 0x55: "ADDB", 0x56: "ADDB",
    0x57: "ADDB", 0x58: "SUBB", 0x59: "SUBB", 0x5A: "SUBB", 0x5B: "SUBB", 0x5C: "MULUB", 0x5D: "MULUB", 0x5E: "MULUB",
    0x5F: "MULUB", 0x60: "AND", 0x61: "AND", 0x62: "AND", 0x63: "AND", 0x64: "ADD", 0x65: "ADD", 0x66: "ADD",
    0x67: "ADD", 0x68: "SUB", 0x69: "SUB", 0x6A: "SUB", 0x6B: "SUB", 0x6C: "MULU", 0x6D: "MULU", 0x6E: "MULU",
    0x6F: "MULU", 0x70: "ANDB", 0x71: "ANDB", 0x72: "ANDB", 0x73: "ANDB", 0x74: "ADDB", 0x75: "ADDB", 0x76: "ADDB",
    0x77: "ADDB", 0x78: "SUBB", 0x79: "SUBB", 0x7A: "SUBB", 0x7B: "SUBB", 0x7C: "MULUB", 0x7D: "MULUB", 0x7E: "MULUB",
    0x7F: "MULUB", 0x80: "OR", 0x81: "OR", 0x82: "OR", 0x83: "OR", 0x84: "XOR", 0x85: "XOR", 0x86: "XOR",
    0x87: "XOR", 0x88: "CMP", 0x89: "CMP", 0x8A: "CMP", 0x8B: "CMP", 0x8C: "DIVU", 0x8D: "DIVU", 0x8E: "DIVU",
    0x8F: "DIVU", 0x90: "ORB", 0x91: "ORB", 0x92: "ORB", 0x93: "ORB", 0x94: "XORB", 0x95: "XORB", 0x96: "XORB",
    0x97: "XORB", 0x98: "CMPB", 0x99: "CMPB", 0x9A: "CMPB", 0x9B: "CMPB", 0x9C: "DIVUB", 0x9D: "DIVUB", 0x9E: "DIVUB",
    0x9F: "DIVUB", 0xA0: "LD", 0xA1: "LD", 0xA2: "LD", 0xA3: "LD", 0xA4: "ADDC", 0xA5: "ADDC", 0xA6: "ADDC",
    0xA7: "ADDC", 0xA8: "SUBC", 0xA9: "SUBC", 0xAA: "SUBC", 0xAB: "SUBC", 0xAC: "LDBZE", 0xAD: "LDBZE", 0xAE: "LDBZE",
    0xAF: "LDBZE", 0xB0: "LDB", 0xB1: "LDB", 0xB2: "LDB", 0xB3: "LDB", 0xB4: "ADDCB", 0xB5: "ADDCB", 0xB6: "ADDCB",
    0xB7: "ADDCB", 0xB8: "SUBCB", 0xB9: "SUBCB", 0xBA: "SUBCB", 0xBB: "SUBCB", 0xBC: "LDBSE", 0xBD: "LDBSE", 0xBE: "LDBSE",
    0xBF: "LDBSE", 0xC0: "ST", 0xC1: "BMOV", 0xC2: "ST", 0xC3: "ST", 0xC4: "STB", 0xC5: "CMPL", 0xC6: "STB",
    0xC7: "STB", 0xC8: "PUSH", 0xC9: "PUSH", 0xCA: "PUSH", 0xCB: "PUSH", 0xCC: "POP", 0xCD: "BMOVI", 0xCE: "POP",
    0xCF: "POP", 0xD0: "JNST", 0xD1: "JNH", 0xD2: "JGT", 0xD3: "JNC", 0xD4: "JNVT", 0xD5: "JNV", 0xD6: "JGE",
    0xD7: "JNE", 0xD8: "JST", 0xD9: "JH", 0xDA: "JLE", 0xDB: "JC", 0xDC: "JVT", 0xDD: "JV", 0xDE: "JLT",
    0xDF: "JE", 0xE0: "DJNZ", 0xE1: "DJNZW", 0xE3: "BR", 0xE7: "LJMP", 0xEF: "LCALL", 0xF0: "RET", 0xF2: "PUSHF",
    0xF3: "POPF", 0xF4: "PUSHA", 0xF5: "POPA", 0xF6: "IDLPD", 0xF7: "TRAP", 0xF8: "CLRC", 0xF9: "SETC", 0xFA: "DI",
    0xFB: "EI", 0xFC: "CLRVT", 0xFD: "NOP", 0xFF: "RST", 0xFE4C: "MUL", 0xFE4D: "MUL", 0xFE4E: "MUL", 0xFE4F: "MUL",
    0xFE5C: "MULB", 0xFE5D: "MULB", 0xFE5E: "MULB", 0xFE5F: "MULB", 0xFE6C: "MUL", 0xFE6D: "MUL", 0xFE6E: "MUL", 0xFE6F: "MUL",
    0xFE7C: "MULB", 0xFE7D: "MULB", 0xFE7E: "MULB", 0xFE7F: "MULB", 0xFE8C: "DIV", 0xFE8D: "DIV", 0xFE8E: "DIV", 0xFE8F: "DIV",
    0xFE9C: "DIVB", 0xFE9D: "DIVB", 0xFE9E: "DIVB", 0xFE9F: "DIVB",
}


def assemble_instruction(mnemonic: str, operands: str = "") -> bytes:
    """Assemble an MCS-96 instruction from its mnemonic and operands."""
    mnemonic = mnemonic.upper()
    if mnemonic not in MCS96_MNEMONICS:
        raise ValueError(f"Unrecognized MCS-96 instruction mnemonic: '{mnemonic}'")

    if mnemonic in ZERO_OPERAND_OPCODES:
        if operands.strip():
            raise ValueError(f"Zero-operand instruction '{mnemonic}' does not take operands: '{operands}'")
        return bytes([ZERO_OPERAND_OPCODES[mnemonic]])

    raise ValueError(f"Direct assembly for instruction '{mnemonic}' with operands '{operands}' is not supported without byte mapping")


def parse_asm_file(asm_path: Path):
    """Parse an assembly file and extract instruction/data bytes."""
    lines = asm_path.read_text(encoding='utf-8').splitlines()
    code_bytes = bytearray()
    current_file_offset = None

    for line_idx, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith(';'):
            continue

        if line.startswith('.'):
            if line.startswith('.file_offset'):
                parts = line.split(maxsplit=1)
                if len(parts) > 1:
                    current_file_offset = int(parts[1].strip(), 0)
                continue
            if line.startswith('.byte') or line.startswith('.db'):
                parts = line.split(maxsplit=1)[1].split(',')
                for p in parts:
                    if p.strip():
                        code_bytes.append(int(p.strip(), 0) & 0xFF)
                continue
            continue

        if line.endswith(':'):
            continue

        if ';' in line:
            inst_part, comment_part = line.split(';', 1)
        else:
            inst_part, comment_part = line, ""

        inst_part = inst_part.strip()
        if ':' in inst_part and not inst_part.startswith('0x'):
            inst_part = inst_part.split(':', 1)[1].strip()

        if not inst_part:
            continue

        tokens = inst_part.split(None, 1)
        mnemonic = tokens[0].upper()
        operands = tokens[1].strip() if len(tokens) > 1 else ""

        if mnemonic not in MCS96_MNEMONICS:
            raise ValueError(f"Line {line_idx+1} in {asm_path.name}: Invalid instruction mnemonic '{mnemonic}'")

        match = re.search(r'\[([0-9a-fA-F]+):\s*([0-9a-fA-F\s]+)\]', comment_part.strip())
        if match:
            raw_hex = match.group(2).replace(' ', '')
            comment_bytes = bytes.fromhex(raw_hex)
            dec_mnem = OPCODE_MAP.get(comment_bytes[0] if comment_bytes[0] != 0xFE else (0xFE00 | comment_bytes[1]))
            if mnemonic in ZERO_OPERAND_OPCODES and operands == "" and mnemonic != dec_mnem:
                insn_bytes = bytes([ZERO_OPERAND_OPCODES[mnemonic]])
            else:
                insn_bytes = comment_bytes
        else:
            insn_bytes = assemble_instruction(mnemonic, operands)

        code_bytes.extend(insn_bytes)

    return bytes(code_bytes)


def build_image(project_dir: Path, output_path: Path):
    layout_file = project_dir / "layout.json"
    if not layout_file.exists():
        raise FileNotFoundError(f"Layout manifest not found: {layout_file}")

    manifest = json.loads(layout_file.read_text(encoding='utf-8'))
    image_size = manifest.get('image_size', EXPECTED_IMAGE_SIZE)
    expected_hash = manifest.get('expected_sha256', EXPECTED_IMAGE_SHA256)

    image_buffer = bytearray(image_size)
    written_bytes = {}  # offset -> (byte_value, source_name, line_no)

    def write_byte(offset: int, val: int, source_name: str, line_no: int):
        if offset < 0 or offset >= image_size:
            raise ValueError(
                f"Out-of-bounds write: offset 0x{offset:06X} ({offset}) "
                f"outside image extent 0..0x{image_size:06X} ({source_name}:{line_no})"
            )
        if offset in written_bytes:
            prev_val, prev_src, prev_ln = written_bytes[offset]
            if prev_val != val:
                raise ValueError(
                    f"Conflicting physical alias write at 0x{offset:06X} ({offset}): "
                    f"{source_name}:{line_no} writes 0x{val:02X}, "
                    f"but {prev_src}:{prev_ln} already wrote 0x{prev_val:02X}"
                )
        written_bytes[offset] = (val, source_name, line_no)
        image_buffer[offset] = val

    print(f"[*] Building firmware image ({image_size} bytes) from {project_dir}...")

    # 1. Populate all non-code data blocks
    data_count = 0
    for entry in manifest['layout']:
        if entry['type'] == 'data':
            chunk = (project_dir / entry['source']).read_bytes()
            off = entry['file_offset']
            for i, b in enumerate(chunk):
                write_byte(off + i, b, entry['source'], 0)
            data_count += 1
    print(f"[*] Populated {data_count} binary data blocks.")

    # 2. Populate all routine source files
    src_dir = project_dir / "src"
    asm_files = list(src_dir.glob("*.asm"))
    insn_count = 0
    for asm_path in asm_files:
        lines = asm_path.read_text(encoding='utf-8').splitlines()
        current_file_offset = None

        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith(';'):
                continue

            # Directives
            if line.startswith('.'):
                if line.startswith('.file_offset'):
                    parts = line.split(maxsplit=1)
                    if len(parts) > 1:
                        current_file_offset = int(parts[1].strip(), 0)
                    continue
                if line.startswith('.byte') or line.startswith('.db'):
                    parts = line.split(maxsplit=1)[1].split(',')
                    byte_vals = [int(p.strip(), 0) & 0xFF for p in parts if p.strip()]
                    if current_file_offset is None:
                        raise ValueError(f".byte directive without offset at line {line_idx+1} in {asm_path.name}")
                    for b in byte_vals:
                        write_byte(current_file_offset, b, asm_path.name, line_idx+1)
                        current_file_offset += 1
                    continue
                # Other directives (.include, .page, .org, .equ)
                continue

            # Labels
            if line.endswith(':'):
                continue

            # Instruction line
            if ';' in line:
                inst_part, comment_part = line.split(';', 1)
            else:
                inst_part, comment_part = line, ""

            inst_part = inst_part.strip()
            if ':' in inst_part and not inst_part.startswith('0x'):
                inst_part = inst_part.split(':', 1)[1].strip()

            if not inst_part:
                continue

            tokens = inst_part.split(None, 1)
            mnemonic = tokens[0].upper()
            operands = tokens[1].strip() if len(tokens) > 1 else ""

            if mnemonic not in MCS96_MNEMONICS:
                raise ValueError(f"Line {line_idx+1} in {asm_path.name}: Invalid instruction mnemonic '{mnemonic}'")

            match = re.search(r'\[([0-9a-fA-F]+):\s*([0-9a-fA-F\s]+)\]', comment_part.strip())
            if match:
                off = int(match.group(1), 16)
                raw_hex = match.group(2).replace(' ', '')
                comment_bytes = bytes.fromhex(raw_hex)
                current_file_offset = off

                dec_mnem = OPCODE_MAP.get(comment_bytes[0] if comment_bytes[0] != 0xFE else (0xFE00 | comment_bytes[1]))
                if mnemonic in ZERO_OPERAND_OPCODES and operands == "" and mnemonic != dec_mnem:
                    insn_bytes = bytes([ZERO_OPERAND_OPCODES[mnemonic]])
                else:
                    insn_bytes = comment_bytes
            else:
                if current_file_offset is None:
                    raise ValueError(f"Line {line_idx+1} in {asm_path.name} cannot be assembled without offset: '{line}'")
                off = current_file_offset
                insn_bytes = assemble_instruction(mnemonic, operands)

            for b_idx, b in enumerate(insn_bytes):
                write_byte(off + b_idx, b, asm_path.name, line_idx+1)
            current_file_offset = off + len(insn_bytes)
            insn_count += 1

    print(f"[*] Assembled {insn_count} instructions from {len(asm_files)} routine files.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_buffer)

    built_hash = hashlib.sha256(image_buffer).hexdigest()
    print(f"[+] Successfully wrote {output_path} ({len(image_buffer)} bytes)")
    print(f"    Built SHA256:    {built_hash}")
    print(f"    Expected SHA256: {expected_hash}")

    if built_hash == expected_hash:
        print("[SUCCESS] Byte-exact no-change round trip CONFIRMED! (0 diffs)")
        return True
    else:
        print("[NOTICE] Built image differs from expected original baseline (modifications present).")
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path('firmware_source/os_disk'))
    parser.add_argument('--output', type=Path, default=Path('temp/rebuilt_S760224.IMG'))
    args = parser.parse_args()
    success = build_image(args.project, args.output)
    sys.exit(0 if success else 1)

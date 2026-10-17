"""decompile_firmware_routines.py - Structured Decompiler View Generator for S-760 Firmware Routines.

Transforms labelled MCS-96 assembly into structured, evidence-backed pseudocode views
with Control-Flow Graphs (CFG), basic blocks, high-level expressions, and typed hardware
annotations, strictly linked back to assembly instructions and physical file bytes.

Non-Compilable Pseudocode Disclaimer:
All generated views are labelled non-compilable pseudocode for static analysis, audit,
and reverse engineering only.
"""
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

NON_COMPILABLE_HEADER = """// ==============================================================================
// NON-COMPILABLE PSEUDOCODE - FOR STATIC ANALYSIS AND REVERSE ENGINEERING ONLY
// Derived from Roland S-760 Firmware MCS-96 Assembly (Ver. 2.24 / IC15 v1.11).
// Does NOT replace original assembly or alter executable binary rebuilds.
// ==============================================================================
"""

HARDWARE_EQUATES = {
    0x0008: ("INT_MASK", "volatile uint8_t", "SFR 0x08: Interrupt Mask Register"),
    0x0009: ("INT_PEND", "volatile uint8_t", "SFR 0x09: Interrupt Pending Register"),
    0x000A: ("TIMER1", "volatile uint16_t", "SFR 0x0A: Hardware Timer 1 (16-bit free running)"),
    0x000C: ("TIMER2", "volatile uint16_t", "SFR 0x0C: Hardware Timer 2 / Event Counter"),
    0x0012: ("INT_PEND1", "volatile uint8_t", "SFR 0x12: Interrupt Pending 1 Register"),
    0x0013: ("INT_MASK1", "volatile uint8_t", "SFR 0x13: Interrupt Mask 1 Register"),
    0x0014: ("WSR", "volatile uint8_t", "SFR 0x14: Window Select Register"),
    0x0015: ("IOS0", "volatile uint8_t", "SFR 0x15: Input/Output Status 0 Register"),
    0x0016: ("IOS1", "volatile uint8_t", "SFR 0x16: Input/Output Status 1 Register"),
    0x0018: ("SP", "uint16_t*", "SFR 0x18: System Stack Pointer"),
    0xF000: ("GATE_ARRAY_CTRL", "volatile uint8_t*", "MMIO 0xF000: CPU Gate Array strobe/pulse latch"),
    0xF006: ("DSP_DATA_LATCH", "volatile uint8_t*", "MMIO 0xF006: Fujitsu MB87422/24 DSP data port"),
    0xF008: ("DSP_ADDR_LATCH", "volatile uint8_t*", "MMIO 0xF008: Fujitsu MB87422/24 DSP address/control"),
    0xD018: ("VDP_VRAM_DATA", "volatile uint8_t*", "MMIO 0xD018: Roland RFSC16A VDP VRAM data port"),
    0xD034: ("VDP_ADDR_LO", "volatile uint8_t*", "MMIO 0xD034: VDP VRAM 17-bit pointer (low byte)"),
    0xD036: ("VDP_ADDR_HI", "volatile uint8_t*", "MMIO 0xD036: VDP VRAM 17-bit pointer (high byte)"),
    0xE000: ("FDC_STATUS_CMD", "volatile uint8_t*", "MMIO 0xE000: uPD72068 FDC status/command / SED1335 LCD"),
    0xE002: ("FDC_FIFO_DATA", "volatile uint8_t*", "MMIO 0xE002: uPD72068 FDC FIFO / SED1335 LCD data"),
    0xE400: ("SPC_BDID", "volatile uint8_t*", "MMIO 0xE400: MB89352A SCSI Bus Device ID"),
}


@dataclass
class AsmInstruction:
    line_number: int
    label: Optional[str]
    mnemonic: str
    operands: str
    file_offset: int
    raw_bytes: str
    text_line: str


@dataclass
class BasicBlock:
    id: int
    label: str
    instructions: List[AsmInstruction] = field(default_factory=list)
    successors: List[Tuple[int, str]] = field(default_factory=list)  # (block_id, condition/kind)
    predecessors: List[int] = field(default_factory=list)


def parse_routine_asm(asm_path: Path) -> Tuple[dict, List[AsmInstruction]]:
    metadata = {
        "name": asm_path.stem,
        "page": 0,
        "org": 0,
        "file_offset": 0,
        "evidence": ""
    }
    instructions = []

    content = asm_path.read_text(encoding='utf-8')
    current_label = None

    for line_idx, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue

        # Parse header metadata
        if stripped.startswith(";"):
            if "Page:" in stripped and "Logical Start:" in stripped:
                m = re.search(r'Page:\s*(0x[0-9a-fA-F]+)', stripped)
                if m: metadata["page"] = int(m.group(1), 16)
                m = re.search(r'Logical Start:\s*(0x[0-9a-fA-F]+)', stripped)
                if m: metadata["org"] = int(m.group(1), 16)
            elif "File Offset:" in stripped:
                m = re.search(r'File Offset:\s*(0x[0-9a-fA-F]+)', stripped)
                if m: metadata["file_offset"] = int(m.group(1), 16)
            elif "Evidence:" in stripped:
                metadata["evidence"] = stripped.split("Evidence:", 1)[1].strip()
            continue

        # Directives
        if stripped.startswith("."):
            continue

        # Labels
        if stripped.endswith(":") and not ";" in stripped:
            current_label = stripped[:-1].strip()
            continue

        # Instruction with machine byte comment: MNEMONIC [OPERANDS] ; [OFFSET: BYTES]
        m = re.match(r'^(?:([a-zA-Z0-9_]+):\s*)?([A-Z0-9]+)(?:\s+([^;]+))?\s*;\s*\[([0-9a-fA-F]+):\s*([0-9a-fA-F\s]+)\]', stripped)
        if m:
            label = m.group(1) or current_label
            current_label = None
            mnemonic = m.group(2).upper()
            operands = (m.group(3) or "").strip()
            file_off = int(m.group(4), 16)
            raw_hex = m.group(5).replace(" ", "").upper()

            instructions.append(AsmInstruction(
                line_number=line_idx,
                label=label,
                mnemonic=mnemonic,
                operands=operands,
                file_offset=file_off,
                raw_bytes=raw_hex,
                text_line=line
            ))

    return metadata, instructions


def build_control_flow_graph(instructions: List[AsmInstruction]) -> List[BasicBlock]:
    """Divides routine instructions into basic blocks and connects CFG edges."""
    if not instructions:
        return []

    # Step 1: Identify leader instructions
    leaders: Set[int] = {0}
    label_to_index: Dict[str, int] = {}

    for idx, ins in enumerate(instructions):
        if ins.label:
            label_to_index[ins.label] = idx

    for idx, ins in enumerate(instructions):
        mnem = ins.mnemonic
        # Branch / jump / call targets are leaders
        if mnem.startswith("J") or mnem in ("SJMP", "LJMP", "DJNZ", "DJNZW", "SCALL", "LCALL"):
            # Target operand
            parts = [p.strip() for p in ins.operands.split(",")]
            target_label = parts[-1]
            if target_label in label_to_index:
                leaders.add(label_to_index[target_label])
            # Next instruction after a jump/branch/call is also a leader
            if idx + 1 < len(instructions):
                leaders.add(idx + 1)
        elif mnem in ("RET", "RETI", "TRAP", "RST"):
            if idx + 1 < len(instructions):
                leaders.add(idx + 1)

    sorted_leaders = sorted(leaders)
    blocks: List[BasicBlock] = []
    index_to_block: Dict[int, int] = {}

    for b_id, start_idx in enumerate(sorted_leaders):
        end_idx = sorted_leaders[b_id + 1] if b_id + 1 < len(sorted_leaders) else len(instructions)
        block_ins = instructions[start_idx:end_idx]
        block_label = block_ins[0].label or f"bb_{start_idx:04X}"
        block = BasicBlock(id=b_id, label=block_label, instructions=block_ins)
        blocks.append(block)
        for i in range(start_idx, end_idx):
            index_to_block[i] = b_id

    # Step 2: Connect edges
    for b_id, block in enumerate(blocks):
        last_ins = block.instructions[-1]
        mnem = last_ins.mnemonic
        last_idx = instructions.index(last_ins)
        parts = [p.strip() for p in last_ins.operands.split(",")] if last_ins.operands else []

        if mnem in ("SJMP", "LJMP"):
            target_label = parts[-1]
            if target_label in label_to_index:
                dest_b = index_to_block[label_to_index[target_label]]
                block.successors.append((dest_b, "unconditional"))
                blocks[dest_b].predecessors.append(b_id)
        elif mnem.startswith("J") or mnem in ("DJNZ", "DJNZW"):
            target_label = parts[-1]
            if target_label in label_to_index:
                dest_b = index_to_block[label_to_index[target_label]]
                cond_kind = "branch_true"
                block.successors.append((dest_b, cond_kind))
                blocks[dest_b].predecessors.append(b_id)
            if last_idx + 1 < len(instructions):
                fallthrough_b = index_to_block[last_idx + 1]
                block.successors.append((fallthrough_b, "branch_false"))
                blocks[fallthrough_b].predecessors.append(b_id)
        elif mnem in ("RET", "RETI", "TRAP", "RST"):
            pass  # Terminal block, no fallthrough
        else:
            # Normal instruction fallthrough
            if last_idx + 1 < len(instructions):
                fallthrough_b = index_to_block[last_idx + 1]
                block.successors.append((fallthrough_b, "fallthrough"))
                blocks[fallthrough_b].predecessors.append(b_id)

    return blocks


def annotate_operand(operand: str) -> str:
    """Replaces raw MMIO / SFR addresses with verified architectural symbols."""
    text = operand
    for addr, (sym, ctype, desc) in HARDWARE_EQUATES.items():
        # Match only address operands, not immediate values prefixed with '#'
        pattern = re.compile(rf'(?<![#0-9a-zA-Z_])0x{addr:04X}(?![0-9a-zA-Z_])', re.IGNORECASE)
        text = pattern.sub(sym, text)
        if addr < 0x100:
            pattern_short = re.compile(rf'(?<![#0-9a-zA-Z_])0x{addr:02X}(?![0-9a-zA-Z_])', re.IGNORECASE)
            text = pattern_short.sub(sym, text)
    return text


def instruction_to_expression(ins: AsmInstruction) -> str:
    """Translates an MCS-96 instruction to a readable C-like expression."""
    mnem = ins.mnemonic
    ops = [p.strip() for p in ins.operands.split(",")] if ins.operands else []
    annotated_ops = [annotate_operand(op) for op in ops]

    if mnem == "NOP":
        return "/* nop */;"
    elif mnem == "DI":
        return "__disable_interrupts();"
    elif mnem == "EI":
        return "__enable_interrupts();"
    elif mnem == "PUSHA":
        return "__push_all();"
    elif mnem == "POPA":
        return "__pop_all();"
    elif mnem in ("RET", "RETI"):
        return "return;"
    elif mnem == "PUSH":
        return f"*(--SP) = {annotated_ops[0]};"
    elif mnem == "POP":
        return f"{annotated_ops[0]} = *(SP++);"
    elif mnem in ("LD", "LDB"):
        if len(ops) >= 2:
            cast = "(uint8_t)" if mnem == "LDB" else ""
            return f"{annotated_ops[0]} = {cast}{annotated_ops[1]};"
    elif mnem in ("ST", "STB"):
        if len(ops) >= 2:
            return f"{annotated_ops[1]} = {annotated_ops[0]};"
    elif mnem in ("ADD", "ADDB"):
        if len(ops) == 2:
            return f"{annotated_ops[0]} += {annotated_ops[1]};"
        elif len(ops) >= 3:
            return f"{annotated_ops[0]} = {annotated_ops[1]} + {annotated_ops[2]};"
    elif mnem in ("SUB", "SUBB"):
        if len(ops) == 2:
            return f"{annotated_ops[0]} -= {annotated_ops[1]};"
        elif len(ops) >= 3:
            return f"{annotated_ops[0]} = {annotated_ops[1]} - {annotated_ops[2]};"
    elif mnem in ("AND", "ANDB"):
        if len(ops) == 2:
            return f"{annotated_ops[0]} &= {annotated_ops[1]};"
        elif len(ops) >= 3:
            return f"{annotated_ops[0]} = {annotated_ops[1]} & {annotated_ops[2]};"
    elif mnem in ("OR", "ORB"):
        if len(ops) == 2:
            return f"{annotated_ops[0]} |= {annotated_ops[1]};"
        elif len(ops) >= 3:
            return f"{annotated_ops[0]} = {annotated_ops[1]} | {annotated_ops[2]};"
    elif mnem in ("XOR", "XORB"):
        if len(ops) == 2:
            return f"{annotated_ops[0]} ^= {annotated_ops[1]};"
        elif len(ops) >= 3:
            return f"{annotated_ops[0]} = {annotated_ops[1]} ^ {annotated_ops[2]};"
    elif mnem in ("SHL", "SHLB"):
        return f"{annotated_ops[0]} <<= {annotated_ops[1]};"
    elif mnem in ("SHR", "SHRB"):
        return f"{annotated_ops[0]} >>= {annotated_ops[1]};"
    elif mnem in ("INC", "INCB"):
        return f"{annotated_ops[0]}++;"
    elif mnem in ("DEC", "DECB"):
        return f"{annotated_ops[0]}--;"
    elif mnem in ("CLR", "CLRB"):
        return f"{annotated_ops[0]} = 0;"
    elif mnem in ("CMP", "CMPB"):
        return f"/* compare */ flags = ({annotated_ops[0]} - {annotated_ops[1]});"
    elif mnem in ("SJMP", "LJMP"):
        return f"goto {annotated_ops[0]};"
    elif mnem in ("SCALL", "LCALL"):
        return f"{annotated_ops[0]}();"
    elif mnem == "JE":
        return f"if (EQUAL) goto {annotated_ops[0]};"
    elif mnem == "JNE":
        return f"if (!EQUAL) goto {annotated_ops[0]};"
    elif mnem == "JC":
        return f"if (CARRY) goto {annotated_ops[0]};"
    elif mnem == "JNC":
        return f"if (!CARRY) goto {annotated_ops[0]};"
    elif mnem in ("JGT", "JGE", "JLT", "JLE"):
        cond = mnem[1:]
        return f"if ({cond}) goto {annotated_ops[0]};"
    elif mnem == "JBS":
        return f"if ({annotated_ops[0]} & (1 << {annotated_ops[1]})) goto {annotated_ops[2]};"
    elif mnem == "JBC":
        return f"if (!({annotated_ops[0]} & (1 << {annotated_ops[1]}))) goto {annotated_ops[2]};"
    elif mnem in ("DJNZ", "DJNZW"):
        return f"if (--{annotated_ops[0]} != 0) goto {annotated_ops[1]};"

    return f"/* {mnem} {', '.join(annotated_ops)} */;"


def decompile_routine(asm_path: Path) -> dict:
    """Decompiles a routine assembly file into a structured view."""
    meta, instructions = parse_routine_asm(asm_path)
    blocks = build_control_flow_graph(instructions)

    decompiled_blocks = []
    used_hardware: Dict[str, dict] = {}

    for b in blocks:
        block_exprs = []
        for ins in b.instructions:
            expr = instruction_to_expression(ins)
            # Scan for hardware equates used
            for addr, (sym, ctype, desc) in HARDWARE_EQUATES.items():
                if sym in expr and sym not in used_hardware:
                    used_hardware[sym] = {
                        "address": f"0x{addr:04X}",
                        "type": ctype,
                        "description": desc
                    }

            block_exprs.append({
                "line": ins.line_number,
                "file_offset": f"0x{ins.file_offset:06X}",
                "bytes": ins.raw_bytes,
                "asm": f"{ins.mnemonic:<8} {ins.operands}".strip(),
                "expr": expr
            })

        decompiled_blocks.append({
            "block_id": b.id,
            "label": b.label,
            "instructions_count": len(b.instructions),
            "predecessors": [f"bb_{p:02d}" for p in b.predecessors],
            "successors": [{"target": f"bb_{s[0]:02d}", "condition": s[1]} for s in b.successors],
            "expressions": block_exprs
        })

    return {
        "routine": meta["name"],
        "page": f"0x{meta['page']:02X}",
        "org": f"0x{meta['org']:04X}",
        "file_offset": f"0x{meta['file_offset']:06X}",
        "evidence": meta["evidence"],
        "blocks_count": len(blocks),
        "instructions_count": len(instructions),
        "hardware_symbols": used_hardware,
        "control_flow_graph": decompiled_blocks
    }


def generate_pseudocode_c(view: dict) -> str:
    """Formats the decompiled routine as a readable pseudocode C-like file."""
    lines = [
        NON_COMPILABLE_HEADER,
        f"// Routine:     {view['routine']}",
        f"// Memory Org:  Page {view['page']}, Address {view['org']}",
        f"// File Offset: {view['file_offset']}",
        f"// Evidence:    {view['evidence']}",
        "// ==============================================================================",
        ""
    ]

    # Declarations of accessed hardware registers
    if view["hardware_symbols"]:
        lines.append("// Hardware MMIO & SFR Declarations")
        for sym, info in view["hardware_symbols"].items():
            lines.append(f"extern {info['type']:<22} {sym}; // {info['address']}: {info['description']}")
        lines.append("")

    lines.append(f"void fn_{view['routine']}(void)")
    lines.append("{")

    for block in view["control_flow_graph"]:
        lines.append(f"  {block['label']}:")
        for expr_data in block["expressions"]:
            file_off = expr_data["file_offset"]
            raw_hex = expr_data["bytes"]
            asm = expr_data["asm"]
            expr = expr_data["expr"]
            lines.append(f"    {expr:<42} // [{file_off}: {raw_hex:<10}] {asm}")
        lines.append("")

    lines.append("}")
    return '\n'.join(lines) + '\n'


def decompile_project(project_dir: Path, output_dir: Path):
    """Decompiles all routines in a project directory."""
    src_dir = project_dir / "src"
    if not src_dir.exists():
        raise FileNotFoundError(f"Project src directory {src_dir} missing")

    output_dir.mkdir(parents=True, exist_ok=True)
    asm_files = sorted(src_dir.glob("*.asm"))

    index = []
    for asm_path in asm_files:
        view = decompile_routine(asm_path)

        # Save structured JSON
        json_path = output_dir / f"{asm_path.stem}.json"
        json_path.write_text(json.dumps(view, indent=2), encoding='utf-8')

        # Save readable pseudocode
        c_path = output_dir / f"{asm_path.stem}.pseudocode.c"
        c_path.write_text(generate_pseudocode_c(view), encoding='utf-8')

        index.append({
            "routine": view["routine"],
            "blocks": view["blocks_count"],
            "instructions": view["instructions_count"],
            "hardware_symbols": list(view["hardware_symbols"].keys()),
            "json_view": json_path.name,
            "pseudocode_view": c_path.name
        })

    (output_dir / "index.json").write_text(json.dumps({
        "project": project_dir.name,
        "routines_count": len(index),
        "routines": index
    }, indent=2), encoding='utf-8')
    print(f"[+] Successfully decompiled {len(index)} routines from {project_dir.name} into {output_dir}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, help="Firmware source project (e.g. firmware_source/os_disk)")
    parser.add_argument("--routine", type=Path, help="Single routine .asm file")
    parser.add_argument("--output", type=Path, required=True, help="Output directory for decompiler views")
    args = parser.parse_args()

    if args.project:
        decompile_project(args.project, args.output)
    elif args.routine:
        args.output.mkdir(parents=True, exist_ok=True)
        view = decompile_routine(args.routine)
        (args.output / f"{args.routine.stem}.json").write_text(json.dumps(view, indent=2), encoding='utf-8')
        (args.output / f"{args.routine.stem}.pseudocode.c").write_text(generate_pseudocode_c(view), encoding='utf-8')
        print(f"[+] Decompiled {args.routine.name} to {args.output}")
    else:
        parser.error("Specify either --project or --routine")


if __name__ == "__main__":
    main()

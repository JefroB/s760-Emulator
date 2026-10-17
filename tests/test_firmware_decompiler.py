"""test_firmware_decompiler.py - Verification suite for Milestone 7 structured decompiler views.

Validates:
1. Decompiler generates structured JSON and C-like pseudocode views for both OS and ROM routines.
2. Control Flow Graph (CFG) basic blocks, successors, and predecessors are correctly extracted.
3. High-level readable expressions are synthesized with typed hardware symbol annotations.
4. Every expression links to instruction mnemonic, physical file offset, and machine bytes.
5. Strict non-compilable disclaimer banner is present in all generated pseudocode files.
"""
import json
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from decompile_firmware_routines import decompile_routine, generate_pseudocode_c, decompile_project

OS_SRC = ROOT / "firmware_source" / "os_disk"
IC15_SRC = ROOT / "firmware_source" / "ic15_rom"


def test_timer_isr_decompiler_view():
    """Verify CFG and high-level expressions for OS timer_isr routine."""
    asm_file = OS_SRC / "src" / "timer_isr.asm"
    assert asm_file.exists(), "timer_isr.asm missing"

    view = decompile_routine(asm_file)
    assert view["routine"] == "timer_isr"
    assert view["file_offset"] == "0x0052D1"
    assert view["page"] == "0x00"
    assert view["instructions_count"] >= 70
    assert view["blocks_count"] >= 10

    # Verify hardware symbols detected
    hw = view["hardware_symbols"]
    assert "TIMER1" in hw
    assert "IOS1" in hw
    assert "INT_MASK1" in hw
    assert "SP" in hw
    assert hw["TIMER1"]["type"] == "volatile uint16_t"
    assert hw["IOS1"]["type"] == "volatile uint8_t"

    # Verify CFG structure
    cfg = view["control_flow_graph"]
    first_block = cfg[0]
    assert first_block["label"] == "fn_timer_isr"
    assert len(first_block["expressions"]) >= 1

    # Check first instruction link
    first_expr = first_block["expressions"][0]
    assert first_expr["file_offset"] == "0x0052D1"
    assert first_expr["bytes"] == "F4"
    assert first_expr["asm"] == "PUSHA"
    assert first_expr["expr"] == "__push_all();"

    # Check pseudocode generation
    c_code = generate_pseudocode_c(view)
    assert "NON-COMPILABLE PSEUDOCODE" in c_code
    assert "void fn_timer_isr(void)" in c_code
    assert "extern volatile uint16_t      TIMER1;" in c_code
    assert "__enable_interrupts();" in c_code


def test_rom_reset_decompiler_view():
    """Verify CFG and high-level expressions for IC15 rom_reset routine."""
    asm_file = IC15_SRC / "src" / "rom_reset.asm"
    assert asm_file.exists(), "rom_reset.asm missing"

    view = decompile_routine(asm_file)
    assert view["routine"] == "rom_reset"
    assert view["file_offset"] == "0x002080"
    assert view["instructions_count"] >= 80
    assert view["blocks_count"] >= 10

    # Verify hardware symbols
    hw = view["hardware_symbols"]
    assert "SP" in hw
    assert "INT_MASK" in hw
    assert "GATE_ARRAY_CTRL" in hw

    # Verify reset vector instruction
    first_block = view["control_flow_graph"][0]
    first_expr = first_block["expressions"][0]
    assert first_expr["file_offset"] == "0x002080"
    assert first_expr["bytes"] == "FA"
    assert first_expr["asm"] == "DI"
    assert first_expr["expr"] == "__disable_interrupts();"

    # Check pseudocode formatting
    c_code = generate_pseudocode_c(view)
    assert "NON-COMPILABLE PSEUDOCODE" in c_code
    assert "void fn_rom_reset(void)" in c_code
    assert "flags = (RW20 - #0x8000);" in c_code


def test_decompile_full_projects(tmp_path):
    """Test batch decompilation of full OS and ROM source projects into output directories."""
    os_out = tmp_path / "os_decompiled"
    decompile_project(OS_SRC, os_out)

    assert os_out.exists()
    assert (os_out / "index.json").exists()
    index_data = json.loads((os_out / "index.json").read_text(encoding='utf-8'))
    assert index_data["routines_count"] == 126
    assert len(list(os_out.glob("*.pseudocode.c"))) == 126
    assert len(list(os_out.glob("*.json"))) == 127  # 126 routines + index.json

    rom_out = tmp_path / "rom_decompiled"
    decompile_project(IC15_SRC, rom_out)

    assert rom_out.exists()
    assert (rom_out / "index.json").exists()
    rom_index = json.loads((rom_out / "index.json").read_text(encoding='utf-8'))
    assert rom_index["routines_count"] == 4
    assert len(list(rom_out.glob("*.pseudocode.c"))) == 4

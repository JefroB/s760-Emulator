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


@pytest.fixture
def synthetic_project(tmp_path):
    """Invented listing: test the view generator without redistributed firmware."""
    src = tmp_path / 'synthetic' / 'src'
    src.mkdir(parents=True)
    (src / 'example.asm').write_text('''; Page: 0x00, Logical Start: 0x4000
; File Offset: 0x001000
; Evidence: Synthetic parser/CFG fixture, not a firmware execution test.
fn_example:
    DI                   ; [001000: FA]
    LDB R20, IOS1        ; [001001: B0 16 20]
    JE loc_done          ; [001004: DF 01]
    EI                   ; [001006: FB]
loc_done:
    RET                  ; [001007: F0]
''', encoding='utf-8')
    return src.parent


def test_synthetic_decompiler_links_cfg_and_hardware(synthetic_project):
    view = decompile_routine(synthetic_project / 'src/example.asm')
    assert view['routine'] == 'example'
    assert view['instructions_count'] == 5
    assert view['blocks_count'] == 3
    blocks = view['control_flow_graph']
    assert {edge['target'] for edge in blocks[0]['successors']} == {'bb_01', 'bb_02'}
    assert set(blocks[2]['predecessors']) == {'bb_00', 'bb_01'}
    assert blocks[0]['expressions'][0]['file_offset'] == '0x001000'
    assert blocks[0]['expressions'][0]['bytes'] == 'FA'
    assert blocks[0]['expressions'][0]['expr'] == '__disable_interrupts();'
    assert view['hardware_symbols']['IOS1']['type'] == 'volatile uint8_t'
    code = generate_pseudocode_c(view)
    assert 'NON-COMPILABLE PSEUDOCODE' in code
    assert 'void fn_example(void)' in code
    assert '__enable_interrupts();' in code
    assert '0x001001: B01620' in code


def test_synthetic_project_exports_linked_views(synthetic_project, tmp_path):
    src = synthetic_project / 'src'
    (src / 'second.asm').write_bytes((src / 'example.asm').read_bytes())
    output = tmp_path / 'views'
    decompile_project(synthetic_project, output)
    index = json.loads((output / 'index.json').read_text(encoding='utf-8'))
    assert index['routines_count'] == 2
    for row in index['routines']:
        view = json.loads((output / row['json_view']).read_text(encoding='utf-8'))
        assert view['routine'] == row['routine']
        assert view['instructions_count'] == 5
        assert 'NON-COMPILABLE PSEUDOCODE' in (output / row['pseudocode_view']).read_text(encoding='utf-8')


@pytest.mark.skipif(not (OS_SRC / 'src/timer_isr.asm').is_file(), reason='Private exported OS routine required')
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


@pytest.mark.skipif(not (IC15_SRC / 'src/rom_reset.asm').is_file(), reason='Private exported boot-ROM routine required')
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


@pytest.mark.skipif(not all((p / 'src').is_dir() for p in (OS_SRC, IC15_SRC)),
                    reason='Private exported OS and boot-ROM projects required')
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

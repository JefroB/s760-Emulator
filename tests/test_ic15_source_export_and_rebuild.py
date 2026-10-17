"""test_ic15_source_export_and_rebuild.py - Automated verification of IC15 boot ROM source round-trip.

Tests:
1. IC15 source project structure validation.
2. Routine assembly file formatting and instruction parsing for IC15.
3. Byte-exact ROM binary reconstruction matching original SHA256 (0 diffs).
4. Source-level instruction modification producing exact 1-byte diff at reset vector.
5. Strict rejection of invalid mnemonics and out-of-bounds layout writes.
"""

import hashlib
import json
import shutil
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_firmware_image import build_image

IC15_PROJECT_DIR = ROOT / "firmware_source" / "ic15_rom"
ORIGINAL_ROM = ROOT / "roms" / "BOOT" / "Roland_S-760_v1.11.BIN"
EXPECTED_SHA256 = 'ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6'
EXPECTED_ROM_SIZE = 32768


pytestmark = pytest.mark.skipif(
    not (IC15_PROJECT_DIR / "data").is_dir(),
    reason="Local firmware export data required; run the source exporter with private firmware",
)

def test_ic15_project_structure_exists():
    """Verify that the exported IC15 source project has layout, include, src, and data directories."""
    assert IC15_PROJECT_DIR.exists(), f"Source project {IC15_PROJECT_DIR} missing"
    assert (IC15_PROJECT_DIR / "layout.json").exists(), "layout.json missing"
    assert (IC15_PROJECT_DIR / "include" / "s760_registers.inc").exists(), "s760_registers.inc missing"
    assert (IC15_PROJECT_DIR / "src").exists(), "src directory missing"
    assert (IC15_PROJECT_DIR / "data").exists(), "data directory missing"


def test_ic15_routine_assembly_files_validity():
    """Verify that IC15 routine assembly files contain valid directives and machine byte comments."""
    asm_files = list((IC15_PROJECT_DIR / "src").glob("*.asm"))
    assert len(asm_files) == 4, f"Expected 4 routine files, found {len(asm_files)}"

    reset_asm = IC15_PROJECT_DIR / "src" / "rom_reset.asm"
    assert reset_asm.exists()
    content = reset_asm.read_text(encoding='utf-8')
    assert "fn_rom_reset:" in content
    assert ".page 0x780" in content
    assert ".org 0x2080" in content
    assert ".file_offset 0x002080" in content
    assert "DI" in content


def test_ic15_byte_exact_round_trip(tmp_path):
    """Build the IC15 ROM from source into a temporary directory and verify byte-exact SHA256 match."""
    output_bin = tmp_path / "rebuilt_ic15_test.BIN"
    success = build_image(IC15_PROJECT_DIR, output_bin)
    assert success is True, "Build image did not report round trip success"
    assert output_bin.exists(), "Rebuilt ROM file was not created"

    rebuilt_bytes = output_bin.read_bytes()
    assert len(rebuilt_bytes) == EXPECTED_ROM_SIZE, f"Expected {EXPECTED_ROM_SIZE} bytes, got {len(rebuilt_bytes)}"

    rebuilt_hash = hashlib.sha256(rebuilt_bytes).hexdigest()
    assert rebuilt_hash == EXPECTED_SHA256, f"Rebuilt hash {rebuilt_hash} != expected {EXPECTED_SHA256}"


def test_ic15_source_modification_produces_modified_image(tmp_path):
    """Test modifying one instruction in rom_reset.asm (DI -> NOP) and verifying exact 1-byte diff."""
    project_copy = tmp_path / "modified_ic15_project"
    shutil.copytree(IC15_PROJECT_DIR, project_copy)

    target_asm = project_copy / "src" / "rom_reset.asm"
    lines = target_asm.read_text(encoding='utf-8').splitlines()

    modified = False
    for i, line in enumerate(lines):
        if "DI" in line and "[002080: FA]" in line:
            # Change instruction mnemonic from DI to NOP
            lines[i] = line.replace("DI", "NOP")
            modified = True
            break
    assert modified, "Target reset DI instruction line not found for modification"
    target_asm.write_text('\n'.join(lines), encoding='utf-8')

    output_bin = tmp_path / "modified_ic15.BIN"
    success = build_image(project_copy, output_bin)
    assert success is False, "Build should report modification present"

    mod_bytes = output_bin.read_bytes()
    orig_bytes = ORIGINAL_ROM.read_bytes()
    assert len(mod_bytes) == len(orig_bytes) == EXPECTED_ROM_SIZE

    diffs = [idx for idx in range(len(mod_bytes)) if mod_bytes[idx] != orig_bytes[idx]]
    assert diffs == [0x2080], f"Expected only offset 0x2080 to differ, got: {[hex(d) for d in diffs]}"
    assert orig_bytes[0x2080] == 0xFA  # DI opcode
    assert mod_bytes[0x2080] == 0xFD   # NOP opcode


def test_ic15_invalid_instruction_is_rejected(tmp_path):
    """Test that invalid mnemonics are rejected during IC15 ROM build."""
    project_copy = tmp_path / "invalid_ic15_project"
    shutil.copytree(IC15_PROJECT_DIR, project_copy)

    target_asm = project_copy / "src" / "rom_reset.asm"
    content = target_asm.read_text(encoding='utf-8')
    target_asm.write_text(content.replace("DI", "NOT_AN_INSTRUCTION"), encoding='utf-8')

    with pytest.raises(ValueError):
        build_image(project_copy, tmp_path / "invalid_ic15.BIN")


def test_ic15_out_of_bounds_write_is_rejected(tmp_path):
    """Test that out-of-bounds writes (exceeding 32KB extent) are rejected during IC15 ROM build."""
    project_copy = tmp_path / "oob_ic15_project"
    shutil.copytree(IC15_PROJECT_DIR, project_copy)

    target_asm = project_copy / "src" / "rom_reset.asm"
    content = target_asm.read_text(encoding='utf-8')
    # Change comment offset from 002080 to 008010 (outside 32768 = 0x8000 extent)
    target_asm.write_text(content.replace("[002080: FA]", "[008010: FD]"), encoding='utf-8')

    with pytest.raises(ValueError):
        build_image(project_copy, tmp_path / "oob_ic15.BIN")

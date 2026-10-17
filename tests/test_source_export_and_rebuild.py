"""test_source_export_and_rebuild.py - Automated verification of editable source project round-trip.

Tests:
1. Source export and directory structure validation.
2. Routine assembly file formatting and instruction parsing.
3. Byte-exact disk image reconstruction matching original SHA256 (0 diffs).
"""

import hashlib
import json
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_firmware_image import build_image

ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "firmware_source" / "os_disk"
ORIGINAL_IMG = ROOT / "S760224.IMG"
EXPECTED_SHA256 = '3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd'


pytestmark = pytest.mark.skipif(
    not (PROJECT_DIR / "data").is_dir(),
    reason="Local firmware export data required; run the source exporter with private firmware",
)

def test_project_structure_exists():
    """Verify that the exported source project has layout, include, src, and data directories."""
    assert PROJECT_DIR.exists(), f"Source project {PROJECT_DIR} missing"
    assert (PROJECT_DIR / "layout.json").exists(), "layout.json missing"
    assert (PROJECT_DIR / "include" / "s760_registers.inc").exists(), "s760_registers.inc missing"
    assert (PROJECT_DIR / "src").exists(), "src directory missing"
    assert (PROJECT_DIR / "data").exists(), "data directory missing"


def test_routine_assembly_files_validity():
    """Verify that routine assembly files contain valid directives and machine byte comments."""
    asm_files = list((PROJECT_DIR / "src").glob("*.asm"))
    assert len(asm_files) >= 126, f"Expected >= 126 routine files, found {len(asm_files)}"

    # Check sample routine mouse_handshake.asm
    mouse_asm = PROJECT_DIR / "src" / "mouse_handshake.asm"
    assert mouse_asm.exists()
    content = mouse_asm.read_text(encoding='utf-8')
    assert "fn_mouse_handshake:" in content
    assert ".page 0x4B" in content
    assert "PUSHA" in content
    assert "POPA" in content


def test_byte_exact_round_trip(tmp_path):
    """Build the image from source into a temporary directory and verify SHA256 match."""
    output_img = tmp_path / "rebuilt_test.IMG"
    success = build_image(PROJECT_DIR, output_img)
    assert success is True, "Build image did not report round trip success"
    assert output_img.exists(), "Rebuilt image file was not created"

    rebuilt_bytes = output_img.read_bytes()
    assert len(rebuilt_bytes) == 1474560, f"Expected 1,474,560 bytes, got {len(rebuilt_bytes)}"

    rebuilt_hash = hashlib.sha256(rebuilt_bytes).hexdigest()
    assert rebuilt_hash == EXPECTED_SHA256, f"Rebuilt hash {rebuilt_hash} != expected {EXPECTED_SHA256}"


def test_source_modification_produces_modified_image(tmp_path):
    """Test modifying one source file in a temporary project copy and verifying precise diff."""
    import shutil
    project_copy = tmp_path / "modified_project"
    shutil.copytree(PROJECT_DIR, project_copy)

    # Modify one instruction in timer_isr.asm (change PUSHA to NOP)
    target_asm = project_copy / "src" / "timer_isr.asm"
    lines = target_asm.read_text(encoding='utf-8').splitlines()

    # Replace PUSHA [0052D1: F4] with NOP [0052D1: FD]
    modified = False
    for i, line in enumerate(lines):
        if "PUSHA" in line and "[0052D1: F4]" in line:
            lines[i] = "    NOP                                         ; [0052D1: FD]"
            modified = True
            break
    assert modified, "Target instruction line not found for modification"
    target_asm.write_text('\n'.join(lines), encoding='utf-8')

    # Build modified image
    output_img = tmp_path / "modified.IMG"
    success = build_image(project_copy, output_img)
    assert success is False, "Build should report modification present"

    mod_bytes = output_img.read_bytes()
    orig_bytes = ORIGINAL_IMG.read_bytes()
    assert len(mod_bytes) == len(orig_bytes) == 1474560

    # Diff should be exactly 1 byte at offset 0x0052D1
    diffs = [idx for idx in range(len(mod_bytes)) if mod_bytes[idx] != orig_bytes[idx]]
    assert diffs == [0x52D1], f"Expected only offset 0x52D1 to differ, got: {[hex(d) for d in diffs]}"
    assert orig_bytes[0x52D1] == 0xF4
    assert mod_bytes[0x52D1] == 0xFD

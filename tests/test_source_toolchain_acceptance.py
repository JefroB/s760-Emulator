"""Source-toolchain acceptance test suite.

Validates that:
- BUG-088: Source instruction mnemonics determine encoding, and invalid mnemonics are rejected.
- BUG-089: Conflicting physical alias writes and out-of-bounds layout writes are strictly rejected.
"""
from pathlib import Path
import shutil
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_firmware_image import build_image


@pytest.fixture
def project(tmp_path):
    if not (ROOT / 'firmware_source/os_disk/data').is_dir():
        pytest.skip('Local OS firmware export data required')
    target = tmp_path / 'project'
    shutil.copytree(ROOT / 'firmware_source/os_disk', target)
    return target


def test_mnemonic_only_edit_encodes_new_instruction(project, tmp_path):
    source = project / 'src/timer_isr.asm'
    text = source.read_text(encoding='utf-8')
    line = next(l for l in text.splitlines() if 'PUSHA' in l and '[0052D1: F4]' in l)
    source.write_text(text.replace(line, line.replace('PUSHA', 'NOP')), encoding='utf-8')
    output = tmp_path / 'edited.IMG'
    build_image(project, output)
    before, after = (ROOT / 'S760224.IMG').read_bytes(), output.read_bytes()
    assert len(before) == len(after)
    assert [i for i, (a, b) in enumerate(zip(before, after)) if a != b] == [0x52d1]
    assert after[0x52d1] == 0xfd


def test_invalid_instruction_is_rejected(project, tmp_path):
    source = project / 'src/timer_isr.asm'
    source.write_text(source.read_text(encoding='utf-8').replace('PUSHA', 'NOT_AN_INSTRUCTION'), encoding='utf-8')
    with pytest.raises(ValueError):
        build_image(project, tmp_path / 'invalid.IMG')


def test_conflicting_physical_alias_edit_is_rejected(project, tmp_path):
    source = project / 'src/frontier_p3b_6294.asm'
    text = source.read_text(encoding='utf-8')
    import re
    offset = 87886
    pattern = re.compile(r'(\[' + f'{offset:06X}' + r':\s*)([0-9A-F]{2})')
    assert pattern.search(text)
    source.write_text(pattern.sub(lambda m: m[1] + f'{int(m[2],16)^1:02X}', text), encoding='utf-8')
    with pytest.raises(ValueError):
        build_image(project, tmp_path / 'alias-conflict.IMG')


def test_out_of_bounds_write_is_rejected(project, tmp_path):
    source = project / 'src/timer_isr.asm'
    text = source.read_text(encoding='utf-8')
    assert '[0052D1: F4]' in text
    source.write_text(text.replace('[0052D1: F4]', '[168010: FD]'), encoding='utf-8')
    with pytest.raises(ValueError):
        build_image(project, tmp_path / 'out-of-bounds.IMG')

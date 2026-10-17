import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('ic15_export', Path(__file__).resolve().parents[1] / 'scripts/ghidra/export_ic15_contexts.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_resource_view_wraps_at_actual_rom_mirror():
    rom = bytes(i // 0x1000 for i in range(0x8000))
    data = module.view_bytes(rom, 0x798, 0x8000)
    assert data[:0x2000] == rom[0x6000:]
    assert data[0x2000:] == rom[:0x2000]


def test_fetch_views_do_not_shift_entry_addresses():
    rom = bytes(i // 0x1000 for i in range(0x8000))
    assert module.view_bytes(rom, 0x780, 0) == rom[:0x4000]
    assert module.view_bytes(rom, 0x790, 0x4000) == rom[0x4000:]


@pytest.mark.parametrize('page,base', [(0x3f0,0x4000), (0x780,0x2080)])
def test_unqualified_context_is_rejected(page,base):
    with pytest.raises(ValueError):
        module.view_bytes(bytes(0x8000),page,base)


def test_output_cannot_contain_original_inputs(tmp_path):
    source = tmp_path / 'input.bin'
    source.write_bytes(bytes(0x8000))
    with pytest.raises(ValueError,match='contain either input'):
        module.export(source,tmp_path/'manifest.json',tmp_path)
    assert source.read_bytes() == bytes(0x8000)

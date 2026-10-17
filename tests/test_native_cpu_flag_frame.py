"""Isolated CPU fixture: validates ISA frames, not original firmware behavior."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_native_flags_accept_rom_style_manual_frame(tmp_path):
    if not all((ROOT / p).is_file() for p in ('mame-source/mames760.exe', 'roms/System/S760224.IMG')):
        pytest.skip('Local native CPU executable and audited OS fixture required')
    state = tmp_path / 'isolated-cpu'
    p = subprocess.run([sys.executable, str(ROOT / 'scripts/verify_native_cpu_flags.py'),
                        '--state-dir', str(state)], cwd=ROOT, text=True, capture_output=True, timeout=90)
    assert p.returncode == 0, p.stdout + p.stderr
    result = json.loads((state / 'result.json').read_text())
    assert result['passed'] and result['manual_frame']
    assert result['saved_extension'] == 0x450e
    assert result['wsr'] == 0x0e and result['mask1'] == 0x45
    assert result['interrupts'] is False

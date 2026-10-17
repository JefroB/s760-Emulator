"""Actual CPU execution timing against documented KB state times."""
import json
from pathlib import Path
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_native_kb_control_and_stack_state_times(tmp_path):
    if not all((ROOT / p).is_file() for p in ('mame-source/mames760.exe', 'roms/System/S760224.IMG')):
        pytest.skip('Local native executable and private OS fixture required')
    state = tmp_path / 'cpu-control-times'
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/verify_native_cpu_control_times.py'),
                             '--state-dir', str(state)], cwd=ROOT, capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads((state / 'result.json').read_text())
    assert data['passed'] and len(data['results']) == 50
    assert not data['failures']
    assert all(v['stack_balanced'] for v in data['results'])

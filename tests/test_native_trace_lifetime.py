"""Removed diagnostic taps must not retain themselves through Lua callbacks."""
import os
from pathlib import Path
import re
import subprocess
import sys
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from s760_runtime import NativeRuntime, RuntimeConfig


def test_removed_bus_trace_taps_are_collectible(tmp_path):
    exe = Path(os.environ.get('S760_MAME_EXE', ROOT / 'mame-source/mames760.exe'))
    rom = ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN'
    disk = ROOT / 'roms/System/S760224.IMG'
    if not all(p.is_file() for p in (exe, rom, disk)):
        pytest.skip('Native MAME and local firmware required')

    source = (ROOT / 'scripts/s760_runtime.lua').read_text(encoding='utf-8')
    # Weak keys observe actual tap lifetime without extending it. Collection
    # runs only after removal, outside memory callbacks, and changes no guest state.
    assert source.count('    return trace\n') == 1
    assert source.count('            bus_trace = nil\n') == 1
    source = 'local retired_taps=setmetatable({}, {__mode="k"})\n' + source
    source = source.replace('    return trace\n',
                            '    retired_taps[trace.read]=true\n'
                            '    retired_taps[trace.write]=true\n'
                            '    return trace\n', 1)
    source = source.replace('            bus_trace = nil\n',
                            '            bus_trace = nil\n'
                            '            collectgarbage("collect")\n'
                            '            collectgarbage("collect")\n'
                            '            local retained=0\n'
                            '            for _ in pairs(retired_taps) do retained=retained+1 end\n'
                            '            print("[RETAINED-TAPS] "..retained)\n', 1)
    observer = tmp_path / 'lifetime.lua'
    observer.write_text(source + '\nemu.pause()\n', encoding='utf-8')
    launch = subprocess.Popen

    def observed_launch(command, **kwargs):
        command = list(command)
        command[command.index('-autoboot_script') + 1] = str(observer)
        return launch(command, **kwargs)

    cfg = RuntimeConfig(exe, rom, disk, tmp_path / 'state', sound=False, throttle=False)
    with patch('s760_runtime.subprocess.Popen', observed_launch), NativeRuntime(cfg) as runtime:
        runtime.request('pause')
        for _ in range(12):
            runtime.request('bus_trace', enabled=True, first=0x101030, last=0x101031)
            trace, _ = runtime.request('bus_trace', enabled=False)
            assert trace['rows'] == [] and trace['dropped'] == 0
    log = (cfg.state_dir / 'runtime.log').read_text(encoding='utf-8')
    assert 'LUA ERROR' not in log.upper(), log
    retained = [int(v) for v in re.findall(r'\[RETAINED-TAPS\] (\d+)', log)]
    assert retained == [0] * 12, log

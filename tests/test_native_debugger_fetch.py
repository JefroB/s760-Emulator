"""BUG-085: debugger history must use instruction-fetch banks, not data banks."""
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]

OBSERVER = r'''
local machine=manager.machine
local cpu=machine.devices[':maincpu']
local program=cpu.spaces['program']
local debugger=assert(machine.debugger)
local observed=false
fetch_control_tap=program:install_read_tap(0x8904,0x8905,'debug-fetch-control',function(a,d,m)
 if observed or (m & 255)==0 or program:read_u16(0x10c)~=0x798 then return end
 observed=true
 print(string.format('[FETCH-CONTROL] fetch=%04x data=%04x',program:read_u16(0x102),program:read_u16(0x10a)))
 print(string.format('[DATA-BYTES] %02x %02x %02x',program:read_u8(0x4b1d),program:read_u8(0x4b1e),program:read_u8(0x4b1f)))
 local first=#debugger.consolelog
 debugger:command('history :maincpu,20')
 for line=first+1,#debugger.consolelog do print('[HISTORY] '..tostring(debugger.consolelog[line])) end
 if cpu.spaces['opcodes'] then
  local opcodes=cpu.spaces['opcodes']
  print(string.format('[FETCH-BYTES] %02x %02x %02x',opcodes:read_u8(0x4b1d),opcodes:read_u8(0x4b1e),opcodes:read_u8(0x4b1f)))
 end
end)
emu.register_frame_done(function() if observed then machine:exit() end end)
'''


def test_original_rom_history_uses_fetch_view(tmp_path):
    exe = Path(os.environ.get('S760_MAME_EXE', ROOT / 'mame-source/mames760.exe'))
    rom = ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN'
    os_image = ROOT / 'S760224.IMG'
    if not all(p.is_file() for p in (exe, rom, os_image)):
        pytest.skip('Native MAME, original boot ROM and OS image required')

    media = tmp_path / 'roms/s760'
    media.mkdir(parents=True)
    shutil.copyfile(os_image, media / 's760224.img')
    script = tmp_path / 'observer.lua'
    script.write_text(OBSERVER, encoding='utf-8')
    env = {k: v for k, v in os.environ.items() if not k.startswith('S760_')}
    env.update(S760_ROM_BOOT=str(rom), S760_FLOPPY=str(media / 's760224.img'),
               S760_NATIVE_VALUE_ENCODER='1')
    result = subprocess.run(
        [str(exe), 's760', '-rompath', str(tmp_path / 'roms'),
         '-nvram_directory', str(tmp_path / 'nvram'), '-cfg_directory', str(tmp_path / 'cfg'),
         '-video', 'none', '-sound', 'none', '-skip_gameinfo', '-nothrottle',
         '-seconds_to_run', '30', '-autoboot_delay', '0', '-autoboot_script', str(script),
         '-debug', '-debugger', 'none'], cwd=tmp_path, env=env,
        capture_output=True, text=True, timeout=60,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    output = result.stdout + result.stderr
    (tmp_path / 'console.log').write_text(output, encoding='utf-8')
    assert result.returncode == 0, output
    assert 'LUA ERROR' not in output.upper(), output
    assert '[FETCH-CONTROL] fetch=0790 data=03f0' in output, output
    # A differing data view is the negative control; don't repair it to pass.
    assert '[DATA-BYTES] 00 00 00' in output, output
    assert re.search(r'\[HISTORY\] 4[Bb]1[Dd]:\s+ldb\s+da,\s*\[28\]\+', output, re.I), output
    assert '[FETCH-BYTES] b2 29 da' in output, output

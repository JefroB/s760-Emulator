"""Original ROM command-phase transfer regression using ordinary setup input."""
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_rom_scsi_command_counter_and_completion(tmp_path):
    exe = Path(os.environ.get('S760_MAME_EXE', ROOT / 'mame-source/mames760.exe'))
    rom = ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN'
    os_image = ROOT / 'S760224.IMG'
    hd = ROOT / 'roms/SCSI/HD00_512.img'
    if not all(p.is_file() for p in (exe, rom, os_image, hd)):
        pytest.skip('Native MAME, original boot ROM, OS and HD fixture required')
    # Reuse the recorded ordinary panel sequence, not saved guest RAM or PC.
    evidence = json.loads((ROOT / 'docs/condensed/validation/ic15-native-scsi-command-contract-2026-10-16.json').read_text())
    source = evidence['observer_and_input_source']
    source += r'''
local completed=0 local active=0
contract_status=space:install_read_tap(0xe408,0xe40d,'command-contract',function(a,d,m)
 local pc=cpu.state['PC'].value
 if a==0xe40c and pc==0x25b8 and (d&0xf0)==0xb0 then active=active+1 end
 if a==0xe408 and pc==0x2586 and (d&0x10)~=0 then
  assert(space:read_u8(0xe418)==0 and space:read_u8(0xe41a)==0 and space:read_u8(0xe41c)==0,'SPC command counter did not complete')
  completed=completed+1
 end
end)
emu.register_frame_done(function()
 if frames==1740 then
  assert(active>0 and completed>0,'ROM command transfer never completed')
  print(string.format('[COMMAND-CONTRACT] active=%d completed=%d',active,completed))
 end
end)
'''
    lua = tmp_path / 'command.lua'
    lua.write_text(source)
    rd = tmp_path / 'roms/s760'
    rd.mkdir(parents=True)
    shutil.copyfile(os_image, rd / 's760224.img')
    (rd / 'invalid.img').write_bytes(bytes(1474560))
    sd = tmp_path / 'roms/SCSI'
    sd.mkdir()
    shutil.copyfile(hd, sd / hd.name)
    env = {k: v for k, v in os.environ.items() if not k.startswith('S760_')}
    env.update(S760_ROM_BOOT=str(rom), S760_FLOPPY=str(rd / 'invalid.img'), S760_NATIVE_VALUE_ENCODER='1')
    cmd = [str(exe), 's760', '-rompath', str(tmp_path / 'roms'), '-nvram_directory', str(tmp_path / 'nvram'),
           '-cfg_directory', str(tmp_path / 'cfg'), '-video', 'none', '-sound', 'none', '-skip_gameinfo',
           '-nothrottle', '-seconds_to_run', '30', '-autoboot_delay', '0', '-autoboot_script', str(lua)]
    p = subprocess.run(cmd, cwd=tmp_path, env=env, capture_output=True, text=True, timeout=90,
                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    output = p.stdout + p.stderr
    (tmp_path / 'console.log').write_text(output)
    assert p.returncode == 0, output[-4000:]
    assert '[COMMAND-CONTRACT]' in output, output[-4000:]
    assert 'LUA ERROR' not in output.upper(), output[-4000:]
    assert 'pc=25f2 addr=e414' in output
    assert 'pc=24c7 addr=e404 value=00e0' in output

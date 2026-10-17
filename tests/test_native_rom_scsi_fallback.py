"""Ordinary original-ROM failure recovery with private unchanged media."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('target', ['absent', 'bad_header'])
def test_scsi_failure_falls_back_to_original_floppy(target, tmp_path):
    exe = Path(os.environ.get('S760_MAME_EXE', ROOT / 'mame-source/mames760.exe'))
    rom = ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN'
    disk = ROOT / 'S760224.IMG'
    hd = ROOT / 'roms/SCSI/HD00_512.img'
    if not all(p.is_file() for p in (exe, rom, disk)) or target == 'bad_header' and not hd.is_file():
        pytest.skip('Local native firmware/media fixtures required')
    name = 'ic15-native-scsi-absent-fallback-2026-10-16.json' if target == 'absent' else 'ic15-native-scsi-bad-header-fallback-2026-10-16.json'
    source = json.loads((ROOT / 'docs/condensed/validation' / name).read_text(encoding='utf-8'))['observer_and_input_source']
    # Observe the actual selection when Exit is pressed. Periodic STATE output
    # can miss stage 3 entirely when otherwise-correct instruction timing changes.
    exit_event = "elseif stage==3 and cooldown==0 then pulse(exit,'Exit') stage=4 end"
    assert source.count(exit_event) == 1
    source = source.replace(exit_event,
        "elseif stage==3 and cooldown==0 then "
        "print(string.format('[SELECTED-SCSI0] field=%02x boot=%02x',"
        "space:read_u8(0x4d30),space:read_u8(0x4caf))) "
        "pulse(exit,'Exit') stage=4 end")
    script = tmp_path / 'ordinary-input.lua'
    script.write_text(source, encoding='utf-8')
    rd = tmp_path / 'roms/s760'
    rd.mkdir(parents=True)
    shutil.copyfile(disk, rd / 's760224.img')
    sd = tmp_path / 'roms/SCSI'
    sd.mkdir()
    if target == 'bad_header':
        shutil.copyfile(hd, sd / hd.name)
    env = {k:v for k,v in os.environ.items() if not k.startswith('S760_')}
    env.update(S760_ROM_BOOT=str(rom), S760_FLOPPY=str(rd / 's760224.img'), S760_NATIVE_VALUE_ENCODER='1')
    cmd = [str(exe), 's760', '-rompath', str(tmp_path/'roms'), '-nvram_directory', str(tmp_path/'nvram'),
           '-cfg_directory', str(tmp_path/'cfg'), '-video', 'none', '-sound', 'none', '-skip_gameinfo', '-nothrottle',
           '-seconds_to_run', '30', '-autoboot_delay', '0', '-autoboot_script', str(script)]
    p = subprocess.run(cmd, cwd=tmp_path, env=env, capture_output=True, text=True, timeout=90,
                       creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    output = p.stdout+p.stderr
    (tmp_path/'console.log').write_text(output,encoding='utf-8')
    assert p.returncode == 0, output[-4000:]
    assert 'LUA ERROR' not in output.upper(), output[-4000:]
    assert '[SELECTED-SCSI0] field=01 boot=02' in output, 'Ordinary menu did not select SCSI0'
    handoffs = re.findall(r'\[HANDOFF\] pc=4755 value=0000 mask=ffff',output)
    assert len(handoffs)==1, 'Original ROM did not hand off exactly once'
    assert '[LAST-BOOT] pc=4432 value=08' in output, 'Fallback did not publish floppy boot source'
    if target == 'absent':
        assert re.search(r'\[TIMEOUT\] pc=237[0f] value=0004',output)
    else:
        assert '[HEADER-FIRST] pc=4613 value=0053 mask=00ff' in output
    assert (rd/'s760224.img').read_bytes()==disk.read_bytes()

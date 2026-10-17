"""Native Boot-ROM SCSI payload DMA and OS handoff regression test (BUG-082)."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_rom_scsi_payload_dma_and_handoff(tmp_path):
    exe = Path(os.environ.get('S760_MAME_EXE', ROOT / 'mame-source/mames760.exe'))
    rom = ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN'
    os_image = ROOT / 'S760224.IMG'
    hd_fixture = ROOT / 'roms/SCSI/HD00_512.img'
    val_json = ROOT / 'docs/condensed/validation/ic15-native-scsi-valid-header-2026-10-16.json'

    if not all(p.is_file() for p in (exe, rom, os_image, hd_fixture, val_json)):
        pytest.skip('Native MAME, boot ROM, OS image, HD fixture, and validation spec required')

    evidence = json.loads(val_json.read_text(encoding='utf-8'))
    lua_source = evidence['observer_and_input_source']

    script = tmp_path / 'scsi-boot.lua'
    script.write_text(lua_source, encoding='utf-8')

    rd = tmp_path / 'roms/s760'
    rd.mkdir(parents=True)
    shutil.copyfile(os_image, rd / 's760224.img')
    (rd / 'invalid.img').write_bytes(bytes(1474560))

    sd = tmp_path / 'roms/SCSI'
    sd.mkdir(parents=True)
    disk = bytearray(hd_fixture.read_bytes())
    disk[:16] = bytes.fromhex('0000000053373730204d523235410040')
    payload = os_image.read_bytes()[0x4800:0x100800]
    disk[4 * 512:4 * 512 + len(payload)] = payload
    disk[0x15ac * 512:0x15ac * 512 + 0x7c000] = payload[0x80000:]
    (sd / 'HD00_512.img').write_bytes(disk)

    cd = ROOT / 'roms/SCSI/CD10_2048.iso'
    if cd.is_file():
        shutil.copyfile(cd, sd / cd.name)

    env = {k: v for k, v in os.environ.items() if not k.startswith('S760_')}
    env.update(
        S760_ROM_BOOT=str(rom),
        S760_FLOPPY=str(rd / 'invalid.img'),
        S760_NATIVE_VALUE_ENCODER='1',
    )

    cmd = [
        str(exe), 's760',
        '-rompath', str(tmp_path / 'roms'),
        '-nvram_directory', str(tmp_path / 'nvram'),
        '-cfg_directory', str(tmp_path / 'cfg'),
        '-video', 'none',
        '-sound', 'none',
        '-skip_gameinfo',
        '-nothrottle',
        '-seconds_to_run', '30',
        '-autoboot_delay', '0',
        '-autoboot_script', str(script),
        '-log'
    ]

    p = subprocess.run(
        cmd,
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    )

    output = p.stdout + p.stderr
    (tmp_path / 'console.log').write_text(output, encoding='utf-8')

    assert p.returncode == 0, output[-4000:]
    assert 'LUA ERROR' not in output.upper(), output[-4000:]

    # Verify that large DMA was initiated with 512KB count (0x080000)
    assert '[LARGE-DMA] pc=269d encoded=0000 tc=080000' in output

    # Verify that DMA completed and unblocked the ROM loop to execute handoff
    assert '[HANDOFF] pc=4755 value=0000 mask=ffff' in output

    # Verify that the loaded OS executed and is running its bank trampolines
    assert '[HANDOFF] pc=cdd9 value=0000 mask=ffff' in output
    assert '[HANDOFF] pc=cdec value=0000 mask=ffff' in output

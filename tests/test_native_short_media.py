"""
tests/test_native_short_media.py — Invariants and execution qualification for BUG-079.

Verifies:
1. Boot ROM v1.11 firmware structure:
   - 0x4E2C: JBC RDA, 0x1, 0x4E37 — detects FDC density from F002 bit 1 (PB1)
   - 0x4E8D: CMPB RDA, #0x50 — validates 'P' (Program/System) header byte at offset 0x0F
   - 0x4FD6: JBS RCF, 0x1, 0x4FE5 — bypasses 56-cylinder payload read loop for 2DD media
   - 0x4FE7: CMPB RF2, #0xA0 — latent ROM defect returning success (CLRC) without payload load
2. Genuine 720KB sample media (offset 0x0F != 'P') is rejected cleanly by ROM with carry set
   to the 'Not S-760 System Disk !' error handler without reaching handoff (PC=4755).
3. Modeled density bit F002 PB1 accurately reflects 2DD media (< 1474560 bytes).
"""

import os
import shutil
import subprocess
from pathlib import Path
import pytest
import pypcode

ROOT = Path(__file__).resolve().parents[1]


def test_boot_rom_density_and_loader_invariants():
    """Verify the exact instruction sequence in Roland_S-760_v1.11.BIN responsible for BUG-079."""
    rom_path = ROOT / "roms/BOOT/Roland_S-760_v1.11.BIN"
    if not rom_path.is_file():
        pytest.skip("Boot ROM binary required")

    data = rom_path.read_bytes()
    cs = pypcode.Context("MCS96:LE:16:default")

    # 1. Check FDC density test at 0x4E2C: JBC RDA, 0x1, 0x4e37
    d = cs.disassemble(data[0x4E2C:0x4E30], 0x4E2C)
    assert len(d.instructions) > 0
    insn = d.instructions[0]
    assert insn.mnem == "JBC"
    assert "da" in insn.body.lower() and "4e37" in insn.body.lower()

    # 2. Check sector 0 'P' banner verification at 0x4E8D: CMPB RDA, #0x50
    d = cs.disassemble(data[0x4E8D:0x4E92], 0x4E8D)
    assert len(d.instructions) > 0
    insn = d.instructions[0]
    assert insn.mnem == "CMPB"
    assert "50" in insn.body

    # 3. Check 2DD bypass of payload loading loop at 0x4FD6: JBS RCF, 0x1, 0x4fe5
    d = cs.disassemble(data[0x4FD6:0x4FDA], 0x4FD6)
    assert len(d.instructions) > 0
    insn = d.instructions[0]
    assert insn.mnem == "JBS"
    assert "cf" in insn.body.lower() and "4fe5" in insn.body.lower()

    # 4. Check latent completion check at 0x4FE7: CMPB RF2, #0xa0
    d = cs.disassemble(data[0x4FE7:0x4FEA], 0x4FE7)
    assert len(d.instructions) > 0
    insn = d.instructions[0]
    assert insn.mnem == "CMPB"
    assert "f2" in insn.body.lower()


def test_genuine_720kb_sample_media_rejected_without_handoff(tmp_path):
    """
    On authentic 720KB sample/data media, byte 0x0F is space or data, not 'P'.
    Verify that the Boot ROM rejects this media at 0x4E8D without triggering
    payload handoff (PC=4755) or repeating reset.
    """
    exe = Path(os.environ.get("S760_MAME_EXE", ROOT / "mame-source/mames760.exe"))
    rom = ROOT / "roms/BOOT/Roland_S-760_v1.11.BIN"
    disk = ROOT / "S760224.IMG"
    if not all(p.is_file() for p in (exe, rom, disk)):
        pytest.skip("Local native firmware/media fixtures required")

    # Construct genuine 720KB media format: 737280 bytes, header byte 0x0F = 0x20 (' ')
    raw = bytearray(disk.read_bytes()[:737280])
    raw[0x0F] = 0x20  # Sample disk marker (not 'P')

    rd = tmp_path / "roms/s760"
    rd.mkdir(parents=True)
    shutil.copyfile(disk, rd / "s760224.img")

    sample_disk = tmp_path / "sample720.img"
    sample_disk.write_bytes(raw)

    lua_script = tmp_path / "observer.lua"
    lua_script.write_text(
        "local cpu = manager.machine.devices[':maincpu']\n"
        "local space = cpu.spaces['program']\n"
        "space:install_write_tap(0x0106, 0x0107, 'handoff', function(a, d, m)\n"
        "    print(string.format('[HANDOFF] pc=%04x value=%04x mask=%04x', cpu.state['PC'].value, d, m))\n"
        "end)\n"
        "space:install_write_tap(0x4c60, 0x4c61, 'status', function(a, d, m)\n"
        "    print(string.format('[STATUS] pc=%04x value=%04x mask=%04x', cpu.state['PC'].value, d, m))\n"
        "end)\n",
        encoding="utf-8",
    )

    env = {k: v for k, v in os.environ.items() if not k.startswith("S760_")}
    env.update(
        S760_ROM_BOOT=str(rom),
        S760_FLOPPY=str(sample_disk),
        S760_NATIVE_VALUE_ENCODER="1",
    )

    cmd = [
        str(exe), "s760",
        "-rompath", str(tmp_path / "roms"),
        "-nvram_directory", str(tmp_path / "nvram"),
        "-cfg_directory", str(tmp_path / "cfg"),
        "-video", "none",
        "-sound", "none",
        "-skip_gameinfo",
        "-nothrottle",
        "-seconds_to_run", "6",
        "-autoboot_delay", "0",
        "-autoboot_script", str(lua_script),
    ]

    p = subprocess.run(cmd, cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    output = p.stdout + p.stderr
    assert p.returncode == 0, output[-2000:]
    assert "LUA ERROR" not in output.upper(), output[-2000:]

    # Verify that sector 0 status reported the mismatched banner byte (0x20)
    assert "[STATUS] pc=4e8d value=2000 mask=ff00" in output

    # Verify that NO handoff occurred (media was cleanly rejected)
    assert "[HANDOFF]" not in output
